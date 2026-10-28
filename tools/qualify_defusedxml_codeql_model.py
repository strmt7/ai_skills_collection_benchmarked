"""Exercise a CodeQL file-path model with independent positive and negative controls."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

MODEL_NAME = "strmt7/defusedxml-paths"
GENERATED_MODEL_NAME = "generated/extension-pack"
QUERY = "codeql/python-queries:Security/CWE-022/PathInjection.ql"
FIXTURE = """from flask import Flask, request
from defusedxml import ElementTree as A
import defusedxml.ElementTree as B
from defusedxml.ElementTree import parse as C, iterparse as D
import defusedxml.minidom as M
from defusedxml.minidom import parse as N
from defusedxml import pulldom as P
from defusedxml.pulldom import parse as Q
from xml.etree import ElementTree as Standard

app = Flask(__name__)
@app.get('/a')
def a():
    A.parse(request.args['path'])  # positive
    return 'ok'
@app.get('/b')
def b():
    B.parse(source=request.args['path'])  # positive
    return 'ok'
@app.get('/c')
def c():
    C(request.args['path'])  # positive
    return 'ok'
@app.get('/d')
def d():
    A.iterparse(request.args['path'])  # positive
    return 'ok'
@app.get('/e')
def e():
    B.iterparse(source=request.args['path'])  # positive
    return 'ok'
@app.get('/f')
def f():
    D(request.args['path'])  # positive
    return 'ok'
@app.get('/g')
def g():
    M.parse(request.args['path'])  # positive
    return 'ok'
@app.get('/h')
def h():
    N(file=request.args['path'])  # positive
    return 'ok'
@app.get('/i')
def i():
    P.parse(request.args['path'])  # positive
    return 'ok'
@app.get('/j')
def j():
    Q(stream_or_string=request.args['path'])  # positive
    return 'ok'
@app.get('/standard')
def standard():
    Standard.parse(request.args['path'])  # positive-standard
    return 'ok'
@app.get('/safe')
def safe():
    A.parse('fixed.xml')
    M.parse(file='fixed.xml')
    P.parse('fixed.xml')
    return 'ok'
@app.get('/content')
def content():
    M.parseString(request.args['xml'])
    return 'ok'
"""


def run_command(command: list[str], log: Path) -> None:
    """Run CodeQL and retain its native output for diagnosis."""
    result = subprocess.run(command, capture_output=True, timeout=300, check=False)
    log.write_bytes(result.stdout + b"\n" + result.stderr)
    if result.returncode:
        raise RuntimeError(f"CodeQL command failed; see {log.name}")


def model_names(analysis_run: dict[str, object]) -> set[str]:
    """Return model packs identified in a SARIF run."""
    tool = analysis_run["tool"]
    if not isinstance(tool, dict):
        raise ValueError("Invalid CodeQL tool metadata")
    return {
        entry["name"]
        for entry in tool.get("extensions", [])
        if entry.get("properties", {}).get("isCodeQLModelPack") is True
    }


def require_successful_invocations(analysis_run: dict[str, object]) -> None:
    """Reject missing or failed CodeQL invocations."""
    invocations = analysis_run.get("invocations", [])
    if not isinstance(invocations, list) or not invocations:
        raise ValueError("CodeQL did not report successful execution")
    if any(inv.get("executionSuccessful") is not True for inv in invocations):
        raise ValueError("CodeQL did not report successful execution")
    if any(n.get("level") == "error" for inv in invocations for n in inv.get("toolExecutionNotifications", [])):
        raise ValueError("CodeQL reported an analysis error")


def locations(path: Path) -> tuple[set[int], set[str]]:
    """Read and validate control result locations and model metadata."""
    data = json.loads(path.read_text(encoding="utf-8"))
    runs = data["runs"]
    if len(runs) != 1:
        raise ValueError("Expected exactly one CodeQL run")
    require_successful_invocations(runs[0])
    rows = runs[0].get("results", [])
    if any(r.get("ruleId") != "py/path-injection" for r in rows):
        raise ValueError("Unexpected rule in path-injection control")
    physical_locations = [r["locations"][0]["physicalLocation"] for r in rows]
    if any(location["artifactLocation"].get("uri") != "fixture.py" for location in physical_locations):
        raise ValueError("Unexpected source file in path-injection control")
    positions = [location["region"]["startLine"] for location in physical_locations]
    if len(positions) != len(set(positions)):
        raise ValueError("Duplicate path-injection results")
    return set(positions), model_names(runs[0])


def verify_analysis(directory: Path) -> dict[str, object]:
    """Verify the required model was recorded in successful analysis runs."""
    files = sorted(directory.glob("*.sarif"))
    if not files:
        raise ValueError("No CodeQL analysis SARIF files found")
    checked = 0
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        runs = data.get("runs", [])
        if not runs:
            raise ValueError(f"No CodeQL runs in {path.name}")
        for analysis_run in runs:
            require_successful_invocations(analysis_run)
            if GENERATED_MODEL_NAME not in model_names(analysis_run):
                raise ValueError(f"Required model pack absent from {path.name}")
            checked += 1
    return {"passed": True, "analysis_runs_checked": checked, "model": GENERATED_MODEL_NAME}


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codeql", help="CodeQL executable path for native controls")
    parser.add_argument("--model", type=Path, help="Local model pack directory for native controls")
    parser.add_argument("--output", type=Path, help="New directory for native control evidence")
    parser.add_argument("--analysis-dir", type=Path, help="Verify the model is present in hosted analysis SARIF")
    return parser


def qualify(args: argparse.Namespace) -> dict[str, object]:
    """Run baseline and model controls and save their evidence."""
    output = args.output.absolute()
    output.mkdir(parents=False, exist_ok=False)
    fixture_dir = output / "fixture"
    fixture_dir.mkdir()
    fixture = fixture_dir / "fixture.py"
    fixture.write_text(FIXTURE, encoding="utf-8", newline="\n")
    expected = {i for i, line in enumerate(FIXTURE.splitlines(), 1) if "# positive" in line}
    if len(expected) != 11:
        raise ValueError("Control fixture must contain all 11 positive cases")
    standard_cases = [i for i, line in enumerate(FIXTURE.splitlines(), 1) if "# positive-standard" in line]
    if len(standard_cases) != 1:
        raise ValueError("Control fixture must contain one standard-library case")
    standard = standard_cases[0]
    db = output / "database"
    base = [args.codeql, "database", "analyze", str(db), QUERY, "--threads", "2", "--ram", "3072"]
    run_command(
        [
            args.codeql,
            "database",
            "create",
            str(db),
            "--language",
            "python",
            "--source-root",
            str(fixture_dir),
            "--threads",
            "2",
            "--ram",
            "3072",
        ],
        output / "create.log",
    )
    baseline = output / "baseline.sarif"
    modeled = output / "modeled.sarif"
    run_command(base + ["--format", "sarifv2.1.0", "--output", str(baseline)], output / "baseline.log")
    run_command(
        base
        + [
            "--rerun",
            "--format",
            "sarifv2.1.0",
            "--output",
            str(modeled),
            "--additional-packs",
            str(args.model.resolve()),
            "--model-packs",
            MODEL_NAME + "@0.0.1",
        ],
        output / "modeled.log",
    )
    old, _ = locations(baseline)
    new, packs = locations(modeled)
    if standard not in old or not old <= expected or new != expected or MODEL_NAME not in packs:
        raise ValueError(
            f"Model control failed: expected={sorted(expected)} baseline={sorted(old)} modeled={sorted(new)}"
        )
    discovered_model = fixture_dir / ".github/codeql/extensions/defusedxml-paths"
    discovered_model.parent.mkdir(parents=True)
    shutil.copytree(args.model, discovered_model)
    config = output / "code-scanning.yml"
    config.write_text("queries: [{uses: security-extended}]\n", encoding="utf-8")
    discovered_db = output / "discovered-database"
    run_command(
        [
            args.codeql,
            "database",
            "create",
            str(discovered_db),
            "--language",
            "python",
            "--source-root",
            str(fixture_dir),
            "--codescanning-config",
            str(config),
            "--threads",
            "2",
            "--ram",
            "3072",
        ],
        output / "discovered-create.log",
    )
    discovered = output / "discovered.sarif"
    run_command(
        [
            args.codeql,
            "database",
            "analyze",
            str(discovered_db),
            QUERY,
            "--threads",
            "2",
            "--ram",
            "3072",
            "--format",
            "sarifv2.1.0",
            "--output",
            str(discovered),
        ],
        output / "discovered.log",
    )
    found, generated_packs = locations(discovered)
    generated_sinks = discovered_db / "temp/extension-pack/extensions/defusedxml-paths/models/sinks.yml"
    if (
        found != expected
        or GENERATED_MODEL_NAME not in generated_packs
        or generated_sinks.read_bytes() != (args.model / "models/sinks.yml").read_bytes()
    ):
        raise ValueError("Automatically discovered model control failed")
    receipt = {
        "passed": True,
        "expected_cases": len(expected),
        "baseline_cases": len(old),
        "modeled_cases": len(new),
        "discovered_cases": len(found),
        "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
        "modeled_sha256": hashlib.sha256(modeled.read_bytes()).hexdigest(),
        "discovered_sha256": hashlib.sha256(discovered.read_bytes()).hexdigest(),
        "model_pack_sha256": hashlib.sha256((args.model / "codeql-pack.yml").read_bytes()).hexdigest(),
        "model_sinks_sha256": hashlib.sha256((args.model / "models/sinks.yml").read_bytes()).hexdigest(),
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main(argv: list[str] | None = None) -> int:
    """Run controls or verify an existing repository analysis."""
    args = build_parser().parse_args(argv)
    try:
        if args.analysis_dir is not None:
            if args.codeql is not None or args.model is not None or args.output is not None:
                raise ValueError("Analysis verification cannot be combined with native control options")
            result = verify_analysis(args.analysis_dir)
        else:
            if args.codeql is None or args.model is None or args.output is None:
                raise ValueError("Native controls require --codeql, --model and --output")
            result = qualify(args)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())

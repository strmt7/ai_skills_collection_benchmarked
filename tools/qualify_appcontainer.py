"""Run native confinement controls and validator controls; never a model score."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any

import appcontainer_runtime as runtime
import grade_validator_appcontainer as grader
from _windows_appcontainer import Native, checked_path, checked_tree, run_appcontainer

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "artifacts/agent-trials/development-v2/repetition-1/default/submission"
PROBE = ROOT / "tools/appcontainer_access_probe.py"
PUBLISHED = ROOT / "artifacts/component-controls/appcontainer"
SOURCE_FILES = (
    *grader.TRUSTED_FILES,
    *grader.TASK_FILES,
    "tools/qualify_appcontainer.py",
    "tools/appcontainer_access_probe.py",
    "artifacts/agent-trials/development-v2/repetition-1/default/submission/tools/check_benchmark_artifact.py",
)
LIMITS = {
    "exit_status": ("raise SystemExit(7)", 7, None),
    "timeout": ("import time; time.sleep(30)", 124, "timeout"),
    "output": ("import os\nwhile True:\n os.write(1, b'x'*8192)", 125, "output_limit"),
    "memory": ("try:\n x=bytearray(512*1024*1024)\nexcept MemoryError:\n print('memory denied')", 0, None),
    "child": (
        "import subprocess,sys\ntry:\n subprocess.run([sys.executable,'-c','pass'],check=True)\n"
        "except OSError:\n print('child denied')",
        0,
        None,
    ),
}


def access_controls(home: Path, output: Path) -> dict[str, Any]:
    output.mkdir()
    readable, sealed, scratch = [output / name for name in ("readable", "sealed", "scratch")]
    for directory in (readable, sealed, scratch):
        directory.mkdir()
    script = readable / PROBE.name
    shutil.copyfile(PROBE, script)
    allowed, oracle = readable / "allowed.txt", sealed / "oracle.txt"
    allowed.write_text("permitted", encoding="utf-8")
    oracle.write_text("owned sealed sentinel", encoding="utf-8")
    native = Native()
    owner = native.owner_sid()
    original = {p: native.descriptor(p) for p in [home / "runtime", *checked_tree(home / "runtime")]}
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(2)
        listener.settimeout(2)
        arguments = [
            "-I",
            "-S",
            "-B",
            str(script),
            str(allowed),
            str(oracle),
            str(scratch),
            str(os.getpid()),
            str(listener.getsockname()[1]),
        ]
        normal = subprocess.run([str(home / "runtime/python.exe"), *arguments], capture_output=True, timeout=10)
        (output / "normal.stdout.native").write_bytes(normal.stdout)
        (output / "normal.stderr.native").write_bytes(normal.stderr)
        reference = json.loads(normal.stdout)
        connection, _ = listener.accept()
        connection.close()
        if normal.returncode or any(
            reference[key] for key in ["sealed_read_denied", "parent_memory_access_denied", "readonly_write_denied"]
        ):
            raise ValueError("The normal-process access control failed")
        if reference["network_connect_status"] != 0 or reference["sealed_dacl_change_status"] != 0:
            raise ValueError("The normal-process network or ACL control failed")
        # The matched normal control deliberately changed these owned sentinels.
        allowed.write_text("permitted", encoding="utf-8")
        native.grant(sealed, owner, None)
        native.grant(oracle, owner, None)
        confined_scratch = output / "confined-scratch"
        confined_scratch.mkdir()
        arguments[6] = str(confined_scratch)
        process = run_appcontainer(
            home / "runtime/python.exe",
            arguments,
            workspace=ROOT / ".venv",
            readable=[home / "runtime", readable],
            scratch=confined_scratch,
            output=output / "confined",
        )
        actual = json.loads((output / "confined/stdout.native").read_bytes())
        listener.settimeout(0.25)
        try:
            connection, _ = listener.accept()
            connection.close()
            network_received = True
        except TimeoutError:
            network_received = False
    expected = [
        "allowed_read",
        "sealed_read_denied",
        "parent_memory_access_denied",
        "readonly_write_denied",
        "scratch_write",
    ]
    if process["exit_code"] or not all(actual[key] for key in expected):
        raise ValueError("Confined filesystem or process-memory access control failed")
    if actual["sealed_dacl_change_status"] != 5 or actual["parent_open_error"] != 5:
        raise ValueError("Confined ACL or process-memory denial was not observed")
    if actual["network_connect_status"] == 0 or network_received:
        raise ValueError("A confined connection reached the owned loopback listener")
    if oracle.read_text() != "owned sealed sentinel" or allowed.read_text() != "permitted":
        raise ValueError("A read-only sentinel changed")
    if any(native.descriptor(path) != value for path, value in original.items()):
        raise ValueError("Runtime ACLs were not restored exactly")
    return {"normal": reference, "confined": actual, "process": process, "connection_received": network_received}


def limit_controls(home: Path, output: Path) -> dict[str, Any]:
    output.mkdir()
    observations = {}
    for name, (code, status, reason) in LIMITS.items():
        scratch = output / (name + "-scratch")
        scratch.mkdir()
        process = run_appcontainer(
            home / "runtime/python.exe",
            ["-I", "-S", "-B", "-c", code],
            workspace=ROOT / ".venv",
            readable=[home / "runtime"],
            scratch=scratch,
            output=output / name,
            timeout=1 if name == "timeout" else 5,
            output_limit=65536,
        )
        observed = (output / name / "stdout.native").read_bytes()
        if process["exit_code"] != status or process["termination_reason"] != reason:
            raise ValueError(f"Native resource control failed: {name}")
        if name in {"memory", "child"} and observed.strip() != (name + " denied").encode():
            raise ValueError(f"Native denial sentinel missing: {name}")
        if name == "output" and process["output_bytes"] != 65537:
            raise ValueError("Output overflow evidence must include exactly one byte beyond the budget")
        observations[name] = process
    return observations


def candidate_controls(home: Path, output: Path, revision: str) -> dict[str, Any]:
    output.mkdir()
    frame = (
        "import inspect\nfrom pathlib import Path\nSCHEMA_PATH=Path('unused')\n"
        "def validate_artifact(path):\n expected=inspect.currentframe().f_back.f_locals['expected_complete']\n"
        " return {'verdict':'artifact_complete' if expected else 'artifact_invalid',"
        "'errors':[] if expected else ['oracle'],'warnings':[]}\n"
    )
    stub = "def validate_artifact(path):\n return {'verdict':'artifact_complete','errors':[],'warnings':[]}\n"
    result = {}
    for name, source, expected in [("reference", None, 17), ("frame_oracle", frame, 0), ("always_complete", stub, 2)]:
        submission = REFERENCE
        if source is not None:
            submission = output / (name + "-submission")
            (submission / "tools").mkdir(parents=True)
            (submission / "tools/check_benchmark_artifact.py").write_text(source, encoding="utf-8")
        observed = grader.grade(submission, ROOT, home, output / name, revision)
        result[name] = {
            key: observed[key] for key in ["status", "checks_passed", "checks_total", "agent_performance_claim"]
        }
        if observed["checks_passed"] != expected or observed["checks_total"] != 17:
            raise ValueError(f"Validator control failed: {name}")
    return result


def qualify(home: Path, output: Path, revision: str) -> dict[str, Any]:
    grader.common_workspace(home, output)
    sources = source_graph()
    output.mkdir(parents=True, exist_ok=False)
    pin = json.loads(runtime.SOURCE.read_bytes())
    if errors := runtime.verify(home, pin):
        raise ValueError("; ".join(errors))
    result = {
        "measurement_kind": "native_confinement_component_controls",
        "runtime_version": pin["version"],
        "access": access_controls(home, output / "access"),
        "limits": limit_controls(home, output / "limits"),
        "validators": candidate_controls(home, output / "validators", revision),
        "independent_model_trials": 0,
        "agent_performance_claim": False,
        "source_sha256": sources,
        "fixture_commit": revision,
    }
    if sources != source_graph() or runtime.verify(home, pin):
        raise ValueError("Qualification inputs changed during the control campaign")
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def source_graph() -> list[dict[str, str]]:
    return [{"path": name, "sha256": runtime.digest(ROOT / name)} for name in SOURCE_FILES]


def observed_files(output: Path) -> list[Path]:
    """Select trusted observations explicitly; never enumerate candidate scratch."""
    files = [output / "result.json", output / "access/normal.stdout.native", output / "access/normal.stderr.native"]
    native = [output / "access/confined", *[output / "limits" / name for name in LIMITS]]
    for control in ("reference", "frame_oracle", "always_complete"):
        directory = output / "validators" / control
        files.extend([directory / "result.json", directory / "checks.json"])
        checks = json.loads((directory / "checks.json").read_bytes())
        for check in checks:
            name = check["observation_directory"]
            if not re.fullmatch(r"case-[0-9a-f]{32}/observations", name):
                raise ValueError("Unexpected native observation path")
            native.append(directory / name)
    for directory in native:
        files.extend(directory / name for name in ("profile.json", "process.json", "stdout.native", "stderr.native"))
    return files


def verify_campaign(directory: Path) -> list[str]:
    errors = []
    result = json.loads((directory / "result.json").read_bytes())
    if result.get("source_sha256") != source_graph():
        errors.append("Native qualification source graph is stale")
    if result.get("agent_performance_claim") is not False or result.get("independent_model_trials") != 0:
        errors.append("Component evidence must not claim model performance")
    for path in observed_files(directory):
        checked_path(path)
        if path.name != "process.json":
            continue
        process = json.loads(path.read_bytes())
        expected = {
            "appcontainer": True,
            "capability_count": 0,
            "integrity_sid": "S-1-16-4096",
            "attested_while_suspended": True,
            "assigned_before_resume": True,
            "windows_job": True,
            "kill_on_close": True,
            "active_process_limit": 1,
            "active_processes_after_cleanup": 0,
            "profile_deleted": True,
            "readonly_acls_restored": True,
            "cleanup_errors": [],
        }
        if any(
            type(process.get(key)) is not type(value) or process.get(key) != value for key, value in expected.items()
        ):
            errors.append(f"Native process policy failed: {path.relative_to(directory)}")
        size = sum((path.parent / name).stat().st_size for name in ["stdout.native", "stderr.native"])
        if process.get("output_bytes") != size:
            errors.append(f"Native output byte count differs: {path.relative_to(directory)}")
    errors.extend(verify_scores(directory))
    return errors


def verify_scores(directory: Path) -> list[str]:
    errors = []
    catalog = json.loads((ROOT / "data/skills_catalog.json").read_bytes())[0]
    expected_cases = {name: expected for name, _, expected, _ in grader.cases(catalog, "0" * 40)}
    for name, total in [("reference", 17), ("frame_oracle", 0), ("always_complete", 2)]:
        control = directory / "validators" / name
        result = json.loads((control / "result.json").read_bytes())
        checks = json.loads((control / "checks.json").read_bytes())
        if {row["case"] for row in checks} != expected_cases.keys() or len(checks) != len(expected_cases):
            errors.append(f"Validator case graph differs: {name}")
            continue
        count = 0
        for row in checks:
            native = control / row["observation_directory"]
            process = json.loads((native / "process.json").read_bytes())
            response = grader.parse_response(native / "stdout.native")
            passed = (
                process["exit_code"] == 0
                and process["termination_reason"] is None
                and grader.accepted(response, expected_cases[row["case"]])
            )
            count += passed
            if row["passed"] != passed or row["response"] != response or row["process"] != process:
                errors.append(f"Recorded verdict differs from native response: {name}/{row['case']}")
        if count != total or result.get("checks_passed") != count or result.get("checks_total") != len(checks):
            errors.append(f"Validator control score differs: {name}")
        if result.get("checks") != checks:
            errors.append(f"Validator result and incremental observations differ: {name}")
    return errors


def publish(directory: Path) -> dict[str, Any]:
    grader.common_workspace(directory, directory.parent / (directory.name + "-admission"))
    if errors := verify_campaign(directory):
        raise ValueError("; ".join(errors))
    if PUBLISHED.exists():
        raise ValueError("Published evidence already exists; preserve it and review a new destination")
    PUBLISHED.mkdir(parents=True)
    for source in observed_files(directory):
        target = PUBLISHED / source.relative_to(directory)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    hashes = {path.relative_to(PUBLISHED).as_posix(): runtime.digest(path) for path in observed_files(PUBLISHED)}
    manifest = {
        "schema_version": 1,
        "measurement_kind": "native_confinement_component_controls",
        "agent_performance_claim": False,
        "files_sha256": hashes,
    }
    (PUBLISHED / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "files": len(hashes), "agent_performance_claim": False}


def check() -> dict[str, Any]:
    manifest = json.loads((PUBLISHED / "manifest.json").read_bytes())
    files = observed_files(PUBLISHED)
    actual = {path.relative_to(PUBLISHED).as_posix(): runtime.digest(path) for path in files}
    errors = verify_campaign(PUBLISHED)
    if manifest.get("files_sha256") != actual:
        errors.append("Published native observations differ from their complete selected hash graph")
    return {"ok": not errors, "errors": errors, "files": len(files), "agent_performance_claim": False}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-home", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--revision")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--publish", type=Path, help="Admit a private campaign without reading candidate scratch")
    mode.add_argument("--check", action="store_true", help="Check retained evidence and source/observation hashes")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.check:
            status = check()
        elif args.publish:
            status = publish(checked_path(args.publish))
        else:
            if not args.runtime_home or not args.output or not args.revision:
                raise ValueError("A native campaign requires --runtime-home, --output and --revision")
            result = qualify(checked_path(args.runtime_home), checked_path(args.output), args.revision)
            status = {"ok": True, "runtime_version": result["runtime_version"], "validators": result["validators"]}
        print(json.dumps(status))
        return int(not status["ok"])
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"ok": False, "errors": [str(error)], "agent_performance_claim": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

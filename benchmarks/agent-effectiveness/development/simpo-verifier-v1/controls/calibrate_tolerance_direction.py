"""Calibrate trusted SimPO tolerance controls; do not grade agent submissions."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as et
from pathlib import Path

import calibrate as prior
import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
ROOT = TASK.parents[3]
CASES = {
    f"test_asymmetric_tolerance[{delta}-{accepted}-{phase}]"
    for delta, accepted in (("6.00003e-06", "True"), ("-5.99997e-06", "False"))
    for phase in ("initial", "regenerated")
}
OLD = {"initial": "np.allclose(expected, initial,", "regenerated": "np.allclose(expected, regenerated,"}
NEW = {"initial": "np.allclose(initial, expected,", "regenerated": "np.allclose(regenerated, expected,"}


def verify_xml(path: Path, cases: set[str], expected: set[str], exit_code: int) -> list[str]:
    """Check exact case identities and expected outcomes in the native JUnit result."""
    records = list(et.parse(path).iter("testcase"))
    names = [record.attrib["name"] for record in records]
    failed = {record.attrib["name"] for record in records if record.find("failure") is not None}
    if (
        set(names) != cases
        or len(names) != len(cases)
        or failed != expected
        or any(record.find("error") is not None or record.find("skipped") is not None for record in records)
        or exit_code != int(bool(expected))
    ):
        raise ValueError("Native test results differ from the planned control outcomes")
    return sorted(failed)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New directory for local control evidence")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    dependencies = {
        name: importlib.metadata.version(name)
        for name in ("numpy", "pytest", "iniconfig", "packaging", "pluggy", "pygments")
    }
    if os.name == "nt":
        dependencies["colorama"] = importlib.metadata.version("colorama")
    expected_dependencies = {
        "numpy": "2.5.4",
        "pytest": "9.1.1",
        "iniconfig": "2.3.1",
        "packaging": "26.3",
        "pluggy": "1.7.0",
        "pygments": "2.21.0",
    }
    if os.name == "nt":
        expected_dependencies["colorama"] = "0.4.6"
    if platform.python_version() != "3.13.18" or sys.prefix == sys.base_prefix or dependencies != expected_dependencies:
        raise ValueError("Use the locked Python 3.13.18 calibration environment")
    original = TASK / "fixture/test_outputs.py"
    if prior.sha256(original) != prior.ORIGINAL_SHA256:
        raise ValueError("Original fixture differs from its pinned source")
    metadata = json.loads((TASK / "source.json").read_text(encoding="utf-8"))
    if metadata["sha256"] != prior.ORIGINAL_SHA256 or metadata["license_sha256"] != prior.sha256(TASK / "LICENSE"):
        raise ValueError("Source or license provenance differs")
    previous = json.loads(
        (ROOT / "artifacts/research/2026-11-02/simpo-verifier-task-calibration/windows-result.json").read_text(
            encoding="utf-8"
        )
    )
    for name in ("controls/reference.py", "controls/reference_pathlib.py", "controls/test_acceptance.py", "cases.json"):
        if prior.sha256(TASK / name) != previous["inputs_sha256"][name]:
            raise ValueError("Original calibration inputs differ from their retained evidence")
    legacy_cases = json.loads((TASK / "cases.json").read_text(encoding="utf-8"))["cases"]
    if len(legacy_cases) != 17 or len(set(legacy_cases)) != 17:
        raise ValueError("Original case manifest differs")
    inputs = [
        TASK / "TASK.md",
        TASK / "LICENSE",
        TASK / "source.json",
        original,
        TASK / "cases.json",
        HERE / "calibrate.py",
        HERE / "test_acceptance.py",
        HERE / "reference.py",
        HERE / "reference_pathlib.py",
        HERE / "test_tolerance_direction.py",
        HERE / "calibrate_tolerance_direction.py",
        ROOT / "benchmarks/component-controls/simpo-postrun/requirements-windows.txt",
        ROOT / "benchmarks/component-controls/simpo-postrun/requirements-linux.txt",
        ROOT / "artifacts/research/2026-11-02/simpo-verifier-task-calibration/windows-result.json",
    ]
    hashes = {path.relative_to(ROOT).as_posix(): prior.sha256(path) for path in inputs}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    with tempfile.TemporaryDirectory(prefix="simpo-tolerance-calibration-") as directory:
        scratch = Path(directory)
        text = (HERE / "reference.py").read_text(encoding="utf-8")
        if any(text.count(needle) != 1 for needle in OLD.values()):
            raise ValueError("Reference comparison expressions are absent or ambiguous")
        variants = {"reference": HERE / "reference.py", "reference-pathlib": HERE / "reference_pathlib.py"}
        for name, phases in (
            ("reverse-initial", ("initial",)),
            ("reverse-regenerated", ("regenerated",)),
            ("reverse-both", ("initial", "regenerated")),
        ):
            mutated = text
            for phase in phases:
                mutated = mutated.replace(OLD[phase], NEW[phase])
            path = scratch / f"{name}.py"
            path.write_text(mutated, encoding="utf-8", newline="\n")
            variants[name] = path
        for name, path in variants.items():
            phases = (
                ("initial", "regenerated")
                if name == "reverse-both"
                else (name.removeprefix("reverse-"),)
                if name.startswith("reverse-")
                else ()
            )
            expected = {case for case in CASES if any(case.endswith(f"-{phase}]") for phase in phases)}
            controls = [("boundary", HERE / "test_tolerance_direction.py", CASES, expected)]
            if phases:
                controls.append(("legacy", HERE / "test_acceptance.py", set(legacy_cases), set()))
            for suffix, test, cases, expected_failures in controls:
                xml = output / f"{name}-{suffix}.xml"
                env = dict(
                    os.environ,
                    SIMPO_VERIFIER=str(path),
                    PYTHONPATH=str(HERE),
                    PYTHONUTF8="1",
                    PYTHONIOENCODING="utf-8",
                    PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                    PYTHONDONTWRITEBYTECODE="1",
                )
                env.pop("PYTEST_ADDOPTS", None)
                env.pop("PYTEST_PLUGINS", None)
                command = [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-o",
                    "addopts=",
                    "-p",
                    "no:cacheprovider",
                    "--tb=no",
                    f"--basetemp={scratch / (name + '-' + suffix + '-tmp')}",
                    f"--junitxml={xml}",
                    str(test),
                ]
                process = subprocess.run(command, cwd=scratch, env=env, capture_output=True, timeout=120, check=False)
                (output / f"{name}-{suffix}.stdout").write_bytes(process.stdout)
                (output / f"{name}-{suffix}.stderr").write_bytes(process.stderr)
                failed = verify_xml(xml, cases, expected_failures, process.returncode)
                results[f"{name}-{suffix}"] = {
                    "exit_code": process.returncode,
                    "failed_cases": failed,
                    "stdout_sha256": prior.sha256(output / f"{name}-{suffix}.stdout"),
                    "stderr_sha256": prior.sha256(output / f"{name}-{suffix}.stderr"),
                    "junit_sha256": prior.sha256(xml),
                }
    if hashes != {path.relative_to(ROOT).as_posix(): prior.sha256(path) for path in inputs}:
        raise ValueError("Calibration inputs changed during execution")
    result = {
        "schema_version": 1,
        "status": "passed",
        "scope": "Trusted development controls only; not an agent trial or confined grader.",
        "platform": platform.system(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pytest": pytest.__version__,
        "dependencies": dependencies,
        "inputs_sha256": hashes,
        "new_cases": sorted(CASES),
        "legacy_case_count": len(legacy_cases),
        "variants": results,
        "agent_performance_tested": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

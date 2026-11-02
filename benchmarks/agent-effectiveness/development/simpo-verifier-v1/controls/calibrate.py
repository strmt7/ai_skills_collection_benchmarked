"""Calibrate a development task against only its three checked-in controls.

This process imports those trusted controls on the host. It is not a sandbox
and must not be used to grade agent submissions or other untrusted code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as et
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parent
TASK = HERE.parent
ORIGINAL_SHA256 = "05590869057aeaac1032f2177b0b2bf80f56828af3dba66f100e4d1346b2e62f"
ORIGINAL_FAILURES = {
    "test_invalid_input_or_regenerated_output_is_rejected[wrong_initial_key]",
    "test_invalid_input_or_regenerated_output_is_rejected[wrong_values]",
    "test_invalid_input_or_regenerated_output_is_rejected[outside_tolerance]",
    "test_invalid_input_or_regenerated_output_is_rejected[wrong_key]",
    "test_invalid_input_or_regenerated_output_is_rejected[wrong_shape]",
    "test_invalid_input_or_regenerated_output_is_rejected[nonfinite]",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new directory for local command evidence")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    original = TASK / "fixture/test_outputs.py"
    if sha256(original) != ORIGINAL_SHA256:
        raise ValueError("Original fixture does not match the pinned public source")
    cases = json.loads((TASK / "cases.json").read_text(encoding="utf-8"))["cases"]
    if not isinstance(cases, list) or len(cases) != len(set(cases)) or len(cases) != 17:
        raise ValueError("Expected 17 distinct declared cases")
    inputs = [original, HERE / "test_acceptance.py", HERE / "reference.py", HERE / "reference_pathlib.py"]
    results = []
    targets = [("reference", inputs[2]), ("reference_pathlib", inputs[3])]
    if platform.system() == "Linux":
        targets.insert(0, ("original", inputs[0]))
    with tempfile.TemporaryDirectory(prefix="simpo-task-calibration-") as temporary:
        for name, target in targets:
            xml = output / f"{name}.xml"
            env = dict(
                os.environ,
                SIMPO_VERIFIER=str(target),
                PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
                PYTHONDONTWRITEBYTECODE="1",
            )
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
                f"--junitxml={xml}",
                str(HERE / "test_acceptance.py"),
            ]
            process = subprocess.run(command, cwd=temporary, env=env, capture_output=True, timeout=120, check=False)
            (output / f"{name}.stdout").write_bytes(process.stdout)
            (output / f"{name}.stderr").write_bytes(process.stderr)
            if not xml.is_file():
                raise ValueError(f"{name} did not produce test results")
            records = list(et.parse(xml).iter("testcase"))
            names = [record.attrib["name"] for record in records]
            failed = [record.attrib["name"] for record in records if record.find("failure") is not None]
            invalid = any(record.find("error") is not None or record.find("skipped") is not None for record in records)
            expected_failures = ORIGINAL_FAILURES if name == "original" else set()
            if (
                invalid
                or len(names) != len(set(names))
                or set(names) != set(cases)
                or set(failed) != expected_failures
                or process.returncode != (1 if expected_failures else 0)
            ):
                raise ValueError(f"{name} calibration did not match its independently declared outcomes")
            results.append(
                {
                    "control": name,
                    "passed": len(names) - len(failed),
                    "failed_cases": sorted(failed),
                    "stdout_sha256": sha256(output / f"{name}.stdout"),
                    "stderr_sha256": sha256(output / f"{name}.stderr"),
                    "junit_sha256": sha256(xml),
                }
            )
    result = {
        "schema_version": 1,
        "status": "passed",
        "platform": platform.system(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pytest": pytest.__version__,
        "inputs_sha256": {
            path.relative_to(TASK).as_posix(): sha256(path)
            for path in [*inputs, TASK / "cases.json", HERE / "calibrate.py"]
        },
        "controls": results,
        "original_control": "executed" if platform.system() == "Linux" else "not run: Linux source environment",
        "subprocess_simulated": True,
        "live_simpo_training": False,
        "agent_submission_graded": False,
        "sandbox_qualified": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

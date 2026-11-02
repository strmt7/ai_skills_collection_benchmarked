"""Qualify the maintained Python inventory on owned source fixtures."""

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
from importlib.metadata import version
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = ROOT / (
    "included/repaired/skills/by-category/documents-spreadsheets-presentations/"
    "reddit-verified-gtm-registry/docs-from-code-python-inventory/scripts/inventory.py"
)
EXPECTED = {"fastapi": "0.162.0", "flask": "3.1.3", "pytest": "9.2.0"}
GENERIC_CASE = "test_generic_type_parameters_are_retained"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    versions = {name: version(name) for name in EXPECTED}
    if versions != EXPECTED:
        raise ValueError("The installed framework and pytest versions differ from the tested graph")
    cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))["cases"]
    if not isinstance(cases, list) or len(cases) != len(set(cases)) or len(cases) != 25:
        raise ValueError("Expected 25 distinct control cases")
    lock_name = "requirements-windows.txt" if os.name == "nt" else "requirements-linux.txt"
    inputs = [
        SCRIPT,
        HERE / "test_inventory.py",
        HERE / "cases.json",
        HERE / "reproduce.py",
        HERE / lock_name,
        ROOT / "benchmarks/dependency-regressions/docs_from_code_fixture.py",
        ROOT / "benchmarks/dependency-regressions/docs_from_code_controls.py",
    ]
    before = {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in inputs}
    with tempfile.TemporaryDirectory(prefix="docs-python-inventory-") as temporary:
        xml = output / "pytest.xml"
        env = dict(
            os.environ,
            DOCS_INVENTORY_SCRIPT=str(SCRIPT),
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
            "--tb=short",
            f"--junitxml={xml}",
            "--basetemp",
            str(Path(temporary) / "pytest"),
            str(HERE / "test_inventory.py"),
        ]
        process = subprocess.run(command, cwd=temporary, env=env, capture_output=True, timeout=180, check=False)
        (output / "pytest.stdout").write_bytes(process.stdout)
        (output / "pytest.stderr").write_bytes(process.stderr)
    records = list(et.parse(xml).iter("testcase")) if xml.is_file() else []
    names = [record.attrib.get("name") for record in records]
    failures = [record.attrib.get("name") for record in records if record.find("failure") is not None]
    errors = [record.attrib.get("name") for record in records if record.find("error") is not None]
    skipped = [record.attrib.get("name") for record in records if record.find("skipped") is not None]
    expected_skips = {GENERIC_CASE} if sys.version_info < (3, 12) else set()
    status = (
        "passed"
        if process.returncode == 0
        and len(names) == len(set(names))
        and set(names) == set(cases)
        and not failures
        and not errors
        and set(skipped) == expected_skips
        and before == {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in inputs}
        else "failed"
    )
    result: dict[str, Any] = {
        "schema_version": 1,
        "status": status,
        "platform": platform.system(),
        "python": platform.python_version(),
        "versions": versions,
        "inputs_sha256": before,
        "test_cases": len(names),
        "passed_cases": len(names) - len(failures) - len(errors) - len(skipped),
        "skipped_cases": skipped,
        "failed_cases": failures,
        "error_cases": errors,
        "pytest_returncode": process.returncode,
        "stdout_sha256": sha256(output / "pytest.stdout"),
        "stderr_sha256": sha256(output / "pytest.stderr"),
        "junit_sha256": sha256(xml) if xml.is_file() else None,
        "target_project_imported_by_inventory": False,
        "owned_runtime_fixture_executed": True,
        "graphify_executed": False,
        "typescript_fallback_tested": False,
        "agent_performance_tested": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

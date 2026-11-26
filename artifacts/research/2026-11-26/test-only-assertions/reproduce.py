"""Measure coverage and assertion strength on a small dispatch transformation."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.etree import ElementTree

PROGRAM = """def dispatch(rows):
    route = []
    for code, units in rows:
        if units <= 0:
            continue
        route.extend([code] * units)
    return route
"""
PROGRAMS = {
    "reference": PROGRAM,
    "reordered": PROGRAM.replace("return route", "return sorted(route)"),
    "missing_units": PROGRAM.replace("* units", "* min(units, 1)"),
}
TEST = """from dispatch_rows import dispatch


def test_dispatch_lists_units_in_route_order():
    result = dispatch([("B", 2), ("zero", 0), ("A", 1), ("B", 1)])
"""
SUITES = {
    "shape": TEST + "    assert isinstance(result, list) and all(isinstance(code, str) for code in result)\n",
    "behavior": TEST + '    assert result == ["B", "B", "A", "B"]\n',
}


def measure(directory: Path, program: str, suite: str) -> dict:
    directory.mkdir()
    (directory / "dispatch_rows.py").write_text(program, encoding="utf-8", newline="\n")
    (directory / "test_contract.py").write_text(suite, encoding="utf-8", newline="\n")
    environment = dict(os.environ, PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", COVERAGE_FILE=str(directory / ".coverage"))

    def native(arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, "-I", "-B", "-m", "coverage", *arguments],
            cwd=directory,
            env=environment,
            capture_output=True,
            check=False,
            timeout=25,
        )

    test = native(
        [
            "run",
            "--branch",
            "--source=dispatch_rows",
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--junitxml=outcome.xml",
            "test_contract.py",
        ]
    )
    assert test.returncode in (0, 1), test.stderr.decode(errors="replace")
    report = ElementTree.parse(directory / "outcome.xml").getroot()
    [case] = report.findall(".//testcase")
    assert case.attrib["name"] == "test_dispatch_lists_units_in_route_order"
    assert case.find("error") is None and case.find("skipped") is None
    failed = case.find("failure") is not None
    assert int(failed) == test.returncode
    export = native(["json", "-o", "coverage.json"])
    assert export.returncode == 0, export.stderr.decode(errors="replace")
    observed = json.loads((directory / "coverage.json").read_bytes())["files"]["dispatch_rows.py"]
    return {
        "exit": test.returncode,
        "assertion_failed": failed,
        "executed_lines": observed["executed_lines"],
        "executed_branches": observed["executed_branches"],
        "statement_count": observed["summary"]["num_statements"],
        "branch_count": observed["summary"]["num_branches"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    with TemporaryDirectory(prefix="test-only-", dir=output.parent) as temporary:
        directory = Path(temporary)
        results = {
            name: {arm: measure(directory / f"{name}-{arm}", program, suite) for arm, suite in SUITES.items()}
            for name, program in PROGRAMS.items()
        }
    assert all(results[name]["shape"]["exit"] == 0 for name in PROGRAMS)
    assert results["reference"]["shape"] == results["reference"]["behavior"]
    assert {name for name in PROGRAMS if results[name]["behavior"]["assertion_failed"]} == {
        "reordered",
        "missing_units",
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(
            {
                "python_version": sys.version.split()[0],
                "pytest_version": version("pytest"),
                "coverage_version": version("coverage"),
                "cases": results,
                "model_attempts": 0,
            },
            stream,
            sort_keys=True,
            indent=2,
        )
        stream.write("\n")
    print(json.dumps({"cases": len(results) * len(SUITES), "behavior_defects_detected": 2, "model_attempts": 0}))


if __name__ == "__main__":
    main()

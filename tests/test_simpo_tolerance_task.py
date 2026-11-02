"""Validate retained SimPO tolerance controls and their result parser."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import types
import xml.etree.ElementTree as et
from pathlib import Path
from unittest.mock import patch

import pytest
from helpers import ROOT

TASK = ROOT / "benchmarks/agent-effectiveness/development/simpo-verifier-v1"
EVIDENCE = ROOT / "artifacts/research/2026-11-02/simpo-tolerance-direction-v1"
SPEC = importlib.util.spec_from_file_location(
    "simpo_tolerance_calibration", TASK / "controls/calibrate_tolerance_direction.py"
)
assert SPEC and SPEC.loader
calibrate = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"calibrate": types.ModuleType("calibrate"), "numpy": types.ModuleType("numpy")}):
    SPEC.loader.exec_module(calibrate)

CASES = {
    f"test_asymmetric_tolerance[{delta}-{accepted}-{phase}]"
    for delta, accepted in (("6.00003e-06", "True"), ("-5.99997e-06", "False"))
    for phase in ("initial", "regenerated")
}


def test_platform_results_bind_input_bytes_and_preserve_legacy_blind_spot() -> None:
    qualification = json.loads((EVIDENCE / "qualification.json").read_text(encoding="utf-8"))
    assert qualification["agent_performance_tested"] is False
    assert qualification["legacy_case_count"] == 17 and qualification["additional_cases"] == 4
    assert {item["platform"] for item in qualification["runs"]} == {"Windows", "Linux"}
    for item in qualification["runs"]:
        raw = (EVIDENCE / item["result"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item["sha256"]
        result = json.loads(raw)
        assert result["status"] == "passed" and result["platform"] == item["platform"]
        assert (result["python"], result["numpy"], result["pytest"]) == ("3.13.18", "2.5.4", "9.1.1")
        assert result["legacy_case_count"] == 17 and set(result["new_cases"]) == CASES
        assert result["agent_performance_tested"] is False
        task_prefix = "benchmarks/agent-effectiveness/development/simpo-verifier-v1/"
        expected_inputs = {
            task_prefix + name
            for name in (
                "TASK.md",
                "LICENSE",
                "source.json",
                "fixture/test_outputs.py",
                "cases.json",
                "controls/calibrate.py",
                "controls/test_acceptance.py",
                "controls/reference.py",
                "controls/reference_pathlib.py",
                "controls/test_tolerance_direction.py",
                "controls/calibrate_tolerance_direction.py",
            )
        }
        expected_inputs.update(
            {
                "benchmarks/component-controls/simpo-postrun/requirements-windows.txt",
                "benchmarks/component-controls/simpo-postrun/requirements-linux.txt",
                "artifacts/research/2026-11-02/simpo-verifier-task-calibration/windows-result.json",
            }
        )
        assert set(result["inputs_sha256"]) == expected_inputs
        for name, expected in result["inputs_sha256"].items():
            assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
        variants = result["variants"]
        assert set(variants) == {
            "reference-boundary",
            "reference-pathlib-boundary",
            "reverse-initial-boundary",
            "reverse-initial-legacy",
            "reverse-regenerated-boundary",
            "reverse-regenerated-legacy",
            "reverse-both-boundary",
            "reverse-both-legacy",
        }
        for name in (
            "reference-boundary",
            "reference-pathlib-boundary",
            "reverse-initial-legacy",
            "reverse-regenerated-legacy",
            "reverse-both-legacy",
        ):
            assert variants[name]["exit_code"] == 0 and variants[name]["failed_cases"] == []
        for phase in ("initial", "regenerated"):
            result_for_phase = variants[f"reverse-{phase}-boundary"]
            assert result_for_phase["exit_code"] == 1
            assert set(result_for_phase["failed_cases"]) == {case for case in CASES if case.endswith(f"-{phase}]")}
        assert variants["reverse-both-boundary"]["exit_code"] == 1
        assert set(variants["reverse-both-boundary"]["failed_cases"]) == CASES


def write_xml(path: Path, names: list[str], failures: set[str], extra: str | None = None) -> None:
    root = et.Element("testsuite")
    for name in names:
        node = et.SubElement(root, "testcase", {"name": name})
        if name in failures:
            et.SubElement(node, "failure")
        if extra is not None and name == names[0]:
            et.SubElement(node, extra)
    et.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def test_xml_parser_accepts_exact_cases_and_failures(tmp_path: Path) -> None:
    path = tmp_path / "result.xml"
    failed = {"one"}
    write_xml(path, ["one", "two"], failed)
    assert calibrate.verify_xml(path, {"one", "two"}, failed, 1) == ["one"]


@pytest.mark.parametrize("change", ["missing", "duplicate", "wrong_failure", "error", "skipped", "exit"])
def test_xml_parser_rejects_incomplete_or_contradictory_results(tmp_path: Path, change: str) -> None:
    path = tmp_path / "result.xml"
    names = ["one", "two"]
    if change == "missing":
        names.pop()
    elif change == "duplicate":
        names.append("one")
    failures = {"two"} if change == "wrong_failure" else {"one"}
    write_xml(path, names, failures, change if change in {"error", "skipped"} else None)
    with pytest.raises(ValueError, match="planned control outcomes"):
        calibrate.verify_xml(path, {"one", "two"}, {"one"}, 0 if change == "exit" else 1)

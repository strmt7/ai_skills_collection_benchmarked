"""Validate the exposed pytest task's control evidence and result parsing."""

import hashlib
import importlib.util
import json

import pytest
from helpers import ROOT

TASK = ROOT / "benchmarks/agent-effectiveness/development/pytest-unittest-pdb-skip-v1"
EVIDENCE = ROOT / "artifacts/research/2026-11-02/pytest-pdb-task-calibration"
SPEC = importlib.util.spec_from_file_location("pytest_pdb_calibrate", TASK / "controls/calibrate.py")
assert SPEC and SPEC.loader
calibrate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(calibrate)


def test_task_source_and_case_manifest_are_bound():
    source = json.loads((TASK / "source.json").read_text(encoding="utf-8"))
    cases = json.loads((TASK / "cases.json").read_text(encoding="utf-8"))["cases"]
    assert source["source_commit"] == calibrate.COMMIT
    assert source["source_sha256"] == calibrate.SOURCE_SHA256
    assert source["agent_performance_tested"] is False
    assert source["upstream_patch_sha256"] == hashlib.sha256(calibrate.upstream_patch()).hexdigest()
    assert source["license_sha256"] == hashlib.sha256((TASK / "LICENSE").read_bytes()).hexdigest()
    assert len(cases) == len(set(cases)) == 25
    assert "test_failed_test_enters_debugger_before_teardown" in cases
    assert set().union(*calibrate.EXPECTED_FAILURES.values()) <= set(cases)


def test_calibration_records_bind_current_inputs_and_preserve_all_expected_failures():
    qualification = json.loads((EVIDENCE / "qualification.json").read_text(encoding="utf-8"))
    assert qualification["agent_performance_tested"] is False
    assert qualification["case_count"] == 25
    assert {entry["platform"] for entry in qualification["runs"]} == {"Windows", "Linux"}
    for entry in qualification["runs"]:
        path = EVIDENCE / entry["result"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["result_sha256"]
        result = json.loads(path.read_text(encoding="utf-8"))
        assert result["status"] == "passed" and result["platform"] == entry["platform"]
        assert result["target_runtime"]["python"] == [3, 11, 18]
        assert (
            result["source_commit"] == calibrate.COMMIT and result["source_git_blob_sha256"] == calibrate.SOURCE_SHA256
        )
        assert result["tracked_checkout_files"] == 571 and result["case_count"] == 25
        assert result["agent_performance_tested"] is False
        assert set(result["inputs_sha256"]) == {
            "TASK.md",
            "LICENSE",
            "source.json",
            "cases.json",
            "controls/calibrate.py",
            "controls/test_skip_contract.py",
            "controls/upstream-patch.json",
            "controls/requirements.in",
            "controls/requirements-windows.txt",
            "controls/requirements-linux.txt",
            "controls/build-requirements.in",
            "controls/build-windows.txt",
            "controls/build-linux.txt",
        }
        assert set(result["variants"]) == set(calibrate.EXPECTED_FAILURES)
        for variant, expected in calibrate.EXPECTED_FAILURES.items():
            assert set(result["variants"][variant]["failed_cases"]) == expected
            assert result["variants"][variant]["exit_code"] == int(bool(expected))
        for name, expected in result["inputs_sha256"].items():
            assert hashlib.sha256((TASK / name).read_bytes()).hexdigest() == expected, name
    assert {entry["platform"] for entry in qualification["upstream_tests"]} == {"Windows", "Linux"}
    for entry in qualification["upstream_tests"]:
        assert (entry["base_failed"], entry["base_passed"], entry["fixed_passed"]) == (1, 4, 5)


def test_observation_parser_preserves_failures_on_both_newline_conventions():
    text = (
        "test_one (test_skip_contract.Contract.test_one) ... ok\n"
        "test_two (test_skip_contract.Contract.test_two) ... FAIL\n"
        "FAIL: test_two (test_skip_contract.Contract.test_two)\n"
        "Ran 2 tests in 0.25s\n\nFAILED (failures=1)\n"
    )
    for output in (text, text.replace("\n", "\r\n")):
        assert calibrate.verify_observations(output.encode(), ["test_one", "test_two"], {"test_two"}, 1) == ["test_two"]


@pytest.mark.parametrize("change", ["missing", "duplicate", "contradictory", "summary", "exit"])
def test_observation_parser_rejects_incomplete_or_inconsistent_results(change):
    one = "test_one (test_skip_contract.Contract.test_one) ... ok\n"
    two = "test_two (test_skip_contract.Contract.test_two) ... FAIL\n"
    detail = "FAIL: test_two (test_skip_contract.Contract.test_two)\n"
    summary = "Ran 2 tests in 0.25s\n\nFAILED (failures=1)\n"
    exit_code = 1
    if change == "missing":
        one = ""
    elif change == "duplicate":
        one *= 2
    elif change == "contradictory":
        two = two.replace("FAIL", "ok")
    elif change == "summary":
        summary = "Ran 1 test in 0.25s\n\nFAILED (failures=1)\n"
    else:
        exit_code = 0
    with pytest.raises(ValueError, match="planned case outcomes"):
        calibrate.verify_observations(
            (one + two + detail + summary).encode(), ["test_one", "test_two"], {"test_two"}, exit_code
        )

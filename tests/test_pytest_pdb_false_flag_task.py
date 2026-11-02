"""Validate the added false-skip controls and their source-bound evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from unittest.mock import patch

import pytest
from helpers import ROOT
from test_pytest_pdb_task import calibrate as prior

TASK = ROOT / "benchmarks/agent-effectiveness/development/pytest-unittest-pdb-skip-v1"
EVIDENCE = ROOT / "artifacts/research/2026-11-02/pytest-pdb-false-flag-v1"
SPEC = importlib.util.spec_from_file_location("pytest_pdb_false_flag", TASK / "controls/calibrate_false_flag.py")
assert SPEC and SPEC.loader
calibrate = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"calibrate": prior}):
    SPEC.loader.exec_module(calibrate)


def test_both_platform_calibrations_bind_inputs_and_retained_outcomes() -> None:
    qualification = json.loads((EVIDENCE / "qualification.json").read_text(encoding="utf-8"))
    assert qualification["agent_performance_tested"] is False
    assert qualification["legacy_case_count"] == 25 and qualification["additional_cases"] == 2
    assert {item["platform"] for item in qualification["runs"]} == {"Windows", "Linux"}
    for item in qualification["runs"]:
        raw = (EVIDENCE / item["result"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == item["sha256"]
        result = json.loads(raw)
        assert result["status"] == "passed" and result["platform"] == item["platform"]
        assert result["target_runtime"]["python"] == [3, 11, 18]
        assert result["source_commit"] == prior.COMMIT and result["source_git_blob_sha256"] == prior.SOURCE_SHA256
        assert result["tracked_checkout_files"] == 571 and result["legacy_case_count"] == 25
        assert set(result["new_cases"]) == calibrate.CASES
        assert result["agent_performance_tested"] is False
        for name, expected in result["inputs_sha256"].items():
            assert hashlib.sha256((TASK / name).read_bytes()).hexdigest() == expected, name
        variants = result["variants"]
        assert set(variants) == {
            "base-new",
            "gold-new",
            "alternative-new",
            "presence-mutant-new",
            "presence-mutant-legacy",
        }
        for name in ("base-new", "gold-new", "alternative-new", "presence-mutant-legacy"):
            assert variants[name]["exit_code"] == 0 and variants[name]["failed_cases"] == []
        assert variants["presence-mutant-new"]["exit_code"] == 1
        assert set(variants["presence-mutant-new"]["failed_cases"]) == calibrate.CASES


def observation(failed: set[str]) -> bytes:
    lines = []
    for name in sorted(calibrate.CASES):
        state = "FAIL" if name in failed else "ok"
        lines.append(f"{name} (test_skip_false_flag_contract.Contract.{name}) ... {state}")
    lines.extend(f"FAIL: {name} (test_skip_false_flag_contract.Contract.{name})" for name in sorted(failed))
    lines.extend(["Ran 2 tests in 0.1s", "", f"FAILED (failures={len(failed)})" if failed else "OK"])
    return ("\n".join(lines) + "\n").encode()


@pytest.mark.parametrize("failed", [set(), {"test_direct_false_flag_preserves_debugger_order"}, calibrate.CASES])
def test_observation_parser_checks_both_newline_conventions(failed: set[str]) -> None:
    raw = observation(failed)
    for value in (raw, raw.replace(b"\n", b"\r\n")):
        assert calibrate.verify_new_observations(value, failed, int(bool(failed))) == sorted(failed)


@pytest.mark.parametrize("change", ["missing", "duplicate", "detail", "summary", "exit"])
def test_observation_parser_rejects_inconsistent_output(change: str) -> None:
    failed = {"test_direct_false_flag_preserves_debugger_order"}
    raw = observation(failed).decode()
    if change == "missing":
        raw = "\n".join(line for line in raw.split("\n") if not line.startswith("test_inherited"))
    elif change == "duplicate":
        raw = raw.replace("Ran 2 tests", raw.splitlines()[0] + "\nRan 2 tests")
    elif change == "detail":
        raw = raw.replace("FAIL: test_direct", "FAIL: different_test_direct")
    elif change == "summary":
        raw = raw.replace("Ran 2 tests", "Ran 1 test")
    with pytest.raises(ValueError, match="planned cases"):
        calibrate.verify_new_observations(raw.encode(), failed, 0 if change == "exit" else 1)

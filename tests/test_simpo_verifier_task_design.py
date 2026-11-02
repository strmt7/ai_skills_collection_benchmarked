"""Check the development-task provenance and recorded calibration scope."""

import hashlib
import json

from helpers import ROOT

TASK = ROOT / "benchmarks/agent-effectiveness/development/simpo-verifier-v1"
RESULTS = ROOT / "artifacts/research/2026-11-02/simpo-verifier-task-calibration"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pinned_upstream_fixture_and_license():
    source = json.loads((TASK / "source.json").read_text(encoding="utf-8"))
    assert source["commit"] == "55bfe693f2a19f6b2f29aca3f54fe98b9d994668"
    assert source["sha256"] == digest(TASK / "fixture/test_outputs.py")
    assert source["license"] == "Apache-2.0"
    assert source["license_sha256"] == digest(TASK / "LICENSE")


def test_calibrations_bind_inputs_and_do_not_claim_a_model_trial():
    cases = json.loads((TASK / "cases.json").read_text(encoding="utf-8"))["cases"]
    assert len(cases) == len(set(cases)) == 17
    for platform in ("windows", "linux"):
        result = json.loads((RESULTS / f"{platform}-result.json").read_text(encoding="utf-8"))
        assert result["status"] == "passed"
        assert result["platform"].lower() == platform
        for path, expected in result["inputs_sha256"].items():
            assert digest(TASK / path) == expected, path
        assert result["subprocess_simulated"] is True
        assert result["live_simpo_training"] is False
        assert result["agent_submission_graded"] is False
        assert result["sandbox_qualified"] is False
        controls = {control["control"]: control for control in result["controls"]}
        for name in ("reference", "reference_pathlib"):
            assert controls[name]["passed"] == 17
            assert controls[name]["failed_cases"] == []
        if platform == "linux":
            assert controls["original"]["passed"] == 11
            assert len(controls["original"]["failed_cases"]) == 6
            assert set(controls["original"]["failed_cases"]) <= set(cases)
        else:
            assert "original" not in controls
            assert result["original_control"] == "not run: Linux source environment"

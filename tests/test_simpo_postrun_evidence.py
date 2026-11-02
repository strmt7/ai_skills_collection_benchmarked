"""Verify that the recorded snapshot controls refer to the committed inputs."""

import hashlib
import json

from helpers import ROOT


def test_snapshot_control_evidence():
    evidence = ROOT / "artifacts/research/2026-11-02/simpo-postrun-comparison"
    qualification = json.loads((evidence / "qualification.json").read_text(encoding="utf-8"))
    assert qualification["reference_sha256"] == "162e3cd015afa98503a8419c6955523ba7c4401cd50f34e7d8f7e601e8489d2c"
    for name, digest in qualification["files_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    expected = {
        "correct": ("matching", "within_tolerance"),
        "wrong_values": ("nonmatching", "values_outside_tolerance"),
        "wrong_key": ("nonmatching", "missing_or_duplicate_losses"),
        "broadcastable_shape": ("nonmatching", "shape_mismatch"),
        "nonfinite": ("nonmatching", "nonfinite_values"),
    }
    for platform in ("windows", "linux"):
        result = json.loads((evidence / f"{platform}-result.json").read_text(encoding="utf-8"))
        assert result["platform"].lower() == platform
        assert result["reference_sha256"] == qualification["reference_sha256"]
        assert (
            result["comparator_sha256"]
            == qualification["files_sha256"]["benchmarks/component-controls/simpo-postrun/compare.py"]
        )
        assert {
            name: (case["status"], case["reason"]) for name, case in result["regenerated_cases"].items()
        } == expected
        for field in (
            "subprocess_or_regeneration_executed",
            "actual_generation_proven",
            "benchmark_harness_executed",
            "agent_performance_tested",
        ):
            assert result[field] is False

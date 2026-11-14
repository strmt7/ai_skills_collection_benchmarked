"""Preserve native quota and deadline evidence without implying task readiness."""

from __future__ import annotations

import errno
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "artifacts/research/2026-11-13/native-project-resources"


def test_native_resource_evidence_matches_current_source_and_kernel_observations() -> None:
    review = json.loads((FOLDER / "review.json").read_bytes())
    for name, digest in review["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    for name, digest in review["artifacts"].items():
        assert hashlib.sha256((FOLDER / name).read_bytes()).hexdigest() == digest, name
    native = json.loads((FOLDER / "native-resources.json").read_bytes())
    profiles = {row["id"]: row for row in native["native_resource_profiles"]}
    legacy = profiles["legacy-default"]["native"]
    project = profiles["explicit-project"]["native"]
    assert legacy["binary"]["errno"] == errno.EACCES
    assert legacy["storage"]["errno"] == errno.ENOSPC
    assert legacy["storage"]["filesystem_bytes"] == 16 * 1024**2
    assert project["binary"] == {"exit_code": 0, "stdout": "42\n", "stderr": "", "errno": None}
    assert project["storage"]["written_bytes"] == 20 * 1024**2
    assert project["storage"]["filesystem_bytes"] == 4 * 1024**3
    assert project["cgroup"] == {
        "cpu.max": "400000 100000",
        "memory.max": str(8 * 1024**3),
        "memory.swap.max": "0",
        "pids.max": "32",
    }
    lifecycle = json.loads((FOLDER / "lifecycle.native.json").read_bytes())
    assert lifecycle["ready"]["lease_seconds"] == 2460
    assert lifecycle["worker_process"]["termination_reason"] == "timeout"
    assert lifecycle["worker_process"]["job_active_processes_after_cleanup"] == 0
    assert lifecycle["watchdog_removed_without_explicit_close"]
    assert lifecycle["extended_journal_recovered"]
    assert native["closed_container_leases"] == 3 and native["remaining_owned_containers"] == 0
    assert not review["selected_task_builds_qualified"]
    assert not review["full_multistage_controller_integrated"]
    assert review["model_invocations"] == review["counted_attempts"] == 0
    assert not review["model_improvement_established"]


def test_native_grader_controls_preserve_long_deadlines_and_failure_distinctions() -> None:
    report = json.loads((FOLDER / "grader-controls.json").read_bytes())
    controls = {row["id"]: row for row in report["controls"]}
    assert len(controls) == 7
    assert all(row["native_summary"]["passed"] for row in controls.values())
    assert controls["baseline"]["native_summary"]["status"] == "task_failed"
    assert controls["baseline"]["native_summary"]["native_counts"]["failed"] == 18
    invalid = controls["wrong-import"]["native_summary"]
    assert invalid["status"] == "harness_error" and invalid["diagnostic_fraction"] is None
    for schema, lease_seconds in ((2, 960), (3, 1080)):
        control = controls[f"long-deadline-schema-{schema}"]
        assert control["native_deadline_binding"]["test_timeout_seconds"] == 900
        assert control["native_deadline_binding"]["lease_seconds"] == lease_seconds
        assert control["native_summary"]["native_counts"]["passed"] == 11
    assert not report["complete_fixed_cohort_admitted"]
    assert report["model_invocations"] == report["counted_attempts"] == 0

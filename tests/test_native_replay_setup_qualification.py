"""Keep automatic-setup qualification separate from model-effectiveness evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from validate_native_qualification_index import validate

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "artifacts/research/2026-11-13/maintained-node-replay-setup"


def test_maintained_setup_preserves_build_history_and_current_dependency_qualification() -> None:
    review = json.loads((FOLDER / "review.json").read_bytes())
    for name, digest in review["artifacts"].items():
        assert hashlib.sha256((FOLDER / name).read_bytes()).hexdigest() == digest
    qualification = validate(ROOT)
    assert qualification["ok"], qualification["errors"]
    controls = json.loads((FOLDER / "native-controls.json").read_bytes())
    builds = controls["builds"]
    assert len(builds) == review["native_image_builds_compared"] == 3
    assert sum(row["current_implementation"] for row in builds) == review["current_implementation_builds"] == 1
    assert len({row["image_id"] for row in builds}) == len({row["archive"]["sha256"] for row in builds}) == 1
    assert len({row["layer"]["sha256"] for row in builds}) == 1
    assert all(row["all_child_jobs_closed"] and row["closed_lease"] and row["image_tags"] == [] for row in builds)
    assert builds[0]["automatic_image_load_observed"] and builds[-1]["retained_source_snapshot_files"] > 0
    assert all(row["probes"] == builds[0]["probes"] for row in builds)
    assert review["same_host_byte_reproducibility"] and not review["cross_host_reproducibility_established"]
    assert len(controls["rejection_controls"]) == review["live_expected_failure_controls"] == 5
    for case in controls["rejection_controls"]:
        assert case["expected_cli_exit_code"] == case["actual_cli_exit_code"] == 1
        assert case["negative_rejection_qualified"] and case["process"]["job_active_processes_after_cleanup"] == 0
    assert controls["existing_successful_installation_unchanged"] and not controls["full_archive_copy_for_tag_removal"]
    assert review["model_invocations"] == review["counted_attempts"] == 0
    assert not review["model_improvement_established"] and not review["task_execution_admitted"]
    assert not review["publisher_equivalent"] and review["public_model_launch_guard"] == "closed"

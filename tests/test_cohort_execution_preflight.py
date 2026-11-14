"""Preserve complete publisher contracts and separate client controls from model admission."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from validate_native_qualification_index import validate

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "artifacts/research/2026-11-13"


def checked_review(folder: Path) -> dict[str, Any]:
    review: dict[str, Any] = json.loads((folder / "review.json").read_bytes())
    for name, digest in review["artifacts"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
    return review


def test_cohort_keeps_all_selected_tasks_and_every_enabled_evaluator() -> None:
    folder = RESEARCH / "cohort-execution-preflight"
    review = checked_review(folder)
    matrix = json.loads((folder / "matrix.json").read_bytes())
    selection_path = ROOT / "benchmarks/agent-effectiveness/development/swe-skills-pilot-v1/selection.json"
    selection = json.loads(selection_path.read_bytes())
    assert matrix["selection_sha256"] == hashlib.sha256(selection_path.read_bytes()).hexdigest()
    assert len(matrix["tasks"]) == review["tasks"] == selection["planned_tasks"] == 12
    assert review["planned_attempts"] == selection["planned_attempts"] == 36
    for task, selected in zip(matrix["tasks"], selection["selected"], strict=True):
        assert task["task_id"] == selected["task_id"] and task["skill_id"] == selected["skill_id"]
        assert (
            task["source_repository"] == selected["repository"] and task["source_commit"] == selected["source_commit"]
        )
        assert task["condition_order"] == selected["condition_order"] and not task["common_execution_admitted"]
    methods = dict(Counter(item["method"] for row in matrix["tasks"] for item in row["enabled_evaluators"]))
    assert methods == matrix["enabled_evaluator_counts"] == review["enabled_evaluator_counts"]
    assert methods == {"unit_test": 12, "build_check": 3}
    assert not review["original_frame_tasks_replaced_or_removed"] and not review["common_execution_admitted"]
    assert not review["publisher_runtime_reproduced"] and review["model_invocations"] == review["counted_attempts"] == 0
    images = json.loads((folder / "image-manifests.json").read_bytes())
    assert len(images["images"]) == len(matrix["unique_publisher_images"]) == review["publisher_images"] == 7
    assert {row["repository"] for row in images["images"]} == set(matrix["unique_publisher_images"])
    verified = [row for row in images["images"] if row["manifest_verified"]]
    assert len(verified) == review["exact_platform_manifests_verified"] == 5
    for row in verified:
        path = folder / "manifests" / (row["repository"].split("/")[-1] + ".json")
        assert "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest() == row["manifest_digest"]
        assert row["immutable_reference"].endswith("@" + row["manifest_digest"])
    requests = json.loads((folder / "native-image-requests.json").read_bytes())
    assert not images["passed"] and not requests["capture_passed"] and not review["all_required_images_resolved"]
    assert len(requests["unresolved"]) == review["anonymous_manifest_requests_unresolved"] == 2
    assert all(
        row["native_exit_code"] == 1 and "authentication required" in row["stderr"] for row in requests["unresolved"]
    )
    assert requests["all_child_jobs_closed"] and requests["image_layers_downloaded"] == 0
    assert all(row["process"]["job_active_processes_after_cleanup"] == 0 for row in requests["requests"])


def test_anonymous_client_has_live_discovery_control_and_preserves_grader_results() -> None:
    folder = RESEARCH / "anonymous-registry-client"
    review = checked_review(folder)
    # Historical provenance stays immutable; source changes need explicit fresh qualification.
    bootstrap = checked_review(RESEARCH / "windows-bootstrap-runtime")
    previous = bootstrap["previous_anonymous_client_review"]
    assert previous["path"] == (folder / "review.json").relative_to(ROOT).as_posix()
    assert previous["sha256"] == hashlib.sha256((folder / "review.json").read_bytes()).hexdigest()
    qualification = validate(ROOT)
    assert qualification["ok"], qualification["errors"]
    controls = json.loads((folder / "native-controls.json").read_bytes())
    negative, positive = controls["controls"]
    assert negative["native_exit_code"] == 0
    assert negative["helper_calls_after"] > negative["helper_calls_before"]
    assert positive["native_exit_code"] == 0 and positive["helper_calls_after"] == positive["helper_calls_before"]
    assert controls["base_interpreter_inventory_unchanged"] and controls["only_owned_canary_helper_used"]
    assert not controls["host_credential_helpers_used"] and controls["image_layers_downloaded"] == 0
    regressions = json.loads((folder / "grader-regressions.json").read_bytes())
    cases = {row["id"]: row for row in regressions["controls"]}
    assert len(cases) == review["native_grader_regression_cases"] == 5
    assert cases["windows-pydicom-positive"]["windows_contract_cases_passed"] == 15
    assert cases["windows-pydicom-positive"]["original_verifier_cases_passed"] == 18
    assert cases["windows-pydicom-positive"]["native_command_exit_code"] == 0
    assert cases["baseline"]["native_counts"] == {"passed": 0, "failed": 18, "skipped": 0, "errors": 0, "total": 18}
    assert cases["wrong-import"]["status"] == "harness_error" and cases["wrong-import"]["diagnostic_fraction"] is None
    assert cases["schema-2"]["native_counts"]["passed"] == cases["schema-3"]["native_counts"]["passed"] == 11
    assert regressions["complete_inventory_unchanged_within_and_across_three_grades"]
    assert regressions["complete_grader_dependency_objects"] == 2525 and regressions["closed_container_leases"] == 9
    record_path = ROOT / review["task_record"]["path"]
    assert hashlib.sha256(record_path.read_bytes()).hexdigest() == review["task_record"]["sha256"]
    record = json.loads(record_path.read_bytes())
    previous = ROOT / record["previous_diagnostic_record"]
    assert hashlib.sha256(previous.read_bytes()).hexdigest() == record["previous_diagnostic_record_sha256"]
    assert (
        record["publisher_declared_unit_test_timeout_seconds"]
        == record["current_diagnostic_unit_test_timeout_seconds"]
        == 300
    )
    assert "windows_actual_pinned_source_import_and_native_numpy_qualified" not in record
    assert record["model_invocations"] == record["counted_attempts"] == 0
    assert not record["execution_admitted"] and not record["actual_target_model_execution_qualified"]
    assert not record["agent_efficacy_established"] and not review["model_improvement_established"]


def test_windows_bootstrap_update_keeps_native_controls_and_unadmitted_history() -> None:
    folder = RESEARCH / "windows-bootstrap-runtime"
    review = checked_review(folder)
    bootstrap = json.loads((folder / "bootstrap-controls.json").read_bytes())
    assert bootstrap["passed"] and bootstrap["all_owned_jobs_closed"]
    assert bootstrap["host_path_and_registry_unchanged"] and bootstrap["source_fixture_inputs_equal_active_inputs"]
    assert bootstrap["control_groups_executed"] == len(bootstrap["control_groups"]) == 39
    assert bootstrap["input_files"] == 26 and bootstrap["native_node_version"] == review["node_version"]
    controls = json.loads((folder / "grader-controls.json").read_bytes())["controls"]
    assert len(controls) == review["native_grader_control_groups"] == 5
    cases = {case["id"]: case for case in controls}
    assert all(case["passed"] for case in controls)
    assert cases["windows-positive"]["windows_cases_passed"] == 15
    assert cases["windows-positive"]["linux_counts"]["passed"] == 18
    assert cases["baseline"]["native_counts"]["failed"] == 18
    assert cases["wrong-import"]["status"] == "harness_error"
    assert cases["wrong-import"]["diagnostic_fraction"] is None
    assert cases["schema-2"]["native_counts"]["passed"] == cases["schema-3"]["native_counts"]["passed"] == 11
    history = json.loads((folder / "qualification-history.json").read_bytes())
    assert history["initial_handoff_accepted_attempt"] == 9 and len(history["unadmitted_attempts"]) == 8
    assert not any(row["admitted"] for row in history["unadmitted_attempts"])
    assert not history["raw_prior_records_modified"]
    assert review["model_invocations"] == review["counted_attempts"] == 0
    assert not review["agent_efficacy_established"] and not review["commercial_release_ready"]
    architecture = json.loads((folder / "architecture-controls.json").read_bytes())
    assert architecture["passed"] and len(architecture["controls"]) == 4
    assert not architecture["initial_checkpoint_admitted"]
    assert architecture["initial_failed_controls"] == ["bootstrap-live", "supervisor-rebuild-check"]
    previous_bootstrap = review["previous_bootstrap_review"]
    assert hashlib.sha256((ROOT / previous_bootstrap["path"]).read_bytes()).hexdigest() == previous_bootstrap["sha256"]
    previous = review["previous_runtime_review"]
    assert hashlib.sha256((ROOT / previous["path"]).read_bytes()).hexdigest() == previous["sha256"]


def test_local_node_replay_qualifies_runtime_without_admitting_model_outcomes() -> None:
    folder = RESEARCH / "node-local-replay"
    review = checked_review(folder)
    recipe = json.loads((folder / "recipe.json").read_bytes())
    controls = json.loads((folder / "native-controls.json").read_bytes())
    assert recipe["runtime_schema_version"] == 2 and recipe["base_layers_unchanged"]
    assert recipe["node_version"] == "v26.13.1" and recipe["npm_version"] == "11.20.0"
    assert not recipe["original_image_aliases_resolved"] and not recipe["publisher_equivalent"]
    selection = ROOT / "benchmarks/agent-effectiveness/development/swe-skills-pilot-v1/selection.json"
    assert recipe["selection_sha256"] == hashlib.sha256(selection.read_bytes()).hexdigest()
    assert recipe["candidate_files_unchanged"] == review["candidate_files_unchanged"] == 18245
    assert controls["checks_executed"] == review["native_checks"] == len(controls["controls"]) == 8
    assert all(
        row["passed"] and row["native_exit_code"] == row["remaining_job_processes"] == 0 for row in controls["controls"]
    )
    live = controls["live_runtime"]
    assert live["passed"] and live["source_unchanged"] and live["processes_closed"] and live["closed_lease"] == "closed"
    assert [row["id"] for row in live["results"]] == ["node", "npm", "npx"]
    assert json.loads(live["results"][0]["stdout"])["version"] == "v26.13.1"
    assert all(row["stdout"] == "11.20.0" for row in live["results"][1:])
    for case in controls["rejected_archives"]["cases"]:
        assert case["rejected"] and case["all_jobs_closed"]
        assert case["engine_loads"] == case["registry_pulls"] == 0
    grader = {row["id"]: row for row in controls["publisher_grader_regressions"]}
    assert grader["windows-pydicom-positive"]["native_counts"]["passed"] == 18
    assert grader["baseline"]["native_counts"]["failed"] == 18
    assert grader["wrong-import"]["status"] == "harness_error" and grader["wrong-import"]["diagnostic_fraction"] is None
    assert grader["schema-2"]["native_counts"]["passed"] == grader["schema-3"]["native_counts"]["passed"] == 11
    assert controls["closed_grader_leases"] == 9 and controls["complete_dependency_objects"] == 2525
    assert controls["complete_inventory_unchanged_within_and_across_three_grades"]
    assert review["model_invocations"] == review["counted_attempts"] == 0
    assert not review["model_improvement_established"] and not review["common_execution_admitted"]

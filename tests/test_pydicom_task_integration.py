"""Keep selected-task diagnostics separate from admitted model results."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts/research/2026-11-13/pydicom-task-integration"
PILOT = ROOT / "benchmarks/agent-effectiveness/development/swe-skills-pilot-v1"


def test_complete_project_inventory_reconstructs_the_pinned_git_tree() -> None:
    source = json.loads((EVIDENCE / "project-source.json").read_bytes())
    assert source["source_commit"] == "f15214fb9bc83d063f481552c487b02b28bfb7cc"
    assert source["complete_git_blob_inventory_verified"] and source["recursive_git_tree_recomputed"]
    files = source["files"]
    assert len(files) == 541 and sum(row["bytes"] for row in files.values()) == source["expanded_bytes"]
    assert len({name.casefold() for name in files}) == len(files)
    children: dict[str, dict[str, dict[str, Any]]] = {"": {}}
    for name, row in files.items():
        parts = PurePosixPath(name).parts
        assert parts and ".." not in parts and not PurePosixPath(name).is_absolute()
        for index in range(len(parts)):
            parent = "/".join(parts[:index])
            children.setdefault(parent, {})
            if index == len(parts) - 1:
                children[parent][parts[index]] = {"mode": row["mode"], "sha": row["git_blob_sha1"]}
            else:
                children[parent][parts[index]] = {"mode": "40000", "directory": "/".join(parts[: index + 1])}
    digests: dict[str, str] = {}
    for name in sorted(children, key=lambda value: (value.count("/"), len(value)), reverse=True):
        entries = children[name]
        ordered = sorted(entries, key=lambda leaf: leaf.encode() + (b"/" if entries[leaf]["mode"] == "40000" else b""))
        raw = b""
        for leaf in ordered:
            entry = entries[leaf]
            identity = digests[entry["directory"]] if entry["mode"] == "40000" else entry["sha"]
            raw += entry["mode"].encode() + b" " + leaf.encode() + b"\0" + bytes.fromhex(identity)
        digests[name] = hashlib.sha1(b"tree " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False).hexdigest()
    assert digests[""] == source["source_tree_sha1"] == "77cf924c4d3b0150d05345d20d561eed731a6f8b"


def test_native_graph_and_original_negative_verifier_controls_remain_explicit() -> None:
    report = json.loads((EVIDENCE / "review.json").read_bytes())
    for name, expected in report["artifacts"].items():
        assert hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest() == expected
    record_path = ROOT / report["task_record"]["path"]
    assert hashlib.sha256(record_path.read_bytes()).hexdigest() == report["task_record"]["sha256"]
    result = json.loads((EVIDENCE / "result.json").read_bytes())
    inventory = json.loads((EVIDENCE / "dependency-inventory.json").read_bytes())
    rows = inventory["inventory"]
    assert len(rows) == len({row["path"] for row in rows}) == result["inventory_objects"]
    raw = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(raw).hexdigest() == inventory["inventory_sha256"] == result["inventory_sha256"]
    assert result["fresh_hash_locked_reinstall_equal"] and result["system_interpreter_unchanged"]
    assert result["wrong_wheel_digest_rejected"] and result["identical_dependency_inventories"]
    assert result["repetitions"] == 2 and result["unused_candidate_projects"] == ["colorama"]
    assert len(result["resolved_versions"]) == 8
    cases = {row["case"]: row for row in result["cases"]}
    assert len(cases) == len(result["cases"]) == report["distinct_component_controls"] == 9
    assert cases["installed-package-origin-rejected"]["rejected"] is True
    assert cases["task-user-cannot-write-grader-environment"]["rejected"] is True
    for label, passes, failures in (
        ("original-evaluator-on-untouched-baseline", 0, 18),
        ("original-evaluator-on-intentionally-failing-deliverables", 3, 15),
    ):
        case = cases[label]
        assert case["exit_code"] != 0
        assert case["counts"] == {"collected": 18, "passed": passes, "failed": failures, "errors": 0, "skipped": 0}
    assert result["original_test_verifier_executed"] is True and result["publisher_scoring_class_executed"] is False
    assert result["task_solution_written"] is False and result["counted_attempts"] == result["model_invocations"] == 0


def test_task_exposure_and_partial_readiness_do_not_admit_model_execution() -> None:
    record = json.loads((PILOT / "task-integration/pydicom-v1.json").read_bytes())
    selection_raw = (PILOT / "selection.json").read_bytes()
    selection = json.loads(selection_raw)
    assert record["selection_sha256"] == hashlib.sha256(selection_raw).hexdigest()
    selected = next(row for row in selection["selected"] if row["task_id"] == record["task_id"])
    assert record["project_commit"] == selected["source_commit"]
    assert selection["planned_tasks"] == 12 and selection["planned_attempts"] == 36
    assert record["partition"] == "development"
    assert record["linux_dependency_graph_qualified"] and record["original_verifier_failure_controls_qualified"]
    for key in (
        "original_verifier_success_control_qualified",
        "publisher_scoring_class_qualified_for_this_task",
        "windows_subject_tool_access_qualified",
        "maintained_grader_dependency_profile_implemented",
        "execution_admitted",
        "complete_preregistration",
        "agent_efficacy_established",
    ):
        assert record[key] is False
    exposure = json.loads((EVIDENCE / "library-exposure.json").read_bytes())
    assert (
        exposure["before_selected_task_content_capture"]
        and exposure["candidate_skill_bytes_unchanged_after_integration"]
    )
    assert exposure["task_and_evaluator_now_exposed_to_integration_controller"] is True
    assert exposure["public_timestamp_attestation"] is False and exposure["candidate_intervention_admitted"] is False


def test_maintained_grader_qualification_preserves_task_identity_and_admission_boundary() -> None:
    record_path = PILOT / "task-integration/pydicom-v2.json"
    record = json.loads(record_path.read_bytes())
    previous_path = ROOT / record["previous_diagnostic_record"]
    previous = json.loads(previous_path.read_bytes())
    assert record["task_id"] == previous["task_id"]
    assert record["previous_diagnostic_record_sha256"] == hashlib.sha256(previous_path.read_bytes()).hexdigest()
    assert record["selection_sha256"] == previous["selection_sha256"]
    assert record["maintained_grader_dependency_profile_implemented"]
    assert record["original_publisher_scoring_class_failure_controls_qualified"]
    assert record["legacy_and_dependency_profile_generic_success_controls_qualified"]
    assert record["model_invocations"] == record["counted_attempts"] == 0
    for key in (
        "original_verifier_success_control_for_selected_task_qualified",
        "windows_subject_tool_access_qualified",
        "complete_preregistration",
        "execution_admitted",
        "agent_efficacy_established",
    ):
        assert record[key] is False
    folder = ROOT / "artifacts/research/2026-11-13/native-grader-dependencies"
    report = json.loads((folder / "review.json").read_bytes())
    assert report["task_record"] == {
        "path": record_path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(record_path.read_bytes()).hexdigest(),
    }
    for name, digest in report["artifacts"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
    controls = json.loads((folder / "controls.json").read_bytes())["controls"]
    assert len(controls) == report["qualification"]["native_control_cases"] == 6
    assert sum(row["closed_leases"] for row in controls) == report["native_facts"]["closed_native_leases"]
    assert all(row["passed"] and row["model_invocations"] == row["counted_attempts"] == 0 for row in controls)
    assert all(row["remaining_owned_containers"] == 0 for row in controls)


def test_latest_windows_handoff_evidence_preserves_revocations_and_zero_model_outcomes() -> None:
    folder = ROOT / "artifacts/research/2026-11-13/windows-pydicom-and-stable-tools"
    review = json.loads((folder / "review.json").read_bytes())
    for name, digest in review["artifacts"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
    record_path = ROOT / review["task_record"]["path"]
    assert hashlib.sha256(record_path.read_bytes()).hexdigest() == review["task_record"]["sha256"]
    record = json.loads(record_path.read_bytes())
    previous_path = ROOT / record["previous_diagnostic_record"]
    previous = json.loads(previous_path.read_bytes())
    assert record["task_id"] == previous["task_id"] and record["selection_sha256"] == previous["selection_sha256"]
    assert record["previous_diagnostic_record_sha256"] == hashlib.sha256(previous_path.read_bytes()).hexdigest()
    assert record["windows_source_write_pytest_collection_and_linux_handoff_qualified"]
    assert record["scripted_qualification_only"] and not record["execution_admitted"]
    assert not record["actual_target_model_execution_qualified"] and not record["agent_efficacy_established"]
    assert review["model_invocations"] == review["counted_attempts"] == record["model_invocations"] == 0
    controls = json.loads((folder / "native-controls.json").read_bytes())["controls"]
    assert len(controls) == 2
    for row in controls:
        assert row["native_tool_exit_code"] == 0 and row["junit_testcases_passed"] == 1
        assert row["source_files_preserved"] == 541 and row["collected_files"] == 543
        assert row["original_linux_native_counts"] == {
            "passed": 0,
            "failed": 18,
            "skipped": 0,
            "errors": 0,
            "total": 18,
        }
    revoked = json.loads((folder / "revoked-controls.json").read_bytes())
    assert len(revoked["revoked"]) == 2
    assert all(row["previous_pass_claim_revoked"] and row["native_tool_exit_code"] != 0 for row in revoked["revoked"])
    assert revoked["model_outcomes_removed_or_replaced"] is False


def test_scripted_task_success_does_not_become_a_model_result_or_admission() -> None:
    folder = ROOT / "artifacts/research/2026-11-13/pydicom-task-success-controls"
    report = json.loads((folder / "review.json").read_bytes())
    for name, digest in report["artifacts"].items():
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == digest
    record_path = ROOT / report["task_record"]["path"]
    assert hashlib.sha256(record_path.read_bytes()).hexdigest() == report["task_record"]["sha256"]
    record = json.loads(record_path.read_bytes())
    previous_path = ROOT / record["previous_diagnostic_record"]
    previous = json.loads(previous_path.read_bytes())
    assert record["previous_diagnostic_record_sha256"] == hashlib.sha256(previous_path.read_bytes()).hexdigest()
    assert record["task_id"] == previous["task_id"] and record["selection_sha256"] == previous["selection_sha256"]
    assert not previous["original_verifier_success_control_for_selected_task_qualified"]
    assert record["original_verifier_success_control_for_selected_task_qualified"]
    assert record["original_publisher_scoring_class_success_control_for_selected_task_qualified"]
    assert record["controller_authored_task_solution_fixture_written"] and record["scripted_qualification_only"]
    assert record["model_invocations"] == record["counted_attempts"] == 0
    for field in (
        "execution_admitted",
        "complete_preregistration",
        "actual_target_model_execution_qualified",
        "agent_efficacy_established",
    ):
        assert record[field] is False
    assert report["model_invocations"] == report["counted_attempts"] == 0
    assert not report["model_improvement_established"] and not report["candidate_skill_content_changed_after_exposure"]
    result = json.loads((folder / "controls.json").read_bytes())
    controls = result["controls"]
    assert len(controls) == report["controlled_passing_repetitions"] == record["task_success_control_repetitions"] == 2
    assert result["complete_inventories_equal_across_repetitions"]
    for row in controls:
        assert row["native_tool_exit_code"] == 0 and row["windows_junit_passed"] == 15
        assert row["original_linux_junit_passed"] == 18 and row["original_publisher_status"] == "passed"
        assert row["original_publisher_fraction"] == 1 and row["original_publisher_user_is_nonroot"]
        assert row["complete_grader_dependency_objects"] == 2525 and row["complete_dependency_inventory_unchanged"]
        assert row["original_project_files_preserved"] == 541 and row["collected_files"] == 544
        assert row["closed_container_leases"] == 2 and row["subject_job_remaining_processes"] == 0
        assert row["temporary_listener_stopped"] and row["selected_task_solution_written_by_controller"]
        assert row["model_invocations"] == row["counted_attempts"] == 0
    correction = json.loads((folder / "metadata-scope-correction.json").read_bytes())
    assert correction["inherited_raw_summary_field_not_accepted"]
    assert correction["core_task_success_independently_verified"]
    assert not correction["original_raw_receipts_modified"] and not correction["model_outcomes_removed_or_replaced"]

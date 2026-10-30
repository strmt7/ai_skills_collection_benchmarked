import copy
import json
import shutil
from pathlib import Path

import pytest
import summarize_agent_trials as single
import summarize_multi_task_trials as target
from _trial_comparisons import compare_blocks

pytest_plugins = ("test_summarize_agent_trials",)


DEFINITIONS = {"default": {"skills": []}, "candidate": {"skills": ["fixed-bundle"]}}


def report(task, baseline, candidate):
    attempts = [
        *(
            {"repetition": index, "condition": "default", "status": status, "usage": None}
            for index, status in enumerate(baseline, 1)
        ),
        *(
            {"repetition": index, "condition": "candidate", "status": status, "usage": None}
            for index, status in enumerate(candidate, 1)
        ),
    ]
    return {
        "task_id": task,
        "protocol_sha256": task * 64,
        "grading_manifest_sha256": "f" * 64,
        "expected_grading_cases": 2,
        "limitations": ["fixture limitation"],
        "block_comparison": compare_blocks(attempts, set(DEFINITIONS)),
        "model_requested": "model",
        "reasoning_effort_requested": "high",
        "partition": "development",
        "task_count": 1,
        "conditions": {
            "default": {"planned_attempts": len(baseline)},
            "candidate": {"planned_attempts": len(candidate)},
        },
        "attempts": attempts,
    }


def test_tasks_have_equal_weight_instead_of_pooled_attempt_weight():
    reports = [
        report("a", ["task_passed"], ["task_passed"]),
        report("b", ["task_failed"] * 4, ["task_passed"] * 4),
    ]
    result = target.aggregate(reports, [DEFINITIONS, copy.deepcopy(DEFINITIONS)])
    comparison = result["comparisons"]["candidate"]
    assert comparison == {
        "planned_tasks": 2,
        "fully_scored_tasks": 2,
        "unscored_tasks": 0,
        "equal_task_weight_mean_difference": {"numerator": 1, "denominator": 2},
    }
    assert result["quality_superiority_established"] is False


def test_token_differences_use_equal_task_weight_and_paired_blocks():
    first = report("a", ["task_passed", "task_passed"], ["task_passed", "task_passed"])
    second = report("b", ["task_passed"], ["task_passed"])
    for item, inputs in ((first, (100, 100, 110, 130)), (second, (100, 90))):
        for attempt, count in zip(item["attempts"], inputs, strict=True):
            attempt["usage"] = {"input_tokens": count, "output_tokens": count // 10}
        item["block_comparison"] = compare_blocks(item["attempts"], set(DEFINITIONS))
    result = target.aggregate([first, second], [DEFINITIONS, DEFINITIONS])
    comparison = result["token_comparisons"]["candidate"]
    assert comparison["planned_tasks"] == 2
    assert comparison["fully_comparable_tasks"] == 2
    assert comparison["planned_blocks"] == 3
    assert comparison["comparable_blocks"] == 3
    assert comparison["equal_task_weight_mean_delta"]["input_tokens"] == {"numerator": 5, "denominator": 1}
    assert comparison["equal_task_weight_mean_delta"]["output_tokens"] == {"numerator": 1, "denominator": 2}
    assert comparison["tasks"][0]["mean_delta"]["input_tokens"] == {"numerator": 20, "denominator": 1}


@pytest.mark.parametrize(
    "status,usage", [("task_passed", None), ("task_failed", {"input_tokens": 50, "output_tokens": 5})]
)
def test_missing_or_nonpassing_paired_usage_prevents_aggregate(status, usage):
    first = report("a", ["task_passed"], ["task_passed"])
    second = report("b", ["task_passed"], [status])
    for item in (first, second):
        for attempt in item["attempts"]:
            attempt["usage"] = {"input_tokens": 100, "output_tokens": 10}
    second["attempts"][1]["usage"] = usage
    for item in (first, second):
        item["block_comparison"] = compare_blocks(item["attempts"], set(DEFINITIONS))
    result = target.aggregate([first, second], [DEFINITIONS, DEFINITIONS])
    comparison = result["token_comparisons"]["candidate"]
    assert comparison["planned_blocks"] == 2
    assert comparison["comparable_blocks"] == 1
    assert comparison["fully_comparable_tasks"] == 1
    assert comparison["equal_task_weight_mean_delta"] is None
    assert comparison["tasks"][1]["mean_delta"] is None


def test_inconsistent_paired_block_data_is_rejected():
    item = report("a", ["task_passed"], ["task_passed"])
    for attempt in item["attempts"]:
        attempt["usage"] = {"input_tokens": 100, "output_tokens": 10}
    item["block_comparison"] = compare_blocks(item["attempts"], set(DEFINITIONS))
    item["block_comparison"]["comparisons"]["candidate"]["blocks"][0]["token_delta"]["input_tokens"] = 99
    with pytest.raises(ValueError, match="disagree with the attempts"):
        target.aggregate([item], [DEFINITIONS])


def test_paired_token_task_means_remain_exact_fractions():
    first = report("a", ["task_passed", "task_passed"], ["task_passed", "task_passed"])
    second = report("b", ["task_passed"], ["task_passed"])
    for item, inputs in ((first, (100, 100, 101, 102)), (second, (100, 100))):
        for attempt, count in zip(item["attempts"], inputs, strict=True):
            attempt["usage"] = {"input_tokens": count, "output_tokens": 0}
        item["block_comparison"] = compare_blocks(item["attempts"], set(DEFINITIONS))
    result = target.aggregate([first, second], [DEFINITIONS, DEFINITIONS])
    assert result["token_comparisons"]["candidate"]["equal_task_weight_mean_delta"]["input_tokens"] == {
        "numerator": 3,
        "denominator": 4,
    }


def test_empty_token_task_set_is_rejected():
    with pytest.raises(ValueError, match="nonempty"):
        target.summarize_paired_tokens([], "candidate")


@pytest.mark.parametrize("status", ["harness_error", "invalid_scope", "timed_out"])
def test_unscored_attempts_are_not_failures_or_dropped(status):
    reports = [report("a", ["task_passed"], ["task_passed"]), report("b", ["task_passed"], [status])]
    result = target.aggregate(reports, [DEFINITIONS, DEFINITIONS])
    assert result["comparisons"]["candidate"]["unscored_tasks"] == 1
    assert result["comparisons"]["candidate"]["equal_task_weight_mean_difference"] is None
    assert result["tasks"][1]["attempt_status_counts"]["candidate"][status] == 1
    assert result["tasks"][1]["pass_rates"]["candidate"] is None


def test_duplicate_ids_and_condition_changes_are_rejected():
    a = report("a", ["task_passed"], ["task_passed"])
    with pytest.raises(ValueError, match="unique"):
        target.aggregate([a, copy.deepcopy(a)], [DEFINITIONS, DEFINITIONS])
    b = report("b", ["task_passed"], ["task_passed"])
    changed = {"default": {"skills": []}, "candidate": {"skills": ["different-bundle"]}}
    with pytest.raises(ValueError, match="definitions differ"):
        target.aggregate([a, b], [DEFINITIONS, changed])


@pytest.mark.parametrize(
    "field,value", [("model_requested", "other"), ("reasoning_effort_requested", "low"), ("partition", "holdout")]
)
def test_mixed_experiment_conditions_are_rejected(field, value):
    a = report("a", ["task_passed"], ["task_passed"])
    b = report("b", ["task_passed"], ["task_passed"])
    b[field] = value
    with pytest.raises(ValueError, match="differ"):
        target.aggregate([a, b], [DEFINITIONS, DEFINITIONS])


def test_planned_denominator_mismatch_is_rejected():
    a = report("a", ["task_passed"], ["task_passed"])
    a["conditions"]["candidate"]["planned_attempts"] = 2
    with pytest.raises(ValueError, match="denominator"):
        target.aggregate([a], [DEFINITIONS])


def test_missing_planned_task_fails_without_creating_report(tmp_path, capsys):
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tasks": [{"id": "x", "protocol": "missing.json", "protocol_sha256": "x", "trials": "trials"}],
            }
        ),
        encoding="utf-8",
    )
    assert target.main(["--plan", str(plan)]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_plan_rejects_duplicate_json_keys(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text('{"schema_version": 1, "tasks": [], "tasks": []}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        target.run_plan(plan)


def test_model_snapshot_availability_is_preserved():
    item = report("a", ["task_passed", "task_passed"], ["task_passed", "task_passed"])
    item["attempts"][0]["provider_model_snapshot"] = "snapshot-a"
    item["attempts"][2]["provider_model_snapshot"] = "snapshot-b"
    result = target.aggregate([item], [DEFINITIONS])
    snapshots = result["tasks"][0]["provider_model_snapshots"]
    assert snapshots["default"] == {"unavailable_attempts": 1, "reported_counts": {"snapshot-a": 1}}
    assert snapshots["candidate"] == {"unavailable_attempts": 1, "reported_counts": {"snapshot-b": 1}}


def test_unplanned_condition_is_rejected():
    item = report("a", ["task_passed"], ["task_passed"])
    item["attempts"].append({"condition": "unexpected", "status": "task_passed"})
    with pytest.raises(ValueError, match="unplanned"):
        target.aggregate([item], [DEFINITIONS])


def test_plan_rejects_modified_protocol_before_loading_reports(tmp_path, monkeypatch):
    protocol = tmp_path / "protocol.json"
    protocol.write_text("{}", encoding="utf-8")
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tasks": [{"id": "x", "protocol": "protocol.json", "protocol_sha256": "0" * 64, "trials": "trials"}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(target, "summarize", lambda *args: pytest.fail("unmatched source must not be summarized"))
    with pytest.raises(ValueError, match="Protocol hash differs"):
        target.run_plan(plan)


def test_plan_changed_during_verification_is_rejected(tmp_path, monkeypatch):
    import hashlib

    protocol = tmp_path / "protocol.json"
    protocol.write_text(json.dumps({"conditions": DEFINITIONS}), encoding="utf-8")
    digest = hashlib.sha256(protocol.read_bytes()).hexdigest()
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tasks": [{"id": "a", "protocol": "protocol.json", "protocol_sha256": digest, "trials": "trials"}],
            }
        ),
        encoding="utf-8",
    )

    def changed(*args):
        plan.write_text(plan.read_text(encoding="utf-8") + " ", encoding="utf-8")
        result = report("a", ["task_passed"], ["task_passed"])
        result["protocol_sha256"] = digest
        return result

    monkeypatch.setattr(target, "summarize", changed)
    with pytest.raises(ValueError, match="changed during verification"):
        target.run_plan(plan)


def test_boolean_schema_version_is_not_an_integer_version(tmp_path):
    plan = tmp_path / "plan.json"
    plan.write_text('{"schema_version":true,"tasks":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid multi-task plan"):
        target.run_plan(plan)


def test_negative_and_positive_task_differences_are_weighted_exactly():
    first = report("a", ["task_failed"], ["task_passed"])
    second = report("b", ["task_passed", "task_passed"], ["task_passed", "task_failed"])
    result = target.aggregate([first, second], [DEFINITIONS, DEFINITIONS])
    assert result["comparisons"]["candidate"]["equal_task_weight_mean_difference"] == {"numerator": 1, "denominator": 4}
    assert result["tasks"][0]["limitations"] == ["fixture limitation"]
    assert result["tasks"][0]["attempts"] == first["attempts"]
    assert result["condition_definitions"] == DEFINITIONS


def test_boolean_and_integer_condition_parameters_are_not_equivalent():
    first = report("a", ["task_passed"], ["task_passed"])
    second = report("b", ["task_passed"], ["task_passed"])
    yes = {"default": {}, "candidate": {"flag": True}}
    one = {"default": {}, "candidate": {"flag": 1}}
    with pytest.raises(ValueError, match="definitions differ"):
        target.aggregate([first, second], [yes, one])


def test_historical_example_revalidates_recorded_attempts():
    root = Path(__file__).resolve().parents[1]
    plan = root / "benchmarks/agent-effectiveness/development/multi-task-historical-example.json"
    result = target.run_plan(plan)
    assert result["task_count"] == 1
    assert result["tasks"][0]["attempt_status_counts"]["default"]["task_passed"] == 3
    assert result["tasks"][0]["provider_model_snapshots"]["default"]["unavailable_attempts"] == 3
    assert result["comparisons"]["improved"]["equal_task_weight_mean_difference"] == {
        "numerator": 0,
        "denominator": 1,
    }
    assert result["quality_superiority_established"] is False


def test_two_task_plan_revalidates_each_complete_trial(matched, tmp_path):
    protocol, trials = matched
    other = tmp_path / "second"
    other.mkdir()
    second_protocol = other / "protocol.json"
    config = json.loads(protocol.read_text(encoding="utf-8"))
    config["task"]["id"] = "another-fixture"
    second_protocol.write_text(json.dumps(config), encoding="utf-8")
    second_hash = single.sha256(second_protocol)
    manifest = json.loads(protocol.with_name("protocol.grading.json").read_text(encoding="utf-8"))
    manifest["protocol_sha256"] = second_hash
    second_protocol.with_name("protocol.grading.json").write_text(json.dumps(manifest), encoding="utf-8")
    second_trials = other / "trials"
    shutil.copytree(trials, second_trials)
    for condition in config["conditions"]:
        directory = second_trials / "repetition-1" / condition
        launch = directory / "launch.json"
        launch.write_text(json.dumps({"protocol_sha256": second_hash}), encoding="utf-8")
        result_path = directory / "result.json"
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result["protocol_sha256"] = second_hash
        result["task_id"] = "another-fixture"
        result["evidence_sha256"]["launch.json"] = single.sha256(launch)
        result_path.write_text(json.dumps(result), encoding="utf-8")
    plan = tmp_path / "multi.json"
    plan.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tasks": [
                    {
                        "id": "independent-fixture",
                        "protocol": str(protocol),
                        "protocol_sha256": single.sha256(protocol),
                        "trials": str(trials),
                    },
                    {
                        "id": "another-fixture",
                        "protocol": str(second_protocol),
                        "protocol_sha256": second_hash,
                        "trials": str(second_trials),
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    report = target.run_plan(plan)
    assert report["task_count"] == 2
    assert report["comparisons"]["improved"]["equal_task_weight_mean_difference"] == {"numerator": 0, "denominator": 1}
    (second_trials / "repetition-1/improved/result.json").unlink()
    with pytest.raises(ValueError, match="has not completed"):
        target.run_plan(plan)


def test_plan_rejects_reusing_a_protocol_under_another_task_id(tmp_path, monkeypatch):
    import hashlib

    protocol = tmp_path / "protocol.json"
    protocol.write_text(json.dumps({"conditions": DEFINITIONS}), encoding="utf-8")
    digest = hashlib.sha256(protocol.read_bytes()).hexdigest()
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tasks": [
                    {"id": "a", "protocol": "protocol.json", "protocol_sha256": digest, "trials": "first"},
                    {"id": "b", "protocol": "protocol.json", "protocol_sha256": digest, "trials": "second"},
                ],
            }
        ),
        encoding="utf-8",
    )
    first = report("a", ["task_passed"], ["task_passed"])
    first["protocol_sha256"] = digest
    monkeypatch.setattr(target, "summarize", lambda *args: first)
    with pytest.raises(ValueError, match="occurs more than once"):
        target.run_plan(plan)

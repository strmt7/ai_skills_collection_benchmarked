import copy
import itertools
import json
import shutil
from fractions import Fraction
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


def test_paired_outcomes_show_opposing_task_effects_without_pooling_their_weights():
    reports = [
        report("a", ["task_passed"], ["task_failed"]),
        report("b", ["task_failed"] * 4, ["task_passed"] * 4),
    ]
    result = target.aggregate(reports, [DEFINITIONS, DEFINITIONS])
    paired = result["paired_outcomes"]["candidate"]
    assert paired["planned_tasks"] == 2
    assert paired["planned_blocks"] == 5
    assert paired["pooled_block_counts"]["candidate_only_passed"] == 4
    assert paired["pooled_block_counts"]["baseline_only_passed"] == 1
    assert paired["equal_task_weight_block_fractions"]["candidate_only_passed"] == {"numerator": 1, "denominator": 2}
    assert paired["equal_task_weight_block_fractions"]["baseline_only_passed"] == {"numerator": 1, "denominator": 2}
    assert paired["task_direction_counts"] == {
        "candidate_ahead": 1,
        "baseline_ahead": 1,
        "equal": 0,
        "unscored": 0,
    }
    assert result["comparisons"]["candidate"]["equal_task_weight_mean_difference"] == {
        "numerator": 0,
        "denominator": 1,
    }


def test_paired_outcomes_distinguish_agreement_from_opposing_wins():
    agreement = report("a", ["task_passed", "task_failed"], ["task_passed", "task_failed"])
    disagreement = report("b", ["task_passed", "task_failed"], ["task_failed", "task_passed"])
    first = target.aggregate([agreement], [DEFINITIONS])
    second = target.aggregate([disagreement], [DEFINITIONS])
    assert (
        first["comparisons"]["candidate"]["equal_task_weight_mean_difference"]
        == second["comparisons"]["candidate"]["equal_task_weight_mean_difference"]
    )
    assert first["paired_outcomes"]["candidate"]["pooled_block_counts"] == {
        "both_passed": 1,
        "candidate_only_passed": 0,
        "baseline_only_passed": 0,
        "neither_passed": 1,
        "unscored": 0,
    }
    assert second["paired_outcomes"]["candidate"]["pooled_block_counts"] == {
        "both_passed": 0,
        "candidate_only_passed": 1,
        "baseline_only_passed": 1,
        "neither_passed": 0,
        "unscored": 0,
    }


def test_paired_outcomes_keep_unscored_blocks_and_tasks_visible():
    reports = [
        report("a", ["task_passed"], ["timed_out"]),
        report("b", ["task_failed"] * 2, ["task_passed"] * 2),
    ]
    result = target.aggregate(reports, [DEFINITIONS, DEFINITIONS])
    paired = result["paired_outcomes"]["candidate"]
    assert paired["pooled_block_counts"]["unscored"] == 1
    assert paired["equal_task_weight_block_fractions"]["unscored"] == {"numerator": 1, "denominator": 2}
    assert paired["equal_task_weight_block_fractions"]["candidate_only_passed"] == {"numerator": 1, "denominator": 2}
    assert paired["task_direction_counts"]["unscored"] == 1
    assert paired["task_direction_counts"]["candidate_ahead"] == 1
    assert result["comparisons"]["candidate"]["equal_task_weight_mean_difference"] is None


@pytest.mark.parametrize("baseline,candidate", itertools.product(sorted(target.STATUSES), repeat=2))
def test_paired_outcome_fractions_partition_all_status_pairs(baseline, candidate):
    result = target.aggregate([report("a", [baseline], [candidate])], [DEFINITIONS])
    paired = result["paired_outcomes"]["candidate"]
    expected = {
        ("task_passed", "task_passed"): "both_passed",
        ("task_passed", "task_failed"): "baseline_only_passed",
        ("task_failed", "task_passed"): "candidate_only_passed",
        ("task_failed", "task_failed"): "neither_passed",
    }.get((baseline, candidate), "unscored")
    assert paired["pooled_block_counts"] == {outcome: int(outcome == expected) for outcome in target.OUTCOMES}
    assert paired["equal_task_weight_block_fractions"] == {
        outcome: {"numerator": int(outcome == expected), "denominator": 1} for outcome in target.OUTCOMES
    }


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


def test_all_attempt_usage_includes_failures_and_uses_equal_task_weight():
    first = report("a", ["task_passed"], ["task_failed"])
    second = report("b", ["task_passed", "timed_out"], ["task_passed", "harness_error"])
    for item, inputs in ((first, (10, 20)), (second, (20, 40, 30, 50))):
        for attempt, count in zip(item["attempts"], inputs, strict=True):
            attempt["usage"] = {"input_tokens": count, "output_tokens": count // 5}
        item["block_comparison"] = compare_blocks(item["attempts"], set(DEFINITIONS))
    result = target.aggregate([first, second], [DEFINITIONS, DEFINITIONS])
    usage = result["all_attempt_usage"]
    candidate = usage["conditions"]["candidate"]
    assert candidate["observed_token_totals"] == {"input_tokens": 100, "output_tokens": 20}
    assert candidate["by_status"]["harness_error"] == {
        "attempts": 1,
        "usage_observed_attempts": 1,
        "observed_token_totals": {"input_tokens": 50, "output_tokens": 10},
    }
    assert usage["condition_minus_default"]["candidate"] == {
        "input_tokens": {"numerator": 10, "denominator": 1},
        "output_tokens": {"numerator": 2, "denominator": 1},
    }
    assert result["token_comparisons"]["candidate"]["equal_task_weight_mean_delta"] is None
    assert result["quality_superiority_established"] is False


def test_all_attempt_usage_keeps_missing_values_and_observed_zero_distinct():
    item = report("a", ["task_passed", "timed_out"], ["task_failed", "harness_error"])
    for attempt, usage in zip(
        item["attempts"],
        ({"input_tokens": 0, "output_tokens": 0}, None, {"input_tokens": 7, "output_tokens": 3}, None),
        strict=True,
    ):
        attempt["usage"] = usage
    item["block_comparison"] = compare_blocks(item["attempts"], set(DEFINITIONS))
    summary = target.aggregate([item], [DEFINITIONS])["all_attempt_usage"]
    assert summary["conditions"]["default"]["observed_token_totals"] == {"input_tokens": 0, "output_tokens": 0}
    assert summary["conditions"]["default"]["usage_unavailable_attempts"] == 1
    assert summary["conditions"]["candidate"]["observed_token_totals"] == {"input_tokens": 7, "output_tokens": 3}
    assert summary["conditions"]["candidate"]["equal_task_weight_mean_tokens_per_attempt"] is None
    assert summary["conditions"]["candidate"]["by_status"]["harness_error"]["observed_token_totals"] is None
    assert summary["condition_minus_default"]["candidate"] is None


def test_all_attempt_usage_availability_matches_exhaustive_observation_patterns():
    """Check every missing/present pattern against separately calculated subtotals."""
    for present in itertools.product((False, True), repeat=4):
        reports = [
            report("a", ["task_passed"], ["task_failed"]),
            report("b", ["timed_out"], ["harness_error"]),
        ]
        counts = (0, 4, 5, 0)
        for index, attempt in enumerate(item for task in reports for item in task["attempts"]):
            attempt["usage"] = {"input_tokens": counts[index], "output_tokens": 0} if present[index] else None
        for item in reports:
            item["block_comparison"] = compare_blocks(item["attempts"], set(DEFINITIONS))
        usage = target.aggregate(reports, [DEFINITIONS, DEFINITIONS])["all_attempt_usage"]
        for condition, indices in (("default", (0, 2)), ("candidate", (1, 3))):
            values = [counts[i] for i in indices if present[i]]
            result = usage["conditions"][condition]
            assert result["usage_observed_attempts"] == len(values)
            assert result["observed_token_totals"] == (
                {"input_tokens": sum(values), "output_tokens": 0} if values else None
            )
            assert (result["equal_task_weight_mean_tokens_per_attempt"] is not None) == (len(values) == 2)
        assert (usage["condition_minus_default"]["candidate"] is not None) == all(present)


@pytest.mark.parametrize(
    "invalid",
    [{"input_tokens": True, "output_tokens": 0}, {"input_tokens": 1, "output_tokens": 0, "cached_input_tokens": 2}],
)
def test_all_attempt_usage_rejects_invalid_counts_even_for_unscored_attempts(invalid):
    item = report("a", ["task_passed"], ["harness_error"])
    item["attempts"][1]["usage"] = invalid
    item["block_comparison"] = compare_blocks(item["attempts"], set(DEFINITIONS))
    with pytest.raises(ValueError, match="usage|token"):
        target.aggregate([item], [DEFINITIONS])


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


@pytest.mark.parametrize("missing_status", ["harness_error", "invalid_scope", "timed_out"])
def test_missing_outcome_bounds_match_exhaustive_binary_completions(missing_status):
    """Enumerate hypothetical completions independently of the bound calculation."""
    original = [
        (["task_passed", missing_status], ["task_failed", missing_status]),
        ([missing_status], ["task_passed"]),
    ]
    reports = [report(str(index), baseline, candidate) for index, (baseline, candidate) in enumerate(original)]
    result = target.aggregate(reports, [DEFINITIONS] * len(reports))
    assert result["comparisons"]["candidate"]["equal_task_weight_mean_difference"] is None
    bounds = result["missing_outcome_sensitivity"]["candidate"]
    positions = [
        (task, condition, index)
        for task, groups in enumerate(original)
        for condition, statuses in enumerate(groups)
        for index, status in enumerate(statuses)
        if status == missing_status
    ]
    means = []
    for assignment in itertools.product(("task_passed", "task_failed"), repeat=len(positions)):
        completed = [[list(group) for group in groups] for groups in original]
        for (task, condition, index), status in zip(positions, assignment, strict=True):
            completed[task][condition][index] = status
        differences = [
            Fraction(candidate.count("task_passed"), len(candidate))
            - Fraction(baseline.count("task_passed"), len(baseline))
            for baseline, candidate in completed
        ]
        means.append(sum(differences, Fraction()) / len(differences))
    assert Fraction(**bounds["equal_task_weight_lower"]) == min(means)
    assert Fraction(**bounds["equal_task_weight_upper"]) == max(means)
    assert bounds["tasks_with_unscored_attempts"] == 2
    assert result["quality_superiority_established"] is False


def test_complete_and_fully_unscored_sensitivity_extremes():
    complete = report("a", ["task_failed", "task_passed"], ["task_passed", "task_passed"])
    result = target.aggregate([complete], [DEFINITIONS])
    bounds = result["missing_outcome_sensitivity"]["candidate"]
    assert bounds["equal_task_weight_lower"] == bounds["equal_task_weight_upper"] == {"numerator": 1, "denominator": 2}
    assert bounds["tasks_with_unscored_attempts"] == 0
    unscored = report("b", ["harness_error"], ["timed_out"])
    bounds = target.aggregate([unscored], [DEFINITIONS])["missing_outcome_sensitivity"]["candidate"]
    assert bounds["equal_task_weight_lower"] == {"numerator": -1, "denominator": 1}
    assert bounds["equal_task_weight_upper"] == {"numerator": 1, "denominator": 1}


def test_all_two_block_status_patterns_match_enumerated_bounds():
    statuses = ("task_passed", "task_failed", "harness_error")
    for pattern in itertools.product(statuses, repeat=4):
        baseline, candidate = pattern[:2], pattern[2:]
        result = target.aggregate([report("a", baseline, candidate)], [DEFINITIONS])
        bounds = result["missing_outcome_sensitivity"]["candidate"]
        positions = [index for index, value in enumerate(pattern) if value == "harness_error"]
        possible = []
        for assignment in itertools.product(("task_passed", "task_failed"), repeat=len(positions)):
            completed = list(pattern)
            for index, value in zip(positions, assignment, strict=True):
                completed[index] = value
            possible.append(Fraction(completed[2:].count("task_passed") - completed[:2].count("task_passed"), 2))
        assert Fraction(**bounds["equal_task_weight_lower"]) == min(possible)
        assert Fraction(**bounds["equal_task_weight_upper"]) == max(possible)


def test_missing_outcome_bounds_keep_condition_identity():
    definitions = {**DEFINITIONS, "other": {"skills": ["other-bundle"]}}
    item = report("a", ["task_passed"], ["harness_error"])
    item["attempts"].append({"repetition": 1, "condition": "other", "status": "task_passed", "usage": None})
    item["conditions"]["other"] = {"planned_attempts": 1}
    item["block_comparison"] = compare_blocks(item["attempts"], set(definitions))
    bounds = target.aggregate([item], [definitions])["missing_outcome_sensitivity"]
    assert bounds["candidate"]["equal_task_weight_lower"] == {"numerator": -1, "denominator": 1}
    assert bounds["candidate"]["equal_task_weight_upper"] == {"numerator": 0, "denominator": 1}
    assert (
        bounds["other"]["equal_task_weight_lower"]
        == bounds["other"]["equal_task_weight_upper"]
        == {
            "numerator": 0,
            "denominator": 1,
        }
    )


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


def test_snapshot_evidence_identifies_mismatch_and_missing_pairs():
    item = report("a", ["task_passed", "task_passed"], ["task_passed", "task_passed"])
    item["attempts"][0]["provider_model_snapshot"] = "snapshot-a"
    item["attempts"][2]["provider_model_snapshot"] = "snapshot-b"
    result = target.aggregate([item], [DEFINITIONS])
    assert result["model_snapshot_evidence"]["candidate"] == {
        "planned_pairs": 2,
        "same_reported_identifier_pairs": 0,
        "different_reported_identifier_pairs": 1,
        "incomplete_pairs": 1,
        "reported_identifiers": ["snapshot-a", "snapshot-b"],
        "status": "inconsistent_reported_identifiers",
    }
    assert result["comparisons"]["candidate"]["equal_task_weight_mean_difference"] == {
        "numerator": 0,
        "denominator": 1,
    }


@pytest.mark.parametrize(
    "snapshots, status",
    [
        ([(None, None), (None, None)], "incomplete"),
        ([("a", None), ("a", "a")], "incomplete"),
        ([("a", "a"), ("a", "a")], "single_reported_identifier"),
        ([("a", "a"), ("b", "b")], "inconsistent_reported_identifiers"),
    ],
)
def test_snapshot_evidence_classifies_across_tasks(snapshots, status):
    reports = [report("a", ["task_passed"], ["task_passed"]), report("b", ["task_passed"], ["task_passed"])]
    for item, (baseline, candidate) in zip(reports, snapshots, strict=True):
        item["attempts"][0]["provider_model_snapshot"] = baseline
        item["attempts"][1]["provider_model_snapshot"] = candidate
    evidence = target.aggregate(reports, [DEFINITIONS, DEFINITIONS])["model_snapshot_evidence"]["candidate"]
    assert evidence["status"] == status
    assert evidence["planned_pairs"] == 2


def test_snapshot_evidence_is_specific_to_each_candidate():
    item = report("a", ["task_passed"], ["task_passed"])
    item["attempts"][0]["provider_model_snapshot"] = "a"
    item["attempts"][1]["provider_model_snapshot"] = "a"
    item["attempts"].append(
        {"repetition": 1, "condition": "other", "status": "task_passed", "usage": None, "provider_model_snapshot": "b"}
    )
    item["conditions"]["other"] = {"planned_attempts": 1}
    definitions = {**DEFINITIONS, "other": {"skills": ["other"]}}
    item["block_comparison"] = compare_blocks(item["attempts"], set(definitions))
    evidence = target.aggregate([item], [definitions])["model_snapshot_evidence"]
    assert evidence["candidate"]["status"] == "single_reported_identifier"
    assert evidence["other"]["status"] == "inconsistent_reported_identifiers"
    assert evidence["other"]["different_reported_identifier_pairs"] == 1


@pytest.mark.parametrize("invalid", ["", 42, False, ["snapshot"]])
def test_invalid_reported_snapshot_is_rejected(invalid):
    item = report("a", ["task_passed"], ["task_passed"])
    item["attempts"][0]["provider_model_snapshot"] = invalid
    with pytest.raises(ValueError, match="snapshots must be nonempty strings or null"):
        target.aggregate([item], [DEFINITIONS])


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

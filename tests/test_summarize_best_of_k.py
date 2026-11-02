"""Check recorded-subset metrics independently of the implementation's formula."""

from __future__ import annotations

import hashlib
import itertools
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

import pytest
import summarize_best_of_k as target
from _trial_comparisons import STATUSES

pytest_plugins = ("test_summarize_agent_trials",)


def observed_fraction(statuses: tuple[str, ...], k: int) -> Fraction:
    subsets = list(itertools.combinations(statuses, k))
    return Fraction(sum("task_passed" in subset for subset in subsets), len(subsets))


def report(tasks: list[tuple[list[str], list[str]]]) -> dict:
    rows = []
    for index, (baseline, candidate) in enumerate(tasks):
        counts = {}
        for name, statuses in (("default", baseline), ("candidate", candidate)):
            count = Counter(statuses)
            counts[name] = {status: count[status] for status in STATUSES}
        rows.append({"task_id": str(index), "attempt_status_counts": counts})
    return {
        "plan_sha256": "a" * 64,
        "partition": "development",
        "model_requested": "example",
        "reasoning_effort_requested": "high",
        "condition_definitions": {"default": {}, "candidate": {}},
        "task_count": len(rows),
        "tasks": rows,
    }


def test_subset_success_matches_explicit_combinations() -> None:
    for n in range(1, 9):
        for passed in range(n + 1):
            statuses = ("task_passed",) * passed + ("task_failed",) * (n - passed)
            for k in range(1, n + 1):
                assert target.subset_success(n, passed, k) == observed_fraction(statuses, k)


@pytest.mark.parametrize("args", [(0, 0, 1), (3, 4, 1), (3, -1, 1), (3, 1, 0), (3, 1, 4), (True, 1, 1)])
def test_invalid_counts_are_rejected(args: tuple[int, int, int]) -> None:
    with pytest.raises(ValueError):
        target.subset_success(*args)


def test_unknown_outcomes_bound_every_possible_assignment() -> None:
    for n in range(1, 6):
        for statuses in itertools.product(("task_passed", "task_failed", "timed_out"), repeat=n):
            for k in range(1, n + 1):
                result = target.analyze(report([(list(statuses), list(statuses))]), k, "default")
                row = result["tasks"][0]["conditions"]["candidate"]
                unknown = statuses.count("timed_out")
                possibilities = []
                for assignment in itertools.product(("task_passed", "task_failed"), repeat=unknown):
                    replacements = iter(assignment)
                    completed = tuple(next(replacements) if status == "timed_out" else status for status in statuses)
                    possibilities.append(observed_fraction(completed, k))
                assert Fraction(**row["missing_outcome_lower"]) == min(possibilities)
                assert Fraction(**row["missing_outcome_upper"]) == max(possibilities)
                assert (row["estimate"] is None) == (unknown > 0)


def test_unequal_attempt_counts_have_equal_task_weight_and_insufficient_k_is_visible() -> None:
    data = report(
        [
            (["task_passed", "task_failed", "task_failed"], ["task_passed", "task_passed", "task_failed"]),
            (["task_passed", "task_failed"], ["task_failed", "task_failed"]),
        ]
    )
    result = target.analyze(data, 2, "default")
    assert Fraction(**result["conditions"]["default"]["equal_task_weight_estimate"]) == Fraction(5, 6)
    assert Fraction(**result["conditions"]["candidate"]["equal_task_weight_estimate"]) == Fraction(1, 2)
    assert Fraction(**result["candidate_minus_baseline"]["candidate"]["estimate_difference"]) == Fraction(-1, 3)
    insufficient = target.analyze(data, 3, "default")
    assert insufficient["tasks"][1]["conditions"]["candidate"]["insufficient_attempts"] is True
    assert insufficient["conditions"]["candidate"]["equal_task_weight_estimate"] is None
    assert insufficient["candidate_minus_baseline"]["candidate"]["missing_lower_difference"] is None


def test_unscored_values_never_become_a_point_estimate() -> None:
    data = report([(["task_passed", "timed_out"], ["task_passed", "task_passed"])])
    result = target.analyze(data, 2, "default")
    baseline = result["conditions"]["default"]
    assert baseline["equal_task_weight_estimate"] is None
    assert Fraction(**baseline["equal_task_weight_missing_lower"]) == 1
    assert Fraction(**baseline["equal_task_weight_missing_upper"]) == 1
    assert result["candidate_minus_baseline"]["candidate"]["estimate_difference"] is None
    assert result["quality_superiority_established"] is False


def test_non_default_baseline_compares_its_own_attempts() -> None:
    data = report([(["task_passed", "task_passed"], ["task_passed", "task_failed"])])
    data["condition_definitions"]["karpathy"] = {}
    data["tasks"][0]["attempt_status_counts"]["karpathy"] = {
        status: 2 if status == "task_failed" else 0 for status in STATUSES
    }
    result = target.analyze(data, 1, "karpathy")
    assert Fraction(**result["candidate_minus_baseline"]["candidate"]["estimate_difference"]) == Fraction(1, 2)
    assert Fraction(**result["candidate_minus_baseline"]["default"]["estimate_difference"]) == 1


@pytest.mark.parametrize("k", [0, -1, 1001, True])
def test_invalid_k_and_baseline_are_rejected(k: int) -> None:
    with pytest.raises(ValueError):
        target.analyze(report([(["task_passed"], ["task_failed"])]), k, "default")
    with pytest.raises(ValueError):
        target.analyze(report([(["task_passed"], ["task_failed"])]), 1, "missing")


def test_cli_revalidates_real_trial_fixture(matched, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    protocol, trials = matched
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "tasks": [
                    {
                        "id": "independent-fixture",
                        "protocol": protocol.name,
                        "protocol_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
                        "trials": trials.name,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert target.main(["--plan", str(plan), "--k", "1"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True
    assert result["plan_sha256"] == hashlib.sha256(plan.read_bytes()).hexdigest()
    assert result["task_count"] == 1
    assert result["quality_superiority_established"] is False
    task = result["tasks"][0]
    assert len(task["attempts"]) == 2
    assert all(len(attempt["result_sha256"]) == 64 for attempt in task["attempts"])
    assert task["provider_model_snapshots"]["default"]["unavailable_attempts"] == 1
    altered = json.loads(plan.read_text(encoding="utf-8"))
    altered["tasks"][0]["protocol_sha256"] = "f" * 64
    plan.write_text(json.dumps(altered), encoding="utf-8")
    assert target.main(["--plan", str(plan), "--k", "1"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False

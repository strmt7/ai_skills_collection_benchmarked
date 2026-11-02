"""Validate exact paired analysis with independent finite-outcome enumeration."""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
import math
from fractions import Fraction
from pathlib import Path

import analyze_paired_task_outcomes as target
import pytest

pytest_plugins = ("test_summarize_agent_trials",)


def analysis_plan(**changes):
    plan = {
        "schema_version": 1,
        "trial_plan_sha256": "a" * 64,
        "partition": "holdout",
        "baseline": "default",
        "candidate": "candidate",
        "alternative": "greater",
        "family_comparisons": 2,
        "family_alpha": "0.05",
    }
    plan.update(changes)
    return plan


def task_report(pairs):
    tasks = []
    for index, (baseline, candidate) in enumerate(pairs):
        tasks.append(
            {
                "task_id": str(index),
                "attempts": [
                    {"condition": "default", "repetition": 1, "status": baseline},
                    {"condition": "candidate", "repetition": 1, "status": candidate},
                ],
            }
        )
    return {
        "plan_sha256": "a" * 64,
        "partition": "holdout",
        "model_requested": "model",
        "reasoning_effort_requested": "high",
        "condition_definitions": {"default": {}, "candidate": {}},
        "task_count": len(tasks),
        "tasks": tasks,
    }


def test_exact_tails_match_independent_coin_flip_enumeration():
    assert target.exact_p_value(0, 0, "greater") == 1
    assert target.exact_p_value(0, 0, "two-sided") == 1
    for n in range(1, 10):
        sample = [sum(sequence) for sequence in itertools.product((0, 1), repeat=n)]
        for wins in range(n + 1):
            greater = Fraction(sum(value >= wins for value in sample), len(sample))
            lower = Fraction(sum(value <= min(wins, n - wins) for value in sample), len(sample))
            assert target.exact_p_value(wins, n - wins, "greater") == greater
            assert target.exact_p_value(wins, n - wins, "two-sided") == min(Fraction(1), 2 * lower)


def test_analysis_preserves_direction_family_and_unverified_assumptions():
    pairs = [("task_failed", "task_passed")] * 8 + [("task_passed", "task_failed")] + [("task_passed", "task_passed")]
    result = target.analyze(task_report(pairs), analysis_plan())
    assert result["outcomes"] == {
        "both_passed": 1,
        "baseline_only_passed": 1,
        "candidate_only_passed": 8,
        "neither_passed": 0,
    }
    assert Fraction(**result["candidate_minus_baseline_pass_rate"]) == Fraction(7, 10)
    assert Fraction(**result["exact_conditional_p_value"]) == Fraction(5, 256)
    assert Fraction(**result["bonferroni_adjusted_p_value"]) == Fraction(5, 128)
    assert result["reject_equal_discordance_under_assumptions"] is True
    assert result["quality_superiority_established"] is False
    assert result["task_independence_verified"] is False
    assert result["preregistration_verified"] is False
    assert result["provider_model_identity_verified"] is False
    assert result["reported_snapshot_pairs"]["incomplete"] == 10
    reverse = target.analyze(task_report(pairs), analysis_plan(baseline="candidate", candidate="default"))
    assert Fraction(**reverse["candidate_minus_baseline_pass_rate"]) == Fraction(-7, 10)
    assert reverse["reject_equal_discordance_under_assumptions"] is False


def test_no_discordance_is_not_evidence_of_an_advantage():
    result = target.analyze(
        task_report([("task_passed", "task_passed"), ("task_failed", "task_failed")]), analysis_plan()
    )
    assert result["exact_conditional_p_value"] == {"numerator": 1, "denominator": 1}
    assert result["reject_equal_discordance_under_assumptions"] is False


@pytest.mark.parametrize("status", ["timed_out", "invalid_scope", "harness_error"])
def test_unscored_pairs_are_not_silently_filtered_or_failed(status):
    with pytest.raises(ValueError, match="Unscored"):
        target.analyze(task_report([("task_passed", status)]), analysis_plan())


def test_repeated_or_unmatched_attempts_are_refused():
    report = task_report([("task_passed", "task_passed")])
    extra = copy.deepcopy(report["tasks"][0]["attempts"][0])
    extra["repetition"] = 2
    report["tasks"][0]["attempts"].append(extra)
    with pytest.raises(ValueError, match="exactly one matched"):
        target.analyze(report, analysis_plan())
    report["tasks"][0]["attempts"].pop()
    report["tasks"][0]["attempts"][1]["repetition"] = 2
    with pytest.raises(ValueError, match="exactly one matched"):
        target.analyze(report, analysis_plan())


@pytest.mark.parametrize(
    "changes",
    [
        {"schema_version": True},
        {"trial_plan_sha256": "A" * 64},
        {"family_comparisons": True},
        {"family_comparisons": 0},
        {"family_comparisons": 1001},
        {"family_alpha": "NaN"},
        {"family_alpha": "0"},
        {"family_alpha": 0.05},
        {"alternative": "less"},
        {"candidate": "default"},
    ],
)
def test_invalid_analysis_plans_are_rejected(changes):
    with pytest.raises(ValueError):
        target.parse_plan(analysis_plan(**changes))


def test_mixed_or_unavailable_snapshot_evidence_is_not_hidden():
    report = task_report([("task_failed", "task_passed")] * 3)
    for task, values in zip(report["tasks"], (("one", "one"), ("one", "two"), (None, "one")), strict=True):
        for attempt, value in zip(task["attempts"], values, strict=True):
            attempt["provider_model_snapshot"] = value
    result = target.analyze(report, analysis_plan())
    assert result["reported_snapshot_pairs"] == {"same": 1, "different": 1, "incomplete": 1}
    assert result["distinct_reported_snapshot_identifiers"] == 2
    assert result["provider_model_identity_verified"] is False


def test_cli_revalidates_real_report_fixture_and_binds_the_plan(matched, tmp_path: Path, capsys):
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
    digest = hashlib.sha256(plan.read_bytes()).hexdigest()
    choices = tmp_path / "analysis.json"
    choices.write_text(
        json.dumps(analysis_plan(trial_plan_sha256=digest, partition="development", candidate="improved")),
        encoding="utf-8",
    )
    assert target.main(["--plan", str(plan), "--analysis-plan", str(choices)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True
    assert result["plan_sha256"] == digest
    assert result["analysis_plan_sha256"] == hashlib.sha256(choices.read_bytes()).hexdigest()
    assert result["outcomes"]["both_passed"] == 1
    choices.write_text(
        json.dumps(analysis_plan(trial_plan_sha256="f" * 64, partition="development", candidate="improved")),
        encoding="utf-8",
    )
    assert target.main(["--plan", str(plan), "--analysis-plan", str(choices)]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_non_default_reference_uses_its_own_matched_outcomes():
    report = task_report([("task_passed", "task_passed"), ("task_failed", "task_failed")])
    report["condition_definitions"]["karpathy"] = {}
    for task, status in zip(report["tasks"], ("task_failed", "task_passed"), strict=True):
        task["attempts"].append({"condition": "karpathy", "repetition": 1, "status": status})
    result = target.analyze(report, analysis_plan(baseline="karpathy"))
    assert result["outcomes"]["candidate_only_passed"] == 1
    assert result["outcomes"]["baseline_only_passed"] == 1
    assert result["candidate_minus_baseline_pass_rate"] == {"numerator": 0, "denominator": 1}


def test_partition_identity_and_condition_must_match_verified_report():
    report = task_report([("task_passed", "task_passed")])
    for plan in (
        analysis_plan(partition="development"),
        analysis_plan(trial_plan_sha256="b" * 64),
        analysis_plan(candidate="missing"),
    ):
        with pytest.raises(ValueError):
            target.analyze(report, plan)
    report["tasks"].append(copy.deepcopy(report["tasks"][0]))
    report["task_count"] = 2
    with pytest.raises(ValueError, match="unique"):
        target.analyze(report, analysis_plan())


def test_two_sided_tail_is_symmetric_and_single_sided_tail_is_directional():
    for wins, losses in ((0, 10), (1, 9), (3, 2), (10, 0)):
        assert target.exact_p_value(wins, losses, "two-sided") == target.exact_p_value(losses, wins, "two-sided")
        assert target.exact_p_value(wins, losses, "greater") + target.exact_p_value(losses, wins, "greater") >= 1


def direct_binomial_cdf(n, wins, p):
    return sum(math.comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(wins + 1))


def test_exact_binomial_upper_grid_matches_independent_tail_enumeration():
    tail = Fraction(1, 80)
    grid = 1 << 32
    for n in range(1, 9):
        for wins in range(n):
            upper = target._binomial_upper(wins, n, tail)
            assert (upper * grid).denominator == 1

            assert direct_binomial_cdf(n, wins, upper) <= tail
            assert direct_binomial_cdf(n, wins, upper - Fraction(1, grid)) > tail
        assert target._binomial_upper(n, n, tail) == 1


def test_paired_intervals_cover_small_exact_multinomial_distributions():
    alpha = Fraction(1, 10)
    # Exact enumeration includes negative dependence of the win and loss
    # indicators. It is independent of the implementation's tail inversion.
    for n in range(1, 7):
        intervals = {
            (wins, losses): target.paired_difference_interval(wins, losses, n, alpha, 1)
            for wins in range(n + 1)
            for losses in range(n - wins + 1)
        }
        for a in range(5):
            for b in range(5 - a):
                p, q = Fraction(a, 4), Fraction(b, 4)
                covered = Fraction()
                for (wins, losses), (lower, upper) in intervals.items():
                    probability = (
                        math.comb(n, wins)
                        * math.comb(n - wins, losses)
                        * p**wins
                        * q**losses
                        * (1 - p - q) ** (n - wins - losses)
                    )
                    if lower <= p - q <= upper:
                        covered += probability
                assert covered >= 1 - alpha


def test_interval_direction_and_family_adjustment():
    alpha = Fraction(1, 20)
    lower, upper = target.paired_difference_interval(8, 1, 10, alpha, 1)
    reverse_lower, reverse_upper = target.paired_difference_interval(1, 8, 10, alpha, 1)
    assert (reverse_lower, reverse_upper) == (-upper, -lower)
    assert lower <= Fraction(7, 10) <= upper
    family_lower, family_upper = target.paired_difference_interval(8, 1, 10, alpha, 10)
    assert family_lower <= lower <= upper <= family_upper
    result = target.analyze(
        task_report(
            [("task_failed", "task_passed")] * 8 + [("task_passed", "task_failed")] + [("task_passed", "task_passed")]
        ),
        analysis_plan(),
    )
    interval = result["familywise_candidate_minus_baseline_interval"]
    assert Fraction(**interval["confidence_level"]) == Fraction(19, 20)
    assert (Fraction(**interval["lower"]), Fraction(**interval["upper"])) == (
        target.paired_difference_interval(8, 1, 10, alpha, 2)
    )


@pytest.mark.parametrize(
    "args",
    [
        (-1, 0, 1, Fraction(1, 20), 1),
        (1, 1, 1, Fraction(1, 20), 1),
        (0, 0, 0, Fraction(1, 20), 1),
        (0, 0, 1, Fraction(0), 1),
        (0, 0, 1, Fraction(1, 20), True),
    ],
)
def test_invalid_interval_parameters_are_rejected(args):
    with pytest.raises(ValueError, match="Invalid paired interval"):
        target.paired_difference_interval(*args)


@pytest.mark.parametrize(
    ("n", "wins", "losses", "family", "reference_lower", "reference_upper"),
    [
        (10, 8, 1, 2, -0.168782977526363, 0.9871990651865448),
        (100, 35, 20, 1, -0.05961208699810197, 0.34786956913242717),
        (1000, 500, 200, 2, 0.2266569871313612, 0.3705954548665743),
        (1, 1, 0, 1, -0.975, 1.0),
        (20, 0, 0, 1, -0.19675967970462538, 0.19675967970462538),
    ],
)
def test_interval_matches_independent_beta_quantile_reference(
    n, wins, losses, family, reference_lower, reference_upper
):
    # Reference endpoints were independently generated using SciPy 1.18.1
    # beta quantiles, not the implementation's integer binomial-tail inversion.
    lower, upper = target.paired_difference_interval(wins, losses, n, Fraction(1, 20), family)
    assert float(lower) <= reference_lower + 1e-12
    assert float(upper) >= reference_upper - 1e-12
    assert float(lower) == pytest.approx(reference_lower, abs=5e-10)
    assert float(upper) == pytest.approx(reference_upper, abs=5e-10)

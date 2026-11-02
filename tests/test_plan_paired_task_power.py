"""Independent small-sample checks for prospective paired-task power."""

from __future__ import annotations

import itertools
import json
import math
from decimal import Decimal
from fractions import Fraction

import pytest
from plan_paired_task_power import critical_tail, main, power


def enumerate_task_pairs(tasks: int, candidate: Fraction, baseline: Fraction, alpha: Fraction) -> Fraction:
    """Enumerate every three-state task sequence and its exact null tail."""
    probabilities = {1: candidate, -1: baseline, 0: 1 - candidate - baseline}
    result = Fraction()
    for outcomes in itertools.product((-1, 0, 1), repeat=tasks):
        wins = outcomes.count(1)
        losses = outcomes.count(-1)
        discordant = wins + losses
        if not discordant:
            continue
        smaller = min(wins, losses)
        p_value = Fraction(2 * sum(math.comb(discordant, k) for k in range(smaller + 1)), 2**discordant)
        if p_value <= alpha:
            result += math.prod(probabilities[outcome] for outcome in outcomes)
    return result


@pytest.mark.parametrize("candidate,baseline", [("0.4", "0.1"), ("0.25", "0.25"), ("1", "0")])
@pytest.mark.parametrize("tasks", [4, 5, 6, 7])
def test_small_sample_matches_explicit_sequence_enumeration(tasks: int, candidate: str, baseline: str) -> None:
    alpha = Fraction(1, 8)
    expected = enumerate_task_pairs(tasks, Fraction(candidate), Fraction(baseline), alpha)
    assert power(tasks, Decimal(candidate), Decimal(baseline), alpha) == pytest.approx(float(expected), abs=1e-13)


def test_exact_boundary_and_null_case() -> None:
    assert critical_tail(6, Fraction(1, 32)) == 0
    assert critical_tail(6, Fraction(1, 33)) == -1
    assert power(6, Decimal("0.5"), Decimal("0.5"), Fraction(1, 32)) == pytest.approx(1 / 32)
    assert power(100, Decimal(0), Decimal(0), Fraction(1, 20)) == 0
    assert power(6, Decimal(1), Decimal(0), Fraction(1, 32)) == pytest.approx(1)


def test_direction_symmetry_and_bonferroni() -> None:
    a, b = Decimal("0.35"), Decimal("0.1")
    unadjusted = power(40, a, b, Fraction(1, 20))
    assert power(40, b, a, Fraction(1, 20)) == pytest.approx(unadjusted)
    assert power(40, a, b, Fraction(1, 40)) <= unadjusted


@pytest.mark.parametrize(
    "tasks,candidate,baseline,alpha,expected",
    [
        (20, "0.3", "0.1", "0.05", 0.17370558536171574),
        (40, "0.45", "0.15", "0.05", 0.636285176962004),
        (50, "0.1", "0.3", "0.025", 0.4245057211283559),
        (80, "0.2", "0.2", "0.05", 0.03137762475818667),
    ],
)
def test_scipy_reference_values(tasks: int, candidate: str, baseline: str, alpha: str, expected: float) -> None:
    assert power(tasks, Decimal(candidate), Decimal(baseline), Fraction(alpha)) == pytest.approx(expected, abs=1e-12)


def test_cli_reports_assumptions_and_exact_threshold(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--tasks", "50", "--candidate-only", "0.3", "--baseline-only", "0.1", "--comparisons", "2"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["independent_scored_task_pairs"] == 50
    assert result["assumed_pass_rate_difference"] == {"numerator": 1, "denominator": 5}
    assert result["per_comparison_alpha"] == {"numerator": 1, "denominator": 40}
    assert 0 < result["power"] < 1
    assert any("unscored" in note for note in result["limitations"])


@pytest.mark.parametrize(
    "arguments",
    [
        ["--tasks", "0", "--candidate-only", "0.3", "--baseline-only", "0.1"],
        ["--tasks", "1", "--candidate-only", "0.9", "--baseline-only", "0.2"],
        [
            "--tasks",
            "1",
            "--candidate-only",
            "0.9999999999999999999999999999",
            "--baseline-only",
            "0.0000000000000000000000000002",
        ],
        ["--tasks", "1", "--candidate-only", "NaN", "--baseline-only", "0.2"],
        ["--tasks", "1", "--candidate-only", "1e-101", "--baseline-only", "0.2"],
        ["--tasks", "1", "--candidate-only", "0.1", "--baseline-only", "0.2", "--alpha", "0"],
        ["--tasks", "1", "--candidate-only", "0.1", "--baseline-only", "0.2", "--comparisons", "0"],
    ],
)
def test_invalid_arguments_fail(arguments: list[str]) -> None:
    with pytest.raises(SystemExit) as error:
        main(arguments)
    assert error.value.code == 2

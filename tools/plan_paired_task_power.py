"""Prospective power for an exact paired binary test on independent tasks.

This tool models one scored comparison per independently sampled task. It does
not analyze recorded trials or turn repeated attempts into independent tasks.
"""

from __future__ import annotations

import argparse
import json
import math
from decimal import Decimal, InvalidOperation
from fractions import Fraction


def probability(value: str) -> Decimal:
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("must be a finite probability between 0 and 1") from exc
    if not result.is_finite() or not 0 <= result <= 1:
        raise argparse.ArgumentTypeError("must be a finite probability between 0 and 1")
    exponent = result.as_tuple().exponent
    if len(result.as_tuple().digits) > 100 or not isinstance(exponent, int) or not -100 <= exponent <= 100:
        raise argparse.ArgumentTypeError("probability precision and exponent must be within 100 decimal places")
    return result


def critical_tail(discordant: int, alpha: Fraction) -> int:
    """Largest lower tail rejected by the two-sided exact conditional test."""
    total = 1 << discordant
    term = 1
    cumulative = 0
    cutoff = -1
    for wins in range((discordant + 1) // 2):
        cumulative += term
        if 2 * cumulative * alpha.denominator > total * alpha.numerator:
            break
        cutoff = wins
        term = term * (discordant - wins) // (wins + 1)
    return cutoff


def binomial_probability(n: int, k: int, p: float) -> float:
    if p == 0:
        return float(k == 0)
    if p == 1:
        return float(k == n)
    return math.exp(
        math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * math.log(p) + (n - k) * math.log1p(-p)
    )


def power(tasks: int, candidate_only: Decimal, baseline_only: Decimal, alpha: Fraction) -> float:
    """Enumerate discordance and conditional rejection probabilities."""
    candidate = Fraction(candidate_only)
    discordant_fraction = candidate + Fraction(baseline_only)
    if not discordant_fraction:
        return 0.0
    discordance = float(discordant_fraction)
    candidate_given_discordance = float(candidate / discordant_fraction)
    contributions = []
    for count in range(1, tasks + 1):
        cutoff = critical_tail(count, alpha)
        if cutoff < 0:
            continue
        rejection = math.fsum(
            binomial_probability(count, wins, candidate_given_discordance)
            for wins in (*range(cutoff + 1), *range(count - cutoff, count + 1))
        )
        contributions.append(binomial_probability(tasks, count, discordance) * rejection)
    return min(1.0, max(0.0, math.fsum(contributions)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", type=int, required=True, help="Independent scored task pairs (1 to 1000)")
    parser.add_argument("--candidate-only", type=probability, required=True, help="P(candidate passes, baseline fails)")
    parser.add_argument("--baseline-only", type=probability, required=True, help="P(baseline passes, candidate fails)")
    parser.add_argument("--alpha", type=probability, default=Decimal("0.05"), help="Family significance level")
    parser.add_argument("--comparisons", type=int, default=1, help="Number of prespecified tests (Bonferroni)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not 1 <= args.tasks <= 1000:
        parser.error("--tasks must be between 1 and 1000")
    candidate = Fraction(args.candidate_only)
    baseline = Fraction(args.baseline_only)
    if candidate + baseline > 1:
        parser.error("discordant probabilities must sum to at most 1")
    if not 0 < args.alpha < 1:
        parser.error("--alpha must be strictly between 0 and 1")
    if not 1 <= args.comparisons <= 1000:
        parser.error("--comparisons must be between 1 and 1000")
    adjusted = Fraction(args.alpha) / args.comparisons
    difference = candidate - baseline
    result = {
        "method": "two-sided exact conditional McNemar test with Bonferroni adjustment",
        "independent_scored_task_pairs": args.tasks,
        "candidate_only_probability": str(args.candidate_only),
        "baseline_only_probability": str(args.baseline_only),
        "assumed_pass_rate_difference": {"numerator": difference.numerator, "denominator": difference.denominator},
        "family_alpha": str(args.alpha),
        "prespecified_comparisons": args.comparisons,
        "per_comparison_alpha": {"numerator": adjusted.numerator, "denominator": adjusted.denominator},
        "power": power(args.tasks, args.candidate_only, args.baseline_only, adjusted),
        "limitations": [
            "Prospective calculation under fixed probabilities; not an observed agent result.",
            "Assumes independent, identically distributed task pairs and one scored comparison per task.",
            "Repeated runs on the same task, unscored outcomes, selection bias and model drift are not modeled.",
            "Power is for detecting either direction, not a probability that the candidate is superior.",
            "The exact conditional test may be conservative; probability sums use floating-point arithmetic.",
        ],
    }
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

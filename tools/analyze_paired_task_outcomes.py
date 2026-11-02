"""Analyze one scored paired outcome per task under an explicit statistical plan.

The calculation does not establish sampling independence, preregistration,
model identity, or superiority. Recorded trials must first pass the existing
multi-task verifier; repeated or unscored outcomes are not silently discarded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

from _trial_transcript import strict_json
from plan_paired_task_power import probability
from summarize_multi_task_trials import fraction, run_plan

PLAN_FIELDS = {
    "schema_version",
    "trial_plan_sha256",
    "partition",
    "baseline",
    "candidate",
    "alternative",
    "family_comparisons",
    "family_alpha",
}


def parse_plan(data: Any) -> dict[str, Any]:
    """Validate a separately recorded analysis choice without asserting when it was made."""
    if not isinstance(data, dict) or set(data) != PLAN_FIELDS:
        raise ValueError("Analysis plan fields differ from the required schema")
    if type(data["schema_version"]) is not int or data["schema_version"] != 1:
        raise ValueError("Invalid analysis plan version")
    digest = data["trial_plan_sha256"]
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("Analysis plan requires a lowercase trial-plan SHA-256")
    if any(not isinstance(data[key], str) or not data[key].strip() for key in ("partition", "baseline", "candidate")):
        raise ValueError("Partition and both conditions must be nonempty strings")
    if data["baseline"] == data["candidate"] or data["alternative"] not in ("greater", "two-sided"):
        raise ValueError("Choose distinct conditions and a supported alternative")
    comparisons = data["family_comparisons"]
    if type(comparisons) is not int or not 1 <= comparisons <= 1000:
        raise ValueError("Family comparisons must be an integer from 1 to 1000")
    if not isinstance(data["family_alpha"], str):
        raise ValueError("Family alpha must be a decimal string")
    try:
        alpha = probability(data["family_alpha"])
    except argparse.ArgumentTypeError as exc:
        raise ValueError("Invalid family alpha") from exc
    if not 0 < alpha < 1:
        raise ValueError("Family alpha must be strictly between 0 and 1")
    return data


def exact_p_value(candidate_only: int, baseline_only: int, alternative: str) -> Fraction:
    """Compute the exact conditional binomial tail under equal discordant probabilities."""
    if any(type(x) is not int or x < 0 for x in (candidate_only, baseline_only)):
        raise ValueError("Discordant counts must be nonnegative integers")
    n = candidate_only + baseline_only
    if n > 1000 or alternative not in ("greater", "two-sided"):
        raise ValueError("Unsupported discordance count or alternative")
    if not n:
        return Fraction(1)
    if alternative == "greater":
        numerator = sum(math.comb(n, k) for k in range(candidate_only, n + 1))
    else:
        numerator = min(1 << n, 2 * sum(math.comb(n, k) for k in range(min(candidate_only, baseline_only) + 1)))
    return Fraction(numerator, 1 << n)


# Fixed dyadic grid makes the exact binomial-tail comparisons reproducible.
# Rounding each upper endpoint outward preserves the coverage guarantee.
_INTERVAL_GRID = 1 << 32


def _binomial_cdf_at_most(n: int, successes: int, numerator: int, tail: Fraction) -> bool:
    """Compare a binomial CDF on the grid using integer arithmetic only."""
    if numerator == 0:
        return False  # CDF is one; tail is strictly below one.
    if numerator == _INTERVAL_GRID:
        return successes < n
    failure = _INTERVAL_GRID - numerator
    term = failure**n
    total = term
    for k in range(successes):
        term = term * (n - k) * numerator // ((k + 1) * failure)
        total += term
    return total * tail.denominator <= _INTERVAL_GRID**n * tail.numerator


def _binomial_upper(successes: int, n: int, tail: Fraction) -> Fraction:
    """One-sided Clopper-Pearson bound, rounded up on the fixed grid."""
    if successes == n:
        return Fraction(1)
    low, high = 0, _INTERVAL_GRID
    while low + 1 < high:
        middle = (low + high) // 2
        if _binomial_cdf_at_most(n, successes, middle, tail):
            high = middle
        else:
            low = middle
    return Fraction(high, _INTERVAL_GRID)


def paired_difference_interval(
    wins: int, losses: int, n: int, family_alpha: Fraction, family_size: int
) -> tuple[Fraction, Fraction]:
    """Return a conservative familywise interval for P(candidate only) - P(baseline only)."""
    if (
        any(type(value) is not int for value in (wins, losses, n, family_size))
        or not 1 <= n <= 1000
        or wins < 0
        or losses < 0
        or wins + losses > n
        or not 1 <= family_size <= 1000
        or not isinstance(family_alpha, Fraction)
        or not 0 < family_alpha < 1
    ):
        raise ValueError("Invalid paired interval parameters")
    # Four one-sided binomial bounds per comparison; the union bound controls
    # the full declared family without requiring win/loss independence.
    tail = family_alpha / (4 * family_size)
    win_upper = _binomial_upper(wins, n, tail)
    loss_upper = _binomial_upper(losses, n, tail)
    win_lower = 1 - _binomial_upper(n - wins, n, tail)
    loss_lower = 1 - _binomial_upper(n - losses, n, tail)
    return win_lower - loss_upper, win_upper - loss_lower


def analyze(report: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    """Analyze an already verified multi-task report according to the recorded plan."""
    plan = parse_plan(plan)
    if report["plan_sha256"] != plan["trial_plan_sha256"] or report["partition"] != plan["partition"]:
        raise ValueError("Analysis plan does not bind the verified trial plan and partition")
    baseline, candidate = plan["baseline"], plan["candidate"]
    definitions = report["condition_definitions"]
    if baseline not in definitions or candidate not in definitions:
        raise ValueError("Analysis conditions are not both in the verified trial plan")
    tasks = report["tasks"]
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 1000 or report["task_count"] != len(tasks):
        raise ValueError("One to 1000 verified tasks are required")
    ids = [task["task_id"] for task in tasks]
    if any(not isinstance(task_id, str) or not task_id for task_id in ids) or len(set(ids)) != len(ids):
        raise ValueError("Task identities must be unique nonempty strings")
    outcomes: Counter[str] = Counter()
    snapshots: Counter[str] = Counter()
    identifiers: set[str] = set()
    for task in tasks:
        attempts = task["attempts"]
        left = [row for row in attempts if row["condition"] == baseline]
        right = [row for row in attempts if row["condition"] == candidate]
        if len(left) != 1 or len(right) != 1 or left[0]["repetition"] != right[0]["repetition"]:
            raise ValueError("Each task requires exactly one matched attempt per compared condition")
        first, second = left[0], right[0]
        if first["status"] not in {"task_passed", "task_failed"} or second["status"] not in {
            "task_passed",
            "task_failed",
        }:
            raise ValueError("Unscored attempts cannot enter this analysis")
        first_pass = first["status"] == "task_passed"
        second_pass = second["status"] == "task_passed"
        outcome = (
            "both_passed"
            if first_pass and second_pass
            else "baseline_only_passed"
            if first_pass
            else "candidate_only_passed"
            if second_pass
            else "neither_passed"
        )
        outcomes[outcome] += 1
        first_snapshot = first.get("provider_model_snapshot")
        second_snapshot = second.get("provider_model_snapshot")
        if any(
            value is not None and (not isinstance(value, str) or not value)
            for value in (first_snapshot, second_snapshot)
        ):
            raise ValueError("Invalid reported snapshot identifier")
        identifiers.update(value for value in (first_snapshot, second_snapshot) if value is not None)
        snapshots[
            "incomplete"
            if first_snapshot is None or second_snapshot is None
            else "same"
            if first_snapshot == second_snapshot
            else "different"
        ] += 1
    wins, losses = outcomes["candidate_only_passed"], outcomes["baseline_only_passed"]
    p_value = exact_p_value(wins, losses, plan["alternative"])
    adjusted = min(Fraction(1), p_value * plan["family_comparisons"])
    alpha = Fraction(probability(plan["family_alpha"]))
    lower, upper = paired_difference_interval(wins, losses, len(tasks), alpha, plan["family_comparisons"])
    return {
        "method": "exact conditional paired binary test with Bonferroni adjustment",
        "plan_sha256": report["plan_sha256"],
        "partition": report["partition"],
        "model_requested": report["model_requested"],
        "reasoning_effort_requested": report["reasoning_effort_requested"],
        "baseline": baseline,
        "candidate": candidate,
        "alternative": plan["alternative"],
        "tasks": len(tasks),
        "outcomes": {
            name: outcomes[name]
            for name in ("both_passed", "baseline_only_passed", "candidate_only_passed", "neither_passed")
        },
        "candidate_minus_baseline_pass_rate": fraction(Fraction(wins - losses, len(tasks))),
        "familywise_candidate_minus_baseline_interval": {
            "lower": fraction(lower),
            "upper": fraction(upper),
            "confidence_level": fraction(1 - alpha),
            "method": "Bonferroni combination of outward-rounded exact binomial bounds",
        },
        "exact_conditional_p_value": fraction(p_value),
        "bonferroni_adjusted_p_value": fraction(adjusted),
        "family_comparisons": plan["family_comparisons"],
        "family_alpha": fraction(alpha),
        "reject_equal_discordance_under_assumptions": adjusted <= alpha,
        "reported_snapshot_pairs": {key: snapshots[key] for key in ("same", "different", "incomplete")},
        "distinct_reported_snapshot_identifiers": len(identifiers),
        "task_independence_verified": False,
        "preregistration_verified": False,
        "provider_model_identity_verified": False,
        "quality_superiority_established": False,
        "limitations": [
            "The conditional test assumes independent task pairs sampled from an appropriate target population and equal discordant probabilities under the null; these assumptions are not verified.",
            "One attempt per condition per task is required; unscored outcomes and repeated trials are rejected rather than counted as failures or independent tasks.",
            "The conservative difference interval assumes independent, identically distributed task pairs; it combines binomial bounds by a union bound across the complete declared family.",
            "The recorded analysis plan and matching hashes do not prove preregistration, holdout integrity, or absence of optional stopping or selective reporting.",
            "Bonferroni adjustment is only valid for a correctly specified complete family of comparisons; multiple looks and unrecorded tests are not controlled.",
            "A two-sided rejection is not evidence of improvement in a particular direction, and a p-value is not an effect size or probability of superiority.",
            "Provider snapshot identifiers are reported metadata, not independently authenticated model identity; missing or differing identifiers limit interpretation.",
            "This calculation does not establish model or skill superiority, generalization, grading authenticity, or causal effects.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True, help="Multi-task trial plan")
    parser.add_argument("--analysis-plan", type=Path, required=True, help="Recorded statistical analysis choices")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        raw = args.analysis_plan.read_bytes()
        plan = parse_plan(strict_json(raw.decode("utf-8")))
        report = run_plan(args.plan)
        result = analyze(report, plan)
        if args.analysis_plan.read_bytes() != raw:
            raise ValueError("Analysis plan changed during verification")
        result["analysis_plan_sha256"] = hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError, KeyError, TypeError, UnicodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

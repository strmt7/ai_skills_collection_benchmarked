"""Describe any-of-k or all-of-k outcomes from verified task reports.

The estimator describes uniformly selected subsets of recorded attempts. Its
use as a future-run probability additionally requires suitable sampling and
selection assumptions, which this tool cannot verify.
"""

from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction
from pathlib import Path
from typing import Any

from summarize_multi_task_trials import SCORED, STATUSES, fraction, run_plan


def subset_success(n: int, successes: int, k: int, *, rule: str = "any") -> Fraction:
    """Exact fraction of k-subsets with at least one pass or all passes."""
    if any(type(value) is not int for value in (n, successes, k)) or not 1 <= k <= n or not 0 <= successes <= n:
        raise ValueError("Require integer counts with 0 <= successes <= n and 1 <= k <= n")
    if rule not in {"any", "all"}:
        raise ValueError("Rule must be 'any' or 'all'")
    total = math.comb(n, k)
    if rule == "all":
        return Fraction(math.comb(successes, k) if successes >= k else 0, total)
    return 1 - Fraction(math.comb(n - successes, k) if n - successes >= k else 0, total)


def analyze(report: dict[str, Any], k: int, baseline: str, *, rule: str = "any") -> dict[str, Any]:
    """Summarize a verified multi-task report without discarding missing outcomes."""
    if rule not in {"any", "all"}:
        raise ValueError("Rule must be 'any' or 'all'")
    if type(k) is not int or not 1 <= k <= 1000:
        raise ValueError("k must be an integer from 1 to 1000")
    conditions = report["condition_definitions"]
    if not isinstance(conditions, dict) or baseline not in conditions:
        raise ValueError("Baseline must be a planned condition")
    tasks = report["tasks"]
    if not isinstance(tasks, list) or not tasks or report["task_count"] != len(tasks):
        raise ValueError("A nonempty verified task set is required")
    if len({task["task_id"] for task in tasks}) != len(tasks):
        raise ValueError("Task identities must be unique")

    values: dict[str, list[tuple[Fraction | None, Fraction | None, Fraction | None]]] = {
        name: [] for name in sorted(conditions)
    }
    task_results = []
    for task in tasks:
        rows = {}
        for condition in values:
            counts = task["attempt_status_counts"][condition]
            if set(counts) != STATUSES or any(type(value) is not int or value < 0 for value in counts.values()):
                raise ValueError("Invalid verified attempt-status counts")
            n = sum(counts.values())
            passed = counts["task_passed"]
            unscored = sum(count for status, count in counts.items() if status not in SCORED)
            if n < k:
                point = lower = upper = None
            else:
                lower = subset_success(n, passed, k, rule=rule)
                upper = subset_success(n, passed + unscored, k, rule=rule)
                point = lower if not unscored else None
            values[condition].append((point, lower, upper))
            rows[condition] = {
                "attempts": n,
                "passed": passed,
                "failed": counts["task_failed"],
                "unscored": unscored,
                "estimate": fraction(point),
                "missing_outcome_lower": fraction(lower),
                "missing_outcome_upper": fraction(upper),
                "insufficient_attempts": n < k,
            }
        task_results.append(
            {
                "task_id": task["task_id"],
                "protocol_sha256": task.get("protocol_sha256"),
                "grading_manifest_sha256": task.get("grading_manifest_sha256"),
                "attempts": task.get("attempts"),
                "provider_model_snapshots": task.get("provider_model_snapshots"),
                "prompt_runtime_evidence": task.get("prompt_runtime_evidence"),
                "conditions": rows,
            }
        )

    def mean(condition: str, index: int) -> Fraction | None:
        entries = [row[index] for row in values[condition]]
        if any(value is None for value in entries):
            return None
        return sum((value for value in entries if value is not None), Fraction()) / len(entries)

    summaries = {}
    comparisons = {}
    for condition in values:
        point, lower, upper = (mean(condition, index) for index in range(3))
        summaries[condition] = {
            "equal_task_weight_estimate": fraction(point),
            "equal_task_weight_missing_lower": fraction(lower),
            "equal_task_weight_missing_upper": fraction(upper),
        }
        if condition != baseline:
            base_point, base_lower, base_upper = (mean(baseline, index) for index in range(3))
            comparisons[condition] = {
                "estimate_difference": fraction(
                    point - base_point if point is not None and base_point is not None else None
                ),
                "missing_lower_difference": fraction(
                    lower - base_upper if lower is not None and base_upper is not None else None
                ),
                "missing_upper_difference": fraction(
                    upper - base_lower if upper is not None and base_lower is not None else None
                ),
            }
    return {
        "method": (
            "exact uniformly sampled k-subset success fraction, with equal task weights"
            if rule == "any"
            else "exact uniformly sampled k-subset all-success fraction, with equal task weights"
        ),
        "success_rule": rule,
        "plan_sha256": report["plan_sha256"],
        "partition": report["partition"],
        "model_requested": report["model_requested"],
        "reasoning_effort_requested": report["reasoning_effort_requested"],
        "baseline": baseline,
        "k": k,
        "task_count": len(tasks),
        "tasks": task_results,
        "conditions": summaries,
        "candidate_minus_baseline": comparisons,
        "quality_superiority_established": False,
        "limitations": [
            "The subset fraction is descriptive; generalizing to future attempts requires appropriate independent and identically distributed sampling, which is not verified.",
            (
                "Best-of-k assumes a way to select a passing candidate; this report does not establish a feasible selection process or account for its cost."
                if rule == "any"
                else "All-of-k requires every selected attempt to pass; it is not a worst-case guarantee or proof of future reliability."
            ),
            "Unscored attempts produce hypothetical assignment bounds rather than an observed estimate; those bounds are not confidence intervals.",
            "Tasks with fewer than k attempts prevent aggregate estimates and bounds for the affected condition.",
            "Adaptive retries, task selection, model drift, shared workspaces and graders can invalidate generalization or causal comparisons.",
            "Matching plan hashes and reported model names do not establish preregistration, grading authenticity or provider model identity.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True, help="Verified multi-task trial plan")
    parser.add_argument("--k", type=int, required=True, help="Number of attempts per sampled subset")
    parser.add_argument("--baseline", default="default", help="Planned reference condition")
    parser.add_argument("--rule", choices=("any", "all"), default="any", help="Require any or all attempts to pass")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = analyze(run_plan(args.plan), args.k, args.baseline, rule=args.rule)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

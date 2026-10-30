"""Describe matched repetition blocks without inferring an agent advantage."""

from __future__ import annotations

import statistics
from collections import Counter
from typing import Any

STATUSES = {"task_passed", "task_failed", "harness_error", "invalid_scope", "timed_out"}
SCORED = {"task_passed", "task_failed"}
OUTCOMES = ("both_passed", "candidate_only_passed", "baseline_only_passed", "neither_passed", "unscored")
TOKEN_KEYS = ("input_tokens", "output_tokens")


def _outcome(baseline: str, candidate: str) -> str:
    """Classify observed task outcomes without counting unscored runs as failures."""
    if baseline not in SCORED or candidate not in SCORED:
        return "unscored"
    if baseline == "task_passed" and candidate == "task_passed":
        return "both_passed"
    if candidate == "task_passed":
        return "candidate_only_passed"
    if baseline == "task_passed":
        return "baseline_only_passed"
    return "neither_passed"


def _token_delta(baseline: Any, candidate: Any) -> dict[str, int] | None:
    """Subtract observed baseline tokens only when both usages are present."""
    if baseline is None or candidate is None:
        return None
    if not isinstance(baseline, dict) or not isinstance(candidate, dict):
        raise ValueError("token usage must be an object or null")
    result = {}
    for key in TOKEN_KEYS:
        left, right = baseline.get(key), candidate.get(key)
        if type(left) is not int or type(right) is not int or left < 0 or right < 0:
            raise ValueError("token usage must contain nonnegative integer counts")
        result[key] = right - left
    return result


def _comparison(index: dict[tuple[int, str], dict[str, Any]], repetitions: list[int], candidate: str) -> dict[str, Any]:
    """Describe all blocks and the subset with two successful observed usages."""
    blocks = []
    for repetition in repetitions:
        baseline = index[repetition, "default"]
        trial = index[repetition, candidate]
        outcome = _outcome(baseline["status"], trial["status"])
        delta = _token_delta(baseline["usage"], trial["usage"]) if outcome == "both_passed" else None
        blocks.append(
            {
                "repetition": repetition,
                "baseline_status": baseline["status"],
                "candidate_status": trial["status"],
                "outcome": outcome,
                "token_delta": delta,
            }
        )
    counts = Counter(block["outcome"] for block in blocks)
    comparable = [block["token_delta"] for block in blocks if block["token_delta"] is not None]
    token_deltas = None
    if comparable:
        token_deltas = {}
        for key in TOKEN_KEYS:
            values = [delta[key] for delta in comparable]
            token_deltas[key] = {"median": statistics.median(values), "min": min(values), "max": max(values)}
    return {
        "planned_blocks": len(repetitions),
        "outcomes": {name: counts[name] for name in OUTCOMES},
        "token_comparable_blocks": len(comparable),
        "both_passed_usage_unavailable": counts["both_passed"] - len(comparable),
        "token_deltas": token_deltas,
        "blocks": blocks,
    }


def compare_blocks(rows: list[dict[str, Any]], conditions: set[str]) -> dict[str, Any]:
    """Compare every planned repetition against the explicit default condition."""
    index: dict[tuple[int, str], dict[str, Any]] = {}
    for row in rows:
        repetition, condition, status = row["repetition"], row["condition"], row["status"]
        if type(repetition) is not int or repetition < 1 or condition not in conditions or status not in STATUSES:
            raise ValueError("invalid repetition, condition or status")
        key = (repetition, condition)
        if key in index:
            raise ValueError("duplicate condition in repetition")
        index[key] = row
    repetitions = sorted({repetition for repetition, _ in index})
    if not repetitions or any(
        (repetition, condition) not in index for repetition in repetitions for condition in conditions
    ):
        raise ValueError("every repetition must contain all conditions")
    if "default" not in conditions:
        return {"baseline": None, "comparisons": {}}
    return {
        "baseline": "default",
        "comparisons": {name: _comparison(index, repetitions, name) for name in sorted(conditions - {"default"})},
    }

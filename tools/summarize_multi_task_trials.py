"""Aggregate verified single-task trial reports without treating attempts as independent tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any

from _trial_comparisons import SCORED, STATUSES
from _trial_transcript import strict_json
from summarize_agent_trials import summarize


def fraction(value: Fraction | None) -> dict[str, int] | None:
    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def aggregate(reports: list[dict[str, Any]], definitions: list[dict[str, Any]]) -> dict[str, Any]:
    """Describe equally weighted task differences; callers must verify reports first."""
    if not reports or len(reports) != len(definitions):
        raise ValueError("A nonempty definition is required for each task")
    ids = [report["task_id"] for report in reports]
    if any(not isinstance(item, str) or not item for item in ids) or len(set(ids)) != len(ids):
        raise ValueError("Task IDs must be nonempty and unique")
    if any(not isinstance(definition, dict) for definition in definitions):
        raise ValueError("Condition definitions must be objects")
    conditions = set(definitions[0])
    if "default" not in conditions or len(conditions) < 2:
        raise ValueError("A default and at least one comparison condition are required")

    def canonical(value: dict[str, Any]) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    if any(canonical(definition) != canonical(definitions[0]) for definition in definitions[1:]):
        raise ValueError("Condition definitions differ across tasks")
    model = reports[0]["model_requested"]
    effort = reports[0]["reasoning_effort_requested"]
    partition = reports[0]["partition"]
    if any(not isinstance(value, str) or not value for value in (model, effort, partition)):
        raise ValueError("Model, effort and partition must be nonempty strings")
    if any(
        report["model_requested"] != model
        or report["reasoning_effort_requested"] != effort
        or report["partition"] != partition
        or report["task_count"] != 1
        or set(report["conditions"]) != conditions
        for report in reports
    ):
        raise ValueError("Task reports differ in model, effort, partition, or condition set")

    rows = []
    for report in reports:
        counts = {}
        snapshots = {}
        rates: dict[str, Fraction | None] = {}
        if any(attempt["condition"] not in conditions for attempt in report["attempts"]):
            raise ValueError("Attempt has an unplanned condition")
        for condition in sorted(conditions):
            statuses = [attempt["status"] for attempt in report["attempts"] if attempt["condition"] == condition]
            if not statuses or any(status not in STATUSES for status in statuses):
                raise ValueError("A task has no attempts or an unknown status")
            planned = report["conditions"][condition]["planned_attempts"]
            if type(planned) is not int or planned < 1 or len(statuses) != planned:
                raise ValueError("Attempt count does not match the planned condition denominator")
            count = Counter(statuses)
            counts[condition] = {status: count[status] for status in sorted(STATUSES)}
            values = [
                attempt.get("provider_model_snapshot")
                for attempt in report["attempts"]
                if attempt["condition"] == condition
            ]
            if any(value is not None and (not isinstance(value, str) or not value) for value in values):
                raise ValueError("Reported model snapshots must be nonempty strings or null")
            snapshots[condition] = {
                "unavailable_attempts": sum(value is None for value in values),
                "reported_counts": dict(sorted(Counter(value for value in values if value is not None).items())),
            }
            rates[condition] = Fraction(count["task_passed"], planned) if all(s in SCORED for s in statuses) else None
        differences = {}
        for condition in sorted(conditions - {"default"}):
            baseline, candidate = rates["default"], rates[condition]
            differences[condition] = candidate - baseline if baseline is not None and candidate is not None else None
        rows.append(
            {
                "task_id": report["task_id"],
                "protocol_sha256": report["protocol_sha256"],
                "grading_manifest_sha256": report["grading_manifest_sha256"],
                "expected_grading_cases": report["expected_grading_cases"],
                "limitations": report["limitations"],
                "block_comparison": report["block_comparison"],
                "attempts": report["attempts"],
                "attempt_status_counts": counts,
                "provider_model_snapshots": snapshots,
                "pass_rates": {condition: fraction(value) for condition, value in rates.items()},
                "candidate_minus_default": {condition: fraction(value) for condition, value in differences.items()},
                "_differences": differences,
            }
        )
    comparisons = {}
    for condition in sorted(conditions - {"default"}):
        values = [row["_differences"][condition] for row in rows]
        complete = [value for value in values if value is not None]
        average = sum(complete, Fraction()) / len(rows) if len(complete) == len(rows) else None
        comparisons[condition] = {
            "planned_tasks": len(rows),
            "fully_scored_tasks": len(complete),
            "unscored_tasks": len(rows) - len(complete),
            "equal_task_weight_mean_difference": fraction(average),
        }
    for row in rows:
        del row["_differences"]
    return {
        "task_count": len(rows),
        "partition": partition,
        "model_requested": model,
        "reasoning_effort_requested": effort,
        "condition_definitions": definitions[0],
        "tasks": rows,
        "comparisons": comparisons,
        "quality_superiority_established": False,
        "limitations": [
            "Descriptive task-weighted differences do not establish statistical significance or generalization.",
            "Unscored attempts prevent an aggregate difference for the affected comparison.",
            "A frozen plan and matching hashes alone do not establish preregistration or grading authenticity.",
            "Requested model identity is not proof of the provider-resolved model snapshot.",
            "Task IDs and protocol hashes do not by themselves prove that tasks are independent.",
            "This report does not compare token cost or elapsed time across tasks.",
        ],
    }


def run_plan(path: Path) -> dict[str, Any]:
    """Verify every declared single-task report and condition before aggregation."""
    raw = path.read_bytes()
    plan = strict_json(raw.decode("utf-8"))
    if (
        not isinstance(plan, dict)
        or set(plan) != {"schema_version", "tasks"}
        or type(plan["schema_version"]) is not int
        or plan["schema_version"] != 1
    ):
        raise ValueError("Invalid multi-task plan")
    if not isinstance(plan["tasks"], list) or not plan["tasks"]:
        raise ValueError("Plan must list at least one task")
    reports = []
    definitions = []
    hashes = set()
    for item in plan["tasks"]:
        if not isinstance(item, dict) or set(item) != {"id", "protocol", "protocol_sha256", "trials"}:
            raise ValueError("Invalid task plan entry")
        if any(not isinstance(item[key], str) or not item[key] for key in item):
            raise ValueError("Task plan values must be nonempty strings")
        protocol = path.parent / item["protocol"]
        trials = path.parent / item["trials"]
        source = protocol.read_bytes()
        digest = hashlib.sha256(source).hexdigest()
        if digest != item["protocol_sha256"] or digest in hashes:
            raise ValueError("Protocol hash differs or occurs more than once")
        hashes.add(digest)
        config = strict_json(source.decode("utf-8"))
        report = summarize(protocol, trials)
        if report["protocol_sha256"] != digest or report["task_id"] != item["id"]:
            raise ValueError("Verified task identity does not match the plan")
        reports.append(report)
        definitions.append(config["conditions"])
    if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(raw).digest():
        raise ValueError("Multi-task plan changed during verification")
    result = aggregate(reports, definitions)
    result["plan_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_plan(args.plan)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

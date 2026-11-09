"""Aggregate verified single-task trial reports without treating attempts as independent tasks."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from typing import Any, cast

from _trial_comparisons import OUTCOMES, SCORED, STATUSES, TOKEN_KEYS, compare_blocks
from _trial_declarations import declared_task_signatures
from _trial_transcript import strict_json
from summarize_agent_trials import _verify_usage, summarize


def fraction(value: Fraction | None) -> dict[str, int] | None:
    if value is None:
        return None
    return {"numerator": value.numerator, "denominator": value.denominator}


def summarize_paired_outcomes(rows: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    """Describe validated matched outcomes without treating repetitions as independent tasks."""
    if not rows:
        raise ValueError("A nonempty task set is required for paired outcome summaries")
    totals: Counter[str] = Counter()
    weighted = dict.fromkeys(OUTCOMES, Fraction())
    directions: Counter[str] = Counter()
    for row in rows:
        comparison = row["block_comparison"]["comparisons"][condition]
        counts, planned = comparison["outcomes"], comparison["planned_blocks"]
        totals.update(counts)
        for outcome in OUTCOMES:
            weighted[outcome] += Fraction(counts[outcome], planned)
        if counts["unscored"]:
            direction = "unscored"
        elif counts["candidate_only_passed"] > counts["baseline_only_passed"]:
            direction = "candidate_ahead"
        elif counts["candidate_only_passed"] < counts["baseline_only_passed"]:
            direction = "baseline_ahead"
        else:
            direction = "equal"
        directions[direction] += 1
    return {
        "planned_tasks": len(rows),
        "planned_blocks": sum(totals.values()),
        "pooled_block_counts": {outcome: totals[outcome] for outcome in OUTCOMES},
        "equal_task_weight_block_fractions": {outcome: fraction(weighted[outcome] / len(rows)) for outcome in OUTCOMES},
        "task_direction_counts": {
            direction: directions[direction] for direction in ("candidate_ahead", "baseline_ahead", "equal", "unscored")
        },
    }


def summarize_planned_order(
    reports: list[dict[str, Any]], configs: list[dict[str, Any]], condition: str
) -> dict[str, Any]:
    """Describe outcomes by planned relative order, not by observed launch order."""
    if not reports or len(reports) != len(configs):
        raise ValueError("A protocol is required for every task")
    groups = ("baseline_first", "candidate_first")
    totals: dict[str, Counter[str]] = {group: Counter() for group in groups}
    tasks = []
    for report, config in zip(reports, configs, strict=True):
        blocks = report["block_comparison"]["comparisons"][condition]["blocks"]
        outcomes = {block["repetition"]: block["outcome"] for block in blocks}
        schedule = config["planned_order"]
        conditions = set(config["conditions"])
        if (
            len(outcomes) != len(blocks)
            or not isinstance(schedule, list)
            or len(schedule) != len(blocks)
            or "default" not in conditions
            or condition not in conditions
        ):
            raise ValueError("Planned order does not match paired blocks")
        counts: dict[str, Counter[str]] = {group: Counter() for group in groups}
        seen: set[int] = set()
        for block in schedule:
            repetition, order = block["repetition"], block["conditions"]
            if (
                type(repetition) is not int
                or repetition in seen
                or repetition not in outcomes
                or not isinstance(order, list)
                or len(order) != len(conditions)
                or set(order) != conditions
                or outcomes[repetition] not in OUTCOMES
            ):
                raise ValueError("Planned order does not match paired blocks")
            seen.add(repetition)
            group = "baseline_first" if order.index("default") < order.index(condition) else "candidate_first"
            counts[group][outcomes[repetition]] += 1
            totals[group][outcomes[repetition]] += 1
        tasks.append(
            {
                "task_id": report["task_id"],
                "outcomes_by_planned_order": {
                    group: {outcome: counts[group][outcome] for outcome in OUTCOMES} for group in groups
                },
            }
        )
    return {
        "planned_tasks": len(tasks),
        "pooled_outcomes_by_planned_order": {
            group: {outcome: totals[group][outcome] for outcome in OUTCOMES} for group in groups
        },
        "tasks": tasks,
    }


def summarize_snapshot_evidence(reports: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    """Describe reported snapshot identifiers without asserting their authenticity."""
    pairs: Counter[str] = Counter()
    identifiers: set[str] = set()
    for report in reports:
        attempts = {(item["repetition"], item["condition"]): item for item in report["attempts"]}
        for block in report["block_comparison"]["comparisons"][condition]["blocks"]:
            repetition = block["repetition"]
            baseline = attempts[repetition, "default"].get("provider_model_snapshot")
            candidate = attempts[repetition, condition].get("provider_model_snapshot")
            identifiers.update(value for value in (baseline, candidate) if value is not None)
            if baseline is None or candidate is None:
                pairs["incomplete"] += 1
            elif baseline == candidate:
                pairs["same"] += 1
            else:
                pairs["different"] += 1
    status = (
        "inconsistent_reported_identifiers"
        if len(identifiers) > 1
        else "incomplete"
        if pairs["incomplete"]
        else "single_reported_identifier"
    )
    return {
        "planned_pairs": sum(pairs.values()),
        "same_reported_identifier_pairs": pairs["same"],
        "different_reported_identifier_pairs": pairs["different"],
        "incomplete_pairs": pairs["incomplete"],
        "reported_identifiers": sorted(identifiers),
        "status": status,
    }


def summarize_prompt_runtime_evidence(reports: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    """Pool within-task path-text comparisons; do not compare paths between tasks."""
    totals: Counter[str] = Counter()
    unavailable_tasks = 0
    for report in reports:
        planned = report["conditions"][condition]["planned_attempts"]
        evidence = report.get("prompt_runtime_evidence")
        if evidence is None:
            counts = {"same_recorded_path": 0, "different_recorded_path": 0, "unavailable_pairs": planned}
        else:
            if not isinstance(evidence, dict):
                raise ValueError("invalid prompt runtime evidence")
            attempts = [
                evidence.get(key) for key in ("recorded_attempts", "not_requested_attempts", "ambiguous_attempts")
            ]
            if any(type(value) is not int or value < 0 for value in attempts) or sum(cast(list[int], attempts)) != len(
                report["attempts"]
            ):
                raise ValueError("invalid prompt runtime attempt counts")
            comparisons = evidence.get("comparisons")
            if not isinstance(comparisons, dict) or set(comparisons) != set(report["conditions"]) - {"default"}:
                raise ValueError("invalid prompt runtime comparisons")
            counts = comparisons[condition]
            if not isinstance(counts, dict) or set(counts) != {
                "planned_pairs",
                "same_recorded_path",
                "different_recorded_path",
                "unavailable_pairs",
            }:
                raise ValueError("invalid prompt runtime pair counts")
            if (
                any(type(value) is not int or value < 0 for value in counts.values())
                or counts["planned_pairs"] != planned
                or sum(counts[key] for key in ("same_recorded_path", "different_recorded_path", "unavailable_pairs"))
                != planned
            ):
                raise ValueError("invalid prompt runtime pair counts")
        totals.update(
            {key: counts[key] for key in ("same_recorded_path", "different_recorded_path", "unavailable_pairs")}
        )
        unavailable_tasks += bool(counts["unavailable_pairs"])
    return {
        "planned_tasks": len(reports),
        "tasks_with_unavailable_pairs": unavailable_tasks,
        "planned_pairs": sum(totals.values()),
        "same_recorded_path": totals["same_recorded_path"],
        "different_recorded_path": totals["different_recorded_path"],
        "unavailable_pairs": totals["unavailable_pairs"],
    }


def summarize_paired_tokens(reports: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    """Average fully observed successful paired deltas with equal weight per task."""
    if not reports:
        raise ValueError("A nonempty task set is required for paired token summaries")
    tasks = []
    for report in reports:
        comparison = report["block_comparison"]["comparisons"][condition]
        blocks = comparison["blocks"]
        planned = comparison["planned_blocks"]
        if (
            type(planned) is not int
            or planned < 1
            or not isinstance(blocks, list)
            or len(blocks) != planned
            or report["conditions"]["default"]["planned_attempts"] != planned
            or report["conditions"][condition]["planned_attempts"] != planned
        ):
            raise ValueError("Paired token block denominator is inconsistent")
        deltas = []
        for block in blocks:
            delta = block["token_delta"]
            if delta is None:
                continue
            if (
                block["outcome"] != "both_passed"
                or not isinstance(delta, dict)
                or set(delta) != set(TOKEN_KEYS)
                or any(type(delta[key]) is not int for key in TOKEN_KEYS)
            ):
                raise ValueError("Invalid paired token delta")
            deltas.append(delta)
        if type(comparison["token_comparable_blocks"]) is not int or comparison["token_comparable_blocks"] != len(
            deltas
        ):
            raise ValueError("Paired token comparable-block count is inconsistent")
        means = (
            {key: Fraction(sum(delta[key] for delta in deltas), planned) for key in TOKEN_KEYS}
            if len(deltas) == planned
            else None
        )
        tasks.append(
            {"task_id": report["task_id"], "planned_blocks": planned, "comparable_blocks": len(deltas), "means": means}
        )
    fully_comparable = [task for task in tasks if task["means"] is not None]
    average = (
        {key: fraction(sum((task["means"][key] for task in tasks), Fraction()) / len(tasks)) for key in TOKEN_KEYS}
        if len(fully_comparable) == len(tasks)
        else None
    )
    return {
        "planned_tasks": len(tasks),
        "fully_comparable_tasks": len(fully_comparable),
        "planned_blocks": sum(task["planned_blocks"] for task in tasks),
        "comparable_blocks": sum(task["comparable_blocks"] for task in tasks),
        "equal_task_weight_mean_delta": average,
        "tasks": [
            {
                "task_id": task["task_id"],
                "planned_blocks": task["planned_blocks"],
                "comparable_blocks": task["comparable_blocks"],
                "mean_delta": {key: fraction(value) for key, value in task["means"].items()}
                if task["means"] is not None
                else None,
            }
            for task in tasks
        ],
    }


def summarize_all_attempt_usage(reports: list[dict[str, Any]], conditions: set[str]) -> dict[str, Any]:
    """Account for observed usage across every status without filling missing values."""
    if not reports or "default" not in conditions:
        raise ValueError("A nonempty task set and default condition are required for usage accounting")

    def observed(rows: list[dict[str, Any]]) -> dict[str, int] | None:
        usages = [row["usage"] for row in rows if row["usage"] is not None]
        return {key: sum(item[key] for item in usages) for key in TOKEN_KEYS} if usages else None

    summaries: dict[str, Any] = {}
    complete_means: dict[str, dict[str, Fraction] | None] = {}
    for condition in sorted(conditions):
        tasks: list[dict[str, Any]] = []
        all_rows: list[dict[str, Any]] = []
        means: list[dict[str, Fraction]] = []
        for report in reports:
            rows = [row for row in report["attempts"] if row["condition"] == condition]
            planned = report["conditions"][condition]["planned_attempts"]
            if type(planned) is not int or planned < 1 or len(rows) != planned:
                raise ValueError("Usage denominator differs from planned attempts")
            for row in rows:
                if row["status"] not in STATUSES:
                    raise ValueError("Unknown usage status")
                _verify_usage(row)
            totals = observed(rows)
            available = sum(row["usage"] is not None for row in rows)
            mean = (
                {key: Fraction(totals[key], planned) for key in TOKEN_KEYS}
                if totals is not None and available == planned
                else None
            )
            if mean is not None:
                means.append(mean)
            tasks.append(
                {
                    "task_id": report["task_id"],
                    "planned_attempts": planned,
                    "usage_observed_attempts": available,
                    "usage_unavailable_attempts": planned - available,
                    "observed_token_totals": totals,
                    "mean_tokens_per_attempt": (
                        {key: fraction(mean[key]) for key in TOKEN_KEYS} if mean is not None else None
                    ),
                }
            )
            all_rows.extend(rows)
        available = sum(row["usage"] is not None for row in all_rows)
        complete = (
            {key: sum((mean[key] for mean in means), Fraction()) / len(reports) for key in TOKEN_KEYS}
            if len(means) == len(reports)
            else None
        )
        complete_means[condition] = complete
        statuses = {}
        for status in sorted(STATUSES):
            rows = [row for row in all_rows if row["status"] == status]
            statuses[status] = {
                "attempts": len(rows),
                "usage_observed_attempts": sum(row["usage"] is not None for row in rows),
                "observed_token_totals": observed(rows),
            }
        summaries[condition] = {
            "planned_attempts": len(all_rows),
            "usage_observed_attempts": available,
            "usage_unavailable_attempts": len(all_rows) - available,
            "observed_token_totals": observed(all_rows),
            "equal_task_weight_mean_tokens_per_attempt": (
                {key: fraction(complete[key]) for key in TOKEN_KEYS} if complete is not None else None
            ),
            "by_status": statuses,
            "tasks": tasks,
        }
    differences = {}
    for condition in sorted(conditions - {"default"}):
        baseline, candidate = complete_means["default"], complete_means[condition]
        differences[condition] = (
            {key: fraction(candidate[key] - baseline[key]) for key in TOKEN_KEYS}
            if baseline is not None and candidate is not None
            else None
        )
    return {"conditions": summaries, "condition_minus_default": differences}


def missing_outcome_sensitivity(rows: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    """Bound the observed-task mean under hypothetical binary outcomes for unscored attempts."""
    if not rows:
        raise ValueError("A nonempty task set is required for missing-outcome sensitivity")
    tasks = []
    for row in rows:
        baseline = row["attempt_status_counts"]["default"]
        candidate = row["attempt_status_counts"][condition]
        planned = sum(baseline.values())
        if planned < 1 or sum(candidate.values()) != planned:
            raise ValueError("Sensitivity analysis requires equal planned condition denominators")
        baseline_unscored = planned - baseline["task_passed"] - baseline["task_failed"]
        candidate_unscored = planned - candidate["task_passed"] - candidate["task_failed"]
        difference = candidate["task_passed"] - baseline["task_passed"]
        lower = Fraction(difference - baseline_unscored, planned)
        upper = Fraction(difference + candidate_unscored, planned)
        tasks.append(
            {
                "task_id": row["task_id"],
                "planned_attempts_per_condition": planned,
                "baseline_unscored": baseline_unscored,
                "candidate_unscored": candidate_unscored,
                "lower": lower,
                "upper": upper,
            }
        )
    return {
        "planned_tasks": len(tasks),
        "tasks_with_unscored_attempts": sum(
            bool(task["baseline_unscored"] or task["candidate_unscored"]) for task in tasks
        ),
        "equal_task_weight_lower": fraction(sum((task["lower"] for task in tasks), Fraction()) / len(tasks)),
        "equal_task_weight_upper": fraction(sum((task["upper"] for task in tasks), Fraction()) / len(tasks)),
        "tasks": [{**task, "lower": fraction(task["lower"]), "upper": fraction(task["upper"])} for task in tasks],
    }


def project_condition_pair(reports: list[dict[str, Any]], baseline: str, candidate: str) -> list[dict[str, Any]]:
    """Project two verified conditions into the existing paired-comparison machinery."""
    if baseline == candidate:
        raise ValueError("Pair members must be distinct")
    projected = []
    for report in reports:
        if baseline not in report["conditions"] or candidate not in report["conditions"]:
            raise ValueError("Pair members must be planned conditions")
        attempts = [
            {**attempt, "condition": "default" if attempt["condition"] == baseline else "candidate"}
            for attempt in report["attempts"]
            if attempt["condition"] in {baseline, candidate}
        ]
        projected.append(
            {
                "task_id": report["task_id"],
                "conditions": {
                    "default": report["conditions"][baseline],
                    "candidate": report["conditions"][candidate],
                },
                "attempts": attempts,
                "block_comparison": compare_blocks(attempts, {"default", "candidate"}),
            }
        )
    return projected


def summarize_non_default_pairs(reports: list[dict[str, Any]], rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare each ordered pair of non-default conditions using their own matched attempts."""
    names = sorted(set(reports[0]["conditions"]) - {"default"})
    pairs: dict[str, Any] = {}
    for baseline in names:
        candidates = {}
        for candidate in names:
            if baseline == candidate:
                continue
            projected = project_condition_pair(reports, baseline, candidate)
            pair_rows = [
                {
                    "task_id": row["task_id"],
                    "block_comparison": item["block_comparison"],
                    "attempt_status_counts": {
                        "default": row["attempt_status_counts"][baseline],
                        "candidate": row["attempt_status_counts"][candidate],
                    },
                }
                for row, item in zip(rows, projected, strict=True)
            ]
            differences = []
            for row in pair_rows:
                left, right = row["attempt_status_counts"]["default"], row["attempt_status_counts"]["candidate"]
                planned = sum(left.values())
                if planned != sum(right.values()) or planned < 1:
                    raise ValueError("Pair members require equal planned condition denominators")
                scored = left["task_passed"] + left["task_failed"] == planned and (
                    right["task_passed"] + right["task_failed"] == planned
                )
                value = Fraction(right["task_passed"] - left["task_passed"], planned) if scored else None
                differences.append({"task_id": row["task_id"], "candidate_minus_baseline": value})
            complete = [
                item["candidate_minus_baseline"] for item in differences if item["candidate_minus_baseline"] is not None
            ]
            average = sum(complete, Fraction()) / len(rows) if len(complete) == len(rows) else None
            candidates[candidate] = {
                "baseline": baseline,
                "candidate": candidate,
                "planned_tasks": len(rows),
                "fully_scored_tasks": len(complete),
                "unscored_tasks": len(rows) - len(complete),
                "equal_task_weight_mean_difference": fraction(average),
                "task_differences": [
                    {**item, "candidate_minus_baseline": fraction(item["candidate_minus_baseline"])}
                    for item in differences
                ],
                "paired_outcomes": summarize_paired_outcomes(pair_rows, "candidate"),
                "missing_outcome_sensitivity": missing_outcome_sensitivity(pair_rows, "candidate"),
                "model_snapshot_evidence": summarize_snapshot_evidence(projected, "candidate"),
                "paired_token_differences": summarize_paired_tokens(projected, "candidate"),
            }
        if candidates:
            pairs[baseline] = candidates
    return pairs


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
        if canonical(report["block_comparison"]) != canonical(compare_blocks(report["attempts"], conditions)):
            raise ValueError("Matched block comparisons disagree with the attempts")
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
                "prompt_runtime_evidence": report.get("prompt_runtime_evidence"),
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
        "non_default_comparisons": summarize_non_default_pairs(reports, rows),
        "paired_outcomes": {
            condition: summarize_paired_outcomes(rows, condition) for condition in sorted(conditions - {"default"})
        },
        "missing_outcome_sensitivity": {
            condition: missing_outcome_sensitivity(rows, condition) for condition in sorted(conditions - {"default"})
        },
        "model_snapshot_evidence": {
            condition: summarize_snapshot_evidence(reports, condition) for condition in sorted(conditions - {"default"})
        },
        "prompt_runtime_evidence": {
            condition: summarize_prompt_runtime_evidence(reports, condition)
            for condition in sorted(conditions - {"default"})
        },
        "token_comparisons": {
            condition: summarize_paired_tokens(reports, condition) for condition in sorted(conditions - {"default"})
        },
        "all_attempt_usage": summarize_all_attempt_usage(reports, conditions),
        "quality_superiority_established": False,
        "limitations": [
            "Descriptive task-weighted differences do not establish statistical significance or generalization.",
            "Pooled paired-block counts are descriptive; task-weighted fractions avoid weighting a task more for having more repetitions, and neither proves independence or superiority.",
            "Direct non-default condition pairs are descriptive and use the same matched attempts; they are not independent replications or evidence of superiority.",
            "Unscored attempts prevent an aggregate difference for the affected comparison.",
            "Missing-outcome bounds hypothetically assign every unscored attempt pass or fail; they are not confidence intervals, observed outcomes, or predictions of reruns.",
            "A frozen plan and matching hashes alone do not establish preregistration or grading authenticity.",
            "Requested model identity is not proof of the provider-resolved model snapshot.",
            "Snapshot identifiers are provider-reported metadata; even matching identifiers do not independently establish model identity.",
            "Runtime path comparisons use text recorded in prompts, not runtime execution evidence; equal text does not prove identical runtimes and different text may refer to the same runtime.",
            "Task IDs and protocol hashes do not by themselves prove that tasks are independent.",
            "Paired token differences require both attempts to pass and usage for every planned block; they are not priced cost or proof of efficiency.",
            "All-attempt usage includes failed and unscored attempts when reported; missing usage prevents complete means and differences, and totals are observed subtotals rather than priced cost.",
            "Input counts include cached input; output counts include reported reasoning output and are not added to it again.",
            "This report does not compare elapsed time across tasks.",
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
    configs = []
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
        configs.append(config)
    if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(raw).digest():
        raise ValueError("Multi-task plan changed during verification")
    signatures = [declared_task_signatures(config) for config in configs]
    task_signatures = [task for task, _ in signatures]
    if len(set(task_signatures)) != len(task_signatures):
        raise ValueError("Plan contains a duplicate declared task prompt and workspace")
    result = aggregate(reports, definitions)
    result["plan_sha256"] = hashlib.sha256(raw).hexdigest()
    result["planned_order_outcomes"] = {
        condition: summarize_planned_order(reports, configs, condition)
        for condition in sorted(set(definitions[0]) - {"default"})
    }
    for baseline, candidates in result["non_default_comparisons"].items():
        for candidate, comparison in candidates.items():
            projected = project_condition_pair(reports, baseline, candidate)
            projected_configs = [
                {
                    "conditions": {
                        "default": config["conditions"][baseline],
                        "candidate": config["conditions"][candidate],
                    },
                    "planned_order": [
                        {
                            "repetition": block["repetition"],
                            "conditions": [
                                "default" if name == baseline else "candidate"
                                for name in block["conditions"]
                                if name in {baseline, candidate}
                            ],
                        }
                        for block in config["planned_order"]
                    ],
                }
                for config in configs
            ]
            comparison["planned_order_outcomes"] = summarize_planned_order(projected, projected_configs, "candidate")
    result["limitations"].append(
        "Order groups describe planned relative positions, not verified execution order or an order effect; "
        "pooled blocks can be dependent and tasks may have unequal repetition counts."
    )
    result["declared_task_signatures"] = [
        {"task_id": report["task_id"], "sha256": task, "workspace_sha256": workspace}
        for report, (task, workspace) in zip(reports, signatures, strict=True)
    ]
    workspaces: dict[str, list[str]] = {}
    for report, (_, workspace) in zip(reports, signatures, strict=True):
        workspaces.setdefault(workspace, []).append(report["task_id"])
    result["declared_shared_workspaces"] = [
        {"workspace_sha256": key, "task_ids": sorted(ids)} for key, ids in sorted(workspaces.items()) if len(ids) > 1
    ]
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

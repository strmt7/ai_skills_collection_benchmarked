"""Render a verified multi-task comparison without claiming statistical superiority."""

from __future__ import annotations

import argparse
import io
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
from textwrap import fill
from typing import Any

from _trial_comparisons import OUTCOMES, STATUSES, compare_blocks
from summarize_multi_task_trials import (
    aggregate,
    missing_outcome_sensitivity,
    run_plan,
    summarize_paired_outcomes,
    summarize_snapshot_evidence,
)


def baseline_chart_view(report: dict[str, Any], baseline: str) -> dict[str, Any]:
    """Recompute a chart view from attempts with an explicit non-default baseline."""
    if baseline == "default":
        return report
    if (
        report["quality_superiority_established"] is not False
        or type(report["task_count"]) is not int
        or report["task_count"] != len(report["tasks"])
    ):
        raise ValueError("Chart requires all planned tasks and no superiority claim")
    definitions = report["condition_definitions"]
    if baseline not in definitions or baseline == "default":
        raise ValueError("Chart baseline must be a declared condition")
    candidates = set(definitions) - {"default", baseline}
    if not candidates:
        raise ValueError("A non-default baseline requires another non-default condition")

    def same(left: Any, right: Any) -> bool:
        return json.dumps(left, sort_keys=True, allow_nan=False) == json.dumps(right, sort_keys=True, allow_nan=False)

    projected_definitions = {
        "default": definitions[baseline],
        **{name: definitions[name] for name in sorted(candidates)},
    }
    reports = []
    for task in report["tasks"]:
        if not same(task["block_comparison"], compare_blocks(task["attempts"], set(definitions))):
            raise ValueError("Recorded blocks disagree with attempts")
        for name in definitions:
            counts = Counter(attempt["status"] for attempt in task["attempts"] if attempt["condition"] == name)
            if not same(task["attempt_status_counts"][name], {status: counts[status] for status in sorted(STATUSES)}):
                raise ValueError("Recorded attempt counts disagree with attempts")
        attempts = [
            {**attempt, "condition": "default" if attempt["condition"] == baseline else attempt["condition"]}
            for attempt in task["attempts"]
            if attempt["condition"] in candidates | {baseline}
        ]
        planned = {
            "default": sum(task["attempt_status_counts"][baseline].values()),
            **{name: sum(task["attempt_status_counts"][name].values()) for name in sorted(candidates)},
        }
        reports.append(
            {
                "task_id": task["task_id"],
                "protocol_sha256": task["protocol_sha256"],
                "grading_manifest_sha256": task["grading_manifest_sha256"],
                "expected_grading_cases": task["expected_grading_cases"],
                "limitations": task["limitations"],
                "block_comparison": compare_blocks(attempts, set(projected_definitions)),
                "model_requested": report["model_requested"],
                "reasoning_effort_requested": report["reasoning_effort_requested"],
                "partition": report["partition"],
                "task_count": 1,
                "conditions": {name: {"planned_attempts": count} for name, count in planned.items()},
                "attempts": attempts,
            }
        )
    projected = aggregate(reports, [projected_definitions] * len(reports))
    for candidate in sorted(candidates):
        direct = report["non_default_comparisons"][baseline][candidate]
        comparison = projected["comparisons"][candidate]
        if (
            direct["baseline"] != baseline
            or direct["candidate"] != candidate
            or any(not same(direct[key], comparison[key]) for key in comparison)
            or not same(direct["paired_outcomes"], projected["paired_outcomes"][candidate])
            or not same(direct["missing_outcome_sensitivity"], projected["missing_outcome_sensitivity"][candidate])
            or not same(direct["model_snapshot_evidence"], projected["model_snapshot_evidence"][candidate])
            or not same(direct["paired_token_differences"], projected["token_comparisons"][candidate])
            or not same(
                direct["task_differences"],
                [
                    {"task_id": row["task_id"], "candidate_minus_baseline": row["candidate_minus_default"][candidate]}
                    for row in projected["tasks"]
                ],
            )
        ):
            raise ValueError("Direct comparison disagrees with recorded attempts")
    projected["plan_sha256"] = report["plan_sha256"]
    projected["chart_baseline"] = baseline
    return projected


def graph_rows(report: dict[str, Any]) -> list[tuple[str, list[Fraction], Fraction | None, int]]:
    """Validate chart denominators and means against the verified task data."""
    conditions = sorted(report["comparisons"])
    tasks = report["tasks"]
    if (
        not conditions
        or not tasks
        or type(report["task_count"]) is not int
        or report["task_count"] != len(tasks)
        or report["quality_superiority_established"] is not False
    ):
        raise ValueError("At least one task and comparison without a superiority claim are required")
    rows = []
    for condition in conditions:
        comparison = report["comparisons"][condition]
        values = [task["candidate_minus_default"][condition] for task in tasks]
        try:
            scored = [Fraction(value["numerator"], value["denominator"]) for value in values if value is not None]
            recorded = comparison["equal_task_weight_mean_difference"]
            mean = Fraction(recorded["numerator"], recorded["denominator"]) if recorded is not None else None
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError("Invalid chart fraction") from exc
        if (
            len(values) != comparison["planned_tasks"]
            or len(scored) != comparison["fully_scored_tasks"]
            or len(values) - len(scored) != comparison["unscored_tasks"]
            or any(not -1 <= value <= 1 for value in scored)
        ):
            raise ValueError("Chart task counts or values disagree with the verified report")
        expected = sum(scored, Fraction()) / len(values) if len(scored) == len(values) else None
        if mean != expected:
            raise ValueError("Chart mean disagrees with the verified task differences")
        rows.append((condition, scored, mean, len(values)))
    return rows


def snapshot_summary(report: dict[str, Any]) -> tuple[int, int, int]:
    """Count unavailable and distinct reported snapshots across all attempts."""
    attempts = [attempt for task in report["tasks"] for attempt in task["attempts"]]
    if not attempts or any(not isinstance(attempt, dict) for attempt in attempts):
        raise ValueError("Chart requires recorded attempts")
    snapshots = [attempt.get("provider_model_snapshot") for attempt in attempts]
    if any(value is not None and (not isinstance(value, str) or not value) for value in snapshots):
        raise ValueError("Invalid model snapshot metadata")
    return sum(value is None for value in snapshots), len(snapshots), len({value for value in snapshots if value})


def snapshot_pair_labels(report: dict[str, Any]) -> dict[str, str]:
    """Validate and describe snapshot evidence separately for each candidate."""
    conditions = set(report["comparisons"])
    if set(report["model_snapshot_evidence"]) != conditions:
        raise ValueError("Snapshot evidence condition set differs from the comparisons")
    for task in report["tasks"]:
        recorded = json.dumps(task["block_comparison"], sort_keys=True, allow_nan=False)
        recomputed = json.dumps(
            compare_blocks(task["attempts"], conditions | {"default"}), sort_keys=True, allow_nan=False
        )
        if recorded != recomputed:
            raise ValueError("Snapshot evidence blocks disagree with attempts")
    descriptions = {
        "incomplete": "incomplete",
        "inconsistent_reported_identifiers": "vary",
        "single_reported_identifier": "one reported",
    }
    labels = {}
    for condition in sorted(conditions):
        evidence = summarize_snapshot_evidence(report["tasks"], condition)
        recorded = report["model_snapshot_evidence"][condition]
        counts = (
            "planned_pairs",
            "same_reported_identifier_pairs",
            "different_reported_identifier_pairs",
            "incomplete_pairs",
        )
        if (
            not isinstance(recorded, dict)
            or any(type(recorded.get(key)) is not int for key in counts)
            or recorded != evidence
        ):
            raise ValueError("Snapshot evidence disagrees with attempts")
        labels[condition] = (
            f"IDs: {descriptions[evidence['status']]}; pairs: "
            f"{evidence['different_reported_identifier_pairs']}/{evidence['planned_pairs']} differ, "
            f"{evidence['incomplete_pairs']} incomplete"
        )
    return labels


def sensitivity_ranges(report: dict[str, Any]) -> dict[str, tuple[Fraction, Fraction] | None]:
    """Validate hypothetical missing-outcome bounds against recorded attempts."""
    conditions = set(report["comparisons"])
    if set(report["missing_outcome_sensitivity"]) != conditions:
        raise ValueError("Missing-outcome sensitivity condition set differs from the comparisons")
    for task in report["tasks"]:
        for condition in conditions | {"default"}:
            counts = Counter(item["status"] for item in task["attempts"] if item["condition"] == condition)
            observed = {status: counts[status] for status in sorted(STATUSES)}
            if json.dumps(task["attempt_status_counts"][condition], sort_keys=True) != json.dumps(
                observed, sort_keys=True
            ):
                raise ValueError("Missing-outcome status counts disagree with attempts")
    ranges = {}
    for condition in sorted(conditions):
        expected = missing_outcome_sensitivity(report["tasks"], condition)
        recorded = report["missing_outcome_sensitivity"][condition]
        if json.dumps(recorded, sort_keys=True, allow_nan=False) != json.dumps(
            expected, sort_keys=True, allow_nan=False
        ):
            raise ValueError("Missing-outcome sensitivity disagrees with attempts")
        ranges[condition] = (
            (Fraction(**expected["equal_task_weight_lower"]), Fraction(**expected["equal_task_weight_upper"]))
            if expected["tasks_with_unscored_attempts"]
            else None
        )
    return ranges


def paired_rows(report: dict[str, Any]) -> list[tuple[str, list[Fraction], int, int, dict[str, int]]]:
    """Recompute paired outcomes from the attempts before displaying them."""
    graph_rows(report)
    conditions = set(report["comparisons"])
    if set(report["paired_outcomes"]) != conditions:
        raise ValueError("Paired outcome condition set differs from the comparisons")
    snapshot_pair_labels(report)
    rows = []
    for condition in sorted(conditions):
        expected = summarize_paired_outcomes(report["tasks"], condition)
        if json.dumps(report["paired_outcomes"][condition], sort_keys=True, allow_nan=False) != json.dumps(
            expected, sort_keys=True, allow_nan=False
        ):
            raise ValueError("Paired outcomes disagree with the recorded attempts")
        values = [Fraction(**expected["equal_task_weight_block_fractions"][outcome]) for outcome in OUTCOMES]
        if sum(values, Fraction()) != 1 or any(value < 0 for value in values):
            raise ValueError("Invalid paired outcome fractions")
        rows.append(
            (
                condition,
                values,
                expected["planned_tasks"],
                expected["planned_blocks"],
                expected["task_direction_counts"],
            )
        )
    return rows


def render_paired_svg(report: dict[str, Any]) -> bytes:
    """Show the equally task-weighted composition of matched outcomes."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    rows = paired_rows(report)
    snapshot_labels = snapshot_pair_labels(report)
    baseline = report.get("chart_baseline", "default")
    baseline_label = "Default" if baseline == "default" else baseline
    styles = (
        ("Both passed", "#0072B2", None, "white"),
        ("Candidate only passed", "#007C58", None, "white"),
        (f"{baseline_label} only passed", "#B44600", None, "white"),
        ("Neither passed", "#4C566A", None, "white"),
        ("Unscored", "#F0E442", "///", "black"),
    )
    condition_labels = [fill(row[0], width=24, break_on_hyphens=False) for row in rows]
    label_lines = max(label.count("\n") + 1 for label in condition_labels)
    with matplotlib.rc_context(
        {"svg.hashsalt": report["plan_sha256"], "svg.fonttype": "none", "font.family": "DejaVu Sans"}
    ):
        figure, axis = plt.subplots(figsize=(11, max(5.3, 4.6 + max(0.7, 0.32 * label_lines) * len(rows))))
        try:
            figure.subplots_adjust(left=0.18, right=0.69, top=0.72, bottom=0.29)
            for row, (condition, values, tasks, blocks, directions) in enumerate(rows):
                left = 0.0
                for value, (_, color, hatch, text_color) in zip(values, styles, strict=True):
                    width = float(value)
                    axis.barh(
                        row, width, left=left, height=0.48, color=color, edgecolor="black", linewidth=0.4, hatch=hatch
                    )
                    if value >= Fraction(1, 10):
                        axis.text(
                            left + width / 2,
                            row,
                            f"{width:.0%}",
                            ha="center",
                            va="center",
                            color=text_color,
                            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1}
                            if hatch
                            else None,
                        )
                    left += width
                task_label = "task" if tasks == 1 else "tasks"
                block_label = "paired block" if blocks == 1 else "paired blocks"
                axis.text(
                    1.03,
                    row,
                    f"{tasks} {task_label}; {blocks} {block_label}\n"
                    f"Task directions: +{directions['candidate_ahead']} / -{directions['baseline_ahead']} / "
                    f"={directions['equal']} / ?{directions['unscored']}\n{snapshot_labels[condition]}",
                    transform=axis.get_yaxis_transform(),
                    va="center",
                    fontsize=8,
                )
            axis.set_yticks(range(len(rows)), condition_labels)
            axis.set_ylim(len(rows) - 0.5, -0.5)
            axis.set_xlim(0, 1)
            axis.set_xticks([0, 0.25, 0.5, 0.75, 1], ["0%", "25%", "50%", "75%", "100%"])
            axis.set_xlabel("Equal-task-weight share of paired blocks")
            figure.suptitle("Paired benchmark outcomes", y=0.98)
            figure.text(
                0.5,
                0.93,
                f"requested model: {report['model_requested']} | requested effort: {report['reasoning_effort_requested']}",
                ha="center",
                fontsize=9,
            )
            figure.legend(
                handles=[
                    Patch(facecolor=color, edgecolor="black", hatch=hatch, label=label)
                    for label, color, hatch, _ in styles
                ],
                loc="upper center",
                bbox_to_anchor=(0.5, 0.89),
                ncols=3,
                frameon=False,
            )
            figure.text(
                0.01,
                0.17,
                "Each task has equal weight; percentages are rounded and small segments are unlabeled.",
                fontsize=8,
            )
            figure.text(
                0.01,
                0.12,
                f"+ candidate ahead; - {baseline} ahead; = equal observed rates; ? unscored task.",
                fontsize=8,
            )
            figure.text(
                0.01,
                0.07,
                "Unscored is not failure. Snapshot IDs are provider-reported and not independently verified.",
                fontsize=8,
            )
            figure.text(
                0.01,
                0.025,
                f"Descriptive only; no significance or superiority claim. Plan {report['plan_sha256'][:12]}; "
                "the hash does not prove preregistration or grading authenticity.",
                fontsize=8,
            )
            output = io.BytesIO()
            figure.savefig(
                output,
                format="svg",
                metadata={
                    "Date": None,
                    "Creator": "render_multi_task_chart.py",
                    "Description": f"plan_sha256={report['plan_sha256']};view=paired_outcomes"
                    + (f";baseline={baseline}" if baseline != "default" else ""),
                },
            )
        finally:
            plt.close(figure)
    return output.getvalue()


def render_svg(report: dict[str, Any]) -> bytes:
    """Show each scored task and any fully observed equal-task-weight mean."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    rows = graph_rows(report)
    baseline = report.get("chart_baseline", "default")
    unavailable, attempts, distinct = snapshot_summary(report)
    snapshot_labels = snapshot_pair_labels(report)
    sensitivity = sensitivity_ranges(report)
    conditions = [row[0] for row in rows]
    with matplotlib.rc_context(
        {"svg.hashsalt": report["plan_sha256"], "svg.fonttype": "none", "font.family": "DejaVu Sans"}
    ):
        figure, axis = plt.subplots(figsize=(10, max(5.1, 4.3 + 0.65 * len(conditions))))
        try:
            figure.subplots_adjust(left=0.16, right=0.64, top=0.70, bottom=0.29)
            axis.axvline(0, color="#64748b", linewidth=1, zorder=1)
            for row, (condition, scored, mean, planned) in enumerate(rows):
                offsets = [((index % 7) - 3) * 0.035 for index in range(len(scored))]
                if scored:
                    axis.scatter(
                        [float(value) for value in scored],
                        [row + offset for offset in offsets],
                        s=38,
                        color="#2563eb",
                        alpha=0.65,
                        zorder=3,
                    )
                if mean is not None:
                    axis.scatter([float(mean)], [row], marker="s", s=65, color="#c2410c", zorder=4)
                    summary = f"{len(scored)}/{planned} scored; mean {mean}"
                else:
                    summary = f"{len(scored)}/{planned} scored; mean unavailable"
                interval = sensitivity[condition]
                if interval is not None:
                    lower, upper = interval
                    axis.hlines(row + 0.18, float(lower), float(upper), color="#475569", linewidth=3, zorder=2)
                    summary += f"\nHypothetical bounds: {lower} to {upper}"
                axis.text(
                    1.03,
                    row,
                    f"{summary}\n{snapshot_labels[condition]}",
                    transform=axis.get_yaxis_transform(),
                    va="center",
                    fontsize=8,
                )
            axis.set_yticks(range(len(conditions)), conditions)
            axis.set_ylim(len(conditions) - 0.5, -0.5)
            axis.set_xlim(-1.05, 1.05)
            axis.set_xticks([-1, -0.5, 0, 0.5, 1], ["-1", "-0.5", "0", "+0.5", "+1"])
            axis.set_xlabel(f"Task pass-rate difference (condition minus {baseline})")
            figure.suptitle(
                f"Task-weighted comparison: {report['partition']} | requested model: {report['model_requested']}"
                f" | requested effort: {report['reasoning_effort_requested']}",
                y=0.97,
            )
            axis.grid(axis="x", alpha=0.2)
            handles = [
                Line2D([], [], marker="o", linestyle="", color="#2563eb", label="Scored task (dots can overlap)"),
                Line2D([], [], marker="s", linestyle="", color="#c2410c", label="Mean, only if all tasks are scored"),
            ]
            if any(interval is not None for interval in sensitivity.values()):
                handles.append(
                    Line2D([], [], color="#475569", linewidth=3, label="Hypothetical missing-outcome bounds")
                )
            figure.legend(
                handles=handles,
                loc="upper center",
                bbox_to_anchor=(0.5, 0.90),
                ncols=2,
                frameon=False,
            )
            figure.text(
                0.01,
                0.14,
                f"Snapshot metadata unavailable: {unavailable}/{attempts}; distinct reported: {distinct}.",
                fontsize=8,
                color="#334155",
            )
            figure.text(
                0.01,
                0.095,
                "Snapshot metadata is not independently verified. Descriptive only; unscored tasks are not failures. "
                + (
                    "Hypothetical bounds are not a confidence interval or superiority claim."
                    if any(interval is not None for interval in sensitivity.values())
                    else "No uncertainty or superiority claim."
                ),
                fontsize=8,
                color="#334155",
            )
            figure.text(
                0.01,
                0.05,
                f"Plan {report['plan_sha256'][:12]}; a plan hash does not prove preregistration or grading authenticity.",
                fontsize=8,
                color="#334155",
            )
            output = io.BytesIO()
            figure.savefig(
                output,
                format="svg",
                metadata={
                    "Date": None,
                    "Creator": "render_multi_task_chart.py",
                    "Description": f"plan_sha256={report['plan_sha256']}"
                    + (f";baseline={baseline}" if baseline != "default" else ""),
                },
            )
        finally:
            plt.close(figure)
    return output.getvalue()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", default="default", help="Declared baseline condition (default: default)")
    parser.add_argument("--view", choices=("difference", "paired"), default="difference")
    parser.add_argument("--check", action="store_true", help="Compare an existing SVG without writing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = baseline_chart_view(run_plan(args.plan), args.baseline)
        rendered = render_paired_svg(report) if args.view == "paired" else render_svg(report)
        if args.check:
            if args.output.read_bytes().replace(b"\r\n", b"\n") != rendered.replace(b"\r\n", b"\n"):
                raise ValueError("Chart differs from the current verified report")
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(rendered)
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, "task_count": report["task_count"], "quality_superiority_established": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

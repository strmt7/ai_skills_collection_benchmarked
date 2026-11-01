"""Render descriptive paired-token differences from verified multi-task reports."""

from __future__ import annotations

import argparse
import io
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from _trial_comparisons import TOKEN_KEYS, compare_blocks
from render_multi_task_chart import snapshot_summary
from summarize_multi_task_trials import run_plan, summarize_paired_tokens


def token_rows(report: dict[str, Any]) -> list[tuple[str, dict[str, list[Fraction]], Any, int, int, int, int]]:
    """Recompute matched pairs and task-weighted summaries before rendering."""
    conditions = set(report["comparisons"]) | {"default"}
    tasks = report["tasks"]
    if (
        len(conditions) < 2
        or not tasks
        or report["task_count"] != len(tasks)
        or report["quality_superiority_established"] is not False
        or set(report["token_comparisons"]) != conditions - {"default"}
    ):
        raise ValueError("Invalid task or condition set")
    inputs = []
    for task in tasks:
        attempts = task["attempts"]
        if task["block_comparison"] != compare_blocks(attempts, conditions):
            raise ValueError("Matched blocks disagree with attempts")
        inputs.append(
            {
                "task_id": task["task_id"],
                "block_comparison": task["block_comparison"],
                "conditions": {
                    condition: {"planned_attempts": sum(row["condition"] == condition for row in attempts)}
                    for condition in conditions
                },
            }
        )
    rows = []
    for condition in sorted(conditions - {"default"}):
        comparison = summarize_paired_tokens(inputs, condition)
        if report["token_comparisons"][condition] != comparison:
            raise ValueError("Token summaries disagree with matched blocks")
        values: dict[str, list[Fraction]] = {key: [] for key in TOKEN_KEYS}
        for task in comparison["tasks"]:
            if task["mean_delta"] is not None:
                for key in TOKEN_KEYS:
                    item = task["mean_delta"][key]
                    values[key].append(Fraction(item["numerator"], item["denominator"]))
        recorded = comparison["equal_task_weight_mean_delta"]
        mean = (
            {key: Fraction(recorded[key]["numerator"], recorded[key]["denominator"]) for key in TOKEN_KEYS}
            if recorded is not None
            else None
        )
        rows.append(
            (
                condition,
                values,
                mean,
                comparison["fully_comparable_tasks"],
                comparison["planned_tasks"],
                comparison["comparable_blocks"],
                comparison["planned_blocks"],
            )
        )
    return rows


def render_svg(report: dict[str, Any]) -> bytes:
    """Plot observed task means; omit the overall mean when any task is incomplete."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    rows = token_rows(report)
    unavailable, attempts, distinct = snapshot_summary(report)
    with matplotlib.rc_context(
        {"svg.hashsalt": report["plan_sha256"], "svg.fonttype": "none", "font.family": "DejaVu Sans"}
    ):
        figure, axes = plt.subplots(1, 2, figsize=(12, max(5.4, 4.7 + 0.6 * len(rows))), sharey=True)
        try:
            figure.subplots_adjust(left=0.13, right=0.97, top=0.70, bottom=0.32, wspace=0.30)
            for axis, key, label in zip(axes, TOKEN_KEYS, ("Input tokens", "Output tokens"), strict=True):
                axis.axvline(0, color="#64748b", linewidth=1)
                for row, (_condition, values, mean, complete, planned, observed, blocks) in enumerate(rows):
                    offsets = [((index % 7) - 3) * 0.035 for index in range(len(values[key]))]
                    if values[key]:
                        axis.scatter(
                            [float(value) for value in values[key]],
                            [row + offset for offset in offsets],
                            s=38,
                            color="#2563eb",
                            alpha=0.65,
                            zorder=3,
                        )
                    if mean is not None:
                        axis.scatter([float(mean[key])], [row], marker="s", s=65, color="#c2410c", zorder=4)
                    summary = f"{complete}/{planned} tasks; {observed}/{blocks} blocks"
                    if mean is None:
                        summary += "; mean unavailable"
                    axis.text(0.02, row - 0.25, summary, transform=axis.get_yaxis_transform(), fontsize=8)
                axis.set_xlabel(f"{label}: condition minus default")
                axis.grid(axis="x", alpha=0.2)
            axes[0].set_yticks(range(len(rows)), [row[0] for row in rows])
            axes[0].set_ylim(len(rows) - 0.5, -0.5)
            figure.suptitle(
                f"Paired token differences: {report['partition']} | requested model: {report['model_requested']}"
                f" | requested effort: {report['reasoning_effort_requested']}",
                y=0.97,
            )
            figure.legend(
                handles=[
                    Line2D([], [], marker="o", linestyle="", color="#2563eb", label="Complete task mean"),
                    Line2D([], [], marker="s", linestyle="", color="#c2410c", label="Equal-task mean if all complete"),
                ],
                loc="upper center",
                bbox_to_anchor=(0.5, 0.91),
                ncols=2,
                frameon=False,
            )
            figure.text(
                0.01,
                0.19,
                f"Snapshot metadata unavailable: {unavailable}/{attempts}; distinct reported: {distinct} (unverified).",
                fontsize=8,
            )
            figure.text(
                0.01,
                0.145,
                "Both attempts must pass and report usage in every planned block for a task mean.",
                fontsize=8,
            )
            figure.text(
                0.01,
                0.10,
                "Not priced cost, efficiency or superiority; input includes cached and output includes reasoning tokens.",
                fontsize=8,
            )
            figure.text(
                0.01,
                0.055,
                f"Plan {report['plan_sha256'][:12]}; its hash does not prove preregistration or grading authenticity.",
                fontsize=8,
            )
            output = io.BytesIO()
            figure.savefig(
                output,
                format="svg",
                metadata={
                    "Date": None,
                    "Creator": "render_token_chart.py",
                    "Description": f"plan_sha256={report['plan_sha256']}",
                },
            )
        finally:
            plt.close(figure)
    return output.getvalue()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="Compare an existing SVG without writing")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run_plan(args.plan)
        rendered = render_svg(report)
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

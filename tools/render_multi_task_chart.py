"""Render a verified multi-task comparison without claiming statistical superiority."""

from __future__ import annotations

import argparse
import io
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from summarize_multi_task_trials import run_plan


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


def render_svg(report: dict[str, Any]) -> bytes:
    """Show each scored task and any fully observed equal-task-weight mean."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    rows = graph_rows(report)
    conditions = [row[0] for row in rows]
    with matplotlib.rc_context(
        {"svg.hashsalt": report["plan_sha256"], "svg.fonttype": "none", "font.family": "DejaVu Sans"}
    ):
        figure, axis = plt.subplots(figsize=(10, max(4.6, 3.8 + 0.65 * len(conditions))))
        try:
            figure.subplots_adjust(left=0.16, right=0.75, top=0.70, bottom=0.27)
            axis.axvline(0, color="#64748b", linewidth=1, zorder=1)
            for row, (_condition, scored, mean, planned) in enumerate(rows):
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
                axis.text(1.03, row, summary, transform=axis.get_yaxis_transform(), va="center", fontsize=9)
            axis.set_yticks(range(len(conditions)), conditions)
            axis.set_ylim(len(conditions) - 0.5, -0.5)
            axis.set_xlim(-1.05, 1.05)
            axis.set_xticks([-1, -0.5, 0, 0.5, 1], ["-1", "-0.5", "0", "+0.5", "+1"])
            axis.set_xlabel("Task pass-rate difference (condition minus default)")
            figure.suptitle(
                f"Task-weighted comparison: {report['partition']} | requested model: {report['model_requested']}",
                y=0.97,
            )
            axis.grid(axis="x", alpha=0.2)
            figure.legend(
                handles=[
                    Line2D([], [], marker="o", linestyle="", color="#2563eb", label="Scored task (dots can overlap)"),
                    Line2D(
                        [], [], marker="s", linestyle="", color="#c2410c", label="Mean, only if all tasks are scored"
                    ),
                ],
                loc="upper center",
                bbox_to_anchor=(0.5, 0.90),
                ncols=2,
                frameon=False,
            )
            figure.text(
                0.01,
                0.08,
                "Descriptive only; unscored tasks are not failures. No uncertainty or superiority claim.",
                fontsize=8,
                color="#334155",
            )
            figure.text(
                0.01,
                0.035,
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
            if args.output.read_bytes() != rendered:
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

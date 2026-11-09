from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch

import render_multi_task_chart as target
from _trial_comparisons import compare_blocks
from _trial_summary import aggregate, summarize_snapshot_evidence


def fixture_report(*, incomplete: bool = False, single: bool = False, candidate_name: str = "candidate"):
    definitions = {"default": {"skills": []}, candidate_name: {"skills": ["example"]}}
    reports = []
    rows = [
        ("a", ["task_passed", "task_failed"], ["task_passed", "task_passed"]),
        ("b", ["task_passed"], ["harness_error" if incomplete else "task_passed"]),
    ]
    if single:
        rows = rows[1:]
    for task, baseline, candidate in rows:
        attempts = [
            {"repetition": i, "condition": condition, "status": status, "usage": None, "provider_model_snapshot": None}
            for condition, statuses in (("default", baseline), (candidate_name, candidate))
            for i, status in enumerate(statuses, 1)
        ]
        reports.append(
            {
                "task_id": task,
                "protocol_sha256": task * 64,
                "grading_manifest_sha256": "f" * 64,
                "expected_grading_cases": 1,
                "limitations": [],
                "block_comparison": compare_blocks(attempts, set(definitions)),
                "model_requested": "fixture",
                "reasoning_effort_requested": "high",
                "partition": "synthetic control",
                "task_count": 1,
                "conditions": {name: {"planned_attempts": len(baseline)} for name in definitions},
                "attempts": attempts,
            }
        )
    result = aggregate(reports, [definitions] * len(reports))
    result["plan_sha256"] = "0" * 64
    return result


def reference_fixture_report(*, incomplete: bool = False):
    definitions = {"default": {}, "improved": {"skills": ["bundle"]}, "karpathy": {"skills": ["reference"]}}
    reports = []
    for task, statuses in (
        ("a", {"default": ["task_failed"], "improved": ["task_passed"], "karpathy": ["task_failed"]}),
        (
            "b",
            {
                name: ["timed_out" if incomplete and name == "karpathy" else "task_passed", "task_passed"]
                for name in definitions
            },
        ),
    ):
        attempts = [
            {"repetition": i, "condition": condition, "status": status, "usage": None, "provider_model_snapshot": None}
            for condition, values in statuses.items()
            for i, status in enumerate(values, 1)
        ]
        reports.append(
            {
                "task_id": task,
                "protocol_sha256": task * 64,
                "grading_manifest_sha256": "f" * 64,
                "expected_grading_cases": 1,
                "limitations": [],
                "block_comparison": compare_blocks(attempts, set(definitions)),
                "model_requested": "fixture",
                "reasoning_effort_requested": "high",
                "partition": "synthetic control",
                "task_count": 1,
                "conditions": {name: {"planned_attempts": len(values)} for name, values in statuses.items()},
                "attempts": attempts,
            }
        )
    result = aggregate(reports, [definitions] * len(reports))
    result["plan_sha256"] = "0" * 64
    return result


class ChartRowsTests(unittest.TestCase):
    def test_non_default_baseline_recomputes_direct_pair_from_attempts(self):
        report = reference_fixture_report()
        view = target.baseline_chart_view(report, "karpathy")
        self.assertEqual(view["chart_baseline"], "karpathy")
        self.assertEqual(target.graph_rows(view), [("improved", [Fraction(1), Fraction(0)], Fraction(1, 2), 2)])
        self.assertEqual(target.paired_rows(view)[0][1][1], Fraction(1, 2))
        self.assertIs(target.baseline_chart_view(report, "default"), report)

    def test_non_default_baseline_preserves_unscored_task_and_sensitivity_bounds(self):
        view = target.baseline_chart_view(reference_fixture_report(incomplete=True), "karpathy")
        self.assertEqual(target.graph_rows(view), [("improved", [Fraction(1)], None, 2)])
        self.assertEqual(target.sensitivity_ranges(view)["improved"], (Fraction(1, 2), Fraction(3, 4)))
        self.assertEqual(target.paired_rows(view)[0][4]["unscored"], 1)

    def test_non_default_baseline_rejects_tampered_comparison_and_attempts(self):
        report = reference_fixture_report()
        report["non_default_comparisons"]["karpathy"]["improved"]["equal_task_weight_mean_difference"]["numerator"] = 9
        with self.assertRaisesRegex(ValueError, "Direct comparison"):
            target.baseline_chart_view(report, "karpathy")
        report = reference_fixture_report()
        report["non_default_comparisons"]["karpathy"]["improved"]["equal_task_weight_mean_difference"]["numerator"] = (
            True
        )
        with self.assertRaisesRegex(ValueError, "Direct comparison"):
            target.baseline_chart_view(report, "karpathy")
        report = reference_fixture_report()
        report["tasks"][0]["attempts"][0]["status"] = "task_passed"
        with self.assertRaisesRegex(ValueError, "blocks disagree"):
            target.baseline_chart_view(report, "karpathy")
        report = reference_fixture_report()
        report["quality_superiority_established"] = True
        with self.assertRaisesRegex(ValueError, "no superiority claim"):
            target.baseline_chart_view(report, "karpathy")
        report = reference_fixture_report()
        with self.assertRaisesRegex(ValueError, "declared condition"):
            target.baseline_chart_view(report, "unknown")
        with self.assertRaisesRegex(ValueError, "another non-default"):
            target.baseline_chart_view(fixture_report(), "candidate")

    def test_incomplete_data_has_no_mean(self):
        rows = target.graph_rows(fixture_report(incomplete=True))
        self.assertEqual(len(rows[0][1]), 1)
        self.assertIsNone(rows[0][2])
        self.assertEqual(rows[0][3], 2)

    def test_sensitivity_ranges_are_bound_to_attempts(self):
        report = fixture_report(incomplete=True)
        self.assertEqual(target.sensitivity_ranges(report)["candidate"], (Fraction(-1, 4), Fraction(1, 4)))
        report["missing_outcome_sensitivity"]["candidate"]["equal_task_weight_lower"]["numerator"] = 0
        with self.assertRaisesRegex(ValueError, "sensitivity"):
            target.sensitivity_ranges(report)
        report = fixture_report(incomplete=True)
        report["tasks"][1]["attempt_status_counts"]["candidate"]["harness_error"] = 0
        with self.assertRaisesRegex(ValueError, "counts"):
            target.sensitivity_ranges(report)

    def test_inconsistent_denominator_or_mean_is_rejected(self):
        report = fixture_report()
        report["comparisons"]["candidate"]["fully_scored_tasks"] = 1
        with self.assertRaisesRegex(ValueError, "counts"):
            target.graph_rows(report)
        report = fixture_report(incomplete=True)
        report["comparisons"]["candidate"]["equal_task_weight_mean_difference"] = {"numerator": 1, "denominator": 2}
        with self.assertRaisesRegex(ValueError, "mean"):
            target.graph_rows(report)

    def test_invalid_fraction_and_superiority_claim_are_rejected(self):
        report = fixture_report()
        report["tasks"][0]["candidate_minus_default"]["candidate"]["denominator"] = 0
        with self.assertRaisesRegex(ValueError, "fraction"):
            target.graph_rows(report)
        report = fixture_report()
        report["quality_superiority_established"] = True
        with self.assertRaisesRegex(ValueError, "superiority"):
            target.graph_rows(report)


class PairedRowsTests(unittest.TestCase):
    def test_equal_task_weight_preserves_unscored_blocks(self):
        rows = target.paired_rows(fixture_report(incomplete=True))
        self.assertEqual(
            rows[0][:4], ("candidate", [Fraction(1, 4), Fraction(1, 4), Fraction(), Fraction(), Fraction(1, 2)], 2, 3)
        )
        self.assertEqual(rows[0][4], {"candidate_ahead": 1, "baseline_ahead": 0, "equal": 0, "unscored": 1})

    def test_paired_totals_and_fractions_must_match_attempts(self):
        for field, value in (("planned_blocks", True), ("planned_blocks", 2)):
            report = fixture_report()
            report["paired_outcomes"]["candidate"][field] = value
            with self.assertRaisesRegex(ValueError, "Paired outcomes"):
                target.paired_rows(report)
        report = fixture_report()
        report["paired_outcomes"]["candidate"]["equal_task_weight_block_fractions"]["both_passed"]["numerator"] = 2
        with self.assertRaisesRegex(ValueError, "Paired outcomes"):
            target.paired_rows(report)
        report = fixture_report()
        report["tasks"][0]["attempts"][0]["status"] = "task_failed"
        with self.assertRaisesRegex(ValueError, "blocks disagree"):
            target.paired_rows(report)

    def test_paired_conditions_must_match(self):
        report = fixture_report()
        report["paired_outcomes"] = {}
        with self.assertRaisesRegex(ValueError, "condition set"):
            target.paired_rows(report)


@unittest.skipUnless(importlib.util.find_spec("matplotlib") is not None, "requires the reports extra")
class ChartRenderTests(unittest.TestCase):
    def test_non_default_baseline_labels_both_chart_views_and_metadata(self):
        report = target.baseline_chart_view(reference_fixture_report(), "karpathy")
        for render, label in (
            (target.render_svg, "Task pass-rate difference (condition minus karpathy)"),
            (target.render_paired_svg, "karpathy only passed"),
        ):
            first = render(report)
            self.assertEqual(first, render(report))
            root = ET.fromstring(first)
            text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
            self.assertIn(label, text)
            self.assertIn(";baseline=karpathy", first.decode())

    def test_paired_view_is_reproducible_and_explains_missing_data(self):
        first = target.render_paired_svg(fixture_report(incomplete=True))
        self.assertEqual(first, target.render_paired_svg(fixture_report(incomplete=True)))
        root = ET.fromstring(first)
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        for label in (
            "Paired benchmark outcomes",
            "Equal-task-weight share of paired blocks",
            "Candidate only passed",
            "Default only passed",
            "Unscored",
            "2 tasks; 3 paired blocks",
            "Task directions: +1 / -0 / =0 / ?1",
            "Unscored is not failure. Snapshot IDs are provider-reported and not independently verified.",
            "Descriptive only; no significance or superiority claim.",
            "requested model: fixture | requested effort: high",
            "25%",
            "50%",
        ):
            self.assertIn(label, text)
        self.assertIn(("plan_sha256=" + "0" * 64 + ";view=paired_outcomes").encode(), first)

    def test_paired_view_labels_single_task_and_block(self):
        root = ET.fromstring(target.render_paired_svg(fixture_report(single=True)))
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("1 task; 1 paired block", text)

    def test_paired_view_shows_a_fully_unscored_task_without_a_winner(self):
        root = ET.fromstring(target.render_paired_svg(fixture_report(incomplete=True, single=True)))
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("100%", text)
        self.assertIn("Task directions: +0 / -0 / =0 / ?1", text)
        self.assertIn("Unscored is not failure", text)

    def test_paired_annotation_fits_outside_plot(self):
        from matplotlib.figure import Figure

        original = Figure.savefig

        def verify(figure, *args, **kwargs):
            figure.canvas.draw()
            texts = [text for axis in figure.axes for text in axis.texts if "Task directions:" in text.get_text()]
            self.assertEqual(len(texts), 1)
            bounds = texts[0].get_window_extent(figure.canvas.get_renderer())
            self.assertGreaterEqual(bounds.x0, figure.axes[0].bbox.x1)
            self.assertLessEqual(bounds.x1, figure.bbox.x1)
            for text in figure.texts:
                bounds = text.get_window_extent(figure.canvas.get_renderer())
                self.assertGreaterEqual(bounds.x0, figure.bbox.x0)
                self.assertLessEqual(bounds.x1, figure.bbox.x1)
            return original(figure, *args, **kwargs)

        with patch.object(Figure, "savefig", verify):
            target.render_paired_svg(fixture_report(incomplete=True))

    def test_long_condition_label_remains_inside_figure(self):
        from matplotlib.figure import Figure

        original = Figure.savefig

        def verify(figure, *args, **kwargs):
            figure.canvas.draw()
            labels = figure.axes[0].get_yticklabels()
            self.assertEqual(len(labels), 1)
            self.assertIn("\n", labels[0].get_text())
            self.assertGreaterEqual(labels[0].get_window_extent(figure.canvas.get_renderer()).x0, 0)
            return original(figure, *args, **kwargs)

        with patch.object(Figure, "savefig", verify):
            target.render_paired_svg(fixture_report(candidate_name="candidate-with-a-long-descriptive-identifier"))

    def test_paired_view_cli_writes_and_checks_output(self):
        report = fixture_report()
        with tempfile.TemporaryDirectory() as temp, patch.object(target, "run_plan", return_value=report):
            output = Path(temp) / "paired.svg"
            args = ["--plan", "unused.json", "--output", str(output), "--view", "paired"]
            self.assertEqual(target.main(args), 0)
            self.assertEqual(target.main([*args, "--check"]), 0)
            output.write_bytes(output.read_bytes().replace(b"view=paired_outcomes", b"view=changed"))
            self.assertEqual(target.main([*args, "--check"]), 1)

    def test_unscored_is_labeled_and_not_plotted_as_a_mean(self):
        svg = target.render_svg(fixture_report(incomplete=True))
        root = ET.fromstring(svg)
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("1/2 scored; mean unavailable", text)
        self.assertIn("unscored tasks are not failures", text)
        self.assertIn("Hypothetical bounds: -1/4 to 1/4", text)
        self.assertIn("Hypothetical bounds are not a confidence interval or superiority claim", text)
        self.assertIn("Hypothetical missing-outcome bounds", text)
        self.assertIn("Snapshot metadata unavailable: 6/6; distinct reported: 0", text)
        self.assertIn("IDs: incomplete; pairs: 0/3 differ, 3 incomplete", text)
        self.assertIn("Snapshot metadata is not independently verified", text)
        self.assertIn("requested model: fixture | requested effort: high", text)
        self.assertIn("does not prove preregistration or grading authenticity", text)
        groups = [node.get("id", "") for node in root.iter() if node.get("id", "").startswith("PathCollection_")]
        self.assertEqual(len(groups), 1)

    def test_complete_data_plots_tasks_and_validated_mean(self):
        first = target.render_svg(fixture_report())
        second = target.render_svg(fixture_report())
        self.assertEqual(first, second)
        self.assertIn(("plan_sha256=" + "0" * 64).encode(), first)
        root = ET.fromstring(first)
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("2/2 scored; mean 1/4", text)
        groups = [node.get("id", "") for node in root.iter() if node.get("id", "").startswith("PathCollection_")]
        self.assertEqual(len(groups), 2)

    def test_snapshot_metadata_counts_missing_and_distinct_values(self):
        report = fixture_report()
        report["tasks"][0]["attempts"][0]["provider_model_snapshot"] = "snapshot-a"
        report["tasks"][1]["attempts"][1]["provider_model_snapshot"] = "snapshot-b"
        report["model_snapshot_evidence"]["candidate"] = summarize_snapshot_evidence(report["tasks"], "candidate")
        root = ET.fromstring(target.render_svg(report))
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("Snapshot metadata unavailable: 4/6; distinct reported: 2", text)
        self.assertIn("IDs: vary; pairs: 0/3 differ, 3 incomplete", text)

    def test_snapshot_labels_show_reported_match_and_pair_mismatch(self):
        report = fixture_report()
        for task in report["tasks"]:
            for attempt in task["attempts"]:
                attempt["provider_model_snapshot"] = "snapshot-a"
        report["model_snapshot_evidence"]["candidate"] = summarize_snapshot_evidence(report["tasks"], "candidate")
        root = ET.fromstring(target.render_svg(report))
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("IDs: one reported; pairs: 0/3 differ, 0 incomplete", text)
        report["tasks"][0]["attempts"][2]["provider_model_snapshot"] = "snapshot-b"
        report["model_snapshot_evidence"]["candidate"] = summarize_snapshot_evidence(report["tasks"], "candidate")
        root = ET.fromstring(target.render_svg(report))
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("IDs: vary; pairs: 1/3 differ, 0 incomplete", text)

    def test_inconsistent_snapshot_evidence_is_rejected(self):
        report = fixture_report()
        report["model_snapshot_evidence"]["candidate"]["planned_pairs"] = 1
        with self.assertRaisesRegex(ValueError, "[Ss]napshot evidence"):
            target.render_svg(report)

    def test_boolean_is_not_a_valid_numeric_evidence_count(self):
        report = fixture_report()
        report["model_snapshot_evidence"]["candidate"]["different_reported_identifier_pairs"] = False
        with self.assertRaisesRegex(ValueError, "[Ss]napshot evidence"):
            target.render_svg(report)

    def test_boolean_is_not_a_valid_block_repetition(self):
        report = fixture_report()
        report["tasks"][0]["block_comparison"]["comparisons"]["candidate"]["blocks"][0]["repetition"] = True
        with self.assertRaisesRegex(ValueError, "[Ss]napshot evidence"):
            target.render_svg(report)

    def test_matching_pairs_with_different_identifiers_across_tasks_are_flagged(self):
        report = fixture_report()
        for task, snapshot in zip(report["tasks"], ("snapshot-a", "snapshot-b"), strict=True):
            for attempt in task["attempts"]:
                attempt["provider_model_snapshot"] = snapshot
        report["model_snapshot_evidence"]["candidate"] = summarize_snapshot_evidence(report["tasks"], "candidate")
        root = ET.fromstring(target.render_svg(report))
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("IDs: vary; pairs: 0/3 differ, 0 incomplete", text)

    def test_snapshot_annotation_fits_outside_plot(self):
        from matplotlib.figure import Figure

        original = Figure.savefig

        def verify(figure, *args, **kwargs):
            figure.canvas.draw()
            texts = [text for axis in figure.axes for text in axis.texts if "IDs:" in text.get_text()]
            self.assertEqual(len(texts), 1)
            bounds = texts[0].get_window_extent(figure.canvas.get_renderer())
            self.assertGreaterEqual(bounds.x0, figure.axes[0].bbox.x1)
            self.assertLessEqual(bounds.x1, figure.bbox.x1)
            return original(figure, *args, **kwargs)

        with patch.object(Figure, "savefig", verify):
            target.render_svg(fixture_report())

    def test_check_detects_a_changed_svg(self):
        report = fixture_report()
        output_log = io.StringIO()
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.object(target, "run_plan", return_value=report),
            contextlib.redirect_stdout(output_log),
        ):
            output = Path(temp) / "chart.svg"
            args = ["--plan", "unused.json", "--output", str(output)]
            self.assertEqual(target.main(args), 0)
            self.assertEqual(target.main([*args, "--check"]), 0)
            crlf = output.read_bytes().replace(b"\n", b"\r\n")
            output.write_bytes(crlf)
            self.assertEqual(target.main([*args, "--check"]), 0)
            changed = crlf.replace(b"plan_sha256=" + b"0" * 64, b"plan_sha256=1" + b"0" * 63, 1)
            self.assertNotEqual(changed, crlf)
            output.write_bytes(changed)
            self.assertEqual(target.main([*args, "--check"]), 1)
        self.assertFalse(json.loads(output_log.getvalue().splitlines()[-1])["ok"])

    def test_figure_closes_when_export_fails(self):
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure

        before = plt.get_fignums()
        with (
            patch.object(Figure, "savefig", side_effect=OSError("controlled export failure")),
            self.assertRaisesRegex(OSError, "controlled"),
        ):
            target.render_svg(fixture_report())
        self.assertEqual(plt.get_fignums(), before)


class ChartConsistencyTests(unittest.TestCase):
    def test_task_count_and_difference_range_are_checked(self):
        report = fixture_report()
        report["task_count"] = 1
        with self.assertRaises(ValueError):
            target.graph_rows(report)
        report = fixture_report()
        report["tasks"][0]["candidate_minus_default"]["candidate"]["numerator"] = 3
        with self.assertRaises(ValueError):
            target.graph_rows(report)

    def test_snapshot_counts_require_valid_attempts(self):
        report = fixture_report()
        self.assertEqual(target.snapshot_summary(report), (6, 6, 0))
        report["tasks"][0]["attempts"][0]["provider_model_snapshot"] = "snapshot-a"
        report["tasks"][1]["attempts"][1]["provider_model_snapshot"] = "snapshot-a"
        self.assertEqual(target.snapshot_summary(report), (4, 6, 1))
        report["tasks"][0]["attempts"][1]["provider_model_snapshot"] = ""
        with self.assertRaisesRegex(ValueError, "snapshot"):
            target.snapshot_summary(report)
        report = fixture_report()
        for task in report["tasks"]:
            task["attempts"] = []
        with self.assertRaisesRegex(ValueError, "attempts"):
            target.snapshot_summary(report)


if __name__ == "__main__":
    unittest.main()

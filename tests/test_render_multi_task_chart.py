from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import render_multi_task_chart as target


def fixture_report(*, incomplete: bool = False):
    first = {"numerator": 1, "denominator": 2}
    second = None if incomplete else {"numerator": 0, "denominator": 1}
    return {
        "plan_sha256": "0" * 64,
        "task_count": 2,
        "partition": "synthetic control",
        "model_requested": "fixture",
        "quality_superiority_established": False,
        "comparisons": {
            "candidate": {
                "planned_tasks": 2,
                "fully_scored_tasks": 1 if incomplete else 2,
                "unscored_tasks": 1 if incomplete else 0,
                "equal_task_weight_mean_difference": None if incomplete else {"numerator": 1, "denominator": 4},
            }
        },
        "tasks": [
            {"candidate_minus_default": {"candidate": first}},
            {"candidate_minus_default": {"candidate": second}},
        ],
    }


class ChartRowsTests(unittest.TestCase):
    def test_incomplete_data_has_no_mean(self):
        rows = target.graph_rows(fixture_report(incomplete=True))
        self.assertEqual(len(rows[0][1]), 1)
        self.assertIsNone(rows[0][2])
        self.assertEqual(rows[0][3], 2)

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


@unittest.skipUnless(importlib.util.find_spec("matplotlib") is not None, "requires the reports extra")
class ChartRenderTests(unittest.TestCase):
    def test_unscored_is_labeled_and_not_plotted_as_a_mean(self):
        svg = target.render_svg(fixture_report(incomplete=True))
        root = ET.fromstring(svg)
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("1/2 scored; mean unavailable", text)
        self.assertIn("unscored tasks are not failures", text)
        self.assertIn("No uncertainty or superiority claim", text)
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
            output.write_text("changed", encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()

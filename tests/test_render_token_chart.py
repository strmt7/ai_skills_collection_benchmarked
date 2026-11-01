from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import render_multi_task_chart as quality_chart
import render_token_chart as target
from _trial_comparisons import compare_blocks
from summarize_multi_task_trials import aggregate, summarize_snapshot_evidence


def fixture_report(incomplete: bool = False):
    definitions = {"default": {"skills": []}, "candidate": {"skills": ["example"]}}
    reports = []
    for task, baseline, candidate in (("a", 100, 120), ("b", 100, 90)):
        attempts = [
            {
                "repetition": 1,
                "condition": condition,
                "status": "task_passed",
                "usage": None
                if incomplete and task == "b" and condition == "candidate"
                else {
                    "input_tokens": count,
                    "output_tokens": count // 10,
                },
                "provider_model_snapshot": None,
            }
            for condition, count in (("default", baseline), ("candidate", candidate))
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
                "partition": "synthetic",
                "task_count": 1,
                "conditions": {name: {"planned_attempts": 1} for name in definitions},
                "attempts": attempts,
            }
        )
    result = aggregate(reports, [definitions, definitions])
    result["plan_sha256"] = "0" * 64
    return result


class TokenRowsTests(unittest.TestCase):
    def test_complete_and_incomplete_pairs(self):
        complete = target.token_rows(fixture_report())
        self.assertEqual(complete[0][1]["input_tokens"], [20, -10])
        self.assertEqual(complete[0][2]["input_tokens"], 5)
        incomplete = target.token_rows(fixture_report(incomplete=True))
        self.assertEqual(incomplete[0][1]["input_tokens"], [20])
        self.assertIsNone(incomplete[0][2])
        self.assertEqual(incomplete[0][3:], (1, 2, 1, 2))

    def test_corrupted_comparison_is_rejected(self):
        report = fixture_report()
        report["token_comparisons"]["candidate"]["equal_task_weight_mean_delta"]["input_tokens"]["numerator"] = 999
        with self.assertRaisesRegex(ValueError, "disagree"):
            target.token_rows(report)
        report = fixture_report()
        report["tasks"][0]["block_comparison"]["comparisons"]["candidate"]["blocks"][0]["token_delta"][
            "input_tokens"
        ] = 999
        with self.assertRaisesRegex(ValueError, "disagree"):
            target.token_rows(report)


@unittest.skipUnless(importlib.util.find_spec("matplotlib") is not None, "requires the reports extra")
class TokenRenderTests(unittest.TestCase):
    def test_incomplete_render_labels_missing_data_and_limits(self):
        svg = target.render_svg(fixture_report(incomplete=True))
        root = ET.fromstring(svg)
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("1/2 tasks; 1/2 blocks; mean unavailable", text)
        self.assertIn("Not priced cost, efficiency or superiority", text)
        self.assertIn("Snapshot metadata unavailable: 4/4", text)
        self.assertIn("IDs: incomplete; pairs: 0/2 differ, 2 incomplete", text)

    def test_per_candidate_model_snapshot_warning_is_visible(self):
        report = fixture_report()
        report["tasks"][0]["attempts"][0]["provider_model_snapshot"] = "a"
        report["tasks"][0]["attempts"][1]["provider_model_snapshot"] = "b"
        report["model_snapshot_evidence"]["candidate"] = summarize_snapshot_evidence(report["tasks"], "candidate")
        root = ET.fromstring(target.render_svg(report))
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("IDs: vary; pairs: 1/2 differ, 1 incomplete", text)

    def test_snapshot_warning_rejects_inconsistent_evidence(self):
        report = fixture_report()
        report["model_snapshot_evidence"]["candidate"]["incomplete_pairs"] = 0
        with self.assertRaisesRegex(ValueError, "[Ss]napshot evidence"):
            target.render_svg(report)

    def test_snapshot_annotation_fits_outside_both_plots(self):
        from matplotlib.figure import Figure

        original = Figure.savefig

        def verify(figure, *args, **kwargs):
            figure.canvas.draw()
            texts = [text for axis in figure.axes for text in axis.texts if "IDs:" in text.get_text()]
            self.assertEqual(len(texts), 1)
            bounds = texts[0].get_window_extent(figure.canvas.get_renderer())
            self.assertGreaterEqual(bounds.x0, figure.axes[1].bbox.x1)
            self.assertLessEqual(bounds.x1, figure.bbox.x1)
            return original(figure, *args, **kwargs)

        with patch.object(Figure, "savefig", verify):
            target.render_svg(fixture_report())

    def test_many_candidate_annotations_do_not_overlap(self):
        from matplotlib.figure import Figure

        report = fixture_report()
        names = ["candidate", *(f"candidate-{i}" for i in range(1, 9))]
        conditions = {"default", *names}
        for task in report["tasks"]:
            base = next(attempt for attempt in task["attempts"] if attempt["condition"] == "candidate")
            for name in names[1:]:
                attempt = {**base, "condition": name}
                task["attempts"].append(attempt)
                task["candidate_minus_default"][name] = copy.deepcopy(task["candidate_minus_default"]["candidate"])
                task["attempt_status_counts"][name] = copy.deepcopy(task["attempt_status_counts"]["candidate"])
            task["block_comparison"] = compare_blocks(task["attempts"], conditions)
        for name in names[1:]:
            report["comparisons"][name] = copy.deepcopy(report["comparisons"]["candidate"])
            report["token_comparisons"][name] = copy.deepcopy(report["token_comparisons"]["candidate"])
            report["missing_outcome_sensitivity"][name] = copy.deepcopy(
                report["missing_outcome_sensitivity"]["candidate"]
            )
        for name in names:
            report["model_snapshot_evidence"][name] = summarize_snapshot_evidence(report["tasks"], name)

        original = Figure.savefig

        def verify(figure, *args, **kwargs):
            figure.canvas.draw()
            texts = [text for axis in figure.axes for text in axis.texts if "IDs:" in text.get_text()]
            self.assertEqual(len(texts), len(names))
            bounds = sorted(
                (text.get_window_extent(figure.canvas.get_renderer()) for text in texts), key=lambda b: b.y0
            )
            for lower, upper in zip(bounds, bounds[1:], strict=False):
                self.assertLessEqual(lower.y1, upper.y0)
            self.assertTrue(
                all(
                    bound.x0 >= figure.bbox.x0
                    and bound.x1 <= figure.bbox.x1
                    and bound.y0 >= figure.bbox.y0
                    and bound.y1 <= figure.bbox.y1
                    for bound in bounds
                )
            )
            return original(figure, *args, **kwargs)

        with patch.object(Figure, "savefig", verify):
            quality_chart.render_svg(report)
            target.render_svg(report)

    def test_complete_render_is_deterministic_and_shows_both_token_types(self):
        report = fixture_report()
        first = target.render_svg(report)
        self.assertEqual(first, target.render_svg(report))
        root = ET.fromstring(first)
        text = " ".join("".join(node.itertext()) for node in root.iter() if node.tag.endswith("text"))
        self.assertIn("Input tokens", text)
        self.assertIn("Output tokens", text)
        self.assertIn("2/2 tasks; 2/2 blocks", text)

    def test_check_rejects_modified_chart(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            patch.object(target, "run_plan", return_value=fixture_report()),
            contextlib.redirect_stdout(io.StringIO()),
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

    def test_figure_closes_if_export_fails(self):
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure

        before = plt.get_fignums()
        with (
            patch.object(Figure, "savefig", side_effect=OSError("controlled export failure")),
            self.assertRaisesRegex(OSError, "controlled"),
        ):
            target.render_svg(fixture_report())
        self.assertEqual(plt.get_fignums(), before)


if __name__ == "__main__":
    unittest.main()

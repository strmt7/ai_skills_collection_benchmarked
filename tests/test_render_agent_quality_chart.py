"""Keep unscored attempts distinct from failures in the single-task chart."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import summarize_agent_trials as target


@unittest.skipUnless(importlib.util.find_spec("matplotlib"), "the optional reports dependencies are not installed")
class AgentQualityChartTests(unittest.TestCase):
    @staticmethod
    def report() -> dict[str, Any]:
        return {
            "protocol_sha256": "a" * 64,
            "partition": "development",
            "conditions": {
                "default": {
                    "planned_attempts": 4,
                    "task_passes": 1,
                    "status_counts": {"task_passed": 1, "harness_error": 1, "invalid_scope": 1, "timed_out": 1},
                },
                "improved": {
                    "planned_attempts": 4,
                    "task_passes": 1,
                    "status_counts": {"task_passed": 1, "task_failed": 3},
                },
            },
            "attempts": [],
        }

    def test_unscored_and_failed_attempts_are_visibly_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            target.plots(self.report(), output)
            root = ET.parse(output / "quality.svg").getroot()
        text = [element.text for element in root.iter() if element.tag.endswith("}text")]
        self.assertIn("Passed", text)
        self.assertIn("Failed", text)
        self.assertIn("Unscored", text)
        self.assertIn("1 pass / 0 fail / 3 unscored", text)
        self.assertIn("1 pass / 3 fail / 0 unscored", text)

    def test_plot_freshness_rejects_changed_svg_and_pixels(self) -> None:
        from PIL import Image

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            report = self.report()
            target.plots(report, output)
            target.verify_plots(report, output)
            svg = output / "quality.svg"
            original = svg.read_bytes()
            svg.write_bytes(original.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
            target.verify_plots(report, output)
            svg.write_bytes(original.replace(b"Unscored", b"Changed"))
            with self.assertRaisesRegex(ValueError, "quality.svg"):
                target.verify_plots(report, output)
            svg.write_bytes(original)
            png = output / "quality.png"
            with Image.open(png) as source:
                changed = source.convert("RGBA")
            changed.putpixel((0, 0), (0, 0, 0, 0))
            changed.save(png)
            with self.assertRaisesRegex(ValueError, "quality.png"):
                target.verify_plots(report, output)


if __name__ == "__main__":
    unittest.main()

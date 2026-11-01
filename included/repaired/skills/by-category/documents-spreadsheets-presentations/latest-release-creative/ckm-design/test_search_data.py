"""Controls over the bundled, source-locked data; not an agent benchmark."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "scripts/search.py"


class BundledDataControls(unittest.TestCase):
    def test_all_domains_and_plural_expansion(self):
        cases = (
            ("logo", "style", "minimalist", "exact", 1),
            ("logo", "color", "blue", "exact", 3),
            ("logo", "industry", "healthcare", "exact", 1),
            ("cip", "deliverable", "uniforms", "expanded", 3),
            ("cip", "deliverable", "ID badge", "exact", 3),
            ("cip", "style", "minimalist", "expanded", 0),
            ("cip", "industry", "healthcare", "exact", 1),
            ("cip", "mockup", "desk", "exact", 2),
        )
        for collection, domain, query, mode, count in cases:
            with self.subTest(collection=collection, domain=domain, query=query):
                result = subprocess.run(
                    [sys.executable, "-B", str(SCRIPT), "--collection", collection, "--domain", domain, query],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=20,
                    check=False,
                )
                body = json.loads(result.stdout)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(body["ok"])
                self.assertEqual(body["matching"], mode)
                self.assertEqual(body["count"], count)

    def test_missing_selected_data_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    "--data-dir",
                    directory,
                    "--collection",
                    "cip",
                    "--domain",
                    "deliverable",
                    "uniforms",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=20,
                check=False,
            )
        body = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(body["ok"])
        self.assertTrue(body["error"])


if __name__ == "__main__":
    unittest.main()

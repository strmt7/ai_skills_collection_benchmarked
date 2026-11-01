from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / "scripts/search.py"
FIELDS = ("Deliverable", "Category", "Keywords", "Description", "Mockup Context")
ROWS = (
    {
        "Deliverable": "ID Badge",
        "Category": "Identification",
        "Keywords": "identity pass badge staff",
        "Description": "employee identity card",
        "Mockup Context": "office",
    },
    {
        "Deliverable": "Event Badge",
        "Category": "Events",
        "Keywords": "conference badge attendee",
        "Description": "conference pass",
        "Mockup Context": "convention",
    },
    {
        "Deliverable": "Clinical Uniform",
        "Category": "Apparel",
        "Keywords": "uniform medical staff",
        "Description": "healthcare clothing",
        "Mockup Context": "clinic",
    },
    {
        "Deliverable": "Glass Tile",
        "Category": "Materials",
        "Keywords": "glass tile",
        "Description": "decorative tile",
        "Mockup Context": "showroom",
    },
    {
        "Deliverable": "Caf\u00e9 Sign",
        "Category": "Signage",
        "Keywords": "caf\u00e9 coffee",
        "Description": "shop sign",
        "Mockup Context": "storefront",
    },
    {
        "Deliverable": "News Archive",
        "Category": "Publishing",
        "Keywords": "news archive reports",
        "Description": "press collection",
        "Mockup Context": "pressroom",
    },
    {
        "Deliverable": "New Feature",
        "Category": "Product",
        "Keywords": "new feature launch",
        "Description": "new product",
        "Mockup Context": "app",
    },
)


class SearchContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.data = Path(self.temp.name) / "data"
        self.folder = self.data / "cip"
        self.folder.mkdir(parents=True)
        with (self.folder / "deliverables.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(ROWS)

    def run_query(self, query, *options):
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--data-dir",
                str(self.data),
                "--collection",
                "cip",
                "--domain",
                "deliverable",
                *options,
                query,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
            check=False,
        )
        return result, json.loads(result.stdout)

    def test_two_character_identity_changes_rank(self):
        proc, data = self.run_query("ID badge")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data["results"][0]["fields"]["Deliverable"], "ID Badge")
        self.assertEqual(data["results"][0]["matched_terms"], 2)
        self.assertFalse(data["results"][0]["used_stemming"])

    def test_plural_query_matches_singular(self):
        proc, data = self.run_query("uniforms")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("Clinical Uniform", [x["fields"]["Deliverable"] for x in data["results"]])
        self.assertTrue(data["results"][0]["used_stemming"])

    def test_exact_s_does_not_cut_off_glass(self):
        proc, data = self.run_query("glass")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data["results"][0]["fields"]["Deliverable"], "Glass Tile")

    def test_news_does_not_conflate_with_new(self):
        proc, data = self.run_query("news", "--match", "expanded")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual([x["fields"]["Deliverable"] for x in data["results"]], ["News Archive"])

    def test_partial_matches_are_explicit(self):
        proc, data = self.run_query("ID badge satellite")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data["results"][0]["query_terms"], 3)
        self.assertEqual(data["results"][0]["matched_terms"], 2)

    def test_unicode_casefold(self):
        proc, data = self.run_query("CAF\u00c9")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data["results"][0]["fields"]["Deliverable"], "Caf\u00e9 Sign")

    def test_no_matches_are_successful_and_explicit(self):
        proc, data = self.run_query("zzqnowhere")
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(data["ok"])
        self.assertEqual(data["results"], [])

    def test_missing_dataset_is_nonzero_and_structured(self):
        (self.folder / "deliverables.csv").unlink()
        proc, data = self.run_query("badge")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(data["ok"])
        self.assertIn("error", data)

    def test_empty_or_malformed_dataset_is_rejected(self):
        (self.folder / "deliverables.csv").write_text("wrong,headers\nvalue,other\n", encoding="utf-8")
        proc, data = self.run_query("badge")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(data["ok"])

    def test_header_only_dataset_is_rejected(self):
        (self.folder / "deliverables.csv").write_text(",".join(FIELDS) + "\n", encoding="utf-8")
        proc, data = self.run_query("badge")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(data["ok"])

    def test_single_letter_query_is_rejected(self):
        proc, data = self.run_query("a")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(data["ok"])

    def test_whitespace_query_is_rejected(self):
        proc, data = self.run_query("   ")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(data["ok"])

    def test_token_boundaries_and_ties_are_deterministic(self):
        proc, a = self.run_query("tile")
        proc, b = self.run_query("tile")
        self.assertEqual(a, b)
        self.assertEqual(proc.returncode, 0)

    def test_positive_result_limit(self):
        proc, data = self.run_query("badge", "--max-results", "1")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(len(data["results"]), 1)

    def test_nonpositive_result_limit_rejected(self):
        proc, data = self.run_query("badge", "--max-results", "0")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(data["ok"])

    def test_exact_mode_does_not_expand(self):
        proc, data = self.run_query("uniforms", "--match", "exact")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data["matching"], "exact")
        self.assertEqual(data["results"], [])

    def test_exact_query_does_not_require_dependency(self):
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                str(SCRIPT),
                "--data-dir",
                str(self.data),
                "--collection",
                "cip",
                "--domain",
                "deliverable",
                "ID badge",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
            check=False,
        )
        body = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(body["matching"], "exact")
        self.assertEqual(body["results"][0]["fields"]["Deliverable"], "ID Badge")

    def test_upper_result_limit_rejected(self):
        proc, data = self.run_query("badge", "--max-results", "51")
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(data["ok"])

    def test_unsearchable_dataset_is_rejected(self):
        with (self.folder / "deliverables.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerow(dict.fromkeys(FIELDS, ""))
        proc, data = self.run_query("badge")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("no searchable content", data["error"])

    def test_missing_dependency_is_a_structured_failure(self):
        result = subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                str(SCRIPT),
                "--data-dir",
                str(self.data),
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
        self.assertIn("snowballstemmer", body["error"])


if __name__ == "__main__":
    unittest.main()

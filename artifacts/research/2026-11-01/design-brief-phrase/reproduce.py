"""Reproduce the pinned design brief's handling of a multiword deliverable."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
SOURCE = (
    ROOT
    / "included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design"
    / "scripts/cip/core.py"
)
MANIFEST = ROOT / "artifacts/research/2026-11-01/design-search/source-manifest.json"


def observe() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_hash = manifest["files"]["scripts/cip/core.py"]
    source_bytes = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha256(source_bytes).hexdigest() != expected_hash:
        raise ValueError("pinned source does not match the recorded manifest")

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source_copy = root / "core.py"
        shutil.copyfile(SOURCE, source_copy)
        data = root / "data"
        data.mkdir()
        datasets = {
            "industries.csv": (
                ["Industry", "Keywords", "CIP Style", "Mood", "Key Deliverables"],
                [["Healthcare", "healthcare", "Modern", "calm", "Business Card"]],
            ),
            "styles.csv": (
                ["Style Name", "Category", "Keywords", "Description", "Mood"],
                [["Modern", "General", "modern", "clean", "calm"]],
            ),
            "deliverables.csv": (
                ["Deliverable", "Category", "Keywords", "Description", "Mockup Context"],
                [
                    ["Business Card", "Stationery", "identity contact", "small card", "desk"],
                    ["Business Analytics", "Business", "business business", "business report", "office"],
                ],
            ),
        }
        for name, (headers, rows) in datasets.items():
            with (data / name).open("w", encoding="utf-8", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(headers)
                writer.writerows(rows)

        spec = importlib.util.spec_from_file_location("pinned_cip_core", source_copy)
        if spec is None or spec.loader is None:
            raise ValueError("cannot load the copied source")
        module: Any = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.DATA_DIR = data
        brief = module.get_cip_brief("Example", "healthcare")
        actual = [item["Deliverable"] for item in brief["recommended_deliverables"]]

    expected = ["Business Card"]
    return {
        "artifact_kind": "independent_runtime_readiness_component",
        "source_commit": manifest["source_commit"],
        "source_sha256": expected_hash,
        "fixture": "One named deliverable and one unrelated item sharing one word.",
        "expected": expected,
        "actual": actual,
        "source_satisfies_expected": actual == expected,
        "agent_efficacy_scored": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = json.dumps(observe(), indent=2) + "\n"
    if args.check:
        if args.output.read_text(encoding="utf-8") != result:
            raise SystemExit("recorded observation differs from the current control")
    else:
        args.output.write_text(result, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

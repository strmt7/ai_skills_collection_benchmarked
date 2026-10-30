"""Reproduce the pinned PDF skill's document-information example with synthetic PDFs."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import tempfile
from pathlib import Path

import pypdf
from pypdf import PdfReader, PdfWriter

SKILL = "included/skills/by-category/documents-spreadsheets-presentations/official-reference/pdf-anthropics/SKILL.md"


def run(skill: Path) -> dict[str, object]:
    text = skill.read_text(encoding="utf-8")
    if "meta = reader.metadata" not in text or 'print(f"Title: {meta.title}")' not in text:
        raise ValueError("The pinned metadata example changed; review this control.")
    results = {}
    with tempfile.TemporaryDirectory(prefix="pdf-metadata-control-") as tmp:
        for name, title in (("without_info", None), ("with_title", "Control")):
            writer = PdfWriter()
            writer.add_blank_page(width=72, height=72)
            if title is None:
                writer.metadata = None
            else:
                writer.add_metadata({"/Title": title})
            path = Path(tmp) / f"{name}.pdf"
            with path.open("wb") as stream:
                writer.write(stream)
            metadata = PdfReader(path).metadata
            try:
                value = metadata.title
            except AttributeError as error:
                outcome = {"exception": type(error).__name__, "message": str(error)}
            else:
                outcome = {"exception": None, "title": value}
            results[name] = {"metadata_is_none": metadata is None, "outcome": outcome}
    if not results["without_info"]["metadata_is_none"]:
        raise AssertionError("The no-info fixture unexpectedly has document information")
    if results["without_info"]["outcome"]["exception"] != "AttributeError":
        raise AssertionError("The missing-information example did not reproduce")
    if results["with_title"]["outcome"] != {"exception": None, "title": "Control"}:
        raise AssertionError("The populated-information control failed")
    canonical = text.replace("\r\n", "\n").encode("utf-8")
    return {
        "python": platform.python_version(),
        "platform": platform.system(),
        "pypdf": pypdf.__version__,
        "skill_sha256": hashlib.sha256(canonical).hexdigest(),
        "cases": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-path", type=Path)
    args = parser.parse_args()
    skill = args.skill_path or Path(__file__).resolve().parents[4] / SKILL
    print(json.dumps(run(skill), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

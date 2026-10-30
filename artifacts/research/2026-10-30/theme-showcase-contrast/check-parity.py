"""Compare theme definitions with displayed showcase labels and sample fonts."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
from pathlib import Path

import pypdf
from pypdf import PdfReader
from pypdf.generic import ContentStream

SKILL = "included/skills/by-category/documents-spreadsheets-presentations/official-reference/theme-factory"
HEADER = "Sample Header Text"
BODY = "This is sample body text showing how your content will appear in presentations."


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def sample_fonts(reader: PdfReader, page_number: int) -> dict[str, str]:
    page = reader.pages[page_number - 1]
    fonts = page["/Resources"]["/Font"]
    current = None
    found = {}
    for operands, operator in ContentStream(page.get_contents(), reader).operations:
        if operator in (b"q", b"Q"):
            raise ValueError(f"Page {page_number} uses an unsupported graphics stack")
        if operator == b"Tf":
            current = operands[0]
        elif operator == b"Tj":
            text = str(operands[0])
            if text in (HEADER, BODY):
                label = "header" if text == HEADER else "body"
                if current is None or label in found:
                    raise ValueError(f"Page {page_number} has an ambiguous sample font")
                base = str(fonts[current].get_object()["/BaseFont"]).removeprefix("/")
                found[label] = base.split("+", 1)[-1]
    if set(found) != {"header", "body"}:
        raise ValueError(f"Page {page_number} is missing a sample font")
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", type=Path)
    args = parser.parse_args()
    root = args.skill_dir or Path(__file__).resolve().parents[4] / SKILL
    showcase = root / "theme-showcase.pdf"
    reader = PdfReader(showcase)
    files = sorted((root / "themes").glob("*.md"))
    if len(reader.pages) != 10 or len(files) != 10:
        raise ValueError("Expected ten showcase pages and ten theme definitions")
    pages = [(page.extract_text() or "") for page in reader.pages]
    results = []
    seen = set()
    for file in files:
        text = file.read_text(encoding="utf-8")
        title = text.splitlines()[0].removeprefix("# ").strip()
        matches = [i for i, page in enumerate(pages, 1) if page.splitlines()[0].strip() == title]
        colors = [color.lower() for color in re.findall(r"#[0-9a-fA-F]{6}\b", text)]
        header = re.search(r"\*\*Headers\*\*:\s*([^\n]+)", text)
        body = re.search(r"\*\*Body Text\*\*:\s*([^\n]+)", text)
        if len(matches) != 1 or matches[0] in seen or len(colors) != 4 or not header or not body:
            raise ValueError(f"Theme {title} has ambiguous metadata or a duplicate page")
        page_number = matches[0]
        seen.add(page_number)
        page = pages[page_number - 1]
        page_colors = [color.lower() for color in re.findall(r"#[0-9a-fA-F]{6}\b", page)]
        labels = {}
        for key, label in (("header", "Headers:"), ("body", "Body Text:")):
            match = re.search(re.escape(label) + r"\s*\n([^\n]+)", page)
            if not match:
                raise ValueError(f"Theme {title} has no {key} font label")
            labels[key] = match.group(1).strip()
        declared = {"header": header.group(1).strip(), "body": body.group(1).strip()}
        actual = sample_fonts(reader, page_number)
        if page_colors != colors:
            raise ValueError(f"Theme {title} color labels differ")
        if any(
            normalized(declared[key]) != normalized(labels[key]) or normalized(declared[key]) != normalized(actual[key])
            for key in declared
        ):
            raise ValueError(f"Theme {title} font labels or sample fonts differ")
        canonical = text.replace("\r\n", "\n").encode()
        results.append(
            {
                "theme": title,
                "page": page_number,
                "definition": file.name,
                "definition_sha256": hashlib.sha256(canonical).hexdigest(),
                "colors": colors,
                "fonts": declared,
            }
        )
    if seen != set(range(1, 11)):
        raise ValueError("Some showcase pages were not matched")
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.system(),
                "pypdf": pypdf.__version__,
                "showcase_sha256": hashlib.sha256(showcase.read_bytes()).hexdigest(),
                "themes_checked": len(results),
                "themes": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

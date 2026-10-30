"""Measure selected text and background colors in the pinned theme showcase."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

import pypdf
from pypdf import PdfReader
from pypdf.generic import ContentStream

SHOWCASE = (
    "included/skills/by-category/documents-spreadsheets-presentations/"
    "official-reference/theme-factory/theme-showcase.pdf"
)
THEMES = (
    "Ocean Depths",
    "Sunset Boulevard",
    "Forest Canopy",
    "Modern Minimalist",
    "Golden Hour",
    "Arctic Frost",
    "Desert Rose",
    "Tech Innovation",
    "Botanical Garden",
    "Midnight Galaxy",
)
SAMPLES = (
    ("header", "Sample Header Text", 28.0, 3.0),
    ("body", "This is sample body text showing how your content will appear in presentations.", 12.0, 4.5),
)


def luminance(rgb: tuple[float, ...]) -> float:
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return sum(channel * weight for channel, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))


def contrast(first: tuple[float, ...], second: tuple[float, ...]) -> float:
    dark, light = sorted((luminance(first), luminance(second)))
    return (light + 0.05) / (dark + 0.05)


def as_hex(rgb: tuple[float, ...]) -> str:
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in rgb)


def inspect(
    reader: PdfReader, page_number: int, title: str, sample: tuple[str, str, float, float]
) -> dict[str, object]:
    label, target, expected_size, threshold = sample
    page = reader.pages[page_number - 1]
    operations = ContentStream(page.get_contents(), reader).operations
    if len(operations) < 9 or [op for _, op in operations[5:9]] != [b"rg", b"n", b"re", b"f*"]:
        raise ValueError(f"Page {page_number} background structure changed")
    rect = tuple(float(value) for value in operations[7][0])
    if rect != (0, 0, float(page.mediabox.width), float(page.mediabox.height)):
        raise ValueError(f"Page {page_number} background is not page-sized")
    background = tuple(float(value) for value in operations[5][0])
    current = None
    seen_title = False
    foregrounds = []
    font_size = None
    matrix = None
    for operands, op in operations:
        if op == b"rg":
            current = tuple(float(value) for value in operands)
        elif op == b"cm" and tuple(float(value) for value in operands) != (1, 0, 0, 1, 0, 0):
            raise ValueError(f"Page {page_number} has a scaled transformation")
        elif op == b"Tf":
            font_size = float(operands[1])
        elif op == b"Tm":
            matrix = tuple(float(value) for value in operands[:4])
        elif op in (b"q", b"Q", b"g", b"k", b"cs", b"sc", b"scn", b"Tr", b"gs"):
            raise ValueError(f"Page {page_number} uses an unsupported color or text state")
        elif op == b"Tj":
            content = str(operands[0])
            seen_title = seen_title or content == title
            if content == target:
                foregrounds.append((current, font_size, matrix))
    if not seen_title or len(foregrounds) != 1:
        raise ValueError(f"Page {page_number} target text is missing or ambiguous")
    foreground, actual_size, actual_matrix = foregrounds[0]
    if foreground is None or actual_size != expected_size or actual_matrix != (1, 0, 0, 1):
        raise ValueError(f"Page {page_number} text color, size or transform changed")
    ratio = contrast(foreground, background)
    return {
        "page": page_number,
        "theme": title,
        "sample": label,
        "text": target,
        "font_points": actual_size,
        "foreground": as_hex(foreground),
        "background": as_hex(background),
        "contrast_ratio": round(ratio, 3),
        "reference_threshold": threshold,
        "below_reference": ratio < threshold,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--showcase", type=Path)
    args = parser.parse_args()
    showcase = args.showcase or Path(__file__).resolve().parents[4] / SHOWCASE
    if abs(contrast((0.0, 0.0, 0.0), (1.0, 1.0, 1.0)) - 21.0) > 1e-10:
        raise AssertionError("Black-white formula control failed")
    if abs(contrast((0.2, 0.4, 0.6), (0.2, 0.4, 0.6)) - 1.0) > 1e-10:
        raise AssertionError("Identical-color formula control failed")
    reader = PdfReader(showcase)
    if len(reader.pages) != 10:
        raise ValueError("The showcase page count changed")
    cases = [inspect(reader, page, title, sample) for page, title in enumerate(THEMES, 1) for sample in SAMPLES]
    summary = {
        label: sum(bool(case["below_reference"]) for case in cases if case["sample"] == label)
        for label in ("header", "body")
    }
    if summary != {"header": 1, "body": 7}:
        raise AssertionError("Pinned showcase contrast results changed")
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.system(),
                "pypdf": pypdf.__version__,
                "showcase_sha256": hashlib.sha256(showcase.read_bytes()).hexdigest(),
                "color_model_assumption": "PDF DeviceRGB interpreted as sRGB",
                "below_reference_count": summary,
                "cases": cases,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

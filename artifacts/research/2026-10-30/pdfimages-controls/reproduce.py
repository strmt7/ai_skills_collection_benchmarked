"""Check the pinned PDF skill's image extraction example with synthetic images."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path

import PIL
import reportlab
from PIL import Image
from reportlab.pdfgen import canvas

SKILL = "included/skills/by-category/documents-spreadsheets-presentations/official-reference/pdf-anthropics/SKILL.md"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdfimages", default="pdfimages")
    parser.add_argument("--library-path", type=Path)
    parser.add_argument("--skill-path", type=Path)
    args = parser.parse_args()
    skill = args.skill_path or Path(__file__).resolve().parents[4] / SKILL
    text = skill.read_text(encoding="utf-8")
    if "pdfimages -j input.pdf output_prefix" not in text:
        raise ValueError("The pinned image-extraction example changed; review this control.")
    env = os.environ.copy()
    if args.library_path:
        env["LD_LIBRARY_PATH"] = str(args.library_path)
    version = subprocess.run(
        [args.pdfimages, "-v"], env=env, capture_output=True, text=True, timeout=30, check=True
    ).stderr.splitlines()[0]
    with tempfile.TemporaryDirectory(prefix="pdfimages-control-") as tmp:
        root = Path(tmp)
        image = Image.new("RGB", (4, 3), (37, 83, 121))
        image.save(root / "lossless.png")
        image.save(root / "photo.jpg", quality=95)
        doc = canvas.Canvas(str(root / "input.pdf"), pagesize=(100, 100))
        doc.drawImage(str(root / "lossless.png"), 0, 0, width=20, height=20)
        doc.drawImage(str(root / "photo.jpg"), 25, 0, width=20, height=20)
        doc.save()
        subprocess.run(
            [args.pdfimages, "-j", str(root / "input.pdf"), str(root / "output")],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        files = sorted(root.glob("output-*"))
        if [p.name for p in files] != ["output-000.ppm", "output-001.jpg"]:
            raise AssertionError("Unexpected extracted filenames")
        with Image.open(files[0]) as extracted:
            if extracted.format != "PPM" or extracted.size != (4, 3) or extracted.getpixel((0, 0)) != (37, 83, 121):
                raise AssertionError("Lossless image did not round-trip")
        with Image.open(files[1]) as extracted:
            if extracted.format != "JPEG" or extracted.size != (4, 3):
                raise AssertionError("JPEG extraction failed")
        if files[1].read_bytes() != (root / "photo.jpg").read_bytes():
            raise AssertionError("JPEG stream changed")
        outputs = [p.name for p in files]
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.system(),
                "pillow": PIL.__version__,
                "reportlab": reportlab.Version,
                "pdfimages": version,
                "skill_sha256": hashlib.sha256(text.replace("\r\n", "\n").encode()).hexdigest(),
                "outputs": outputs,
                "lossless_pixels_preserved": True,
                "jpeg_bytes_preserved": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

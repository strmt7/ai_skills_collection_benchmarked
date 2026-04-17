#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path


def read_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".docx":
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", "ignore")
        return "".join(re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml))
    raise ValueError(f"Unsupported script format: {path.suffix}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract plain text from script file")
    parser.add_argument("script_path", help="Path to txt/md/docx script")
    args = parser.parse_args()

    path = Path(args.script_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Script not found: {path}")

    print(read_text(path).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

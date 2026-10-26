#!/usr/bin/env python3
"""Check every exact current mirror resource against publication detection rules."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from _catalog_publication import checked_path
from build_catalog import skill_tree_files
from check_no_secret_patterns import require_publishable_content

ROOT = Path(__file__).resolve().parents[1]


def check(root: Path) -> dict[str, Any]:
    root = root.resolve()
    raw = checked_path(root, "data/skills_catalog.json").read_bytes()
    entries = json.loads(raw)
    if not isinstance(entries, list) or not entries:
        raise ValueError("mirror admission requires a nonempty catalog")
    errors = []
    visited: set[Path] = set()
    total = 0
    for entry in entries:
        try:
            files = skill_tree_files(checked_path(root, entry["mirrored_path"]))
            if not files:
                raise ValueError("mirror resource set is empty")
        except (OSError, ValueError, KeyError, TypeError) as error:
            errors.append(f"catalog resource boundary: {error}")
            continue
        for path in files:
            if path in visited:
                continue
            visited.add(path)
            try:
                content = path.read_bytes()
                total += len(content)
                require_publishable_content(content)
            except (OSError, ValueError) as error:
                errors.append(f"{path.relative_to(root).as_posix()}: {error}")
    return {
        "ok": not errors,
        "errors": errors,
        "catalog_sha256": hashlib.sha256(raw).hexdigest(),
        "catalog_entries": len(entries),
        "checked_resources": len(visited),
        "bytes": total,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = check(args.root)
    except (OSError, ValueError, KeyError, TypeError) as error:
        report = {"ok": False, "errors": [str(error)]}
    print(json.dumps(report, indent=2) if args.json else str(report))
    return int(not report["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

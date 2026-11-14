"""Write a focused GNU Make C++ executable scaffold without replacing user files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="ASCII name: letters, digits, dots, underscores or hyphens")
    parser.add_argument("--output", type=Path, default=Path("Makefile"))
    parser.add_argument("--check", action="store_true", help="Compare an existing unmodified scaffold without writing")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.name) is None:
        parser.error(
            "--name must start with an ASCII letter or digit and contain only letters, digits, dots, underscores or hyphens"
        )
    try:
        template = (Path(__file__).resolve().parent / "templates/cpp.mk").read_text(encoding="utf-8")
        if template.count("@PROJECT@") != 1:
            raise ValueError("Template must declare exactly one project placeholder")
        expected = template.replace("@PROJECT@", args.name)
        if args.check:
            if args.output.read_text(encoding="utf-8") != expected:
                raise ValueError("Existing Makefile differs from the unmodified scaffold")
        else:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(expected)
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, "checked": args.check, "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

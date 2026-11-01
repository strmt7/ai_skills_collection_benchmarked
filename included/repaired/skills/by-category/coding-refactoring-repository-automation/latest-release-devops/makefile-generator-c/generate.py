from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a GNU Make template for a C application or ELF library.")
    parser.add_argument("--kind", choices=("c", "c-lib"), required=True)
    parser.add_argument(
        "--name", required=True, help="Single project name using letters, digits, dots, underscores, or hyphens"
    )
    parser.add_argument("--output", type=Path, default=Path("Makefile"))
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not NAME_PATTERN.fullmatch(args.name):
        parser.error(
            "--name must start with an ASCII letter or digit and contain only letters, digits, dots, underscores, or hyphens"
        )
    template = Path(__file__).resolve().parent / "templates" / f"{args.kind}.mk"
    try:
        template_text = template.read_text(encoding="utf-8")
        if template_text.count("@PROJECT@") != 1:
            raise ValueError("Template must contain exactly one project placeholder")
        text = template_text.replace("@PROJECT@", args.name)
        with args.output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, "kind": args.kind, "name": args.name, "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

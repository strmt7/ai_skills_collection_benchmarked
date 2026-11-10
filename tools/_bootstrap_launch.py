"""Run a development command with the explicitly provisioned package directory."""

from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        raise ValueError("Supply -m MODULE, -c CODE, --version, or a checkout script")
    root = args.root.resolve(strict=True)
    sys.path.insert(0, str(args.packages))
    if command[0] in {"--version", "-V"} and len(command) == 1:
        print(sys.version)
        return 0
    if command[0] in {"-m", "-c"}:
        if len(command) < 2:
            raise ValueError("A module name or code argument is required")
        # Match Python's module/code mode for the explicitly selected checkout.
        sys.path.insert(0, str(root))
        if command[0] == "-m":
            sys.argv = command[1:]
            runpy.run_module(command[1], run_name="__main__", alter_sys=True)
        else:
            sys.argv = ["-c", *command[2:]]
            exec(compile(command[1], "<string>", "exec"), {"__name__": "__main__", "__builtins__": __builtins__})
        return 0
    script = (root / command[0]).resolve(strict=True)
    if not script.is_relative_to(root) or not script.is_file() or script.suffix != ".py":
        raise ValueError("Development scripts must be Python files in the selected checkout")
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), *command[1:]]
    runpy.run_path(str(script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

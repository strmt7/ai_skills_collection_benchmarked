#!/usr/bin/env python3
"""Execute an external behavioral grader in a separate, time-bounded process."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def evaluate(grader: Path, workspace: Path) -> dict:
    if not grader.resolve().is_relative_to(ROOT / "benchmarks/agent-effectiveness/graders"):
        raise ValueError("grader must belong to the independent grader directory")
    spec = importlib.util.spec_from_file_location("trial_external_grader", grader)
    if spec is None or spec.loader is None:
        raise ValueError("external grader is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.evaluate(workspace)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grader", type=Path)
    parser.add_argument("workspace", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = evaluate(args.grader, args.workspace)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

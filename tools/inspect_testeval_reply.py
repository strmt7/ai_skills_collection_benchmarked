"""Inspect final-message delivery and observed usage for one completed TestEval turn."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from _windows_appcontainer import checked_path
from collect_testeval_reply import ROOT, observe_completed_reply


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution", type=Path, required=True, help="Owned native CLI execution records")
    parser.add_argument("--prompt-sha256", required=True, help="Frozen request digest")
    parser.add_argument(
        "--turn-output-budget", type=int, help="Compare the native turn's reported output tokens to this declared count"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        execution = checked_path(args.execution)
        if not execution.is_relative_to(ROOT / ".venv"):
            raise ValueError("Native execution evidence must be controller-owned")
        _, evidence = observe_completed_reply(execution, args.prompt_sha256, turn_output_budget=args.turn_output_budget)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    print(json.dumps({"ok": True, "observation": evidence}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Grade a submitted validator only inside the qualified Windows sandbox."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

import grade_validator_appcontainer_modern as confined
from _windows_appcontainer import checked_path

ROOT = Path(__file__).resolve().parents[1]
GRADER = ROOT / "benchmarks/agent-effectiveness/graders/artifact_validator.py"


def evaluate(
    grader: Path,
    workspace: Path,
    *,
    fixture: Path | None = None,
    revision: str | None = None,
    runtime_home: Path | None = None,
    dependency_home: Path | None = None,
    output: Path | None = None,
) -> dict[str, Any]:
    if grader.resolve() != GRADER.resolve():
        raise ValueError("unsupported external grader")
    if fixture is None or revision is None or runtime_home is None or dependency_home is None or output is None:
        return {
            "status": "harness_error",
            "errors": [
                "Explicit fixture, revision, runtime home, dependency home, and output are required for confined grading"
            ],
            "agent_performance_claim": False,
        }
    try:
        return confined.grade(
            checked_path(workspace),
            checked_path(fixture),
            checked_path(runtime_home),
            checked_path(dependency_home),
            checked_path(output),
            revision,
        )
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        return {"status": "harness_error", "errors": [str(error)], "agent_performance_claim": False}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grader", type=Path)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--revision")
    parser.add_argument("--runtime-home", type=Path)
    parser.add_argument("--dependency-home", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = evaluate(
            args.grader,
            args.workspace,
            fixture=args.fixture,
            revision=args.revision,
            runtime_home=args.runtime_home,
            dependency_home=args.dependency_home,
            output=args.output,
        )
    except (OSError, ValueError) as error:
        result = {"status": "harness_error", "errors": [str(error)], "agent_performance_claim": False}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "task_passed" else 2 if result["status"] == "harness_error" else 1


if __name__ == "__main__":
    raise SystemExit(main())

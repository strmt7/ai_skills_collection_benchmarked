#!/usr/bin/env python3
"""Check a lock against selected project extras in this interpreter without upgrading it."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def requirement_lines(text: str) -> list[str]:
    """Exclude generator metadata and resolver provenance, never requirements or hashes."""
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def verify(project: Path, lock: Path, extras: tuple[str, ...] = ("test", "lint", "security")) -> dict:
    # Seed the resolver with the actual lock. Resolving an empty output instead
    # silently upgrades dependencies and confuses new releases with stale inputs.
    with tempfile.TemporaryDirectory(prefix="skills-lock-check-") as directory:
        candidate = Path(directory) / lock.name
        shutil.copyfile(lock, candidate)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "piptools",
                "compile",
                "--generate-hashes",
                "--allow-unsafe",
                "--no-emit-index-url",
                "--no-emit-trusted-host",
                *(f"--extra={extra}" for extra in extras),
                f"--output-file={candidate}",
                str(project.resolve()),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=600,
            check=False,
        )
        if result.returncode:
            return {"valid": False, "errors": ["dependency resolver failed"], "diagnostic": result.stderr[-4000:]}
        same = requirement_lines(lock.read_text(encoding="utf-8")) == requirement_lines(
            candidate.read_text(encoding="utf-8")
        )
        return {"valid": same, "errors": [] if same else ["lock differs from seeded project resolution"]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT / "pyproject.toml")
    parser.add_argument("--lock", type=Path, default=ROOT / "requirements-lock.txt")
    parser.add_argument(
        "--extra", action="append", help="Project extra to verify; repeatable (default: test, lint, security)"
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = verify(args.project, args.lock, tuple(args.extra) if args.extra else ("test", "lint", "security"))
    except (OSError, subprocess.TimeoutExpired) as exc:
        result = {"valid": False, "errors": [str(exc)]}
    print(json.dumps(result, sort_keys=True) if args.json else result)
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

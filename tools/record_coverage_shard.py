"""Run pytest and bind its native coverage report to the measured source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from defusedxml import ElementTree as ET
from validate_coverage_bundle import (
    LANE_PATTERN,
    ROOT,
    SHARD_RECEIPT,
    git_output,
    inspect_report,
    shard_receipt,
    source_revision,
)


def snapshot_sources(root: Path) -> tuple[str, dict[str, str]]:
    """Capture the Python sources tracked at the checkout commit."""
    revision = source_revision(root)
    if git_output(root, "diff", "--no-ext-diff", "--name-only", revision, "--", "tools/"):
        raise ValueError("coverage measurement requires an unchanged tools checkout")
    files = git_output(root, "ls-tree", "-rz", "--name-only", revision, "--", "tools/")
    sources = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in files.decode("utf-8").split("\0")
        if name.endswith(".py")
    }
    if not sources:
        raise ValueError("no tracked Python tooling sources to measure")
    return revision, sources


def measure(root: Path, directory: Path, lane: str, pytest_args: Sequence[str]) -> int:
    """Publish a producer receipt only after successful tests on unchanged sources."""
    if not LANE_PATTERN.fullmatch(lane):
        raise ValueError(f"invalid coverage matrix lane: {lane!r}")
    revision, sources = snapshot_sources(root)
    directory.mkdir(parents=True)
    report = directory / "coverage.xml"
    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *pytest_args,
            "--cov=tools",
            "--cov-report=term-missing:skip-covered",
            f"--cov-report=xml:{report}",
        ],
        cwd=root,
        env={**os.environ, "COVERAGE_FILE": str(directory / ".coverage")},
        check=False,
    )
    if run.returncode:
        return run.returncode
    if snapshot_sources(root) != (revision, sources):
        raise ValueError("the tooling revision or sources changed during pytest")
    measurement = inspect_report(root, report, directory)
    if any(sources.get(name) != digest for name, digest in measurement["source_sha256"].items()):
        raise ValueError("the report references sources absent from the producer snapshot")
    receipt = shard_receipt(revision, lane, measurement)
    with (directory / SHARD_RECEIPT).open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
        stream.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Define the coverage producer interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--lane", required=True)
    parser.add_argument("--pytest-args", nargs=argparse.REMAINDER, default=())
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the requested pytest lane."""
    args = build_parser().parse_args(argv)
    try:
        return measure(args.root.resolve(), args.directory.resolve(), args.lane, args.pytest_args)
    except (OSError, ValueError, KeyError, ET.ParseError, subprocess.SubprocessError) as error:
        print(f"Coverage producer failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

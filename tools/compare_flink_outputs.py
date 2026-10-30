"""Compare Flink task output as one integer count per job, independent of row order.

The independently supplied reference must contain at least one job. This is a
separate development comparator, not the upstream verifier or a model score.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROW = re.compile(r"\(\s*([+-]?[0-9]+)\s*,\s*([0-9]+)\s*\)")


def parse_rows(text: str, label: str) -> dict[int, int]:
    """Parse and require exactly one record per numeric job identifier."""
    records: dict[int, int] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        match = ROW.fullmatch(line.strip())
        if match is None:
            raise ValueError(f"{label} line {line_number}: expected (jobId,nonnegative_count)")
        job_id, count = (int(value) for value in match.groups())
        if job_id in records:
            raise ValueError(f"{label} line {line_number}: duplicate jobId {job_id}")
        records[job_id] = count
    if not records:
        raise ValueError(f"{label}: no records")
    return records


def compare(expected_text: str, actual_text: str) -> list[str]:
    """Return deterministic differences against a separately supplied reference."""
    expected = parse_rows(expected_text, "expected")
    actual = parse_rows(actual_text, "actual")
    errors = [f"missing jobId {job_id}" for job_id in sorted(expected.keys() - actual.keys())]
    errors.extend(f"unexpected jobId {job_id}" for job_id in sorted(actual.keys() - expected.keys()))
    errors.extend(
        f"jobId {job_id}: expected {expected[job_id]}, got {actual[job_id]}"
        for job_id in sorted(expected.keys() & actual.keys())
        if expected[job_id] != actual[job_id]
    )
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", required=True, type=Path)
    parser.add_argument("--actual", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        errors = compare(args.expected.read_text(encoding="utf-8"), args.actual.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        errors = [str(exc)]
    report = {"passed": not errors, "errors": errors, "upstream_score": False, "model_scored": False}
    print(json.dumps(report, indent=2) if args.json else f"{len(errors)} differences")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

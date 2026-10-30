"""Reconstruct the pinned Flink development reference from public event data."""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import hashlib
import io
import itertools
import json
import platform
import re
from pathlib import Path

HASHES = {
    "jobs": "8d8c0278664757c79b2ce865d3e4e83531abf836e7ed6da3321b8309a3099c58",
    "tasks": "c122f250cf1f9817dc722a5b7457eb5caf122619accfada078de66d40f311501",
    "reference": "54a97eff4388b2a195f047a37250a5bad0648c6f15437bbe35acac3cf610828c",
}
GAP_MICROSECONDS = 600_000_000
ROW = re.compile(r"\((-?[0-9]+),([0-9]+)\)")


def pinned(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Unexpected input bytes: {path.name}")
    return data


def longest_stage(timestamps: list[int], *, split_on_equal: bool) -> int:
    """Return the largest session, counting every submitted event separately."""
    if not timestamps:
        raise ValueError("A stage requires at least one observed submission")
    ordered = sorted(timestamps)
    longest = current = 1
    for previous, current_time in itertools.pairwise(ordered):
        gap = current_time - previous
        split = gap >= GAP_MICROSECONDS if split_on_equal else gap > GAP_MICROSECONDS
        current = 1 if split else current + 1
        longest = max(longest, current)
    return longest


def parse_events(data: bytes, event_column: int, event_type: str) -> dict[int, list[int]]:
    by_job: dict[int, list[int]] = collections.defaultdict(list)
    text = gzip.decompress(data).decode("utf-8")
    for line, row in enumerate(csv.reader(io.StringIO(text, newline="")), 1):
        if len(row) <= event_column:
            raise ValueError(f"Malformed event row {line}")
        if row[event_column] == event_type:
            by_job[int(row[2])].append(int(row[0]))
    return dict(by_job)


def parse_reference(data: bytes) -> dict[int, int]:
    records = {}
    for line in data.decode("utf-8").splitlines():
        match = ROW.fullmatch(line)
        if match is None:
            raise ValueError("Malformed reference tuple")
        job, count = (int(value) for value in match.groups())
        if job in records:
            raise ValueError("Duplicate reference job")
        records[job] = count
    return records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data = {name: pinned(getattr(args, name), digest) for name, digest in HASHES.items()}
    finishes = parse_events(data["jobs"], 3, "4")
    submissions = parse_events(data["tasks"], 5, "0")
    expected = parse_reference(data["reference"])
    common = submissions.keys() & finishes.keys()
    reconstructed = {
        split: {job: longest_stage(submissions[job], split_on_equal=split) for job in common} for split in (True, False)
    }
    exact_gap_count = sum(
        later - earlier == GAP_MICROSECONDS
        for job in common
        for earlier, later in itertools.pairwise(sorted(submissions[job]))
    )
    matches = {mode: result == expected for mode, result in reconstructed.items()}
    report = {
        "platform": platform.system(),
        "python": platform.python_version(),
        "input_sha256": HASHES,
        "finish_job_count": len(finishes),
        "submission_job_count": len(submissions),
        "finished_with_observed_submissions": len(common),
        "finished_without_observed_submissions": len(finishes.keys() - submissions.keys()),
        "submitted_without_observed_finish": len(submissions.keys() - finishes.keys()),
        "submissions_after_last_finish": sum(t > max(finishes[j]) for j in common for t in submissions[j]),
        "reference_records": len(expected),
        "gaps_exactly_ten_minutes": exact_gap_count,
        "reference_matches_split_on_equal": matches[True],
        "reference_matches_split_after_equal": matches[False],
        "flink_job_executed": False,
        "model_scored": False,
    }
    print(json.dumps(report, indent=2))
    return 0 if all(matches.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reproduce paired aggregates from pinned SWE-Skills-Bench publisher tables."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from _trial_transcript import strict_json

MAX_BYTES = 2 * 1024**2
MAX_PAIRS = 20_000
COLUMNS = ["skill", "requirement_batch", "none_pass_rate", "one_pass_rate", "delta_pp"]
SKILL_ID = re.compile(r"[a-z0-9][a-z0-9_.-]{0,127}")
REPOSITORY = re.compile(r"[a-z0-9_.-]+/[a-z0-9_.-]+")
TABLE = re.compile(r"[A-Za-z0-9][A-Za-z0-9.-]*__[A-Za-z0-9][A-Za-z0-9.-]*_cells\.csv")


@dataclass(frozen=True, slots=True)
class RepositorySource:
    repository: str | None
    commit: str | None


@dataclass(frozen=True, slots=True)
class Frame:
    source_commit: str
    batches: tuple[str, ...]
    skills: dict[str, RepositorySource]
    tables: dict[str, str]


def _sha(value: Any, length: int) -> bool:
    return isinstance(value, str) and re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is not None


def parse_frame(value: Any) -> Frame:
    if not isinstance(value, dict) or set(value) != {"schema_version", "source_commit", "skills", "batches", "tables"}:
        raise ValueError("Frame must declare the source, skills, batches and publisher tables")
    if type(value["schema_version"]) is not int or value["schema_version"] != 1 or not _sha(value["source_commit"], 40):
        raise ValueError("Unsupported frame schema or source revision")
    skills, batches, tables = value["skills"], value["batches"], value["tables"]
    if not isinstance(skills, dict) or not skills or not isinstance(batches, list) or not batches:
        raise ValueError("Frame requires a nonempty skill and batch inventory")
    if len(skills) * len(batches) > MAX_PAIRS or batches != [f"batch{i}" for i in range(1, len(batches) + 1)]:
        raise ValueError("Frame has invalid batch identities or exceeds the pair bound")
    if (
        not isinstance(tables, dict)
        or not 1 <= len(tables) <= 32
        or any(
            not isinstance(name, str) or TABLE.fullmatch(name) is None or not _sha(digest, 64)
            for name, digest in tables.items()
        )
    ):
        raise ValueError("Frame has invalid publisher table identities")

    sources = {}
    for name, entry in skills.items():
        if (
            not isinstance(name, str)
            or SKILL_ID.fullmatch(name) is None
            or not isinstance(entry, dict)
            or set(entry) != {"repository", "commit"}
        ):
            raise ValueError("Frame has an invalid skill identity or provenance")
        repository, commit = entry["repository"], entry["commit"]
        if (
            repository is not None
            and (
                not isinstance(repository, str)
                or REPOSITORY.fullmatch(repository) is None
                or any(part in (".", "..") for part in repository.split("/"))
            )
        ) or (commit is not None and (repository is None or not _sha(commit, 40))):
            raise ValueError("Frame has an invalid declared repository or commit")
        sources[name] = RepositorySource(repository, commit)
    return Frame(value["source_commit"], tuple(batches), sources, dict(tables))


def _score(value: str, *, signed: bool = False) -> int:
    pattern = r"-?\d{1,3}\.\d{2}" if signed else r"\d{1,3}\.\d{2}"
    if re.fullmatch(pattern, value) is None:
        raise ValueError("Published scores must be complete decimal percentages")
    hundredths = int(Decimal(value) * 100)
    if abs(hundredths) > 10000:
        raise ValueError("Published score is outside its percentage range")
    return hundredths


def replay_table(raw: bytes, name: str, frame: Frame) -> dict[str, Any]:
    """Verify the full paired frame before calculating descriptive statistics."""
    digest = hashlib.sha256(raw).hexdigest()
    if not 0 < len(raw) <= MAX_BYTES or frame.tables.get(name) != digest:
        raise ValueError("Publisher table exceeds its size bound or differs from the frozen hash")
    reader = csv.reader(io.StringIO(raw.decode("utf-8"), newline=""), strict=True)
    if next(reader, None) != COLUMNS:
        raise ValueError("Publisher table columns differ from the paired result format")

    expected = {(skill, batch) for skill in frame.skills for batch in frame.batches}
    seen = set()
    none_sum = one_sum = delta_sum = 0
    signs: Counter[str] = Counter()
    group_sum: Counter[str] = Counter()
    group_size: Counter[str] = Counter()
    for row in reader:
        if len(row) != len(COLUMNS):
            raise ValueError("Publisher table has an invalid row width")
        skill, batch, none_raw, one_raw, delta_raw = row
        pair = (skill, batch)
        if pair not in expected or pair in seen:
            raise ValueError("Publisher table has an unexpected or duplicate pair")
        seen.add(pair)
        none, one, delta = _score(none_raw), _score(one_raw), _score(delta_raw, signed=True)
        # The publisher rounds the two arms and their difference independently.
        if abs(delta - (one - none)) > 1:
            raise ValueError("Published delta disagrees with its paired percentages")
        none_sum += none
        one_sum += one
        delta_sum += delta
        signs["higher" if delta > 0 else "lower" if delta < 0 else "tied"] += 1
        repository = frame.skills[skill].repository
        if repository is not None:
            group_sum[repository] += delta
            group_size[repository] += 1
    if seen != expected:
        raise ValueError("Publisher table is missing pairs from the frozen frame")

    count = len(expected)
    denominator = 100 * count
    omit_repo = [
        (delta_sum - group_sum[repo]) / (100 * (count - size)) for repo, size in group_size.items() if size < count
    ]
    return {
        "pairs": count,
        "none_mean_percent": none_sum / denominator,
        "one_mean_percent": one_sum / denominator,
        "published_delta_mean_pp": delta_sum / denominator,
        "rounded_arm_difference_pp": (one_sum - none_sum) / denominator,
        "published_delta_direction_counts": {key: signs[key] for key in ("higher", "lower", "tied")},
        "declared_repository_groups": len(group_size),
        "pairs_without_declared_repo_commit": sum(source.commit is None for source in frame.skills.values())
        * len(frame.batches),
        "leave_one_declared_repository_out_delta_pp": (
            {"min": min(omit_repo), "max": max(omit_repo)} if omit_repo else None
        ),
        "table_sha256": digest,
    }


def _read(path: Path) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("Archive input is empty or exceeds its size bound")
    return raw


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--tables-dir", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        raw_frame = _read(args.frame)
        frame = parse_frame(strict_json(raw_frame.decode("utf-8")))
        configurations = {
            name.removesuffix("_cells.csv"): replay_table(_read(args.tables_dir / name), name, frame)
            for name in sorted(frame.tables)
        }
    except (OSError, ValueError, csv.Error) as exc:
        print(json.dumps({"status": "archive_not_verified", "error": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": "publisher_archive_replayed",
                "source_commit": frame.source_commit,
                "frame_sha256": hashlib.sha256(raw_frame).hexdigest(),
                "configurations": configurations,
                "local_model_trials": 0,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

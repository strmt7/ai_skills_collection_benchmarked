"""Freeze a repository-grouped public development sample without reading outcomes."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from _lib_b.io_utils import dumps_deterministic, write_text
from _trial_transcript import strict_json
from verify_swe_skills_bench_results import MAX_BYTES, parse_frame

CONDITIONS = ("default", "karpathy", "collection")


def select_tasks(raw: bytes, *, seed: str, count: int, exclusions: Any) -> dict[str, Any]:
    """Rank declared source groups and take one skill/batch cell per group.

    This is a deterministic development design, not proof of random sampling,
    independent tasks, preregistration timing or a qualified model launcher.
    """
    if not isinstance(seed, str) or re.fullmatch(r"[0-9a-f]{64}", seed) is None:
        raise ValueError("Selection seed must be an explicit lowercase SHA-256 value")
    if type(count) is not int or not 1 <= count <= 1000:
        raise ValueError("Select between one and 1000 distinct repository groups")
    if not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("Task frame exceeds its input bound")
    frame = parse_frame(strict_json(raw.decode("utf-8")))
    if not isinstance(exclusions, dict) or any(
        name not in frame.skills
        or not isinstance(reason, str)
        or not 0 < len(reason) <= 512
        or reason != reason.strip()
        or any(ord(char) < 32 for char in reason)
        for name, reason in exclusions.items()
    ):
        raise ValueError("Exclusions must name existing skills with explicit substantive reasons")
    groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    unresolved = []
    for skill, source in frame.skills.items():
        if skill in exclusions:
            continue
        if source.repository is None or source.commit is None:
            unresolved.append(skill)
            continue
        groups[source.repository.casefold()].extend((skill, batch) for batch in frame.batches)
    if count > len(groups):
        raise ValueError("Requested sample exceeds the eligible distinct repository groups")

    def rank(domain: str, *parts: str) -> tuple[str, tuple[str, ...]]:
        encoded = json.dumps([domain, seed, *parts], separators=(",", ":"), ensure_ascii=True).encode("ascii")
        return hashlib.sha256(encoded).hexdigest(), parts

    orders = sorted(itertools.permutations(CONDITIONS), key=lambda values: rank("condition-order", *values))
    selected = []
    for index, group in enumerate(sorted(groups, key=lambda name: rank("repository", name))[:count]):
        skill, batch = min(groups[group], key=lambda cell: rank("cell", group, *cell))
        source = frame.skills[skill]
        selected.append(
            {
                "task_id": f"swe-skills-bench/{batch}/{skill}",
                "skill_id": skill,
                "batch": batch,
                "repository": source.repository,
                "source_commit": source.commit,
                "repository_group": group,
                "condition_order": list(orders[index % len(orders)]),
            }
        )
    return {
        "schema_version": 1,
        "kind": "swe-skills-bench-public-development-selection",
        "partition": "development",
        "source_commit": frame.source_commit,
        "frame_sha256": hashlib.sha256(raw).hexdigest(),
        "seed": seed,
        "selection_method": "SHA-256 rank of repository groups, then one skill/batch cell per group",
        "planned_tasks": count,
        "conditions": list(CONDITIONS),
        "planned_attempts": count * len(CONDITIONS),
        "frame_skills": len(frame.skills),
        "frame_batches": len(frame.batches),
        "frame_cells": len(frame.skills) * len(frame.batches),
        "eligible_repository_groups": len(groups),
        "eligible_cells": sum(len(cells) for cells in groups.values()),
        "exclusions": dict(sorted(exclusions.items())),
        "unresolved_source_skills": sorted(unresolved),
        "selected": selected,
        "model_invocations": 0,
        "execution_admitted": False,
        "preregistration_timing_verified": False,
        "task_independence_verified": False,
        "limitations": [
            "Source groups are declared repositories, not verified semantic independence or a complete overlap audit.",
            "A fixed seed is reproducible, not proof of random or representative sampling; retain its provenance.",
            "Public development tasks are exposed material and cannot become an untouched confirmatory holdout.",
            "Publisher outcome tables, task briefs, evaluator implementations and reference solutions are not read.",
            "No image, task, scorer, intervention, model or runner is admitted by this selection receipt.",
            "Freeze interventions, common budgets, native metrics, missing-outcome and stopping rules before execution.",
        ],
    }


def _read(path: Path) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    if not 0 < len(raw) <= MAX_BYTES:
        raise ValueError("Selection input is empty or exceeds its input bound")
    return raw


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--exclusions", type=Path, required=True, help="JSON skill ID to predeclared exclusion reason")
    parser.add_argument(
        "--seed", required=True, help="Explicit lowercase SHA-256 seed; retain its independent provenance"
    )
    parser.add_argument("--tasks", type=int, required=True, help="One cell per distinct declared repository group")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="Check the receipt without rewriting it")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.output.resolve() in {args.frame.resolve(), args.exclusions.resolve()}:
            raise ValueError("Selection output must not replace an input")
        raw, exclusions = _read(args.frame), _read(args.exclusions)
        result = select_tasks(raw, seed=args.seed, count=args.tasks, exclusions=strict_json(exclusions.decode("utf-8")))
        result["exclusions_sha256"] = hashlib.sha256(exclusions).hexdigest()
        if _read(args.frame) != raw or _read(args.exclusions) != exclusions:
            raise ValueError("Selection inputs changed during verification")
        expected = dumps_deterministic(result)
        if args.check:
            expected_bytes = expected.encode("utf-8")
            with args.output.open("rb") as stream:
                observed = stream.read(len(expected_bytes) + 1)
            if observed != expected_bytes:
                raise ValueError("Development selection receipt is stale")
        else:
            write_text(args.output, expected)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(
        json.dumps(
            {
                "ok": True,
                "planned_tasks": args.tasks,
                "planned_attempts": result["planned_attempts"],
                "execution_admitted": False,
                "model_invocations": 0,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

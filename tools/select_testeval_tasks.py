"""Check or reproduce the metadata-only public TestEval crossover schedule."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from _lib_b.io_utils import dumps_deterministic, write_text
from _trial_transcript import strict_json

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "benchmarks/agent-effectiveness/development/testeval-pilot-v2"
PUBLISHER = "https://github.com/LLM4SoftwareTesting/TestEval"
CONDITIONS = ("default", "karpathy", "collection")
STRATA = ("1", "2", "3")
PER_STRATUM = 4
MAX_FRAME_BYTES = 1024 * 1024
ORDER_SEED = "testeval-public-order-v2"
Order = tuple[str, ...]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rank(*parts: str) -> str:
    return _sha256("\0".join((ORDER_SEED, *parts)).encode("utf-8"))


def _balanced_blocks() -> tuple[tuple[Order, ...], ...]:
    """Choose 12 orders with position balance within each group of four."""
    orders = tuple(itertools.permutations(CONDITIONS))
    balanced = [
        block
        for block in itertools.combinations_with_replacement(orders, PER_STRATUM)
        if all(
            sorted(sum(order[position] == condition for order in block) for position in range(len(CONDITIONS)))
            == [1, 1, 2]
            for condition in CONDITIONS
        )
    ]
    target = Counter({order: 2 for order in orders})
    eligible = (
        blocks
        for blocks in itertools.product(balanced, repeat=len(STRATA))
        if Counter(itertools.chain.from_iterable(blocks)) == target
    )
    return min(
        eligible,
        key=lambda blocks: (
            sum(PER_STRATUM - len(set(block)) for block in blocks),
            _rank(json.dumps(blocks, separators=(",", ":"))),
        ),
    )


def _positive_task_id(value: Any) -> bool:
    return type(value) is int and 1 <= value <= 1_000_000


def _frame(raw: bytes) -> dict[str, Any]:
    if not 0 < len(raw) <= MAX_FRAME_BYTES:
        raise ValueError("The TestEval metadata frame is empty or exceeds its byte budget")
    data = strict_json(raw.decode("utf-8"))
    fields = {"schema_version", "publisher", "selection_seed", "tasks_by_difficulty", "previous_exposures"}
    if (
        not isinstance(data, dict)
        or data.keys() != fields
        or type(data["schema_version"]) is not int
        or data["schema_version"] != 1
    ):
        raise ValueError("Expected a versioned metadata-only TestEval frame")
    publisher = data["publisher"]
    if (
        not isinstance(publisher, dict)
        or publisher.keys() != {"repository", "commit", "dataset_sha256", "evaluator_sha256"}
        or publisher["repository"] != PUBLISHER
        or any(
            not isinstance(publisher[key], str) or re.fullmatch(f"[a-f0-9]{{{width}}}", publisher[key]) is None
            for key, width in (("commit", 40), ("dataset_sha256", 64), ("evaluator_sha256", 64))
        )
    ):
        raise ValueError("The publisher frame requires its exact Git, dataset and evaluator identities")
    seed = data["selection_seed"]
    if not isinstance(seed, str) or re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", seed) is None:
        raise ValueError("The selection seed must be explicit")
    tasks = data["tasks_by_difficulty"]
    if not isinstance(tasks, dict) or tasks.keys() != set(STRATA):
        raise ValueError("The TestEval frame must declare precisely the three publisher difficulty strata")
    if any(
        not isinstance(group, list) or any(not _positive_task_id(task) for task in group) for group in tasks.values()
    ):
        raise ValueError("Each difficulty stratum must list positive TestEval task IDs")
    task_ids = list(itertools.chain.from_iterable(tasks.values()))
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("TestEval task IDs must be unique across the frame")
    exposures = data["previous_exposures"]
    if not isinstance(exposures, list) or any(
        not isinstance(item, dict)
        or item.keys() != {"task_num", "reason"}
        or not _positive_task_id(item["task_num"])
        or not isinstance(item["reason"], str)
        or not item["reason"].strip()
        or item["reason"] != item["reason"].strip()
        or len(item["reason"]) > 512
        for item in exposures
    ):
        raise ValueError("Each previous exposure must name a task and a reason")
    excluded = [item["task_num"] for item in exposures]
    if len(excluded) != len(set(excluded)) or not set(excluded) <= set(task_ids):
        raise ValueError("Previous exposure IDs must be unique and present in the frame")
    return data


def select(raw: bytes) -> dict[str, Any]:
    """Retain the original seeded case selection and improve within-difficulty order."""
    frame = _frame(raw)
    publisher = frame["publisher"]
    selection_seed = frame["selection_seed"]
    excluded = {item["task_num"] for item in frame["previous_exposures"]}
    blocks = _balanced_blocks()
    selected_strata = []
    position_counts = {}
    for difficulty, block in zip(STRATA, blocks, strict=True):
        eligible = set(frame["tasks_by_difficulty"][difficulty]) - excluded
        if len(eligible) < PER_STRATUM:
            raise ValueError(f"Difficulty {difficulty} has fewer than four eligible tasks")
        pool = sorted(
            eligible,
            key=lambda task: (_sha256(f"{selection_seed}|{publisher['commit']}|{task}".encode()), task),
        )[:PER_STRATUM]
        tasks = sorted(pool, key=lambda task: (_rank("task", str(task)), task))
        orders = sorted(block, key=lambda order: (_rank("order", difficulty, "/".join(order)), order))
        selected_strata.append(
            [
                {"task_num": task, "publisher_difficulty": int(difficulty), "condition_order": list(order)}
                for task, order in zip(tasks, orders, strict=True)
            ]
        )
        position_counts[difficulty] = {
            condition: [sum(order[position] == condition for order in orders) for position in range(len(CONDITIONS))]
            for condition in CONDITIONS
        }
    selected = list(itertools.chain.from_iterable(zip(*selected_strata, strict=True)))
    return {
        "schema_version": 2,
        "kind": "testeval-public-development-selection",
        "partition": "public_development",
        "publisher": publisher,
        "frame_sha256": _sha256(raw),
        "selection_seed": selection_seed,
        "order_seed": ORDER_SEED,
        "source_counts_by_difficulty": {stratum: len(frame["tasks_by_difficulty"][stratum]) for stratum in STRATA},
        "previous_exposures": sorted(frame["previous_exposures"], key=lambda item: item["task_num"]),
        "conditions": list(CONDITIONS),
        "position_counts_by_difficulty": position_counts,
        "global_position_counts": {
            condition: [
                sum(row["condition_order"][position] == condition for row in selected)
                for position in range(len(CONDITIONS))
            ]
            for condition in CONDITIONS
        },
        "selected": selected,
        "planned_attempts": len(selected) * len(CONDITIONS),
        "model_attempts": 0,
        "execution_admitted": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", type=Path, default=PILOT / "frame.json")
    parser.add_argument("--output", type=Path, default=PILOT / "selection.json")
    parser.add_argument("--check", action="store_true", help="Verify the exact receipt without rewriting it")
    return parser


def _read(path: Path) -> bytes:
    with path.open("rb") as stream:
        return stream.read(MAX_FRAME_BYTES + 1)


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        if arguments.frame.resolve() == arguments.output.resolve():
            raise ValueError("The selection output must differ from its input frame")
        raw = _read(arguments.frame)
        result = select(raw)
        output = dumps_deterministic(result)
        if _read(arguments.frame) != raw:
            raise ValueError("The metadata frame changed during selection")
        if arguments.check:
            if _read(arguments.output) != output.encode("utf-8"):
                raise ValueError("The TestEval selection receipt is stale")
        else:
            write_text(arguments.output, output)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, "planned_attempts": result["planned_attempts"], "execution_admitted": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Protect the frozen TestEval case and crossover contracts."""

from __future__ import annotations

import copy
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
import select_testeval_tasks as schedule


def metadata() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "publisher": {
            "repository": schedule.PUBLISHER,
            "commit": "a" * 40,
            "dataset_sha256": "b" * 64,
            "evaluator_sha256": "c" * 64,
        },
        "selection_seed": "independent-control",
        "previous_exposures": [{"task_num": 4, "reason": "Reserved for a previous control"}],
        "tasks_by_difficulty": {
            "1": [1, 2, 3, 4, 5, 6],
            "2": [11, 12, 13, 14, 15, 16],
            "3": [21, 22, 23, 24, 25, 26],
        },
    }


def raw(frame: dict[str, Any]) -> bytes:
    return json.dumps(frame).encode()


def test_crossover_retains_independent_balance_and_sample_identity() -> None:
    frame = metadata()
    result = schedule.select(raw(frame))
    conditions = ("default", "karpathy", "collection")
    selected = result["selected"]
    assert len({row["task_num"] for row in selected}) == 12
    assert 4 not in {row["task_num"] for row in selected}
    assert Counter(tuple(row["condition_order"]) for row in selected) == Counter(
        {order: 2 for order in itertools.permutations(conditions)}
    )
    assert [row["publisher_difficulty"] for row in selected] == [1, 2, 3] * 4
    for stratum in range(1, 4):
        local = [row["condition_order"] for row in selected if row["publisher_difficulty"] == stratum]
        for condition in conditions:
            assert sorted(sum(order[position] == condition for order in local) for position in range(3)) == [1, 1, 2]
    assert result["global_position_counts"] == {condition: [4, 4, 4] for condition in conditions}
    assert result["planned_attempts"] == 36
    assert result["model_attempts"] == 0 and result["execution_admitted"] is False

    shuffled = copy.deepcopy(frame)
    shuffled["tasks_by_difficulty"] = {
        name: list(reversed(values)) for name, values in reversed(frame["tasks_by_difficulty"].items())
    }
    recreated = schedule.select(raw(shuffled))
    assert recreated["selected"] == selected
    assert recreated["frame_sha256"] != result["frame_sha256"]


def test_rejects_overlapping_ids_and_unadmitted_metadata() -> None:
    frame = metadata()
    frame["tasks_by_difficulty"]["3"][0] = frame["tasks_by_difficulty"]["2"][0]
    with pytest.raises(ValueError, match="unique"):
        schedule.select(raw(frame))
    extra = metadata() | {"reference_outputs": []}
    with pytest.raises(ValueError, match="metadata-only"):
        schedule.select(raw(extra))


@pytest.mark.parametrize("value", [True, 0, -7, "1"])
def test_rejects_invalid_task_id_even_if_it_could_sort(value: object) -> None:
    frame = metadata()
    frame["tasks_by_difficulty"]["1"][0] = value
    with pytest.raises(ValueError, match="positive"):
        schedule.select(raw(frame))


def test_rejects_unverifiable_exposure_and_insufficient_stratum() -> None:
    frame = metadata()
    frame["previous_exposures"][0]["task_num"] = 99
    with pytest.raises(ValueError, match="present in the frame"):
        schedule.select(raw(frame))
    frame["previous_exposures"][0]["task_num"] = 4
    frame["tasks_by_difficulty"]["1"] = [1, 2, 3, 4]
    with pytest.raises(ValueError, match="fewer than four"):
        schedule.select(raw(frame))


def test_check_is_read_only_and_input_is_never_overwritten(tmp_path: Path) -> None:
    source = tmp_path / "frame.json"
    target = tmp_path / "selection.json"
    source.write_bytes(raw(metadata()))
    original = source.read_bytes()
    args = ["--frame", str(source), "--output", str(target)]
    assert schedule.main(args) == 0
    assert schedule.main([*args, "--check"]) == 0
    stale = b'{"invalid":true}\n'
    target.write_bytes(stale)
    assert schedule.main([*args, "--check"]) == 1
    assert target.read_bytes() == stale
    assert schedule.main(["--frame", str(source), "--output", str(source)]) == 1
    assert source.read_bytes() == original


def test_checked_in_publisher_schedule_reproduces() -> None:
    assert schedule.main(["--check"]) == 0
    selection = json.loads((schedule.PILOT / "selection.json").read_bytes())
    assert selection["source_counts_by_difficulty"] == {"1": 9, "2": 100, "3": 101}
    assert selection["planned_attempts"] == 36

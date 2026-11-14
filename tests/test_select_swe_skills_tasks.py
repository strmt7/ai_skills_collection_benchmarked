"""Selection must not count repeated repository cells as independent tasks."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
import select_swe_skills_tasks as selector


@pytest.fixture
def frame() -> dict:
    skills: dict[str, dict[str, str | None]] = {
        f"skill{index}": {"repository": f"owner/project{index}", "commit": "b" * 40} for index in range(12)
    }
    skills.update(
        alias={"repository": "owner/project0", "commit": "c" * 40},
        unresolved={"repository": None, "commit": None},
        held={"repository": "owner/held", "commit": "d" * 40},
    )
    return {
        "schema_version": 1,
        "source_commit": "a" * 40,
        "skills": skills,
        "batches": ["batch1", "batch2"],
        "tables": {"unread__publisher_cells.csv": "e" * 64},
    }


def select(frame: dict, **overrides):
    options: dict[str, Any] = {
        "seed": "0" * 64,
        "count": 12,
        "exclusions": {"held": "Owner scope hold before selection"},
    }
    options.update(overrides)
    return selector.select_tasks(json.dumps(frame).encode(), **options)


def test_one_cell_per_repository_preserves_versions_and_unresolved_provenance(frame):
    report = select(frame)
    assert report["frame_cells"] == 30
    assert report["eligible_cells"] == 26
    assert report["eligible_repository_groups"] == report["planned_tasks"] == 12
    assert report["planned_attempts"] == 36
    assert len({task["repository_group"] for task in report["selected"]}) == 12
    assert report["unresolved_source_skills"] == ["unresolved"]
    assert report["exclusions"] == {"held": "Owner scope hold before selection"}
    for task in report["selected"]:
        assert task["source_commit"] == frame["skills"][task["skill_id"]]["commit"]
        assert task["task_id"] == f"swe-skills-bench/{task['batch']}/{task['skill_id']}"


@pytest.mark.parametrize("seed", ["0" * 64, "1" * 64, "a" * 64])
def test_each_six_task_block_uses_all_condition_orders_and_balances_positions(frame, seed):
    tasks = select(frame, seed=seed)["selected"]
    for block in (tasks[:6], tasks[6:]):
        assert len({tuple(task["condition_order"]) for task in block}) == 6
        for position in range(3):
            assert Counter(task["condition_order"][position] for task in block) == dict.fromkeys(selector.CONDITIONS, 2)


def test_frame_serialization_order_and_publisher_table_identity_do_not_select_tasks(frame):
    original = select(frame)
    frame["skills"] = dict(reversed(list(frame["skills"].items())))
    frame["tables"] = {"another__publisher_cells.csv": "f" * 64}
    changed = select(frame)
    assert changed["selected"] == original["selected"]
    assert changed["frame_sha256"] != original["frame_sha256"]


def test_selection_is_reproducible_but_is_neither_holdout_nor_execution_admission(frame):
    first = select(frame)
    assert select(frame) == first
    assert select(frame, seed="1" * 64)["selected"] != first["selected"]
    assert first["partition"] == "development"
    for key in ("execution_admitted", "preregistration_timing_verified", "task_independence_verified"):
        assert first[key] is False
    assert first["model_invocations"] == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"seed": "A" * 64},
        {"seed": ""},
        {"seed": None},
        {"count": True},
        {"count": 0},
        {"count": 13},
        {"count": 1001},
        {"exclusions": []},
        {"exclusions": {"absent": "Reason"}},
        {"exclusions": {"held": ""}},
        {"exclusions": {"held": " "}},
        {"exclusions": {"held": "Reason\nwith newline"}},
        {"exclusions": {"held": "a" * 513}},
    ],
)
def test_invalid_choices_are_rejected_before_any_schedule(frame, overrides):
    with pytest.raises(ValueError):
        select(frame, **overrides)


def test_missing_revision_never_becomes_an_independent_group(frame):
    frame["skills"]["skill0"]["commit"] = None
    frame["skills"].pop("alias")
    with pytest.raises(ValueError, match="eligible"):
        select(frame)
    report = select(frame, count=11)
    assert report["unresolved_source_skills"] == ["skill0", "unresolved"]


@pytest.fixture
def command(tmp_path: Path, frame):
    path, exclusions, output = (tmp_path / name for name in ("frame.json", "exclusions.json", "nested/selection.json"))
    path.write_text(json.dumps(frame), encoding="utf-8")
    exclusions.write_text(json.dumps({"held": "Owner scope hold before selection"}), encoding="utf-8")
    arguments = [
        "--frame",
        str(path),
        "--exclusions",
        str(exclusions),
        "--seed",
        "0" * 64,
        "--tasks",
        "12",
        "--output",
        str(output),
    ]
    return arguments, path, exclusions, output


def test_cli_runs_without_publisher_tables_and_check_never_rewrites(command, monkeypatch, capsys):
    arguments, _, _, output = command
    assert selector.main(arguments) == 0
    assert json.loads(capsys.readouterr().out)["planned_attempts"] == 36
    before = output.read_bytes()
    monkeypatch.setattr(selector, "write_text", lambda *args: pytest.fail("--check attempted a write"))
    assert selector.main([*arguments, "--check"]) == 0
    assert output.read_bytes() == before


@pytest.mark.parametrize("changed", ["frame", "exclusions", "output"])
def test_check_rejects_changed_inputs_or_receipt_and_preserves_output(command, changed, capsys):
    arguments, frame_path, exclusions, output = command
    assert selector.main(arguments) == 0
    selected = {"frame": frame_path, "exclusions": exclusions, "output": output}[changed]
    selected.write_bytes(selected.read_bytes() + b"\n")
    before = output.read_bytes()
    assert selector.main([*arguments, "--check"]) == 1
    assert output.read_bytes() == before


@pytest.mark.parametrize("input_index", [1, 3])
def test_output_cannot_replace_either_input(command, input_index):
    arguments, _, _, _ = command
    source = Path(arguments[input_index])
    before = source.read_bytes()
    assert selector.main([*arguments[:-1], str(source)]) == 1
    assert source.read_bytes() == before


def test_bound_input_and_duplicate_json_keys_are_rejected(command):
    arguments, path, _, _ = command
    path.write_bytes(b" " * (selector.MAX_BYTES + 1))
    assert selector.main(arguments) == 1
    path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
    assert selector.main(arguments) == 1


def test_published_development_selection_matches_its_frozen_inputs():
    import hashlib

    root = Path(__file__).resolve().parents[1]
    base = root / "benchmarks/agent-effectiveness/development/swe-skills-pilot-v1"
    policy = json.loads((base / "policy.json").read_text(encoding="utf-8"))
    receipt = base / "selection.json"
    assert policy["selection_sha256"] == hashlib.sha256(receipt.read_bytes()).hexdigest()
    assert policy["execution_ready"] is False
    assert policy["model_invocations"] == 0
    assert policy["missing_before_execution"]
    assert (
        selector.main(
            [
                "--frame",
                str(root / "artifacts/research/2026-11-11/swe-skills-bench-archive/frame.json"),
                "--exclusions",
                str(base / "exclusions.json"),
                "--seed",
                policy["seed_provenance"]["seed"],
                "--tasks",
                str(policy["planned_tasks"]),
                "--output",
                str(receipt),
                "--check",
            ]
        )
        == 0
    )

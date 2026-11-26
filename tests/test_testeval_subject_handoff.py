"""Check admission and scope before any native TestEval submission is sealed."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import _testeval_subject as subject
import pytest
from _trial_collection_policy import default_collection_policy
from grade_testeval_submission import sha256

PASS = json.dumps(["def test_value(): pass\n"]).encode()


def manifest(workspace: Path) -> bytes:
    files = {}
    for entry in workspace.iterdir():
        data = entry.read_bytes()
        files[entry.name] = {"bytes": len(data), "sha256": sha256(data)}
    return json.dumps(
        {
            "collection_version": 1,
            "status": "collected",
            "policy": default_collection_policy(),
            "files": files,
            "directories": [],
            "directory_count": 0,
            "excluded": [],
            "file_count": len(files),
            "total_bytes": sum(item["bytes"] for item in files.values()),
            "post_inventory_matches": True,
            "atomic_snapshot": False,
            "precondition": "All subject execution must be stopped before capture.",
        }
    ).encode()


@pytest.fixture
def attempt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[subject.TestEvalSubject, list[Path]]:
    root = tmp_path / "repository"
    owned = root / ".venv"
    owned.mkdir(parents=True)
    monkeypatch.setattr(subject, "ROOT", root)
    before = owned / "packet/baseline"
    before.mkdir(parents=True)
    (before / "task.txt").write_bytes(b"Exercise the observable behavior.\n")
    snapshot = manifest(before)
    (before.parent / "baseline.collection.json").write_bytes(snapshot)
    task = owned / "public-task.json"
    task.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "task_id": 685,
                "publisher": {"commit_sha": "a" * 40, "dataset_sha256": "b" * 64, "evaluator_sha256": "c" * 64},
                "programs": {"reference": "d" * 64, "defect": "e" * 64},
                "baseline_manifest_sha256": sha256(snapshot),
            }
        ),
        encoding="utf-8",
    )
    captures: list[Path] = []

    def capture(source: Path, target: Path, observations: Path, python: Path, policy: dict[str, Any]) -> dict[str, str]:
        captures.append(observations)
        shutil.copytree(source, target)
        observations.mkdir()
        (observations / "stdout.native").write_bytes(manifest(source))
        return {"status": "collected"}

    monkeypatch.setattr(subject, "capture_owned", capture)
    prepared = subject.prepare_subject(task, before.parent, tmp_path / "subject", owned / "attempt", Path(__file__))
    assert prepared.workspace.joinpath("task.txt").read_bytes() == before.joinpath("task.txt").read_bytes()
    assert prepared.task_plan.read_bytes() == task.read_bytes()
    assert len(captures) == 1
    return prepared, captures


def record(
    attempt: subject.TestEvalSubject, *, process_changes: dict[str, Any] | None = None, completed: bool = True
) -> None:
    raw = {
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "termination_reason": None,
        "exit_code": 0,
        "job_active_processes_after_cleanup": 0,
    }
    raw.update(process_changes or {})
    execution = attempt.output / "execution"
    execution.mkdir()
    (execution / "process.json").write_text(json.dumps(raw), encoding="utf-8")
    events = [{"type": "turn.started"}]
    if completed:
        events.append({"type": "turn.completed"})
    (execution / "transcript.jsonl").write_bytes(b"".join(json.dumps(event).encode() + b"\n" for event in events))


@pytest.mark.parametrize(
    ("changes", "complete"),
    [
        ({"termination_reason": "timeout", "exit_code": 124}, False),
        ({"job_active_processes_after_cleanup": 1}, True),
        ({"job_active_processes_after_cleanup": False}, True),
        ({"exit_code": False}, True),
        ({}, False),
    ],
)
def test_incomplete_or_unowned_execution_cannot_capture(
    attempt: tuple[subject.TestEvalSubject, list[Path]], changes: dict[str, Any], complete: bool
) -> None:
    prepared, captures = attempt
    record(prepared, process_changes=changes, completed=complete)
    prepared.workspace.joinpath("tests.json").write_bytes(PASS)
    result = subject.finish_subject(prepared)
    assert result["status"] == "execution_incomplete" and result["archive_sha256"] is None
    assert len(captures) == 1
    assert not (prepared.handoff / "submission.tar").exists()


@pytest.mark.parametrize(
    ("files", "classification"),
    [
        ({}, "missing_submission"),
        ({"tests.json": b"[]"}, "submission_invalid"),
        ({"tests.json": PASS, "task.txt": b"changed"}, "submission_scope_changed"),
        ({"other.txt": b"extra"}, "submission_scope_changed"),
        ({"tests.json": PASS}, "sealed"),
    ],
)
def test_completed_workspace_classifies_submission_before_grading(
    attempt: tuple[subject.TestEvalSubject, list[Path]], files: dict[str, bytes], classification: str
) -> None:
    prepared, captures = attempt
    record(prepared)
    for name, data in files.items():
        (prepared.workspace / name).write_bytes(data)
    result = subject.finish_subject(prepared)
    assert result["status"] == classification and len(captures) == 2
    assert result["task_plan_sha256"] == sha256(prepared.task_plan.read_bytes())
    assert result["process_sha256"] == sha256((prepared.output / "execution/process.json").read_bytes())
    assert result["transcript_sha256"] == sha256((prepared.output / "execution/transcript.jsonl").read_bytes())
    archive = prepared.handoff / "submission.tar"
    if classification == "sealed":
        assert result["archive_sha256"] == sha256(archive.read_bytes()) and result["suite_sha256"] == sha256(PASS)
    else:
        assert result["archive_sha256"] is None and not archive.exists()
    with pytest.raises(FileExistsError):
        subject.finish_subject(prepared)


def test_frozen_task_identity_is_checked_before_subject_capture(
    attempt: tuple[subject.TestEvalSubject, list[Path]],
) -> None:
    prepared, captures = attempt
    record(prepared)
    prepared.task_plan.write_bytes(prepared.task_plan.read_bytes() + b"\n")
    prepared.workspace.joinpath("tests.json").write_bytes(PASS)
    result = subject.finish_subject(prepared)
    assert result["status"] == "capture_incomplete" and result["error_type"] == "ValueError"
    assert len(captures) == 1
    assert not (prepared.handoff / "submission.tar").exists()

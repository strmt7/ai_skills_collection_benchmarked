"""Verify diagnostics use native statuses and preserve ambiguous outcomes."""

import hashlib
import json
from pathlib import Path
from typing import Any

import analyze_native_trial_commands as diagnostics
import pytest

COMMAND = "sensitive fixture command"


def command(kind: str, identifier: str, exit_code: int | None = None, text: str = COMMAND) -> dict[str, Any]:
    return {
        "type": f"item.{kind}",
        "item": {
            "type": "command_execution",
            "id": identifier,
            "command": text,
            "exit_code": exit_code,
            "aggregated_output": "fixture private output claims success",
        },
    }


def attempt(directory: Path, *events: dict[str, Any], status: str = "task_failed", tail: bytes = b"") -> bytes:
    raw = b"".join((json.dumps(event) + "\n").encode() for event in events) + tail
    (directory / "transcript.jsonl").write_bytes(raw)
    (directory / "result.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": status,
                "evidence_sha256": {"transcript.jsonl": hashlib.sha256(raw).hexdigest()},
            }
        ),
        encoding="utf-8",
    )
    return raw


def test_counts_observed_exit_codes_and_emits_only_diagnostics(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raw = attempt(
        tmp_path,
        {"type": "turn.started"},
        command("started", "first"),
        command("completed", "first", 2),
        {"type": "item.completed", "item": {"type": "reasoning"}},
        command("started", "second"),
        command("completed", "second", -1),
        command("completed", "different", 2, text="different command"),
        command("completed", "success", 0),
        command("completed", "failure-after-success", 2),
        {"type": "turn.completed"},
    )

    assert diagnostics.main(["--attempt", str(tmp_path)]) == 0
    output = capsys.readouterr().out
    assert COMMAND not in output
    assert "fixture private output" not in output
    assert str(tmp_path) not in output
    result = json.loads(output)
    assert result["ok"] is True
    assert result["attempt_status"] == "task_failed"
    assert result["transcript_sha256"] == hashlib.sha256(raw).hexdigest()
    assert result["attempt_result_sha256"] == hashlib.sha256((tmp_path / "result.json").read_bytes()).hexdigest()
    assert result["turn_completed"] is True
    assert result["commands"] == {
        "observed": 5,
        "exit_zero": 1,
        "exit_nonzero": 4,
        "without_completion": 0,
        "completed_without_exit_code": 0,
        "repeated_identical_failures": 1,
        "longest_identical_failure_streak": 2,
    }


def test_does_not_count_overlapping_commands_or_attempts_separated_by_tool_actions(tmp_path: Path) -> None:
    attempt(
        tmp_path,
        command("started", "parallel-a"),
        command("started", "parallel-b"),
        command("completed", "parallel-b", 2),
        command("completed", "parallel-a", 2),
        {"type": "item.completed", "item": {"type": "file_change"}},
        command("completed", "after-change", 2),
        command("started", "no-completion"),
        command("completed", "after-unresolved", 2),
        {"type": "turn.completed"},
    )
    result = diagnostics.analyze(tmp_path)["commands"]
    assert result["exit_nonzero"] == 4
    assert result["without_completion"] == 1
    assert result["repeated_identical_failures"] == 0
    assert result["longest_identical_failure_streak"] == 1


def test_partially_captured_attempt_keeps_unknown_exit_states(tmp_path: Path) -> None:
    attempt(
        tmp_path,
        {"type": "turn.started"},
        command("started", "open"),
        command("updated", "open"),
        command("completed", "closed"),
        status="harness_error",
        tail=b'{"type":"item.completed","item":',
    )
    result = diagnostics.analyze(tmp_path)
    assert result["turn_completed"] is False
    assert result["commands"]["observed"] == 2
    assert result["commands"]["without_completion"] == 1
    assert result["commands"]["completed_without_exit_code"] == 1
    assert result["commands"]["exit_nonzero"] == result["commands"]["exit_zero"] == 0


def test_scored_attempt_requires_an_intact_completed_turn(tmp_path: Path) -> None:
    attempt(tmp_path, command("completed", "first", 1))
    with pytest.raises(ValueError, match="missing its completed turn"):
        diagnostics.analyze(tmp_path)

    attempt(tmp_path, {"type": "turn.completed"}, tail=b'{"type":')
    with pytest.raises(ValueError, match="invalid event"):
        diagnostics.analyze(tmp_path)


@pytest.mark.parametrize(
    "events",
    [
        [command("started", "duplicate"), command("started", "duplicate")],
        [command("completed", "duplicate", 1), command("completed", "duplicate", 1)],
        [command("started", "conflict"), command("completed", "conflict", 1, text="other command")],
    ],
)
def test_conflicting_command_lifecycle_is_rejected(tmp_path: Path, events: list[dict[str, Any]]) -> None:
    attempt(tmp_path, *events, {"type": "turn.completed"})
    with pytest.raises(ValueError, match="conflicting lifecycle"):
        diagnostics.analyze(tmp_path)


def test_evidence_digest_and_capture_bound_are_checked_before_parsing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = attempt(tmp_path, {"type": "turn.completed"})
    (tmp_path / "transcript.jsonl").write_bytes(raw + b"sensitive altered evidence")
    assert diagnostics.main(["--attempt", str(tmp_path)]) == 2
    result = capsys.readouterr().out
    assert json.loads(result) == {"ok": False, "error": "native transcript digest differs from the recorded attempt"}
    assert "sensitive" not in result

    monkeypatch.setattr(diagnostics, "TRANSCRIPT_LIMIT", len(raw) - 1)
    with pytest.raises(ValueError, match="exceeds the native diagnostics size limit"):
        diagnostics.analyze(tmp_path)

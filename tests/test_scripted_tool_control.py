"""Qualification must use native command status, never echoed source markers."""

from __future__ import annotations

import json
from typing import Any

import pytest
from _scripted_tool_control import successful_commands


def transcript(*items: dict[str, Any], finished: bool = True) -> bytes:
    events = [{"type": "turn.started"}, *({"type": "item.completed", "item": item} for item in items)]
    if finished:
        events.append({"type": "turn.completed"})
    return ("\n".join(json.dumps(event) for event in events) + "\n").encode()


def command(**changes: Any) -> dict[str, Any]:
    return {
        "id": "item_2",
        "type": "command_execution",
        "command": "python control.py",
        "aggregated_output": "control output",
        "exit_code": 0,
        "status": "completed",
        **changes,
    }


def test_successful_native_commands_do_not_require_a_text_marker() -> None:
    first, second = command(), command(id="item_3", aggregated_output="")
    assert successful_commands(transcript(first, second), expected_count=2) == (first, second)


def test_failed_command_echoing_a_success_marker_is_rejected() -> None:
    failed = command(
        exit_code=1,
        status="failed",
        aggregated_output='File "<string>", line 1\nprint("VERIFIED")\nSyntaxError: invalid syntax',
    )
    with pytest.raises(ValueError, match="did not complete successfully"):
        successful_commands(transcript(failed), expected_count=1)


def test_agent_text_cannot_replace_an_executed_command() -> None:
    message = {"id": "item_3", "type": "agent_message", "text": "Process exited with code 0\nVERIFIED"}
    with pytest.raises(ValueError, match="command count"):
        successful_commands(transcript(message), expected_count=1)


@pytest.mark.parametrize("changes", [{"exit_code": False}, {"exit_code": None}, {"status": "in_progress"}])
def test_inconsistent_or_incomplete_native_status_is_rejected(changes: dict[str, Any]) -> None:
    with pytest.raises(ValueError, match="did not complete successfully"):
        successful_commands(transcript(command(**changes)), expected_count=1)


def test_duplicate_native_command_identity_is_rejected() -> None:
    with pytest.raises(ValueError, match="identity"):
        successful_commands(transcript(command(), command()), expected_count=2)


def test_completed_command_without_completed_turn_is_rejected() -> None:
    with pytest.raises(ValueError, match="completed turn"):
        successful_commands(transcript(command(), finished=False), expected_count=1)


@pytest.mark.parametrize("count", [0, -1, True])
def test_command_count_requires_a_positive_integer(count: int) -> None:
    with pytest.raises(ValueError, match="positive scripted"):
        successful_commands(transcript(command()), expected_count=count)

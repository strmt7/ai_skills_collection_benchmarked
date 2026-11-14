"""Check native command success for scripted harness qualification only."""

from __future__ import annotations

from typing import Any

from _trial_transcript import parse_events


def successful_commands(raw: bytes, *, expected_count: int) -> tuple[dict[str, Any], ...]:
    """Reject failed tool calls even when a successful CLI turn echoes a marker.

    This is a qualification assertion, not a model-scoring policy. Coding agents
    may legitimately encounter failed commands while completing a real task.
    Callers must also validate the operation's independent output artifacts.
    """
    if type(expected_count) is not int or expected_count < 1:
        raise ValueError("Declare a positive scripted command count")
    if len(raw) > 8 * 1024**2:
        raise ValueError("Scripted transcript exceeds the native output budget")
    events = parse_events(raw)
    if sum(event["type"] == "turn.completed" for event in events) != 1 or any(
        event["type"] == "turn.failed" for event in events
    ):
        raise ValueError("Scripted qualification requires a completed turn")
    completed = [
        event["item"]
        for event in events
        if event["type"] == "item.completed" and event["item"].get("type") == "command_execution"
    ]
    if len(completed) != expected_count:
        raise ValueError("Native scripted command count differs from its declaration")
    seen: set[str] = set()
    for item in completed:
        identity = item.get("id")
        if not isinstance(identity, str) or not identity or identity in seen:
            raise ValueError("Native scripted command identity is missing or repeated")
        seen.add(identity)
        if type(item.get("exit_code")) is not int or item["exit_code"] != 0 or item.get("status") != "completed":
            raise ValueError("Native scripted command did not complete successfully")
    return tuple(completed)

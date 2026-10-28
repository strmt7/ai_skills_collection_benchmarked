"""Strict, shared parsing for recorded trial events and grader responses."""

from __future__ import annotations

import json
from typing import Any


def strict_json(text: str) -> Any:
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError("non-finite JSON number")

    try:
        return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)
    except RecursionError as exc:
        raise ValueError("JSON nesting exceeds the parser limit") from exc


def parse_events(raw: bytes, *, allow_truncated_final: bool = False) -> list[dict[str, Any]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("transcript is not UTF-8") from exc
    lines = text.splitlines(keepends=True)
    events: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        try:
            event = strict_json(line)
        except json.JSONDecodeError as exc:
            if allow_truncated_final and index == len(lines) - 1 and not line.endswith(("\n", "\r")):
                break
            raise ValueError(f"transcript contains an invalid event on line {index + 1}") from exc
        except ValueError as exc:
            raise ValueError(f"transcript contains an invalid event on line {index + 1}") from exc
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise ValueError(f"transcript contains a malformed event on line {index + 1}")
        if event["type"] == "item.completed" and not isinstance(event.get("item"), dict):
            raise ValueError(f"transcript contains a malformed completed item on line {index + 1}")
        usage = event.get("usage") if event["type"] == "turn.completed" else None
        if usage is not None and (
            not isinstance(usage, dict)
            or any(type(value) is not int or value < 0 for value in usage.values())
            or not {"input_tokens", "output_tokens"}.issubset(usage)
            or usage.get("cached_input_tokens", 0) > usage["input_tokens"]
        ):
            raise ValueError(f"transcript contains invalid usage on line {index + 1}")
        events.append(event)
    if sum(event["type"] == "turn.completed" for event in events) > 1:
        raise ValueError("transcript contains multiple completed turns")
    return events

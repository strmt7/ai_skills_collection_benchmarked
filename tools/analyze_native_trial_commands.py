#!/usr/bin/env python3
"""Summarize recorded command outcomes in one native SWE-Skills attempt."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _trial_transcript import parse_events, strict_json

TRANSCRIPT_LIMIT = 8 * 1024**2 + 1  # Native capture budget plus its one-byte overflow witness.
RESULT_LIMIT = 1024**2
ITEM_EVENTS = {"item.started", "item.updated", "item.completed"}
NON_TOOL_ITEMS = {"agent_message", "reasoning", "error", "todo_list"}


@dataclass(slots=True)
class CommandItem:
    command: str
    first_event: int
    completed_at: int = -1
    exit_code: int | None = None


def read_limited(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f"{path.name} exceeds the native diagnostics size limit")
    return raw


def command_timeline(events: list[dict[str, Any]]) -> tuple[list[CommandItem], list[CommandItem | None]]:
    commands: dict[str, CommandItem] = {}
    timeline: list[CommandItem | None] = []
    for position, event in enumerate(events):
        kind = event["type"]
        if kind.startswith("turn."):
            timeline.append(None)
        if kind not in ITEM_EVENTS:
            continue
        item = event.get("item")
        if not isinstance(item, dict) or not isinstance(item.get("type"), str):
            raise ValueError("invalid item in native transcript")
        if item["type"] != "command_execution":
            if item["type"] not in NON_TOOL_ITEMS:
                timeline.append(None)
            continue
        identifier, text = item.get("id"), item.get("command")
        if not isinstance(identifier, str) or not identifier or not isinstance(text, str) or not text:
            raise ValueError("native command item lacks an id or command")
        observed = commands.get(identifier)
        if observed is None:
            observed = commands[identifier] = CommandItem(text, position)
            timeline.append(observed)
        elif kind == "item.started" or observed.completed_at >= 0 or observed.command != text:
            raise ValueError("conflicting lifecycle for native command item")
        if kind == "item.completed":
            exit_code = item.get("exit_code")
            if exit_code is not None and type(exit_code) is not int:
                raise ValueError("invalid native command exit code")
            observed.completed_at = position
            observed.exit_code = exit_code
    return list(commands.values()), timeline


def command_counts(events: list[dict[str, Any]]) -> dict[str, int]:
    commands, timeline = command_timeline(events)
    previous = None
    streak = longest = repeated = 0
    for item in timeline:
        if item is None or item.exit_code in (None, 0):
            previous = None
            streak = 0
            continue
        if previous and previous.command == item.command and previous.completed_at < item.first_event:
            streak += 1
            repeated += 1
        else:
            streak = 1
        longest = max(longest, streak)
        previous = item
    return {
        "observed": len(commands),
        "exit_zero": sum(item.exit_code == 0 for item in commands),
        "exit_nonzero": sum(item.exit_code not in (None, 0) for item in commands),
        "without_completion": sum(item.completed_at < 0 for item in commands),
        "completed_without_exit_code": sum(item.completed_at >= 0 and item.exit_code is None for item in commands),
        "repeated_identical_failures": repeated,
        "longest_identical_failure_streak": longest,
    }


def analyze(attempt: Path) -> dict[str, Any]:
    result_bytes = read_limited(attempt / "result.json", RESULT_LIMIT)
    result = strict_json(result_bytes.decode("utf-8"))
    if (
        not isinstance(result, dict)
        or type(result.get("schema_version")) is not int
        or result["schema_version"] != 1
        or result.get("status") not in ("task_passed", "task_failed", "harness_error")
        or not isinstance(result.get("evidence_sha256"), dict)
    ):
        raise ValueError("expected a native SWE-Skills attempt result")
    transcript = read_limited(attempt / "transcript.jsonl", TRANSCRIPT_LIMIT)
    digest = hashlib.sha256(transcript).hexdigest()
    if result["evidence_sha256"].get("transcript.jsonl") != digest:
        raise ValueError("native transcript digest differs from the recorded attempt")
    status = result["status"]
    events = parse_events(transcript, allow_truncated_final=status == "harness_error")
    turn_completed = any(event["type"] == "turn.completed" for event in events)
    if status != "harness_error" and not turn_completed:
        raise ValueError("scored attempt transcript is missing its completed turn")
    return {
        "schema_version": 1,
        "attempt_status": status,
        "attempt_result_sha256": hashlib.sha256(result_bytes).hexdigest(),
        "transcript_sha256": digest,
        "turn_completed": turn_completed,
        "commands": command_counts(events),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=Path, required=True, help="Directory containing the native attempt evidence")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = analyze(args.attempt)
    except OSError:
        print(json.dumps({"ok": False, "error": "could not read the native attempt evidence"}))
        return 2
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps({"ok": True, **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Admit source-declared native build outcomes against the original publisher verdict.

This validates execution evidence supplied by a qualified controller. It does
not execute a build, authenticate an evidence producer, or establish model gains.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path, PurePosixPath
from typing import Any

from _trial_transcript import strict_json

LIMIT = 16 * 1024**2


def verify_result(
    *, inventory: bytes, execution: bytes, publisher: bytes, stdout: bytes, stderr: bytes
) -> dict[str, Any]:
    """Preserve native failure/timeout scores; quarantine inconsistent evidence."""
    errors: list[str] = []

    def document(raw: bytes, label: str) -> dict[str, Any]:
        if len(raw) > LIMIT:
            errors.append(label + ": document exceeds its byte budget")
            return {}
        try:
            value = strict_json(raw.decode("utf-8"))
            if not isinstance(value, dict):
                raise ValueError("expected an object")
            return value
        except (UnicodeError, ValueError) as error:
            errors.append(label + ": " + str(error))
            return {}

    declared = document(inventory, "inventory")
    native = document(execution, "execution")
    verdict = document(publisher, "publisher")

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(
        set(declared)
        == {"schema_version", "task_id", "build_command", "working_dir", "expected_exit_code", "timeout_seconds"},
        "inventory: incomplete or unexpected fields",
    )
    require(type(declared.get("schema_version")) is int and declared["schema_version"] == 1, "inventory: schema")
    identifier = declared.get("task_id")
    require(
        isinstance(identifier, str) and re.fullmatch(r"[A-Za-z0-9._:/-]{1,256}", identifier) is not None,
        "inventory: task id",
    )
    command = declared.get("build_command")
    require(isinstance(command, str) and 0 < len(command) <= 65536 and "\0" not in command, "inventory: build command")
    working = declared.get("working_dir")
    valid_directory = (
        isinstance(working, str)
        and "\0" not in working
        and PurePosixPath(working).is_absolute()
        and ".." not in PurePosixPath(working).parts
        and PurePosixPath(working).is_relative_to("/workspace")
        and str(PurePosixPath(working)) == working
    )
    require(valid_directory, "inventory: working directory")
    expected = declared.get("expected_exit_code")
    require(type(expected) is int and -(2**31) <= expected < 2**31, "inventory: expected exit code")
    timeout = declared.get("timeout_seconds")
    require(type(timeout) is int and 1 <= timeout <= 3600, "inventory: timeout")
    require(
        set(native)
        == {
            "schema_version",
            "command",
            "timeout_seconds",
            "exit_code",
            "timed_out",
            "duration_seconds",
            "stdout_sha256",
            "stderr_sha256",
            "execution_complete",
            "remaining_owned_processes",
        },
        "execution: incomplete or unexpected fields",
    )
    require(type(native.get("schema_version")) is int and native["schema_version"] == 1, "execution: schema")
    require(native.get("command") == f"cd {working} && {command}", "execution: command differs from declaration")
    require(
        type(native.get("timeout_seconds")) is int and native["timeout_seconds"] == timeout,
        "execution: timeout differs",
    )
    code = native.get("exit_code")
    valid_code = type(code) is int and -(2**31) <= code < 2**31
    require(valid_code, "execution: exit code")
    timed_out = native.get("timed_out")
    require(type(timed_out) is bool, "execution: timeout flag")
    duration = native.get("duration_seconds")
    valid_duration = False
    if isinstance(duration, (int, float)) and not isinstance(duration, bool):
        valid_duration = 0 <= duration <= 86400 and math.isfinite(duration)
        if timed_out is True and valid_duration and type(timeout) is int:
            require(duration >= timeout, "execution: timeout precedes the declared deadline")
    require(valid_duration, "execution: duration must be finite and between 0 and 86400 seconds")
    require(native.get("execution_complete") is True, "execution: incomplete transport")
    require(
        type(native.get("remaining_owned_processes")) is int and native["remaining_owned_processes"] == 0,
        "execution: remaining owned processes",
    )
    require(len(stdout) + len(stderr) <= LIMIT, "execution: output exceeds its byte budget")
    require(native.get("stdout_sha256") == hashlib.sha256(stdout).hexdigest(), "execution: stdout digest differs")
    require(native.get("stderr_sha256") == hashlib.sha256(stderr).hexdigest(), "execution: stderr digest differs")
    require(set(verdict) == {"level", "method", "status", "score", "message", "details"}, "publisher: fields")
    require(verdict.get("level") == "L1" and verdict.get("method") == "build_check", "publisher: evaluator identity")
    require(isinstance(verdict.get("message"), str), "publisher: message")
    details = verdict.get("details")
    if not isinstance(details, dict):
        errors.append("publisher: details must be an object")
        details = {}
    require(details.get("command") == command, "publisher: build command differs")
    if valid_code and type(timed_out) is bool and type(expected) is int:
        passed = not timed_out and code == expected
        require(
            verdict.get("status") == ("passed" if passed else "failed"), "publisher: status contradicts native outcome"
        )
        score = verdict.get("score")
        require(type(score) in {int, float} and score == float(passed), "publisher: score contradicts native outcome")
        if timed_out:
            require(set(details) == {"command", "timeout", "output"}, "publisher: timeout detail fields")
            require(
                details.get("timeout") == timeout and type(details.get("timeout")) is int, "publisher: timeout differs"
            )
            require(
                details.get("output") == stdout.decode("utf-8", errors="replace")[:2000],
                "publisher: timeout output differs",
            )
        else:
            require(
                type(details.get("exit_code")) is int and details["exit_code"] == code, "publisher: exit code differs"
            )
            if passed:
                require(set(details) == {"command", "exit_code", "duration"}, "publisher: success detail fields")
                require(
                    type(details.get("duration")) in {int, float} and details["duration"] == duration,
                    "publisher: duration differs",
                )
            else:
                require(
                    set(details) == {"command", "exit_code", "expected_exit_code", "error_summary", "full_output"},
                    "publisher: failure detail fields",
                )
                require(
                    type(details.get("expected_exit_code")) is int and details["expected_exit_code"] == expected,
                    "publisher: expected exit code differs",
                )
                require(isinstance(details.get("error_summary"), str), "publisher: error summary")
                require(
                    details.get("full_output") == (stderr or stdout).decode("utf-8", errors="replace")[:5000],
                    "publisher: failure output differs",
                )
    if errors:
        return {"admitted": False, "status": "unscored", "errors": errors}
    return {
        "admitted": True,
        "status": "task_passed" if verdict["status"] == "passed" else "task_failed",
        "score": verdict["score"],
        "task_id": identifier,
        "exit_code": code,
        "timed_out": timed_out,
        "expected_exit_code": expected,
        "duration_seconds": duration,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("inventory", "execution", "publisher", "stdout", "stderr"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--json", action="store_true", help="Emit the machine-readable admission envelope")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        paths = {name: getattr(args, name) for name in ("inventory", "execution", "publisher", "stdout", "stderr")}
        if any(path.stat().st_size > LIMIT for path in paths.values()):
            raise ValueError("An input exceeds the admission byte budget")
        result = verify_result(**{name: path.read_bytes() for name, path in paths.items()})
    except (OSError, ValueError) as error:
        result = {"admitted": False, "status": "unscored", "errors": [str(error)]}
    print(
        json.dumps(result, indent=2)
        if args.json
        else ("ADMITTED: " + result["status"] if result["admitted"] else "UNSCORED: " + "; ".join(result["errors"]))
    )
    return 0 if result["admitted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

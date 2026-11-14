"""Run bounded, model-free command controls through the native Codex protocol."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from _lib_b.io_utils import write_json
from _trial_context import TrialContext, options
from _trial_transcript import strict_json
from _windows_appcontainer import checked_path
from _windows_trial_process import run_owned


def response(path: Path, identifier: int, worker: threading.Thread, deadline: float) -> dict[str, Any]:
    while time.monotonic() < deadline:
        stopped = not worker.is_alive()
        raw = path.read_bytes() if path.exists() else b""
        if len(raw) > 8 * 1024 * 1024:
            raise ValueError("Native protocol output exceeds the control limit")
        for line in raw.splitlines(keepends=True):
            if line.endswith(b"\n"):
                row = strict_json(line.decode("utf-8"))
                if isinstance(row, dict) and row.get("id") == identifier:
                    return row
        if stopped:
            raise RuntimeError("Native control exited before its response")
        time.sleep(0.02)
    raise TimeoutError("Native protocol response deadline exceeded")


def command_control(
    context: TrialContext,
    command: list[str],
    output: Path,
    *,
    environment_overrides: dict[str, str] | None = None,
    timeout_seconds: int = 5,
    output_bytes: int = 16384,
) -> dict[str, Any]:
    """Initialize one private server, execute one bounded command, then close it.

    Only initialize and command/exec are sent. No thread, turn, model inference,
    login, MCP tool, or unrestricted thread/shellCommand request is permitted.
    """
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 300:
        raise ValueError("Native command timeout must be an integer from 1 to 300 seconds")
    if context.signin is not None:
        raise ValueError("Model-free RPC controls require a separate credential-free profile")
    if type(output_bytes) is not int or not 1 <= output_bytes <= 1024**2:
        raise ValueError("Native command output must be an integer from 1 byte to one MiB")
    output = checked_path(output)
    if any(
        output.is_relative_to(root) or root.is_relative_to(output)
        for root in (context.workspace, context.home, *context.readable_roots)
    ):
        raise ValueError("Control observations must be separate from runtime, controller and subject paths")
    output.mkdir(parents=True, exist_ok=False)
    requests = [
        {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "trial-qualification", "version": "1"}}},
        {"method": "initialized", "params": {}},
        {
            "id": 2,
            "method": "command/exec",
            "params": {
                "command": command,
                "cwd": str(context.workspace),
                "timeoutMs": timeout_seconds * 1000,
                "outputBytesCap": output_bytes,
                "env": environment_overrides or {},
            },
        },
    ]
    write_json(output / "requests.json", requests)
    invocation = [str(context.cli), *options(context, "gpt-6.1-sol", "high"), "app-server", "--stdio"]
    read_fd, write_fd = os.pipe()
    observed: dict[str, Any] = {}

    def execute() -> None:
        try:
            with (
                os.fdopen(read_fd, "rb", buffering=0) as stdin,
                (output / "stdout.native").open("xb", buffering=0) as stdout,
                (output / "stderr.native").open("xb", buffering=0) as stderr,
            ):
                observed["process"] = run_owned(
                    invocation,
                    cwd=context.workspace,
                    stdin=stdin,
                    stdout=stdout,
                    stderr=stderr,
                    timeout=timeout_seconds + 35,
                    output_limit=8 * 1024 * 1024,
                    environment=context.controller_environment,
                    memory_limit=2 * 1024**3,
                    process_limit=32,
                )
        except (OSError, RuntimeError, ValueError) as exc:
            observed["process_error"] = {"type": type(exc).__name__, "message": str(exc)}

    worker = threading.Thread(target=execute)
    try:
        worker.start()
    except BaseException:
        os.close(read_fd)
        os.close(write_fd)
        raise
    deadline = time.monotonic() + timeout_seconds + 25
    try:
        with os.fdopen(write_fd, "wb", buffering=0) as writer:
            writer.write((json.dumps(requests[0]) + "\n").encode("utf-8"))
            observed["initialize"] = response(output / "stdout.native", 1, worker, deadline)
            if "error" in observed["initialize"]:
                raise ValueError("Native control rejected initialization")
            for request in requests[1:]:
                writer.write((json.dumps(request) + "\n").encode("utf-8"))
            observed["command"] = response(output / "stdout.native", 2, worker, deadline)
    except (OSError, RuntimeError, ValueError, TimeoutError) as exc:
        observed["client_error"] = {"type": type(exc).__name__, "message": str(exc)}
    except BaseException as exc:
        observed["client_aborted"] = {"type": type(exc).__name__}
        raise
    finally:
        worker.join(timeout=timeout_seconds + 40)
        observed["worker_stopped"] = not worker.is_alive()
        write_json(output / "observations.json", observed)
        if worker.is_alive():
            raise RuntimeError("Native control did not stop within its ownership deadline")
    return observed

"""Bounded process supervision for trusted repository workers."""

from __future__ import annotations

import os
import re
import selectors
import subprocess
import sys
import tempfile
import time
from contextlib import ExitStack, suppress
from pathlib import Path
from typing import IO, Any, BinaryIO, cast

MAX_STDERR = 4096

if sys.platform != "win32":
    from os import killpg
    from signal import SIGKILL

    def _kill_group(pid: int) -> None:
        """Terminate the isolated worker process group."""
        killpg(pid, SIGKILL)

else:

    def _kill_group(pid: int) -> None:
        """Reject the POSIX cleanup path on Windows."""
        raise RuntimeError("POSIX process groups are unavailable on Windows")


_EXIT_MARKER = re.compile(rb"\n__GH_WORKER_EXIT__:(-?[0-9]{1,10})\n\Z")


def _collect_posix_output(
    stdout: IO[bytes], stderr: IO[bytes], deadline: float, output_limit: int
) -> tuple[dict[str, bytearray], str | None, int | None]:
    """Collect pipes until worker status and stdout EOF, with one deadline and limit."""
    outputs = {"stdout": bytearray(), "stderr": bytearray()}
    worker_exit = None
    with selectors.DefaultSelector() as selector:
        selector.register(stdout.fileno(), selectors.EVENT_READ, "stdout")
        selector.register(stderr.fileno(), selectors.EVENT_READ, "stderr")
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return outputs, "timeout", None
            for key, _ in selector.select(remaining):
                available = output_limit + 1 - sum(len(value) for value in outputs.values())
                chunk = os.read(key.fd, min(65536, available))
                if not chunk:
                    selector.unregister(key.fd)
                    continue
                outputs[key.data].extend(chunk)
                if sum(len(value) for value in outputs.values()) > output_limit or len(outputs["stderr"]) > MAX_STDERR:
                    return outputs, "output_limit", None
                if key.data == "stderr":
                    match = _EXIT_MARKER.search(outputs["stderr"])
                    if match:
                        worker_exit = int(match.group(1))
                        del outputs["stderr"][match.start() :]
                        selector.unregister(key.fd)
    return outputs, None if worker_exit is not None else "missing_status", worker_exit


def _cleanup_posix(process: subprocess.Popen[bytes]) -> None:
    """Kill the owned group, reap its leader, and close both output pipes."""
    try:
        try:
            with suppress(ProcessLookupError):
                _kill_group(process.pid)
        finally:
            process.wait(timeout=5)
    finally:
        try:
            if process.stdout is not None:
                process.stdout.close()
        finally:
            if process.stderr is not None:
                process.stderr.close()


def run_posix(command: list[str], timeout: float, output_limit: int, stdin: BinaryIO | None = None) -> dict[str, Any]:
    """Keep the leader unreaped until its owned process group is terminated."""
    if not command or not os.path.isabs(command[0]) or timeout <= 0 or output_limit <= 0:
        raise ValueError("invalid worker bounds")
    process = subprocess.Popen(
        command,
        stdin=stdin if stdin is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    deadline = time.monotonic() + timeout
    try:
        if process.stdout is None or process.stderr is None:
            raise RuntimeError("worker output pipes are unavailable")
        outputs, reason, worker_exit = _collect_posix_output(process.stdout, process.stderr, deadline, output_limit)
    finally:
        _cleanup_posix(process)
    return {
        "exit_code": worker_exit,
        "termination_reason": reason,
        "stdout": bytes(outputs["stdout"]),
        "stderr": bytes(outputs["stderr"]),
    }


def run_windows(command, timeout, output_limit, stdin=None):
    """Use a job to stop the worker and its job-associated descendants."""
    root = str(Path(__file__).resolve().parent)
    sys.path.insert(0, root)
    try:
        from _windows_trial_process import run_owned
    finally:
        sys.path.pop(0)
    with ExitStack() as stack:
        source = stdin if stdin is not None else stack.enter_context(tempfile.TemporaryFile())
        stdout = stack.enter_context(tempfile.TemporaryFile())
        stderr = stack.enter_context(tempfile.TemporaryFile())
        report = run_owned(
            command,
            cwd=Path(root),
            stdin=cast(BinaryIO, source),
            stdout=cast(BinaryIO, stdout),
            stderr=cast(BinaryIO, stderr),
            timeout=timeout,
            output_limit=output_limit,
        )
        stdout.seek(0)
        stderr.seek(0)
        return {
            "exit_code": report["exit_code"],
            "termination_reason": report["termination_reason"],
            "stdout": stdout.read(output_limit + 1),
            "stderr": stderr.read(output_limit + 1),
        }

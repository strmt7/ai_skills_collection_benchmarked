"""Run Windows job-associated processes with bounded output and cleanup."""

from __future__ import annotations

import ctypes as c
import math
import subprocess
import sys
import time
from contextlib import ExitStack
from ctypes import wintypes as w
from pathlib import Path
from typing import Any, BinaryIO

from _windows_appcontainer import (
    Native,
    Pipe,
    Process,
    StartupEx,
    collect,
    last_error,
    require,
    stop_process,
    win_error,
)
from _windows_owned_python import Accounting, ExtendedLimits


def run_owned(
    command: list[str],
    *,
    cwd: Path,
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: BinaryIO,
    timeout: float,
    output_limit: int,
) -> dict[str, Any]:
    """Start suspended and stop all processes assigned to the job before return.

    Windows does not associate every service-created process with the caller's
    job. This controls job members and output, not filesystem, network or service
    access. The caller must independently qualify the sandbox and source bindings.
    """
    if sys.platform != "win32":
        raise ValueError("Owned trial execution requires Windows")
    if (
        not command
        or any(not isinstance(value, str) or "\0" in value for value in command)
        or not Path(command[0]).is_absolute()
        or not Path(command[0]).is_file()
        or not cwd.is_absolute()
        or not cwd.is_dir()
    ):
        raise ValueError("A valid absolute executable and working directory are required")
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout <= 0
        or type(output_limit) is not int
        or not 0 < output_limit <= 1024 * 1024 * 1024
    ):
        raise ValueError("A finite positive time and bounded output limit are required")

    import msvcrt

    native = Native()
    size, process = c.c_size_t(), Process()
    initialize = native.function(
        "kernel", "InitializeProcThreadAttributeList", [c.c_void_p, w.DWORD, w.DWORD, c.POINTER(c.c_size_t)], w.BOOL
    )
    initialize(None, 1, 0, c.byref(size))
    if not size.value:
        raise win_error(last_error())
    attributes = c.create_string_buffer(size.value)
    require(initialize(attributes, 1, 0, c.byref(size)))
    with ExitStack() as resources:
        resources.callback(native.function("kernel", "DeleteProcThreadAttributeList", [c.c_void_p], None), attributes)
        job = native.function("kernel", "CreateJobObjectW", [c.c_void_p, w.LPCWSTR], w.HANDLE)(None, None)
        require(job)
        resources.callback(native.close, job)
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # Kill on job close; do not enable breakaway.
        require(
            native.function("kernel", "SetInformationJobObject", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL)(
                job, 9, c.byref(limits), c.sizeof(limits)
            )
        )
        pipes = []
        for _ in range(2):
            pipe = Pipe(native)
            resources.callback(pipe.close)
            pipes.append(pipe)

        current = native.function("kernel", "GetCurrentProcess", [], w.HANDLE)()
        duplicate = native.function(
            "kernel",
            "DuplicateHandle",
            [w.HANDLE, w.HANDLE, w.HANDLE, c.POINTER(w.HANDLE), w.DWORD, w.BOOL, w.DWORD],
            w.BOOL,
        )
        input_handle = w.HANDLE()
        require(duplicate(current, msvcrt.get_osfhandle(stdin.fileno()), current, c.byref(input_handle), 0, True, 2))
        resources.callback(native.close, input_handle)
        handles = (w.HANDLE * 3)(input_handle.value, pipes[0].write.value, pipes[1].write.value)
        update = native.function(
            "kernel",
            "UpdateProcThreadAttribute",
            [c.c_void_p, w.DWORD, c.c_size_t, c.c_void_p, c.c_size_t, c.c_void_p, c.c_void_p],
            w.BOOL,
        )
        require(update(attributes, 0, 0x20002, handles, c.sizeof(handles), None, None))
        startup = StartupEx()
        startup.startup.cb, startup.startup.flags = c.sizeof(startup), 0x100
        startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = handles
        startup.attributes = c.addressof(attributes)
        create = native.function(
            "kernel",
            "CreateProcessW",
            [
                w.LPCWSTR,
                w.LPWSTR,
                c.c_void_p,
                c.c_void_p,
                w.BOOL,
                w.DWORD,
                c.c_void_p,
                w.LPCWSTR,
                c.POINTER(StartupEx),
                c.POINTER(Process),
            ],
            w.BOOL,
        )
        command_line = c.create_unicode_buffer(subprocess.list2cmdline(command))
        require(
            create(
                command[0],
                command_line,
                None,
                None,
                True,
                0x80000 | 0x4 | 0x8000000,
                None,
                str(cwd),
                c.byref(startup),
                c.byref(process),
            )
        )
        resources.callback(native.close, process.process)
        resources.callback(native.close, process.thread)
        resources.callback(stop_process, native, process.process)
        for pipe in pipes:
            native.close(pipe.write)
            pipe.write = None
        require(
            native.function("kernel", "AssignProcessToJobObject", [w.HANDLE, w.HANDLE], w.BOOL)(job, process.process)
        )
        in_job = w.BOOL()
        require(
            native.function("kernel", "IsProcessInJob", [w.HANDLE, w.HANDLE, c.POINTER(w.BOOL)], w.BOOL)(
                process.process, job, c.byref(in_job)
            )
        )
        if not in_job.value:
            raise RuntimeError("Trial process was not assigned to its job")
        resumed = native.function("kernel", "ResumeThread", [w.HANDLE], w.DWORD)(process.thread)
        if resumed == 0xFFFFFFFF:
            raise win_error(last_error())
        if resumed != 1:
            raise RuntimeError("Trial thread had an unexpected suspension count")
        reason, total = collect(native, process.process, pipes, [stdout, stderr], timeout, output_limit)
        exit_status = w.DWORD()
        get_exit = native.function("kernel", "GetExitCodeProcess", [w.HANDLE, c.POINTER(w.DWORD)], w.BOOL)
        require(native.function("kernel", "TerminateJobObject", [w.HANDLE, w.UINT], w.BOOL)(job, 124 if reason else 0))
        wait = native.function("kernel", "WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD)
        if wait(process.process, 5000) != 0:
            raise RuntimeError("Trial process did not terminate")
        require(get_exit(process.process, c.byref(exit_status)))
        accounting = Accounting()
        query = native.function(
            "kernel", "QueryInformationJobObject", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p], w.BOOL
        )
        deadline = time.monotonic() + 5
        while True:
            require(query(job, 1, c.byref(accounting), c.sizeof(accounting), None))
            if not accounting.active:
                break
            if time.monotonic() > deadline:
                raise RuntimeError("Trial job processes did not terminate")
            time.sleep(0.01)
        return {
            "windows_job": True,
            "assigned_before_resume": True,
            "kill_on_close": True,
            "job_active_processes_after_cleanup": accounting.active,
            "service_created_processes_tracked": False,
            "termination_reason": reason,
            "exit_code": exit_status.value,
            "output_bytes": total,
        }

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
from typing import Any, BinaryIO, TypedDict

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
from _windows_owned_python import Accounting, Counters, ExtendedLimits
from _windows_storage_budget import SpaceBudget


class ProcessBudgetOptions(TypedDict, total=False):
    write_io_limit: int
    space_budget: SpaceBudget


class IoAccounting(c.Structure):
    """JOBOBJECT_BASIC_AND_IO_ACCOUNTING_INFORMATION, including exited members."""

    _fields_ = [("basic", Accounting), ("io", Counters)]


def verify_write_io_budget(record: dict[str, Any], expected_limit: int) -> None:
    """Validate a budget record against its admitted plan without native API calls."""
    fields = {
        "write_io_limit_bytes",
        "job_write_io_bytes",
        "write_io_overshoot_bytes",
        "write_io_observation_error",
        "write_io_enforcement",
        "hard_storage_quota",
    }
    if (
        not isinstance(record, dict)
        or not fields <= record.keys()
        or type(record["write_io_limit_bytes"]) is not int
        or record["write_io_limit_bytes"] != expected_limit
        or record["write_io_enforcement"] != "polled_job_transfer_accounting"
        or record["hard_storage_quota"] is not False
    ):
        raise ValueError("Recorded write-I/O budget differs from the admitted profile")
    value, error = record["job_write_io_bytes"], record["write_io_observation_error"]
    if value is not None and (type(value) is not int or not 0 <= value < 2**64):
        raise ValueError("Recorded job write transfers must be an unsigned 64-bit count")
    if error is None:
        if value is None:
            raise ValueError("Successful write accounting requires an observed count")
    else:
        if (
            not isinstance(error, dict)
            or error.get("api") != "QueryInformationJobObject"
            or type(error.get("information_class")) is not int
            or error["information_class"] != 8
            or record.get("termination_reason") is None
        ):
            raise ValueError("Write accounting errors require a native diagnostic and interrupted execution")
        if set(error) == {"api", "information_class", "winerror"}:
            valid = type(error["winerror"]) is int and 0 <= error["winerror"] < 2**32
        elif set(error) == {"api", "information_class", "expected_bytes", "returned_bytes"}:
            valid = (
                type(error["expected_bytes"]) is int
                and error["expected_bytes"] == 96
                and type(error["returned_bytes"]) is int
                and 0 <= error["returned_bytes"] < 2**32
                and error["returned_bytes"] != 96
            )
        else:
            valid = False
        if not valid:
            raise ValueError("Write accounting diagnostic is invalid")
    expected_overshoot = max(0, value - expected_limit) if value is not None else None
    overshoot = record["write_io_overshoot_bytes"]
    if type(overshoot) is not type(expected_overshoot) or overshoot != expected_overshoot:
        raise ValueError("Write accounting overshoot contradicts its observed count")
    reason = record.get("termination_reason")
    if reason == "resource_observation_error" and error is None:
        raise ValueError("Resource observation failure is missing its diagnostic")
    if reason == "write_io_limit" and (value is None or value <= expected_limit):
        raise ValueError("Write-budget termination is missing its exceeded count")
    if reason is None and expected_overshoot:
        raise ValueError("An exceeded write budget cannot become successful execution")


def run_owned(
    command: list[str],
    *,
    cwd: Path,
    stdin: BinaryIO,
    stdout: BinaryIO,
    stderr: BinaryIO,
    timeout: float,
    output_limit: int,
    environment: dict[str, str] | None = None,
    memory_limit: int = 1024 * 1024 * 1024,
    process_limit: int = 32,
    write_io_limit: int | None = None,
    space_budget: SpaceBudget | None = None,
) -> dict[str, Any]:
    """Start suspended and stop all processes assigned to the job before return.

    Windows does not associate every service-created process with the caller's
    job. This controls job members and output, not filesystem, network or service
    access. The caller must independently qualify the sandbox and source bindings.

    An optional cumulative write-transfer budget is polled during collection
    and checked again after job termination. Overshoot is recorded; this is
    not a hard filesystem quota or a measure of allocated disk space.
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
        or type(memory_limit) is not int
        or not 32 * 1024 * 1024 <= memory_limit <= 8 * 1024 * 1024 * 1024
        or type(process_limit) is not int
        or not 1 <= process_limit <= 128
        or (write_io_limit is not None and (type(write_io_limit) is not int or not 0 < write_io_limit <= 1024**3))
    ):
        raise ValueError("Finite positive time and bounded output, memory, process and write-I/O limits are required")
    environment_block = None
    if environment is not None:
        if not environment or any(
            not isinstance(key, str)
            or not key
            or "=" in key
            or "\0" in key
            or not isinstance(value, str)
            or "\0" in value
            for key, value in environment.items()
        ):
            raise ValueError("A nonempty environment with valid string keys and values is required")
        if len({key.upper() for key in environment}) != len(environment):
            raise ValueError("Environment keys must be unique ignoring case")
        environment_block = c.create_unicode_buffer(
            "\0".join(f"{key}={value}" for key, value in sorted(environment.items(), key=lambda item: item[0].upper()))
            + "\0\0"
        )

    if space_budget is not None:
        space_budget.require_available()

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
        observed_write_bytes: int | None = None
        observation_error: dict[str, Any] | None = None
        query = native.function(
            "kernel", "QueryInformationJobObject", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p], w.BOOL
        )

        def monitor_writes() -> str | None:
            nonlocal observed_write_bytes, observation_error
            if observation_error is not None:
                return "resource_observation_error"
            info, returned = IoAccounting(), w.DWORD()
            if not query(job, 8, c.byref(info), c.sizeof(info), c.byref(returned)):
                observation_error = {
                    "api": "QueryInformationJobObject",
                    "information_class": 8,
                    "winerror": last_error(),
                }
                return "resource_observation_error"
            if returned.value != c.sizeof(info):
                observation_error = {
                    "api": "QueryInformationJobObject",
                    "information_class": 8,
                    "expected_bytes": c.sizeof(info),
                    "returned_bytes": returned.value,
                }
                return "resource_observation_error"
            observed_write_bytes = int(info.io.write_bytes)
            if write_io_limit is not None and observed_write_bytes > write_io_limit:
                return "write_io_limit"
            return None

        def monitor_resources() -> str | None:
            write_reason = monitor_writes() if write_io_limit is not None else None
            space_reason = space_budget.check() if space_budget is not None else None
            return write_reason or space_reason

        limits = ExtendedLimits()
        limits.basic.flags = 0x2000 | 0x200 | 0x8  # Kill on close, total job memory and active process count.
        limits.basic.active_limit = process_limit
        limits.job_memory = memory_limit
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
                0x80000 | 0x4 | 0x8000000 | 0x400,
                environment_block,
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
        reason, total = collect(
            native,
            process.process,
            pipes,
            [stdout, stderr],
            timeout,
            output_limit,
            monitor=monitor_resources if write_io_limit is not None or space_budget is not None else None,
        )
        exit_status = w.DWORD()
        get_exit = native.function("kernel", "GetExitCodeProcess", [w.HANDLE, c.POINTER(w.DWORD)], w.BOOL)
        require(native.function("kernel", "TerminateJobObject", [w.HANDLE, w.UINT], w.BOOL)(job, 124 if reason else 0))
        wait = native.function("kernel", "WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD)
        if wait(process.process, 5000) != 0:
            raise RuntimeError("Trial process did not terminate")
        require(get_exit(process.process, c.byref(exit_status)))
        accounting = Accounting()
        deadline = time.monotonic() + 5
        while True:
            require(query(job, 1, c.byref(accounting), c.sizeof(accounting), None))
            if not accounting.active:
                break
            if time.monotonic() > deadline:
                raise RuntimeError("Trial job processes did not terminate")
            time.sleep(0.01)
        if write_io_limit is not None:
            final_reason = monitor_writes()
            reason = reason or final_reason
        if space_budget is not None:
            final_space_reason = space_budget.check(force=True)
            reason = reason or final_space_reason
        return {
            "windows_job": True,
            "assigned_before_resume": True,
            "kill_on_close": True,
            "job_active_processes_after_cleanup": accounting.active,
            "service_created_processes_tracked": False,
            "termination_reason": reason,
            "exit_code": exit_status.value,
            "output_bytes": total,
            "output_limit_bytes": output_limit,
            "wall_time_limit_seconds": float(timeout),
            "job_memory_limit_bytes": memory_limit,
            "active_process_limit": process_limit,
            "explicit_environment": environment is not None,
            **({"space_budget": space_budget.record()} if space_budget is not None else {}),
            **(
                {
                    "write_io_limit_bytes": write_io_limit,
                    "job_write_io_bytes": observed_write_bytes,
                    "write_io_overshoot_bytes": (
                        max(0, observed_write_bytes - write_io_limit) if observed_write_bytes is not None else None
                    ),
                    "write_io_observation_error": observation_error,
                    "write_io_enforcement": "polled_job_transfer_accounting",
                    "hard_storage_quota": False,
                }
                if write_io_limit is not None
                else {}
            ),
        }

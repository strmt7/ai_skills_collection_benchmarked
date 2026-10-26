"""Bound an owned Windows Python process tree before enabling site packages."""

from __future__ import annotations

import ctypes
import subprocess
import sys
import time
import uuid
from ctypes import wintypes
from pathlib import Path
from typing import Any, BinaryIO

GATE = r"""
import ctypes,sys
from ctypes import wintypes
from pathlib import Path
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
open_job=kernel.OpenJobObjectW
open_job.argtypes,open_job.restype=(wintypes.DWORD,wintypes.BOOL,wintypes.LPCWSTR),wintypes.HANDLE
current=kernel.GetCurrentProcess
current.argtypes,current.restype=(),wintypes.HANDLE
contains=kernel.IsProcessInJob
contains.argtypes,contains.restype=(wintypes.HANDLE,wintypes.HANDLE,ctypes.POINTER(wintypes.BOOL)),wintypes.BOOL
assign=kernel.AssignProcessToJobObject
assign.argtypes,assign.restype=(wintypes.HANDLE,wintypes.HANDLE),wintypes.BOOL
close=kernel.CloseHandle
close.argtypes,close.restype=(wintypes.HANDLE,),wintypes.BOOL
job=open_job(0x0001|0x0004,False,sys.argv[1])
if not job:raise ctypes.WinError(ctypes.get_last_error())
try:
    owned=wintypes.BOOL()
    if not contains(current(),job,ctypes.byref(owned)):raise ctypes.WinError(ctypes.get_last_error())
    if not owned.value and not assign(job,current()):raise ctypes.WinError(ctypes.get_last_error())
    if not contains(current(),job,ctypes.byref(owned)) or not owned.value:raise RuntimeError('Real interpreter is not owned')
finally:
    close(job)
if sys.stdin.buffer.read(3)!=b'go\n':raise RuntimeError('Owning process did not release the start gate')
prefix=Path(sys.argv[2]).resolve()
if not sys.flags.no_site or not sys.flags.isolated:
    raise RuntimeError('Interpreter isolation or prefix mismatch')
import site
site.main()
if Path(sys.prefix).resolve()!=prefix:raise RuntimeError('Site initialization changed the selected environment')
code=sys.argv[3]
sys.argv=['-c',*sys.argv[4:]]
exec(compile(code,'<owned-python-control>','exec'),{'__name__':'__main__'})
"""


class BasicLimits(ctypes.Structure):
    _fields_ = [
        ("process_time", ctypes.c_longlong),
        ("job_time", ctypes.c_longlong),
        ("flags", wintypes.DWORD),
        ("minimum_working_set", ctypes.c_size_t),
        ("maximum_working_set", ctypes.c_size_t),
        ("active_limit", wintypes.DWORD),
        ("affinity", ctypes.c_size_t),
        ("priority", wintypes.DWORD),
        ("scheduling", wintypes.DWORD),
    ]


class Counters(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_ulonglong)
        for name in (
            "read_operations",
            "write_operations",
            "other_operations",
            "read_bytes",
            "write_bytes",
            "other_bytes",
        )
    ]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [
        ("basic", BasicLimits),
        ("io", Counters),
        ("process_memory", ctypes.c_size_t),
        ("job_memory", ctypes.c_size_t),
        ("peak_process_memory", ctypes.c_size_t),
        ("peak_job_memory", ctypes.c_size_t),
    ]


class Accounting(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_longlong) for name in ("user_time", "kernel_time", "period_user_time", "period_kernel_time")
    ] + [(name, wintypes.DWORD) for name in ("faults", "total", "active", "terminated")]


def run_python(
    interpreter: str,
    code: str,
    arguments: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    stdout: BinaryIO,
    stderr: BinaryIO,
    timeout: float = 60,
    output_limit: int = 8 * 1024 * 1024,
) -> tuple[int, dict[str, Any]]:
    """Keep the real interpreter and descendants in a kill-on-close Windows job."""
    if sys.platform != "win32":
        raise ValueError("native Python process controls require Windows")
    if Path(interpreter).resolve() != Path(sys.executable).resolve():
        raise ValueError("owned controls require the current admitted interpreter")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateJobObjectW
    create.argtypes, create.restype = (ctypes.c_void_p, wintypes.LPCWSTR), wintypes.HANDLE
    configure = kernel.SetInformationJobObject
    configure.argtypes, configure.restype = (
        (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD),
        wintypes.BOOL,
    )
    assign = kernel.AssignProcessToJobObject
    assign.argtypes, assign.restype = (wintypes.HANDLE, wintypes.HANDLE), wintypes.BOOL
    query = kernel.QueryInformationJobObject
    query.argtypes, query.restype = (
        (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p),
        wintypes.BOOL,
    )
    terminate = kernel.TerminateJobObject
    terminate.argtypes, terminate.restype = (wintypes.HANDLE, wintypes.UINT), wintypes.BOOL
    close = kernel.CloseHandle
    close.argtypes, close.restype = (wintypes.HANDLE,), wintypes.BOOL
    name = "Local\\ai_skills_pptx_" + uuid.uuid4().hex
    job = create(None, name)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    child = None
    started = time.monotonic()
    reason = None
    try:
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE; no breakaway permission.
        if not configure(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        command = [interpreter, "-I", "-S", "-B", "-c", GATE, name, str(Path(sys.prefix).resolve()), code, *arguments]
        child = subprocess.Popen(
            command,
            cwd=cwd,
            env=environment,
            stdin=subprocess.PIPE,
            stdout=stdout,
            stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        process_handle = getattr(child, "_handle", None)
        if process_handle is None:
            raise RuntimeError("native Windows process handle unavailable")
        if not assign(job, int(process_handle)):
            raise ctypes.WinError(ctypes.get_last_error())
        if child.stdin is None:
            raise RuntimeError("owned interpreter start gate unavailable")
        child.stdin.write(b"go\n")
        child.stdin.close()
        while child.poll() is None:
            if time.monotonic() - started > timeout:
                reason = "timeout"
                break
            if stdout.tell() + stderr.tell() > output_limit:
                reason = "output_limit"
                break
            time.sleep(0.02)
        if stdout.tell() + stderr.tell() > output_limit:
            reason = "output_limit"
        exit_code = child.returncode if reason is None else (124 if reason == "timeout" else 125)
        if not terminate(job, 124 if reason else 0):
            raise ctypes.WinError(ctypes.get_last_error())
        deadline = time.monotonic() + 5
        while True:
            accounting = Accounting()
            if not query(job, 1, ctypes.byref(accounting), ctypes.sizeof(accounting), None):
                raise ctypes.WinError(ctypes.get_last_error())
            if accounting.active == 0:
                break
            if time.monotonic() > deadline:
                raise RuntimeError("owned interpreter descendants did not terminate")
            time.sleep(0.02)
        child.wait(timeout=5)
        if exit_code is None:
            raise RuntimeError("owned interpreter exited without a native status")
        return int(exit_code), {
            "windows_job": True,
            "real_interpreter_gated_before_site": True,
            "kill_on_close": True,
            "active_processes_after_cleanup": accounting.active,
            "termination_reason": reason,
        }
    finally:
        close(job)
        if child is not None:
            if child.stdin is not None and not child.stdin.closed:
                child.stdin.close()
            child.wait(timeout=5)

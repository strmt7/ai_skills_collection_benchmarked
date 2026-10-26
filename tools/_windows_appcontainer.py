"""Run a bounded process with an independently checked Windows AppContainer token."""

from __future__ import annotations

import ctypes as c
import json
import math
import os
import stat
import subprocess
import sys
import time
import uuid
from contextlib import ExitStack
from ctypes import wintypes as w
from pathlib import Path
from typing import Any, BinaryIO

from _windows_owned_python import Accounting, ExtendedLimits


class Startup(c.Structure):
    _fields_ = [
        ("cb", w.DWORD),
        ("reserved", w.LPWSTR),
        ("desktop", w.LPWSTR),
        ("title", w.LPWSTR),
        *[(name, w.DWORD) for name in ("x", "y", "width", "height", "chars_x", "chars_y", "fill", "flags")],
        ("show", w.WORD),
        ("reserved_bytes", w.WORD),
        ("reserved_data", c.c_void_p),
        ("stdin", w.HANDLE),
        ("stdout", w.HANDLE),
        ("stderr", w.HANDLE),
    ]


class StartupEx(c.Structure):
    _fields_ = [("startup", Startup), ("attributes", c.c_void_p)]


class Process(c.Structure):
    _fields_ = [("process", w.HANDLE), ("thread", w.HANDLE), ("pid", w.DWORD), ("tid", w.DWORD)]


class Capabilities(c.Structure):
    _fields_ = [("sid", c.c_void_p), ("capabilities", c.c_void_p), ("count", w.DWORD), ("reserved", w.DWORD)]


class SecurityAttributes(c.Structure):
    _fields_ = [("length", w.DWORD), ("descriptor", c.c_void_p), ("inherit", w.BOOL)]


def require(value: Any) -> None:
    if not value:
        raise c.WinError(c.get_last_error())


class Native:
    def __init__(self) -> None:
        if sys.platform != "win32":
            raise ValueError("AppContainer execution requires Windows")
        self.kernel = c.WinDLL("kernel32", use_last_error=True)
        self.security = c.WinDLL("advapi32", use_last_error=True)
        self.profiles = c.WinDLL("userenv", use_last_error=True)
        self.ole = c.WinDLL("ole32", use_last_error=True)

    def function(self, library: str, name: str, arguments: list[Any], result: Any) -> Any:
        function = getattr(getattr(self, library), name)
        function.argtypes, function.restype = arguments, result
        return function

    def close(self, handle: Any) -> None:
        if handle:
            require(self.function("kernel", "CloseHandle", [w.HANDLE], w.BOOL)(handle))

    def free(self, pointer: Any) -> None:
        self.function("kernel", "LocalFree", [c.c_void_p], c.c_void_p)(pointer)

    def token_data(self, token: Any, kind: int) -> Any:
        get = self.function(
            "security", "GetTokenInformation", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.POINTER(w.DWORD)], w.BOOL
        )
        size = w.DWORD()
        get(token, kind, None, 0, c.byref(size))
        if not size.value:
            raise c.WinError(c.get_last_error())
        buffer = c.create_string_buffer(size.value)
        require(get(token, kind, buffer, size.value, c.byref(size)))
        return buffer

    def sid_text(self, sid: Any) -> str:
        text = w.LPWSTR()
        require(
            self.function("security", "ConvertSidToStringSidW", [c.c_void_p, c.POINTER(w.LPWSTR)], w.BOOL)(
                sid, c.byref(text)
            )
        )
        try:
            if text.value is None:
                raise RuntimeError("Windows returned an empty SID")
            return text.value
        finally:
            self.free(text)

    def process_token(self, process: Any) -> Any:
        token = w.HANDLE()
        require(
            self.function("security", "OpenProcessToken", [w.HANDLE, w.DWORD, c.POINTER(w.HANDLE)], w.BOOL)(
                process, 8, c.byref(token)
            )
        )
        return token

    def owner_sid(self) -> str:
        current = self.function("kernel", "GetCurrentProcess", [], w.HANDLE)()
        token = self.process_token(current)
        try:
            data = self.token_data(token, 1)
            return self.sid_text(c.c_void_p.from_buffer(data).value)
        finally:
            self.close(token)

    def descriptor(self, path: Path) -> bytes:
        descriptor = c.c_void_p()
        code = self.function(
            "security",
            "GetNamedSecurityInfoW",
            [w.LPCWSTR, c.c_int, w.DWORD, c.c_void_p, c.c_void_p, c.c_void_p, c.c_void_p, c.POINTER(c.c_void_p)],
            w.DWORD,
        )(str(path), 1, 4, None, None, None, None, c.byref(descriptor))
        if code:
            raise c.WinError(code)
        try:
            size = self.function("security", "GetSecurityDescriptorLength", [c.c_void_p], w.DWORD)(descriptor)
            return c.string_at(descriptor, size)
        finally:
            self.free(descriptor)

    def set_descriptor(self, path: Path, raw: Any) -> None:
        present, defaulted, acl = w.BOOL(), w.BOOL(), c.c_void_p()
        require(
            self.function(
                "security",
                "GetSecurityDescriptorDacl",
                [c.c_void_p, c.POINTER(w.BOOL), c.POINTER(c.c_void_p), c.POINTER(w.BOOL)],
                w.BOOL,
            )(raw, c.byref(present), c.byref(acl), c.byref(defaulted))
        )
        control, revision = w.WORD(), w.DWORD()
        require(
            self.function(
                "security", "GetSecurityDescriptorControl", [c.c_void_p, c.POINTER(w.WORD), c.POINTER(w.DWORD)], w.BOOL
            )(raw, c.byref(control), c.byref(revision))
        )
        if not present.value:
            raise ValueError("A DACL is required")
        protection = 0x80000000 if control.value & 0x1000 else 0x20000000
        code = self.function(
            "security",
            "SetNamedSecurityInfoW",
            [w.LPWSTR, c.c_int, w.DWORD, c.c_void_p, c.c_void_p, c.c_void_p, c.c_void_p],
            w.DWORD,
        )(str(path), 1, 4 | protection, None, None, acl, None)
        if code:
            raise c.WinError(code)

    def grant(self, path: Path, owner: str, package: str | None, *, writable: bool = False) -> None:
        extra = "" if package is None else f"(A;OICI;{'0x1301bf' if writable else 'GRGX'};;;{package})"
        sddl = f"D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;{owner}){extra}"
        descriptor = c.c_void_p()
        require(
            self.function(
                "security",
                "ConvertStringSecurityDescriptorToSecurityDescriptorW",
                [w.LPCWSTR, w.DWORD, c.POINTER(c.c_void_p), c.c_void_p],
                w.BOOL,
            )(sddl, 1, c.byref(descriptor), None)
        )
        try:
            self.set_descriptor(path, descriptor)
        finally:
            self.free(descriptor)

    def attest(self, process: Any, expected_sid: str) -> dict[str, Any]:
        token = self.process_token(process)
        try:
            app = w.DWORD.from_buffer(self.token_data(token, 29)).value
            count = w.DWORD.from_buffer(self.token_data(token, 30)).value
            sid_data, integrity_data = self.token_data(token, 31), self.token_data(token, 25)
            sid = self.sid_text(c.c_void_p.from_buffer(sid_data).value)
            integrity = self.sid_text(c.c_void_p.from_buffer(integrity_data).value)
            if app != 1 or count != 0 or sid != expected_sid or integrity != "S-1-16-4096":
                raise RuntimeError("Suspended child token does not meet the confinement policy")
            return {
                "appcontainer": True,
                "capability_count": count,
                "appcontainer_sid": sid,
                "integrity_sid": integrity,
                "attested_while_suspended": True,
            }
        finally:
            self.close(token)


def checked_path(path: Path) -> Path:
    """Reject links before resolution, including links in existing ancestors."""
    absolute = Path(os.path.abspath(path))
    for current in [absolute, *absolute.parents]:
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Reparse points are not permitted: {current}")
    return absolute


def checked_tree(path: Path) -> list[Path]:
    checked_path(path)
    files = []
    pending = [path]
    while pending:
        current = pending.pop()
        info = current.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Reparse points cannot be mounted: {current}")
        if stat.S_ISDIR(info.st_mode):
            pending.extend(current.iterdir())
        elif stat.S_ISREG(info.st_mode):
            files.append(current)
        else:
            raise ValueError(f"Only regular files and directories can be mounted: {current}")
    return sorted(files)


def checked_mounts(workspace: Path, readable: list[Path], scratch: Path, executable: Path, output: Path) -> None:
    roots = [*readable, scratch]
    if not readable or not scratch.is_dir() or not executable.is_file():
        raise ValueError("Existing runtime/read mounts and a scratch directory are required")
    for directory in roots:
        if not directory.is_dir() or directory == workspace or not directory.is_relative_to(workspace):
            raise ValueError("Mounts must be directories strictly inside the owned workspace")
        checked_tree(directory)
    for index, directory in enumerate(roots):
        if any(directory.is_relative_to(other) or other.is_relative_to(directory) for other in roots[index + 1 :]):
            raise ValueError("Read-only and writable mounts must not overlap")
    if not any(executable.is_relative_to(directory) for directory in readable):
        raise ValueError("The executable must be inside a read-only mount")
    if any(scratch.iterdir()):
        raise ValueError("Use a new empty scratch directory for each candidate process")
    if output == workspace or not output.is_relative_to(workspace):
        raise ValueError("Trusted output must be strictly inside the owned workspace")
    if any(output.is_relative_to(path) or path.is_relative_to(output) for path in roots):
        raise ValueError("Trusted output must be outside every candidate mount")


class Pipe:
    def __init__(self, native: Native) -> None:
        self.native = native
        self.read: Any = w.HANDLE()
        self.write: Any = w.HANDLE()
        security = SecurityAttributes(c.sizeof(SecurityAttributes), None, True)
        require(
            native.function(
                "kernel",
                "CreatePipe",
                [c.POINTER(w.HANDLE), c.POINTER(w.HANDLE), c.POINTER(SecurityAttributes), w.DWORD],
                w.BOOL,
            )(c.byref(self.read), c.byref(self.write), c.byref(security), 65536)
        )
        try:
            require(
                native.function("kernel", "SetHandleInformation", [w.HANDLE, w.DWORD, w.DWORD], w.BOOL)(self.read, 1, 0)
            )
        except BaseException:
            self.close()
            raise

    def read_available(self, limit: int) -> bytes:
        available = w.DWORD()
        peek = self.native.function(
            "kernel",
            "PeekNamedPipe",
            [w.HANDLE, c.c_void_p, w.DWORD, c.c_void_p, c.POINTER(w.DWORD), c.c_void_p],
            w.BOOL,
        )
        if not peek(self.read, None, 0, None, c.byref(available), None):
            if c.get_last_error() == 109:
                return b""
            raise c.WinError(c.get_last_error())
        if not available.value:
            return b""
        size = min(available.value, 65536, limit)
        buffer, count = c.create_string_buffer(size), w.DWORD()
        require(
            self.native.function(
                "kernel", "ReadFile", [w.HANDLE, c.c_void_p, w.DWORD, c.POINTER(w.DWORD), c.c_void_p], w.BOOL
            )(self.read, buffer, size, c.byref(count), None)
        )
        return buffer.raw[: count.value]

    def close(self) -> None:
        try:
            self.native.close(self.read)
        finally:
            self.read = None
            self.native.close(self.write)
            self.write = None


def environment(scratch: Path) -> Any:
    selected = {
        key.upper(): value for key, value in os.environ.items() if key.upper() in {"SYSTEMROOT", "WINDIR", "COMSPEC"}
    }
    selected.update(
        TEMP=str(scratch), TMP=str(scratch), USERPROFILE=str(scratch), APPDATA=str(scratch), LOCALAPPDATA=str(scratch)
    )
    return c.create_unicode_buffer("\0".join(key + "=" + value for key, value in sorted(selected.items())) + "\0\0")


def execute(
    native: Native,
    executable: Path,
    arguments: list[str],
    scratch: Path,
    sid: Any,
    *,
    output: Path,
    timeout: float,
    output_limit: int,
    memory_limit: int,
) -> dict[str, Any]:
    size, process = c.c_size_t(), Process()
    initialize = native.function(
        "kernel", "InitializeProcThreadAttributeList", [c.c_void_p, w.DWORD, w.DWORD, c.POINTER(c.c_size_t)], w.BOOL
    )
    initialize(None, 2, 0, c.byref(size))
    attributes = c.create_string_buffer(size.value)
    require(initialize(attributes, 2, 0, c.byref(size)))
    with ExitStack() as resources:
        resources.callback(native.function("kernel", "DeleteProcThreadAttributeList", [c.c_void_p], None), attributes)
        job = native.function("kernel", "CreateJobObjectW", [c.c_void_p, w.LPCWSTR], w.HANDLE)(None, None)
        require(job)
        resources.callback(native.close, job)
        pipes = []
        for _ in range(2):
            pipe = Pipe(native)
            resources.callback(pipe.close)
            pipes.append(pipe)
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000 | 0x100 | 0x8 | 0x2
        limits.basic.active_limit = 1
        limits.basic.process_time = int(timeout * 10_000_000)
        limits.process_memory = memory_limit
        require(
            native.function("kernel", "SetInformationJobObject", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD], w.BOOL)(
                job, 9, c.byref(limits), c.sizeof(limits)
            )
        )
        update = native.function(
            "kernel",
            "UpdateProcThreadAttribute",
            [c.c_void_p, w.DWORD, c.c_size_t, c.c_void_p, c.c_size_t, c.c_void_p, c.c_void_p],
            w.BOOL,
        )
        capabilities = Capabilities(sid, None, 0, 0)
        require(update(attributes, 0, 0x20009, c.byref(capabilities), c.sizeof(capabilities), None, None))
        with open(os.devnull, "rb") as stdin:
            import msvcrt

            input_handle = msvcrt.get_osfhandle(stdin.fileno())
            os.set_handle_inheritable(input_handle, True)
            handles = (w.HANDLE * 3)(input_handle, pipes[0].write.value, pipes[1].write.value)
            require(update(attributes, 0, 0x20002, handles, c.sizeof(handles), None, None))
            startup = StartupEx()
            startup.startup.cb, startup.startup.flags = c.sizeof(startup), 0x100
            startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = handles
            startup.attributes = c.addressof(attributes)
            command = c.create_unicode_buffer(subprocess.list2cmdline([str(executable), *arguments]))
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
            require(
                create(
                    str(executable),
                    command,
                    None,
                    None,
                    True,
                    0x80000 | 0x400 | 0x4 | 0x8000000,
                    environment(scratch),
                    str(scratch),
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
        receipt = native.attest(process.process, native.sid_text(sid))
        resume = native.function("kernel", "ResumeThread", [w.HANDLE], w.DWORD)(process.thread)
        if resume == 0xFFFFFFFF:
            raise c.WinError(c.get_last_error())
        with (output / "stdout.native").open("xb") as stdout, (output / "stderr.native").open("xb") as stderr:
            reason, total = collect(native, process.process, pipes, [stdout, stderr], timeout, output_limit)
        status = w.DWORD()
        get_exit = native.function("kernel", "GetExitCodeProcess", [w.HANDLE, c.POINTER(w.DWORD)], w.BOOL)
        terminate = native.function("kernel", "TerminateJobObject", [w.HANDLE, w.UINT], w.BOOL)
        require(terminate(job, 124 if reason == "timeout" else 125 if reason else 0))
        wait = native.function("kernel", "WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD)
        if wait(process.process, 5000) != 0:
            raise RuntimeError("Terminated candidate did not signal completion")
        require(get_exit(process.process, c.byref(status)))
        accounting = Accounting()
        query = native.function(
            "kernel", "QueryInformationJobObject", [w.HANDLE, c.c_int, c.c_void_p, w.DWORD, c.c_void_p], w.BOOL
        )
        deadline = time.monotonic() + 5
        while True:
            require(query(job, 1, c.byref(accounting), c.sizeof(accounting), None))
            if accounting.active == 0:
                break
            if time.monotonic() > deadline:
                raise RuntimeError("AppContainer process did not terminate")
            time.sleep(0.01)
        require(get_exit(process.process, c.byref(status)))
        return {
            **receipt,
            "windows_job": True,
            "assigned_before_resume": True,
            "kill_on_close": True,
            "active_process_limit": 1,
            "process_memory_limit_bytes": memory_limit,
            "cpu_time_limit_seconds": timeout,
            "wall_time_limit_seconds": timeout,
            "output_limit_bytes": output_limit,
            "termination_reason": reason,
            "exit_code": status.value,
            "output_bytes": total,
            "active_processes_after_cleanup": accounting.active,
        }


def stop_process(native: Native, process: Any) -> None:
    wait = native.function("kernel", "WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD)
    state = wait(process, 0)
    if state == 0:
        return
    if state != 0x102:
        raise c.WinError(c.get_last_error())
    terminated = native.function("kernel", "TerminateProcess", [w.HANDLE, w.UINT], w.BOOL)(process, 126)
    error = c.get_last_error()
    if not terminated and error != 5:
        raise c.WinError(error)
    # ERROR_ACCESS_DENIED also occurs when termination has already begun.
    # Accept it only after independently observing process completion.
    if wait(process, 5000) != 0:
        raise RuntimeError("Created candidate process could not be stopped")


def collect(
    native: Native, process: Any, pipes: list[Pipe], files: list[BinaryIO], timeout: float, output_limit: int
) -> tuple[str | None, int]:
    wait = native.function("kernel", "WaitForSingleObject", [w.HANDLE, w.DWORD], w.DWORD)
    deadline, total = time.monotonic() + timeout, 0
    while True:
        received = False
        for pipe, stream in zip(pipes, files, strict=True):
            chunk = pipe.read_available(output_limit + 1 - total)
            if chunk:
                received = True
                stream.write(chunk)
                total += len(chunk)
                if total > output_limit:
                    return "output_limit", total
        state = wait(process, 0)
        if state not in {0, 0x102}:
            raise c.WinError(c.get_last_error())
        if state == 0 and not received:
            return None, total
        if time.monotonic() > deadline:
            return "timeout", total
        time.sleep(0.01)


def seal_profile(native: Native, package_sid: str, owner: str) -> None:
    folder = w.LPWSTR()
    get_folder = native.function("profiles", "GetAppContainerFolderPath", [w.LPCWSTR, c.POINTER(w.LPWSTR)], c.c_long)
    code = get_folder(package_sid, c.byref(folder))
    if code:
        raise RuntimeError(f"GetAppContainerFolderPath failed: HRESULT 0x{code & 0xFFFFFFFF:08x}")
    try:
        if not folder.value or not Path(folder.value).is_absolute():
            raise RuntimeError("Windows returned an invalid owned profile path")
        profile_folder = Path(folder.value)
        checked_tree(profile_folder)
        native.grant(profile_folder, owner, None)
    finally:
        native.function("ole", "CoTaskMemFree", [c.c_void_p], None)(folder)


def restore_readonly(native: Native, restored: list[tuple[Path, bytes]]) -> list[str]:
    errors = []
    for directory, raw in reversed(restored):
        try:
            checked_tree(directory)
            native.set_descriptor(directory, c.create_string_buffer(raw))
        except (OSError, ValueError) as error:
            errors.append(f"Read-only ACL restoration: {error}")
    return errors


def run_appcontainer(
    executable: Path,
    arguments: list[str],
    *,
    workspace: Path,
    readable: list[Path],
    scratch: Path,
    output: Path,
    timeout: float = 10,
    output_limit: int = 2 * 1024 * 1024,
    memory_limit: int = 256 * 1024 * 1024,
) -> dict[str, Any]:
    """No fallback: create, attest, bound and clean up one capability-free process.

    Only newly prepared private trees may be mounted. Read-only ACLs are restored.
    Untrusted scratch contents are retained without traversing or deleting them.
    """
    if sys.platform != "win32":
        raise ValueError("AppContainer execution requires Windows")
    if not math.isfinite(timeout) or timeout <= 0 or output_limit < 1 or memory_limit < 1:
        raise ValueError("Finite positive resource limits are required")
    if any("\0" in arg for arg in arguments):
        raise ValueError("Arguments cannot contain NUL")
    for path in [workspace, executable, scratch, output, *readable]:
        checked_path(path)
    workspace, executable, scratch = [path.resolve(strict=True) for path in (workspace, executable, scratch)]
    output = output.resolve()
    readable = [path.resolve(strict=True) for path in readable]
    checked_mounts(workspace, readable, scratch, executable, output)
    output.mkdir(parents=True, exist_ok=False)
    native, sid, restored = Native(), c.c_void_p(), []
    owner = native.owner_sid()
    native.grant(output, owner, None)
    name = "ai-skills-benchmark-" + uuid.uuid4().hex
    create = native.function(
        "profiles",
        "CreateAppContainerProfile",
        [w.LPCWSTR, w.LPCWSTR, w.LPCWSTR, c.c_void_p, w.DWORD, c.POINTER(c.c_void_p)],
        c.c_long,
    )
    code = create(name, name, "Isolated benchmark candidate", None, 0, c.byref(sid))
    if code:
        raise RuntimeError(f"CreateAppContainerProfile failed: HRESULT 0x{code & 0xFFFFFFFF:08x}")
    package_sid = native.sid_text(sid)
    profile = {"name": name, "sid": package_sid, "created_by_pid": os.getpid()}
    receipt: dict[str, Any] = {}
    cleanup_errors = []
    try:
        (output / "profile.json").write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
        seal_profile(native, package_sid, owner)
        for directory in readable:
            restored.append((directory, native.descriptor(directory)))
            native.grant(directory, owner, package_sid)
        native.grant(scratch, owner, package_sid, writable=True)
        receipt = execute(
            native,
            executable,
            arguments,
            scratch,
            sid,
            output=output,
            timeout=timeout,
            output_limit=output_limit,
            memory_limit=memory_limit,
        )
    finally:
        cleanup_errors = restore_readonly(native, restored)
        readonly_restored = not cleanup_errors
        deleted = native.function("profiles", "DeleteAppContainerProfile", [w.LPCWSTR], c.c_long)(name)
        if deleted:
            cleanup_errors.append(f"Profile deletion HRESULT 0x{deleted & 0xFFFFFFFF:08x}")
        native.function("security", "FreeSid", [c.c_void_p], c.c_void_p)(sid)
        receipt.update(
            profile_deleted=deleted == 0,
            readonly_acls_restored=readonly_restored,
            scratch_retained_without_traversal=True,
            cleanup_errors=cleanup_errors,
        )
        (output / "process.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        if cleanup_errors:
            raise RuntimeError("; ".join(cleanup_errors))
    return receipt

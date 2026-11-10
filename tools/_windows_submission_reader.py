"""Read submission objects through one explicitly owned Windows handle graph."""

from __future__ import annotations

import ctypes
import os
import sys
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from ctypes import wintypes
from pathlib import Path, PurePosixPath
from typing import Any

from _windows_appcontainer import last_error, win_error


class _UnicodeString(ctypes.Structure):
    _fields_ = [("Length", wintypes.USHORT), ("MaximumLength", wintypes.USHORT), ("Buffer", wintypes.LPWSTR)]


class _ObjectAttributes(ctypes.Structure):
    _fields_ = [
        ("Length", wintypes.ULONG),
        ("RootDirectory", wintypes.HANDLE),
        ("ObjectName", ctypes.POINTER(_UnicodeString)),
        ("Attributes", wintypes.ULONG),
        ("SecurityDescriptor", wintypes.LPVOID),
        ("SecurityQualityOfService", wintypes.LPVOID),
    ]


class _IoStatus(ctypes.Structure):
    _fields_ = [("Status", ctypes.c_ssize_t), ("Information", ctypes.c_size_t)]


class _FileInformation(ctypes.Structure):
    _fields_ = [
        ("attributes", wintypes.DWORD),
        ("created", wintypes.FILETIME),
        ("accessed", wintypes.FILETIME),
        ("modified", wintypes.FILETIME),
        ("volume", wintypes.DWORD),
        ("size_high", wintypes.DWORD),
        ("size_low", wintypes.DWORD),
        ("links", wintypes.DWORD),
        ("index_high", wintypes.DWORD),
        ("index_low", wintypes.DWORD),
    ]


def _normalize_path(value: str) -> str:
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    return os.path.normcase(os.path.normpath(value))


def _parts(name: str) -> tuple[str, ...]:
    if not isinstance(name, str):
        raise ValueError("invalid submission path")
    path = PurePosixPath(name)
    if (
        not path.parts
        or path.is_absolute()
        or path.as_posix() != name
        or any(part in {".", ".."} or any(char in part for char in "\\:\0") or part[-1] in " ." for part in path.parts)
    ):
        raise ValueError("invalid submission path")
    return path.parts


class WorkspaceReader:
    """Hold verified directories and files until one collection operation closes."""

    def __init__(self, workspace: Path, *, enumerate_directories: bool = False) -> None:
        if type(enumerate_directories) is not bool:
            raise ValueError("Directory enumeration must be explicitly enabled or disabled")
        self.workspace = workspace
        self.enumerate_directories = enumerate_directories
        self.kernel: Any = None
        self.ntdll: Any = None
        self._stack = ExitStack()
        self._state = "new"
        self._directories: dict[str, Any] = {}
        self._files: dict[str, tuple[Any, int]] = {}

    def _configure(self) -> None:
        if sys.platform != "win32":
            raise ValueError("Safe submission collection requires Windows")
        self.kernel = kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.ntdll = ntdll = ctypes.WinDLL("ntdll")
        kernel.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        kernel.GetFileInformationByHandle.argtypes = [wintypes.HANDLE, ctypes.POINTER(_FileInformation)]
        kernel.GetFileInformationByHandle.restype = wintypes.BOOL
        kernel.GetFileType.argtypes = [wintypes.HANDLE]
        kernel.GetFileType.restype = wintypes.DWORD
        kernel.GetFinalPathNameByHandleW.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
        kernel.GetFinalPathNameByHandleW.restype = wintypes.DWORD
        kernel.ReadFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        kernel.ReadFile.restype = wintypes.BOOL
        kernel.SetFilePointerEx.argtypes = [
            wintypes.HANDLE,
            ctypes.c_longlong,
            ctypes.POINTER(ctypes.c_longlong),
            wintypes.DWORD,
        ]
        kernel.SetFilePointerEx.restype = wintypes.BOOL
        ntdll.NtCreateFile.argtypes = [
            ctypes.POINTER(wintypes.HANDLE),
            wintypes.ULONG,
            ctypes.POINTER(_ObjectAttributes),
            ctypes.POINTER(_IoStatus),
            ctypes.c_void_p,
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.ULONG,
            wintypes.ULONG,
            ctypes.c_void_p,
            wintypes.ULONG,
        ]
        ntdll.NtCreateFile.restype = ctypes.c_long

    def _close(self, handle: Any) -> None:
        if not self.kernel.CloseHandle(handle):
            raise win_error(last_error())

    def _inspect(self, handle: Any, directory: bool) -> _FileInformation:
        info = _FileInformation()
        if not self.kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise win_error(last_error())
        if self.kernel.GetFileType(handle) != 1 or info.attributes & 0x400 or bool(info.attributes & 0x10) != directory:
            raise ValueError("submission path contains a reparse point or wrong object type")
        return info

    def __enter__(self) -> WorkspaceReader:
        if self._state != "new":
            raise ValueError("submission reader cannot be reused")
        if sys.platform != "win32":
            raise ValueError("Safe submission collection requires Windows")
        self._state = "opening"
        try:
            self._configure()
            absolute = os.path.abspath(self.workspace)
            desired = 0x100000 | 0x80 | 0x20 | (1 if self.enumerate_directories else 0)
            root = self.kernel.CreateFileW(absolute, desired, 3, None, 3, 0x02000000 | 0x00200000, None)
            if not root or root == wintypes.HANDLE(-1).value:
                raise ctypes.WinError(ctypes.get_last_error())
            self._stack.callback(self._close, root)
            self._inspect(root, True)
            buffer = ctypes.create_unicode_buffer(32768)
            length = self.kernel.GetFinalPathNameByHandleW(root, buffer, len(buffer), 0)
            if not length or length >= len(buffer):
                raise ValueError("cannot resolve the opened submission directory")
            if _normalize_path(buffer.value) != _normalize_path(absolute):
                raise ValueError("submission directory resolves outside its selected path")
            self._directories[""] = root
            self._state = "open"
            return self
        except BaseException:
            self._state = "closed"
            self._stack.close()
            raise

    def __exit__(self, *_exc: Any) -> None:
        self._state = "closed"
        self._stack.close()

    def _require_open(self) -> None:
        if self._state != "open":
            raise ValueError("submission reader is not open")

    def _relative(self, parent: Any, name: str, directory: bool) -> tuple[Any, _FileInformation]:
        encoded = len(name.encode("utf-16-le"))
        if encoded > 65532:
            raise ValueError("submission path component exceeds the native limit")
        buffer = ctypes.create_unicode_buffer(name)
        text = _UnicodeString(encoded, encoded + 2, ctypes.cast(buffer, wintypes.LPWSTR))
        attrs = _ObjectAttributes(ctypes.sizeof(_ObjectAttributes), parent, ctypes.pointer(text), 0x40, None, None)
        status, result = _IoStatus(), wintypes.HANDLE()
        desired = 0x100000 | 0x80 | (0x20 if directory else 1)
        if directory and self.enumerate_directories:
            desired |= 1
        code = self.ntdll.NtCreateFile(
            ctypes.byref(result),
            desired,
            ctypes.byref(attrs),
            ctypes.byref(status),
            None,
            0,
            3 if directory else 1,
            1,
            0x20 | 0x200000 | (1 if directory else 0x40),
            None,
            0,
        )
        if code != 0:
            raise ValueError(f"cannot safely open submission component (NTSTATUS 0x{code & 0xFFFFFFFF:08x})")
        self._stack.callback(self._close, result)
        return result, self._inspect(result, directory)

    def directory(self, name: str = "") -> Any:
        self._require_open()
        if name in self._directories:
            return self._directories[name]
        parts = _parts(name)
        parent = self._directories[""]
        for index, part in enumerate(parts):
            relative = "/".join(parts[: index + 1])
            if relative not in self._directories:
                self._directories[relative], _ = self._relative(parent, part, True)
            parent = self._directories[relative]
        return parent

    def open_file(self, name: str, *, max_bytes: int) -> tuple[Any, Any, int]:
        self._require_open()
        if type(max_bytes) is not int or not 0 <= max_bytes <= 8 * 1024 * 1024:
            raise ValueError("submission size limit must be between 0 and 8 MiB")
        parts = _parts(name)
        if name not in self._files:
            parent = self.directory("/".join(parts[:-1]))
            candidate, info = self._relative(parent, parts[-1], False)
            size = (info.size_high << 32) | info.size_low
            if info.links != 1:
                raise ValueError("submitted file must have one link")
            self._files[name] = candidate, size
        handle, size = self._files[name]
        if size > max_bytes:
            raise ValueError(f"submitted file exceeds its size limit ({max_bytes} bytes)")
        return self.kernel, handle, size

    def read_file(self, name: str, *, max_bytes: int) -> bytes:
        kernel, handle, expected_size = self.open_file(name, max_bytes=max_bytes)
        if not kernel.SetFilePointerEx(handle, 0, None, 0):
            raise win_error(last_error())
        chunks: list[bytes] = []
        total = 0
        while True:
            buffer, count = ctypes.create_string_buffer(65536), wintypes.DWORD()
            if not kernel.ReadFile(handle, buffer, len(buffer), ctypes.byref(count), None):
                raise win_error(last_error())
            if not count.value:
                if total != expected_size:
                    raise ValueError("submitted file changed while being read")
                return b"".join(chunks)
            total += count.value
            if total > max_bytes:
                raise ValueError("submitted file exceeds its size limit")
            chunks.append(buffer.raw[: count.value])


@contextmanager
def open_workspace_file(workspace: Path, name: str, *, max_bytes: int) -> Iterator[tuple[Any, Any, int]]:
    with WorkspaceReader(workspace) as reader:
        yield reader.open_file(name, max_bytes=max_bytes)


@contextmanager
def open_submission(workspace: Path) -> Iterator[tuple[Any, Any, int]]:
    with open_workspace_file(workspace, "tools/check_benchmark_artifact.py", max_bytes=1024 * 1024) as opened:
        yield opened


def read_workspace_file(workspace: Path, name: str, *, max_bytes: int) -> bytes:
    with WorkspaceReader(workspace) as reader:
        return reader.read_file(name, max_bytes=max_bytes)


def read_submission(workspace: Path) -> bytes:
    return read_workspace_file(workspace, "tools/check_benchmark_artifact.py", max_bytes=1024 * 1024)

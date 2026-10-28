"""Read explicitly selected submission files through held Windows handles."""

from __future__ import annotations

import ctypes
import os
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from ctypes import wintypes
from pathlib import Path, PurePosixPath
from typing import Any


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


@contextmanager
def open_workspace_file(workspace: Path, name: str, *, max_bytes: int) -> Iterator[tuple[Any, Any, int]]:
    """Hold the workspace and every selected ancestor against renames and writes."""
    if sys.platform != "win32":
        raise ValueError("Safe submission collection requires Windows")
    if type(max_bytes) is not int or not 0 <= max_bytes <= 8 * 1024 * 1024:
        raise ValueError("submission size limit must be between 0 and 8 MiB")
    path = PurePosixPath(name)
    parts = path.parts
    if (
        not parts
        or path.is_absolute()
        or path.as_posix() != name
        or any(part in {".", ".."} or any(char in part for char in "\\:\0") or part[-1] in " ." for part in parts)
    ):
        raise ValueError("invalid submission path")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    ntdll = ctypes.WinDLL("ntdll")
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
    handles = []

    def inspect(handle, directory: bool) -> _FileInformation:
        info = _FileInformation()
        if not kernel.GetFileInformationByHandle(handle, ctypes.byref(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if kernel.GetFileType(handle) != 1 or info.attributes & 0x400 or bool(info.attributes & 0x10) != directory:
            raise ValueError("submission path contains a reparse point or wrong object type")
        return info

    def relative(parent, name: str, directory: bool):
        if not name or name in {".", ".."} or any(char in name for char in "\\/:") or name[-1] in " .":
            raise ValueError("invalid submission path component")
        encoded = len(name.encode("utf-16-le"))
        if encoded > 65532:
            raise ValueError("submission path component exceeds the native limit")
        buffer = ctypes.create_unicode_buffer(name)
        text = _UnicodeString(encoded, encoded + 2, ctypes.cast(buffer, wintypes.LPWSTR))
        attrs = _ObjectAttributes(ctypes.sizeof(_ObjectAttributes), parent, ctypes.pointer(text), 0x40, None, None)
        status = _IoStatus()
        result = wintypes.HANDLE()
        desired = 0x100000 | 0x80 | (0x20 if directory else 0x1)
        share = 3 if directory else 1
        options = 0x20 | 0x200000 | (0x1 if directory else 0x40)
        code = ntdll.NtCreateFile(
            ctypes.byref(result),
            desired,
            ctypes.byref(attrs),
            ctypes.byref(status),
            None,
            0,
            share,
            1,
            options,
            None,
            0,
        )
        if code != 0:
            raise ValueError(f"cannot safely open submission component (NTSTATUS 0x{code & 0xFFFFFFFF:08x})")
        handles.append(result)
        return result, inspect(result, directory)

    try:
        absolute = os.path.abspath(workspace)
        root = kernel.CreateFileW(absolute, 0x100000 | 0x80 | 0x20, 3, None, 3, 0x02000000 | 0x00200000, None)
        if not root or root == wintypes.HANDLE(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())
        handles.append(root)
        inspect(root, True)
        buffer = ctypes.create_unicode_buffer(32768)
        length = kernel.GetFinalPathNameByHandleW(root, buffer, len(buffer), 0)
        if not length or length >= len(buffer):
            raise ValueError("cannot resolve the opened submission directory")
        if _normalize_path(buffer.value) != _normalize_path(absolute):
            raise ValueError("submission directory resolves outside its selected path")
        parent = root
        for part in parts[:-1]:
            parent, _ = relative(parent, part, True)
        candidate, info = relative(parent, parts[-1], False)
        size = (info.size_high << 32) | info.size_low
        if info.links != 1 or size > max_bytes:
            raise ValueError(f"submitted file must have one link and be within its size limit ({max_bytes} bytes)")
        yield kernel, candidate, size
    finally:
        for handle in reversed(handles):
            kernel.CloseHandle(handle)


@contextmanager
def open_submission(workspace: Path) -> Iterator[tuple[Any, Any, int]]:
    with open_workspace_file(workspace, "tools/check_benchmark_artifact.py", max_bytes=1024 * 1024) as opened:
        yield opened


def read_workspace_file(workspace: Path, name: str, *, max_bytes: int) -> bytes:
    if sys.platform != "win32":
        raise ValueError("Safe submission collection requires Windows")
    with open_workspace_file(workspace, name, max_bytes=max_bytes) as (kernel, handle, expected_size):
        kernel.ReadFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        kernel.ReadFile.restype = wintypes.BOOL
        chunks: list[bytes] = []
        total = 0
        while True:
            buffer = ctypes.create_string_buffer(65536)
            count = wintypes.DWORD()
            if not kernel.ReadFile(handle, buffer, len(buffer), ctypes.byref(count), None):
                raise ctypes.WinError(ctypes.get_last_error())
            if not count.value:
                if total != expected_size:
                    raise ValueError("submitted validator changed while being read")
                return b"".join(chunks)
            total += count.value
            if total > max_bytes:
                raise ValueError("submitted file exceeds its size limit")
            chunks.append(buffer.raw[: count.value])


def read_submission(workspace: Path) -> bytes:
    return read_workspace_file(workspace, "tools/check_benchmark_artifact.py", max_bytes=1024 * 1024)

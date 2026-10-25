"""Portable, no-follow download opening for the identified Crawl4AI source build.

Copyright 2026 FlitzZip contributors. SPDX-License-Identifier: Apache-2.0
This module is included in Crawl4AI's development-tool wheel, not the archive app.
"""

from __future__ import annotations

import errno
import os
import stat


def validate_download_name(name: str) -> None:
    """Purpose: Reject Windows aliases before Python selects an I/O class. Inputs: Basename. Outputs: None/error."""
    if os.name == "nt" and os.path.isreserved(name):
        raise ValueError("Reserved Windows download destination")


def windows_handle(path: str, flags: int) -> int:
    """Purpose: Open without following reparse points. Inputs: Confined path/open flags. Outputs: Owned handle."""
    import ctypes
    from ctypes import wintypes

    validate_download_name(path)
    allowed = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_TRUNC | os.O_APPEND
    allowed |= os.O_BINARY | os.O_TEXT | os.O_NOINHERIT
    if flags & ~allowed or flags & (os.O_WRONLY | os.O_RDWR) == (os.O_WRONLY | os.O_RDWR):
        raise ValueError("Unsupported download open flags")
    access = 0x80000000 if not flags & os.O_WRONLY else 0
    if flags & (os.O_WRONLY | os.O_RDWR):
        access |= 0x40000000
    disposition = 1 if flags & os.O_EXCL else (4 if flags & os.O_CREAT else 3)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    create.restype = wintypes.HANDLE
    # OPEN_ALWAYS, never CREATE_ALWAYS: validate the opened object before truncating.
    handle = create(os.fsdecode(path), access, 1, None, disposition, 0x00200000 | 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    return handle


def windows_descriptor(path: str, flags: int) -> int:
    """Purpose: Validate before transfer/truncation. Inputs: Confined path/flags. Outputs: Owned regular-file fd."""
    import ctypes
    import msvcrt
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    close = kernel.CloseHandle
    close.argtypes, close.restype = (wintypes.HANDLE,), wintypes.BOOL
    query = kernel.GetFileInformationByHandleEx
    query.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
    query.restype = wintypes.BOOL
    handle = windows_handle(path, flags)
    descriptor = None
    try:
        attributes = (wintypes.DWORD * 2)()
        # FileAttributeTagInfo queries this handle, not a second path-based lookup.
        if not query(handle, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)):
            raise ctypes.WinError(ctypes.get_last_error())
        if attributes[0] & (0x400 | 0x10):
            raise OSError(errno.ELOOP, "Download destination is a reparse point or directory")
        retained = flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_BINARY | os.O_TEXT | os.O_NOINHERIT)
        descriptor = msvcrt.open_osfhandle(handle, retained | os.O_NOINHERIT)
        handle = None  # The descriptor now owns the handle, including all failure cleanup.
        information = os.fstat(descriptor)
        if not stat.S_ISREG(information.st_mode) or information.st_nlink != 1:
            raise OSError(errno.EPERM, "Download destination must be a singly linked regular file")
        if flags & os.O_TRUNC:
            os.ftruncate(descriptor, 0)
        return descriptor
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        raise
    finally:
        if handle is not None:
            close(handle)


def open_download(path: str, flags: int) -> int:
    """Purpose: Preserve platform no-follow semantics. Inputs: Upstream-confined path/flags. Outputs: Owned fd."""
    if os.name == "nt":
        return windows_descriptor(path, flags)
    return os.open(path, flags | os.O_NOFOLLOW)

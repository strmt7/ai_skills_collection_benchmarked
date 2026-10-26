"""Exercise owned filesystem, memory-handle and loopback access sentinels."""

from __future__ import annotations

import argparse
import ctypes as c
import json
import socket
import sys
from ctypes import wintypes as w
from pathlib import Path
from typing import Any


def probe(allowed: Path, sealed: Path, scratch: Path, parent: int, port: int) -> dict[str, Any]:
    if sys.platform != "win32":
        raise ValueError("The native access probe requires Windows")
    kernel, security = c.WinDLL("kernel32", use_last_error=True), c.WinDLL("advapi32", use_last_error=True)
    open_process = kernel.OpenProcess
    open_process.argtypes, open_process.restype = (w.DWORD, w.BOOL, w.DWORD), w.HANDLE
    close = kernel.CloseHandle
    close.argtypes, close.restype = (w.HANDLE,), w.BOOL
    set_acl = security.SetNamedSecurityInfoW
    set_acl.argtypes = (w.LPWSTR, c.c_int, w.DWORD, c.c_void_p, c.c_void_p, c.c_void_p, c.c_void_p)
    set_acl.restype = w.DWORD
    result: dict[str, Any] = {"allowed_read": allowed.read_text() == "permitted"}
    try:
        allowed.write_text("controlled modification")
        result["readonly_write_denied"] = False
    except PermissionError:
        result["readonly_write_denied"] = True
    try:
        sealed.read_bytes()
        result["sealed_read_denied"] = False
    except PermissionError:
        result["sealed_read_denied"] = True
    result["sealed_dacl_change_status"] = set_acl(str(sealed), 1, 4, None, None, None, None)
    handle = open_process(0x10 | 0x400, False, parent)
    result["parent_memory_access_denied"] = not bool(handle)
    result["parent_open_error"] = c.get_last_error()
    if handle:
        close(handle)
    with socket.socket() as connection:
        connection.settimeout(1)
        result["network_connect_status"] = connection.connect_ex(("127.0.0.1", port))
    (scratch / "permitted.txt").write_text("scratch write", encoding="utf-8")
    result["scratch_write"] = True
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("allowed", type=Path)
    parser.add_argument("sealed", type=Path)
    parser.add_argument("scratch", type=Path)
    parser.add_argument("parent", type=int)
    parser.add_argument("port", type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(json.dumps(probe(args.allowed, args.sealed, args.scratch, args.parent, args.port)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

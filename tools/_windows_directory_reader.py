"""Bounded native directory enumeration through held, verified workspace handles."""

from __future__ import annotations

import ctypes
import struct
from ctypes import wintypes
from dataclasses import dataclass
from typing import Any

from _trial_collection_policy import ROOT_EXCLUSIONS, collection_policy, excluded_directory
from _trial_protocol import relative_path
from _windows_submission_reader import WorkspaceReader

HEADER = struct.Struct("<II6qIII")
BUFFER_BYTES = 65536


@dataclass(frozen=True)
class DirectoryEntry:
    name: str
    attributes: int
    size: int
    written: int
    changed: int


def parse_directory_buffer(data: bytes) -> list[DirectoryEntry]:
    """Decode FILE_FULL_DIR_INFO, rejecting overlaps, truncated names and bad links."""
    result = []
    offset = 0
    while True:
        if offset + HEADER.size > len(data):
            raise ValueError("truncated native directory record")
        fields = HEADER.unpack_from(data, offset)
        following, _, _, _, written, changed, size, _, attributes, length, _ = fields
        end = offset + HEADER.size + length
        if length == 0 or length % 2 or end > len(data):
            raise ValueError("invalid native directory filename length")
        name = data[offset + HEADER.size : end].decode("utf-16-le")
        if name not in {".", ".."}:
            if any(char in name for char in "/\\:\0") or name in {"", ".", ".."}:
                raise ValueError("invalid native directory filename")
            result.append(DirectoryEntry(name, attributes, size, written, changed))
        if following == 0:
            return result
        if following % 8 or following < HEADER.size + length or offset + following >= len(data):
            raise ValueError("invalid native directory next-entry offset")
        offset += following


def directory_entries(
    reader: WorkspaceReader, name: str, *, max_entries: int = 32770, max_name_bytes: int = 16 * 1024**2
) -> list[DirectoryEntry]:
    """Read one directory in bounded native pages; never resolve entries with a path walker."""
    if not reader.enumerate_directories:
        raise ValueError("directory enumeration was not enabled")
    if type(max_entries) is not int or not 0 <= max_entries <= 32770:
        raise ValueError("directory entry budget is outside the admitted bounds")
    if type(max_name_bytes) is not int or not 0 <= max_name_bytes <= 16 * 1024**2:
        raise ValueError("directory name budget is outside the admitted bounds")
    kernel = reader.kernel
    kernel.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL
    handle = reader.directory(name)
    result: list[DirectoryEntry] = []
    restart = True
    name_bytes = 0
    # A single directory cannot exceed both admitted object-count bounds.
    while True:
        buffer = ctypes.create_string_buffer(BUFFER_BYTES)
        if not kernel.GetFileInformationByHandleEx(handle, 0xF if restart else 0xE, buffer, len(buffer)):
            code = ctypes.get_last_error()
            if code == 18:  # ERROR_NO_MORE_FILES
                return result
            raise ctypes.WinError(code)
        page = parse_directory_buffer(buffer.raw)
        name_bytes += sum(len(entry.name.encode("utf-8")) for entry in page)
        if name_bytes > max_name_bytes:
            raise ValueError("workspace path bytes exceed the frozen limit")
        result.extend(page)
        if len(result) > max_entries:
            raise ValueError("directory entry count exceeds the admitted object limit")
        restart = False


def inventory(
    reader: WorkspaceReader, declared: dict[str, Any]
) -> tuple[dict[str, DirectoryEntry], list[dict[str, str]], list[str]]:
    """Inspect a complete source namespace with explicit runtime/cache omissions."""
    policy = collection_policy(declared)
    files: dict[str, DirectoryEntry] = {}
    exclusions: list[dict[str, str]] = []
    selected_directories: list[str] = []
    directories = 0
    total = 0
    path_bytes = 0
    identities: set[str] = set()
    pending = [("", 0)]
    while pending:
        directory, depth = pending.pop()
        if depth > policy["max_depth"]:
            raise ValueError("workspace directory depth exceeds the frozen limit")
        remaining = policy["max_files"] + policy["max_directories"] + len(ROOT_EXCLUSIONS) - len(identities)
        for entry in directory_entries(
            reader, directory, max_entries=remaining, max_name_bytes=policy["max_total_path_bytes"] - path_bytes
        ):
            name = directory + "/" + entry.name if directory else entry.name
            path_bytes += len(name.encode("utf-8"))
            if path_bytes > policy["max_total_path_bytes"]:
                raise ValueError("workspace path bytes exceed the frozen limit")
            identity = name.casefold()
            if identity in identities:
                raise ValueError("workspace contains duplicate or conflicting file identities")
            identities.add(identity)
            if entry.attributes & 0x400:
                raise ValueError("workspace contains a reparse point")
            if not directory and name.casefold() in ROOT_EXCLUSIONS:
                exclusions.append({"path": name, "reason": ROOT_EXCLUSIONS[name.casefold()]})
                continue
            if entry.attributes & 0x10:
                if depth + 1 > policy["max_depth"]:
                    raise ValueError("workspace directory depth exceeds the frozen limit")
                directories += 1
                if directories > policy["max_directories"]:
                    raise ValueError("workspace directory count exceeds the frozen limit")
                if reason := excluded_directory(name, policy):
                    exclusions.append({"path": name, "reason": reason})
                else:
                    relative_path(name, workspace=True)
                    selected_directories.append(name)
                    pending.append((name, depth + 1))
                continue
            relative_path(name, workspace=True)
            if len(files) >= policy["max_files"] or not 0 <= entry.size <= policy["max_file_bytes"]:
                raise ValueError("workspace file count or size exceeds the frozen limit")
            total += entry.size
            if total > policy["max_total_bytes"]:
                raise ValueError("workspace bytes exceed the frozen limit")
            files[name] = entry
    return dict(sorted(files.items())), sorted(exclusions, key=lambda item: item["path"]), sorted(selected_directories)

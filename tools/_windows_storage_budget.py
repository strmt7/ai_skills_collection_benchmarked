"""Bounded observations of caller-available space and a stopped workspace's data streams."""

from __future__ import annotations

import ctypes
import struct
import time
from ctypes import wintypes
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from _windows_appcontainer import Native, checked_path, last_error, set_last_error, win_error
from _windows_directory_reader import directory_entries
from _windows_submission_reader import WorkspaceReader

STREAM_HEADER = struct.Struct("<IIqq")
STREAM_BUFFER_BYTES = 65536
MAX_PATH_BYTES = 4 * 1024**2
MAX_DEPTH = 64
SPACE_POLL_SECONDS = 0.5


@dataclass(frozen=True)
class StorageLimits:
    """Explicit plan limits; these are observations, not filesystem quotas."""

    min_free_bytes: int
    max_workspace_bytes: int
    max_workspace_entries: int

    def __post_init__(self) -> None:
        values = asdict(self)
        bounds = {"min_free_bytes": 1024**4, "max_workspace_bytes": 1024**3, "max_workspace_entries": 65536}
        if any(type(value) is not int or not 0 < value <= bounds[name] for name, value in values.items()):
            raise ValueError("Storage limits require positive integers within the admitted bounds")

    @classmethod
    def from_record(cls, value: Any) -> StorageLimits:
        if not isinstance(value, dict) or set(value) != set(cls.__dataclass_fields__):
            raise ValueError("A complete explicit storage-limit record is required")
        return cls(**value)


class WorkspaceStorageExceeded(ValueError):
    """A bounded partial observation proves that the workspace exceeded a limit."""

    def __init__(self, reason: str, observation: dict[str, Any]):
        super().__init__(reason)
        self.reason = reason
        self.observation = dict(observation)


def verify_workspace_measurement(record: Any, limits: StorageLimits) -> None:
    """Admit only a complete, internally consistent observation within the frozen limits."""
    counters = {"logical_bytes", "entries", "files", "directories", "streams"}
    if (
        not isinstance(record, dict)
        or set(record) != counters | {"complete", "measurement"}
        or record["complete"] is not True
        or record["measurement"] != "stopped_workspace_data_stream_lengths"
        or any(type(record[key]) is not int or record[key] < 0 for key in counters)
        or record["entries"] != record["files"] + record["directories"] + record["streams"]
        or record["entries"] > limits.max_workspace_entries
        or record["logical_bytes"] > limits.max_workspace_bytes
    ):
        raise ValueError("Workspace storage observation is incomplete, inconsistent or outside the frozen limits")


def available_space(path: Path) -> dict[str, int]:
    """Query unsigned 64-bit caller and volume values at this actual location."""
    path = checked_path(path)
    values = [ctypes.c_ulonglong() for _ in range(3)]
    query = Native().function(
        "kernel", "GetDiskFreeSpaceExW", [wintypes.LPCWSTR, *([ctypes.POINTER(ctypes.c_ulonglong)] * 3)], wintypes.BOOL
    )
    if not query(str(path), *(ctypes.byref(value) for value in values)):
        raise win_error(last_error())
    return dict(zip(("available_bytes", "total_bytes", "volume_free_bytes"), (v.value for v in values), strict=True))


class SpaceBudget:
    """Latch low-space and observation failures without repeatedly walking files."""

    def __init__(self, limits: StorageLimits, paths: tuple[Path, ...]):
        if not 1 <= len(paths) <= 8:
            raise ValueError("A space budget requires one to eight explicit writable locations")
        self.limits = limits
        self.paths = tuple(dict.fromkeys(checked_path(path) for path in paths))
        self.samples: dict[str, dict[str, int]] = {}
        self.polls = 0
        self.error: dict[str, Any] | None = None
        self.reason: str | None = None
        self._next_poll = 0.0

    def check(self, *, force: bool = False) -> str | None:
        if self.reason is not None:
            return self.reason
        now = time.monotonic()
        if not force and now < self._next_poll:
            return None
        self._next_poll = now + SPACE_POLL_SECONDS
        self.polls += 1
        for path in self.paths:
            name = str(path)
            try:
                sample = available_space(path)
            except (OSError, ValueError) as error:
                self.error = {
                    "api": "GetDiskFreeSpaceExW",
                    "path": name,
                    "error_type": type(error).__name__,
                    "winerror": getattr(error, "winerror", None),
                }
                self.reason = "storage_observation_error"
                return self.reason
            previous = self.samples.get(name)
            self.samples[name] = {
                **sample,
                "lowest_available_bytes": min(
                    sample["available_bytes"],
                    previous["lowest_available_bytes"] if previous else sample["available_bytes"],
                ),
            }
            if sample["available_bytes"] < self.limits.min_free_bytes:
                self.reason = "free_space_limit"
                return self.reason
        return None

    def require_available(self) -> None:
        if reason := self.check(force=True):
            raise ValueError("Storage budget interrupted execution: " + reason)

    def record(self) -> dict[str, Any]:
        return {
            "min_free_bytes": self.limits.min_free_bytes,
            "paths": [str(path) for path in self.paths],
            "samples": {name: dict(value) for name, value in self.samples.items()},
            "polls": self.polls,
            "observation_error": dict(self.error) if self.error is not None else None,
            "termination_reason": self.reason,
            "poll_interval_seconds": SPACE_POLL_SECONDS,
            "enforcement": "polled_caller_available_space",
            "hard_storage_quota": False,
        }


def parse_stream_buffer(data: bytes) -> dict[str, int]:
    """Decode FILE_STREAM_INFO without accepting malformed offsets or duplicate streams."""
    offset = 0
    streams: dict[str, int] = {}
    while True:
        if offset + STREAM_HEADER.size > len(data):
            raise ValueError("Truncated native stream record")
        following, length, size, allocation = STREAM_HEADER.unpack_from(data, offset)
        end = offset + STREAM_HEADER.size + length
        if not length or length % 2 or end > len(data) or size < 0 or allocation < 0:
            raise ValueError("Invalid native stream length or size")
        name = data[offset + STREAM_HEADER.size : end].decode("utf-16-le")
        identity = name.casefold()
        if not name.startswith(":") or not name.endswith(":$DATA") or "\0" in name or identity in streams:
            raise ValueError("Invalid or duplicate native data stream")
        streams[identity] = size
        if following == 0:
            return streams
        if following % 8 or following < STREAM_HEADER.size + length or offset + following >= len(data):
            raise ValueError("Invalid native stream next-entry offset")
        offset += following


def data_streams(reader: WorkspaceReader, handle: Any) -> dict[str, int]:
    """Query the held object once with a fixed buffer; unsupported metadata is an error."""
    query = reader.kernel.GetFileInformationByHandleEx
    query.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    query.restype = wintypes.BOOL
    buffer = ctypes.create_string_buffer(STREAM_BUFFER_BYTES)
    set_last_error(0)
    succeeded = query(handle, 7, buffer, len(buffer))
    code = last_error()
    if code == 38:  # ERROR_HANDLE_EOF is documented even when the call succeeds with no streams.
        if buffer.raw.strip(b"\0"):
            raise ValueError("Native stream EOF contradicts nonempty metadata")
        return {}
    if not succeeded:
        raise win_error(code)
    return parse_stream_buffer(buffer.raw)


def measure_workspace(path: Path, limits: StorageLimits) -> dict[str, Any]:
    """Inspect all stopped-workspace entries and streams, including caches and root streams.

    Call only after all subject processes stop. Held handles deliberately prevent
    replacement while measuring. Logical stream lengths are not physical allocation.
    No file content is read, followed through a reparse point, modified or deleted.
    """
    observation: dict[str, Any] = {
        "complete": False,
        "logical_bytes": 0,
        "entries": 0,
        "files": 0,
        "directories": 0,
        "streams": 0,
        "measurement": "stopped_workspace_data_stream_lengths",
    }
    identities: set[str] = set()
    path_bytes = 0

    def admit() -> None:
        if observation["entries"] > limits.max_workspace_entries:
            raise WorkspaceStorageExceeded("workspace_entries_limit", observation)
        if observation["logical_bytes"] > limits.max_workspace_bytes:
            raise WorkspaceStorageExceeded("workspace_logical_bytes_limit", observation)

    def account_streams(reader: WorkspaceReader, handle: Any, expected_size: int | None = None) -> None:
        streams = data_streams(reader, handle)
        if expected_size is not None and streams.get("::$data", 0) != expected_size:
            raise ValueError("Default stream length differs from held file metadata")
        for size in streams.values():
            observation["logical_bytes"] += size
            observation["streams"] += 1
            observation["entries"] += 1
            admit()

    with WorkspaceReader(path, enumerate_directories=True) as reader:
        account_streams(reader, reader.directory())
        pending = [("", 0)]
        while pending:
            directory, depth = pending.pop()
            remaining = limits.max_workspace_entries - observation["entries"]
            for entry in directory_entries(
                reader, directory, max_entries=min(32770, remaining + 1), max_name_bytes=MAX_PATH_BYTES - path_bytes
            ):
                name = directory + "/" + entry.name if directory else entry.name
                path_bytes += len(name.encode("utf-8"))
                if path_bytes > MAX_PATH_BYTES or depth + 1 > MAX_DEPTH:
                    raise ValueError("Workspace path or depth exceeds the storage observation bound")
                identity = name.casefold()
                if identity in identities or entry.attributes & 0x400:
                    raise ValueError("Workspace contains a duplicate identity or reparse point")
                identities.add(identity)
                observation["entries"] += 1
                admit()
                if entry.attributes & 0x10:
                    observation["directories"] += 1
                    account_streams(reader, reader.directory(name))
                    pending.append((name, depth + 1))
                else:
                    observation["files"] += 1
                    _, handle, size = reader.open_file_metadata(name)
                    if size != entry.size:
                        raise ValueError("Workspace file size changed during stopped observation")
                    account_streams(reader, handle, size)
    observation["complete"] = True
    return observation

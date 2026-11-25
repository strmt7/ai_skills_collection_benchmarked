"""Deterministic, atomic I/O helpers for Batch B generators.

The goals are:
- byte-identical output on re-runs (sorted keys, LF-only, trailing newline)
- crash-safe writes (write to temp file + os.replace)
- no absolute paths leaking into generated content

References:
- https://reproducible-builds.org/docs/stable-outputs/
- https://python-atomicwrites.readthedocs.io/
- https://docs.python.org/3/library/os.html#os.replace
"""

from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
from time import sleep
from typing import Any
from uuid import uuid4


def _replace_file(source: Path, target: Path) -> None:
    # Windows can temporarily reject an atomic rename during another rename or open.
    for delay in (0.01, 0.03, 0.09):
        try:
            os.replace(source, target)
            return
        except PermissionError as error:
            if getattr(error, "winerror", None) not in {5, 32, 33}:
                raise
            sleep(delay)
    os.replace(source, target)


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write one complete artifact using a private staging file on the same filesystem."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".write-{uuid4().hex}.tmp")
    handle = temporary.open("xb")
    try:
        with handle:
            handle.write(data)
            handle.flush()
            # Some filesystems do not support fsync.
            with contextlib.suppress(OSError):
                os.fsync(handle.fileno())
        _replace_file(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def dumps_deterministic(data: Any) -> str:
    """Canonical JSON: UTF-8, indent=2, sort_keys, trailing newline, LF only."""
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_json(path: Path, data: Any) -> None:
    """Write JSON deterministically and atomically."""
    _atomic_write_bytes(path, dumps_deterministic(data).encode("utf-8"))


def write_text(path: Path, text: str) -> None:
    """Write text atomically, normalizing to LF line endings."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    _atomic_write_bytes(path, normalized.encode("utf-8"))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def as_relative_posix(path: Path, root: Path) -> str:
    """Return *path* as a relative, forward-slash POSIX string under *root*.

    Used to keep emitted paths host- and installation-agnostic.
    """
    return path.resolve().relative_to(root.resolve()).as_posix()

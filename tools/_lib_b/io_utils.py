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

import json
import os
from pathlib import Path
from typing import Any


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Write *data* to *path* via a temp file in the same directory + os.replace.

    os.replace is atomic on POSIX and Windows, so readers either see the old
    content or the new content but never a truncated file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as handle:
        handle.write(data)
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except OSError:
            # Best-effort: fsync may be unsupported on some filesystems.
            pass
    os.replace(tmp, path)


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

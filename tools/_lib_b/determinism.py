"""Resolve stable timestamps and catalog commits for deterministic runs.

Precedence rules (highest first):

    timestamp:
        1. env SOURCE_DATE_EPOCH (seconds since 1970-01-01Z), per
           https://reproducible-builds.org/docs/source-date-epoch/
        2. existing manifest's "generated_at_utc" (idempotent regeneration)
        3. caller-provided fallback (e.g. git commit time of the input data)

    catalog commit:
        1. env CATALOG_COMMIT (explicit pin)
        2. existing manifest's "catalog_commit" (idempotent regeneration)
        3. `git rev-parse HEAD` of the caller-supplied root (last resort)

These helpers never call `datetime.now()` or any wall-clock API.
"""

from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _iso_z(epoch_seconds: int) -> str:
    return (
        datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def source_date_epoch() -> int | None:
    value = os.environ.get("SOURCE_DATE_EPOCH")
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def resolve_timestamp(
    *,
    existing_manifest_value: str | None = None,
    fallback_epoch: int | None = None,
) -> str:
    epoch = source_date_epoch()
    if epoch is not None:
        return _iso_z(epoch)
    if existing_manifest_value:
        return existing_manifest_value
    if fallback_epoch is not None:
        return _iso_z(fallback_epoch)
    raise RuntimeError(
        "Cannot resolve a deterministic timestamp: set SOURCE_DATE_EPOCH, "
        "pass a pre-existing manifest value, or pass a fallback_epoch."
    )


def resolve_catalog_commit(
    *,
    root: Path,
    existing_manifest_value: str | None = None,
) -> str:
    pinned = os.environ.get("CATALOG_COMMIT")
    if pinned and _SHA_RE.match(pinned):
        return pinned
    if existing_manifest_value and _SHA_RE.match(existing_manifest_value):
        return existing_manifest_value
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    if not _SHA_RE.match(head):
        raise RuntimeError(f"git rev-parse HEAD returned unexpected value: {head!r}")
    return head


def git_latest_commit_epoch_for(root: Path, paths: list[Path]) -> int | None:
    """Return the latest committer-UNIX-time among commits touching *paths*.

    Useful as a deterministic fallback timestamp that reflects the inputs,
    not the current wall clock.
    """
    if not paths:
        return None
    rel = [str(p.resolve().relative_to(root.resolve())) for p in paths]
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "log", "-1", "--format=%ct", "--", *rel],
            text=True,
        ).strip()
    except subprocess.CalledProcessError:
        return None
    if not out:
        return None
    try:
        return int(out)
    except ValueError:
        return None


def existing_field(manifest_path: Path, *keys: str) -> Any:
    """Return manifest_path[keys[0]][keys[1]]... if the file exists, else None."""
    if not manifest_path.is_file():
        return None
    import json

    try:
        data: Any = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
        if data is None:
            return None
    return data

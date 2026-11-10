"""Render bounded diagnostic diffs; captured file bytes remain authoritative."""

from __future__ import annotations

import difflib
import time
from collections.abc import Callable
from typing import Any


def diagnostic_patch(
    original: dict[str, bytes],
    manifest: dict[str, Any],
    changes: list[dict[str, Any]],
    read: Callable[[str], bytes],
) -> tuple[bytes, dict[str, Any]]:
    """Omit expensive/binary diffs explicitly without losing their captured blobs."""
    output = bytearray()
    omitted: list[str] = []
    started = time.monotonic()
    for change in changes:
        if change["object"] != "file":
            continue
        name = change["path"]
        before = original.get(name, b"")
        size = manifest["files"].get(name, {}).get("bytes", 0)
        if len(before) > 128 * 1024 or size > 128 * 1024 or time.monotonic() - started > 2:
            omitted.append(name)
            continue
        after = read(name) if change["kind"] != "deleted" else b""
        if b"\0" in before or b"\0" in after:
            omitted.append(name)
            continue
        try:
            left, right = before.decode("utf-8").splitlines(True), after.decode("utf-8").splitlines(True)
        except UnicodeError:
            omitted.append(name)
            continue
        if len(left) > 2048 or len(right) > 2048:
            omitted.append(name)
            continue
        lines = difflib.unified_diff(
            left,
            right,
            fromfile="/dev/null" if change["kind"] == "created" else f"a/{name}",
            tofile="/dev/null" if change["kind"] == "deleted" else f"b/{name}",
        )
        encoded = "".join(lines).encode("utf-8")
        if len(output) + len(encoded) > 4 * 1024**2:
            omitted.append(name)
            continue
        output.extend(encoded)
    return bytes(output), {
        "format": "diagnostic_unified_diff_v1",
        "complete": not omitted,
        "omitted_paths": omitted,
        "authority": "Captured files and namespace changes; this bounded view is not an external-suite patch adapter.",
    }

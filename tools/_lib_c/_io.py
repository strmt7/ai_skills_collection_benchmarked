"""Deterministic, UTF-8 JSON/text IO helpers.

All writers emit sorted-key JSON with a trailing newline. This matches the
format committed across the repository and ensures byte-identical output on
repeated runs (RFC 8785-style canonicalisation is not required here because
the existing repo convention is `sort_keys=True` + 2-space indent + trailing
newline, which `json.dumps` produces deterministically for JSON-native
values).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_canonical(path: Path, data: Any) -> None:
    """Write ``data`` as sorted-key, 2-indent JSON with a trailing newline.

    The helper is the only supported writer for generated data files so that
    repeated runs on unchanged inputs produce byte-identical bytes (see
    ``tests/test_static_benchmarks_*`` for the determinism property test).
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    path.write_text(payload, encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

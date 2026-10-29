"""Validate unambiguous identities before consuming catalog or source records."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def require_unique(records: Iterable[dict[str, Any]], key: str, value: str, label: str) -> dict[str, Any]:
    """Return the sole matching record or reject missing and duplicate identities."""
    matches = [record for record in records if record[key] == value]
    if len(matches) != 1:
        raise ValueError(f"{label} must have one {key} record")
    return matches[0]

"""Drift-detection helpers.

The audit/evaluator tools run in two modes: **write** (regenerate outputs)
and **check** (verify committed outputs match what a fresh run would produce).
When ``--check`` fails, operators need to see *what* drifted, not just that
something did. The helpers here produce compact, sortable drift records so
CI logs remain legible even when hundreds of entries change at once.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import Any

_MAX_ENTRIES = 50  # cap shown diffs so CI logs stay bounded


@dataclass
class DriftReport:
    label: str
    entries: list[str] = field(default_factory=list)

    @property
    def is_stale(self) -> bool:
        return bool(self.entries)

    def render(self) -> str:
        if not self.entries:
            return f"{self.label}: current"
        shown = self.entries[:_MAX_ENTRIES]
        suffix = ""
        if len(self.entries) > _MAX_ENTRIES:
            suffix = f"\n  ... {len(self.entries) - _MAX_ENTRIES} more drift entries suppressed"
        body = "\n  - ".join(shown)
        return f"{self.label}: stale ({len(self.entries)} differences)\n  - {body}{suffix}"


def _format_scalar(value: Any) -> str:
    text = repr(value)
    if len(text) > 80:
        text = text[:77] + "..."
    return text


def describe_data_drift(label: str, current: Any, fresh: Any) -> DriftReport:
    """Walk two JSON-like structures and return compact drift descriptors.

    Returned entries have the form ``path: current_repr -> fresh_repr`` so the
    operator can locate the exact field that changed without re-running.
    """

    entries: list[str] = []

    def walk(a: Any, b: Any, path: str) -> None:
        if type(a) is not type(b):
            entries.append(f"{path or '<root>'}: type {type(a).__name__} -> {type(b).__name__}")
            return
        if isinstance(a, dict):
            keys = sorted(set(a) | set(b))
            for key in keys:
                child = f"{path}.{key}" if path else key
                if key not in a:
                    entries.append(f"{child}: <missing> -> {_format_scalar(b[key])}")
                elif key not in b:
                    entries.append(f"{child}: {_format_scalar(a[key])} -> <missing>")
                else:
                    walk(a[key], b[key], child)
        elif isinstance(a, list):
            if len(a) != len(b):
                entries.append(f"{path or '<root>'}: list length {len(a)} -> {len(b)}")
            for idx, (x, y) in enumerate(zip(a, b, strict=False)):
                walk(x, y, f"{path}[{idx}]")
        else:
            if a != b:
                entries.append(f"{path or '<root>'}: {_format_scalar(a)} -> {_format_scalar(b)}")

    walk(current, fresh, "")
    return DriftReport(label=label, entries=entries)


def describe_text_drift(label: str, current: str, fresh: str) -> DriftReport:
    """Return a short unified diff describing text-file drift."""

    if current == fresh:
        return DriftReport(label=label, entries=[])
    diff = list(
        difflib.unified_diff(
            current.splitlines(),
            fresh.splitlines(),
            fromfile="committed",
            tofile="fresh",
            lineterm="",
            n=1,
        )
    )
    return DriftReport(label=label, entries=diff)

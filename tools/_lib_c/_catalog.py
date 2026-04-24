"""Tiny accessors for the committed catalog / manifest / scenario data.

The evaluator/audit tools load the same files repeatedly. Funnelling the
loads through one module keeps read paths centralised and lets tests fake
them without touching every call site.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_catalog(root: Path) -> list[dict[str, Any]]:
    return _load(root / "data" / "skills_catalog.json")


def load_manifest(root: Path) -> dict[str, dict[str, Any]]:
    manifest = _load(root / "included" / "skills" / "manifest.json")
    return {entry["id"]: entry for entry in manifest}


def load_scenarios(root: Path) -> dict[str, dict[str, Any]]:
    scenarios = _load(root / "data" / "benchmark_scenarios.json")
    return {item["id"]: item for item in scenarios}

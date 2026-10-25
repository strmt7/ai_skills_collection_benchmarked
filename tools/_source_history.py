"""Resolve recorded source versions without assigning old evidence to new pins."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import _catalog_publication as publication
import build_catalog


def historical_entries(root: Path) -> list[dict[str, Any]]:
    path = publication.checked_path(root, "data/catalog_source_history.json")
    if not path.exists():
        return []
    history = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(history, dict) or history.get("schema_version") != 1:
        raise ValueError("unsupported source history schema")
    records = history.get("versions")
    if not isinstance(records, list):
        raise ValueError("source history versions must be a list")
    entries = []
    identities = set()
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("entry"), dict):
            raise ValueError("source history requires a catalog entry")
        entry = record["entry"]
        for field in ("id", "source_repo", "source_path", "mirrored_path", "commit_sha", "skill_file_sha256"):
            if not isinstance(entry.get(field), str) or not entry[field]:
                raise ValueError(f"source history requires entry.{field}")
        if not re.fullmatch(r"[0-9a-f]{40}", entry["commit_sha"]) or not re.fullmatch(
            r"[0-9a-f]{64}", entry["skill_file_sha256"]
        ):
            raise ValueError("source history requires exact source hashes")
        scenarios = entry.get("benchmark_scenarios")
        if not isinstance(scenarios, list) or not scenarios or any(not isinstance(item, str) for item in scenarios):
            raise ValueError("source history requires scenario assignments")
        for field, length in (("observed_catalog_revision", 40), ("observed_catalog_sha256", 64)):
            value = record.get(field)
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{" + str(length) + r"}", value):
                raise ValueError(f"source history requires {field}")
        identity = (entry["id"], entry["commit_sha"])
        if identity in identities:
            raise ValueError("duplicate historical source identity")
        identities.add(identity)
        name = record.get("skill_snapshot")
        if not isinstance(name, str) or not name.startswith("artifacts/source-history/"):
            raise ValueError("source history snapshot must stay inside artifacts/source-history")
        snapshot = publication.checked_path(root, name)
        if not snapshot.is_file() or snapshot.stat().st_size > 1024 * 1024:
            raise ValueError("historical source snapshot missing or too large")
        if hashlib.sha256(snapshot.read_bytes()).hexdigest() != record.get("skill_snapshot_sha256"):
            raise ValueError("historical source snapshot bytes changed")
        if build_catalog.sha256_file(snapshot) != entry["skill_file_sha256"]:
            raise ValueError("historical source snapshot differs from catalog source hash")
        build_catalog.validate_preserved_notice(root, record.get("preserved_notice"), entry["commit_sha"])
        entries.append(entry)
    return entries


def resolve_entry(
    root: Path, current: dict[str, Any] | None, skill_id: str, source_commit: str
) -> tuple[dict[str, Any], bool]:
    if current is not None and current["id"] == skill_id and current["commit_sha"] == source_commit:
        return current, False
    for entry in historical_entries(root):
        if entry["id"] == skill_id and entry["commit_sha"] == source_commit:
            return entry, True
    raise ValueError("source_commit does not match catalog commit_sha or a validated historical source")

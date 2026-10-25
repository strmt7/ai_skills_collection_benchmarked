"""Resolve recorded source versions without assigning old evidence to new pins."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import _catalog_publication as publication
import build_catalog


def historical_versions(root: Path) -> list[dict[str, Any]]:
    path = publication.checked_path(root, "data/catalog_source_history.json")
    if not path.exists():
        return []
    history = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(history, dict) or history.get("schema_version") != 1:
        raise ValueError("unsupported source history schema")
    records = history.get("versions")
    if not isinstance(records, list):
        raise ValueError("source history versions must be a list")
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
        license_texts = record.get("license_texts", [])
        if not isinstance(license_texts, list):
            raise ValueError("historical license texts must be a list")
        for notice in license_texts:
            if (
                not isinstance(notice, dict)
                or not isinstance(notice.get("path"), str)
                or not notice["path"].startswith("artifacts/source-notices/")
                or not isinstance(notice.get("source_url"), str)
                or not notice["source_url"].startswith("https://")
            ):
                raise ValueError("historical license text requires an owned path and source URL")
            file = publication.checked_path(root, notice["path"])
            if (
                not file.is_file()
                or file.stat().st_size > 1024 * 1024
                or hashlib.sha256(file.read_bytes()).hexdigest() != notice.get("sha256")
            ):
                raise ValueError("historical license text bytes changed or missing")
        if "scenarios" in record:
            definitions = record["scenarios"]
            if (
                not isinstance(definitions, list)
                or any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in definitions)
                or len({item["id"] for item in definitions}) != len(definitions)
                or {item["id"] for item in definitions} != set(scenarios)
                or not re.fullmatch(r"[0-9a-f]{64}", str(record.get("observed_scenarios_sha256", "")))
            ):
                raise ValueError("historical scenario definitions differ from recorded assignments")
    return records


def historical_entries(root: Path) -> list[dict[str, Any]]:
    return [record["entry"] for record in historical_versions(root)]


def resolve_version(
    root: Path, current: dict[str, Any] | None, skill_id: str, source_commit: str
) -> tuple[dict[str, Any], bool]:
    if current is not None and current["id"] == skill_id and current["commit_sha"] == source_commit:
        return {"entry": current}, False
    for record in historical_versions(root):
        if record["entry"]["id"] == skill_id and record["entry"]["commit_sha"] == source_commit:
            return record, True
    raise ValueError("source_commit does not match catalog commit_sha or a validated historical source")


def resolve_entry(
    root: Path, current: dict[str, Any] | None, skill_id: str, source_commit: str
) -> tuple[dict[str, Any], bool]:
    record, historical = resolve_version(root, current, skill_id, source_commit)
    return record["entry"], historical

"""Enforce recorded source-version holds without treating them as license clearance."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import _catalog_publication as publication


def source_holds(root: Path) -> list[dict[str, Any]]:
    path = publication.checked_path(root, "data/source_admission_holds.json")
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("holds"), list):
        raise ValueError("invalid source admission hold registry")
    seen = set()
    for item in data["holds"]:
        fields = ("source_repo", "source_commit", "reason", "evidence_path", "sha256")
        if not isinstance(item, dict) or any(not isinstance(item.get(key), str) or not item[key] for key in fields):
            raise ValueError("source admission hold requires identity, reason and evidence")
        if not re.fullmatch(r"[0-9a-f]{40}", item["source_commit"]) or not re.fullmatch(
            r"[0-9a-f]{64}", item["sha256"]
        ):
            raise ValueError("source admission hold requires immutable hashes")
        identity = (item["source_repo"], item["source_commit"])
        if identity in seen:
            raise ValueError("duplicate source admission hold")
        seen.add(identity)
        if not item["evidence_path"].startswith("artifacts/research/"):
            raise ValueError("source admission evidence must be inside artifacts/research")
        evidence_path = publication.checked_path(root, item["evidence_path"])
        if not evidence_path.is_file() or evidence_path.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("source admission evidence missing or exceeds its byte budget")
        raw = evidence_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError("source admission evidence hash mismatch")
        evidence = json.loads(raw)
        if (
            not isinstance(evidence, dict)
            or (evidence.get("source_repo"), evidence.get("source_commit")) != identity
            or evidence.get("source_candidate_state") != "held_before_publication"
        ):
            raise ValueError("source admission evidence does not describe the held version")
    return data["holds"]


def require_admitted_source(root: Path, repo: str, commit: str) -> None:
    for item in source_holds(root):
        if (item["source_repo"], item["source_commit"]) == (repo, commit):
            raise ValueError(f"source admission held for {repo}@{commit}: {item['reason']}")

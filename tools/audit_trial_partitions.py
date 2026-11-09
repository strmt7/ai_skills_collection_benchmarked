"""Audit declared development and holdout task overlap before running trials."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from _trial_declarations import declared_task_signatures
from _trial_transcript import strict_json


def audit(path: Path) -> dict[str, Any]:
    """Compare pinned protocols and candidate records; neither proves independence."""
    raw = path.read_bytes()
    manifest = strict_json(raw.decode("utf-8"))
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"schema_version", "tasks"}
        or type(manifest["schema_version"]) is not int
        or manifest["schema_version"] not in {1, 2}
        or not isinstance(manifest["tasks"], list)
        or not manifest["tasks"]
    ):
        raise ValueError("Invalid partition manifest")
    tasks = []
    identities: set[tuple[str, str]] = set()
    for entry in manifest["tasks"]:
        if not isinstance(entry, dict):
            raise ValueError("Invalid partition task")
        kind = entry.get("kind") if manifest["schema_version"] == 2 else "protocol"
        shared = {"id", "partition", "groups"} | ({"kind"} if manifest["schema_version"] == 2 else set())
        fields = {"protocol", "protocol_sha256"} if kind == "protocol" else {"source_record", "source_record_sha256"}
        if kind not in {"protocol", "candidate"} or set(entry) != shared | fields:
            raise ValueError("Invalid partition task")
        if any(not isinstance(entry[key], str) or not entry[key].strip() for key in ("id", "partition")):
            raise ValueError("Task ID and partition must be nonempty strings")
        if entry["partition"] not in {"development", "holdout"}:
            raise ValueError("Partition must be development or holdout")
        groups = entry["groups"]
        if (
            not isinstance(groups, list)
            or not groups
            or any(not isinstance(group, str) or not group.strip() or group != group.strip() for group in groups)
            or len(set(groups)) != len(groups)
        ):
            raise ValueError("Each task needs unique nonempty source groups")
        identity = (entry["partition"], entry["id"])
        if identity in identities:
            raise ValueError("Duplicate task ID within partition")
        identities.add(identity)
        record_key = "protocol" if kind == "protocol" else "source_record"
        record_path = entry[record_key]
        if not isinstance(record_path, str) or not record_path.strip():
            raise ValueError("Task record path must be a nonempty string")
        record_raw = (path.parent / record_path).read_bytes()
        digest = hashlib.sha256(record_raw).hexdigest()
        if entry[f"{record_key}_sha256"] != digest:
            raise ValueError(f"{record_key.replace('_', ' ').capitalize()} digest mismatch")
        record = strict_json(record_raw.decode("utf-8"))
        if not isinstance(record, dict):
            raise ValueError("Invalid task record")
        task_signature: str | None = None
        workspace_signature: str | None = None
        if kind == "protocol":
            if not isinstance(record.get("task"), dict):
                raise ValueError("Invalid task protocol")
            if record["task"].get("id") != entry["id"] or record["task"].get("partition") != entry["partition"]:
                raise ValueError("Protocol task identity or partition differs from manifest")
            task_signature, workspace_signature = declared_task_signatures(record)
            inputs = set(record["input_sha256"].values())
        else:
            if entry["partition"] != "development":
                raise ValueError("Unfrozen candidates must be development tasks")
            repo = record.get("repository")
            commit = record.get("source_commit", record.get("commit"))
            source = record.get("source_file", record.get("path"))
            source_hash = record.get("source_sha256", record.get("sha256"))
            if (
                not isinstance(repo, str)
                or not re.fullmatch(r"[^/\s]+/[^/\s]+", repo)
                or not isinstance(commit, str)
                or not re.fullmatch(r"[0-9a-f]{40}", commit)
                or not isinstance(source, str)
                or not source.strip()
                or not isinstance(source_hash, str)
                or not re.fullmatch(r"[0-9a-f]{64}", source_hash)
            ):
                raise ValueError("Candidate source record lacks pinned source identity")
            inputs = {source_hash}
        tasks.append(
            {
                "id": entry["id"],
                "partition": entry["partition"],
                "kind": kind,
                "groups": set(groups),
                "task_signature": task_signature,
                "workspace_signature": workspace_signature,
                "input_digests": inputs,
            }
        )
    if path.read_bytes() != raw:
        raise ValueError("Partition manifest changed during verification")
    development = [task for task in tasks if task["partition"] == "development"]
    holdout = [task for task in tasks if task["partition"] == "holdout"]
    overlaps = []
    for left in development:
        for right in holdout:
            reasons = []
            if left["id"] == right["id"]:
                reasons.append("same_task_id")
            if left["groups"] & right["groups"]:
                reasons.append("shared_declared_group")
            if left["task_signature"] is not None and left["task_signature"] == right["task_signature"]:
                reasons.append("same_declared_task")
            if left["workspace_signature"] is not None and left["workspace_signature"] == right["workspace_signature"]:
                reasons.append("same_declared_workspace")
            if left["input_digests"] <= right["input_digests"] or right["input_digests"] <= left["input_digests"]:
                reasons.append("input_content_subset")
            if reasons:
                overlaps.append({"development_id": left["id"], "holdout_id": right["id"], "reasons": reasons})
    status = "incomplete" if not development or not holdout else "overlap" if overlaps else "review_required"
    return {
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
        "development_tasks": len(development),
        "development_candidates": sum(task["kind"] == "candidate" for task in development),
        "holdout_tasks": len(holdout),
        "status": status,
        "potential_overlaps": overlaps,
        "limitations": [
            "Group membership is declared, not independently verified; undeclared or semantic overlap may be missed.",
            "A content subset can be ordinary shared files and requires review; it is not proof of contamination.",
            "This audit cannot establish holdout secrecy, prior model exposure, independence, or benchmark superiority.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = audit(args.manifest)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

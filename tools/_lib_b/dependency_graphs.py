"""Explicit, hash-bound whole npm graphs; ordinary hashing never repairs inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from _catalog_publication import checked_path

ROOT = Path(__file__).resolve().parents[2]


def graph_for(repo: str, commit: str, source_path: str, *, root: Path = ROOT) -> dict[str, Any] | None:
    registry = checked_path(root, "data/dependency_graphs.json")
    if not registry.exists():
        return None
    matches = [
        record
        for record in json.loads(registry.read_text(encoding="utf-8"))["graphs"]
        if (record["source_repo"], record["source_commit"], record["source_path"]) == (repo, commit, source_path)
    ]
    if len(matches) > 1:
        raise ValueError("duplicate dependency graph source identity")
    return matches[0] if matches else None


def replacements(source: Path, record: dict[str, Any], *, root: Path = ROOT) -> dict[str, bytes]:
    """Reject changed original or qualified graph; apply no field-level patches."""
    if set(record["files"]) != {"package.json", "package-lock.json"}:
        raise ValueError("dependency graph must replace the complete declaration/lock pair")
    result = {}
    for name, evidence in record["files"].items():
        original = checked_path(source, name).read_bytes()
        # Raw upstream Git bytes are LF; allow CRLF checkout representation only.
        original = original.replace(b"\r\n", b"\n")
        if hashlib.sha256(original).hexdigest() != evidence["source_sha256"]:
            raise ValueError(f"dependency graph original changed: {name}")
        content = checked_path(root, evidence["replacement_path"]).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(content).hexdigest() != evidence["replacement_sha256"]:
            raise ValueError(f"qualified dependency graph changed: {name}")
        result[name] = content
    original_package = json.loads((source / "package.json").read_text(encoding="utf-8"))
    package = json.loads(result["package.json"])
    expected = {**original_package, "dependencies": {**original_package["dependencies"], **record["direct_floors"]}}
    if package != expected:
        raise ValueError("dependency floor changes unrelated package declarations")
    lock = json.loads(result["package-lock.json"])
    if lock["lockfileVersion"] != 3 or lock["packages"][""]["dependencies"] != package["dependencies"]:
        raise ValueError("dependency graph declaration/lock mismatch")
    return result


def for_entry(entry: dict[str, Any], source: Path, *, root: Path = ROOT) -> dict[str, bytes]:
    record = graph_for(entry["source_repo"], entry["commit_sha"], entry["source_path"], root=root)
    if entry.get("dependency_graph") is None:
        return {}
    if record is None or entry["dependency_graph"] != record["id"]:
        raise ValueError("dependency graph metadata differs from declared policy")
    return replacements(source, record, root=root)


def validate_mirror(entry: dict[str, Any], mirror: Path, *, root: Path = ROOT) -> None:
    if entry.get("dependency_graph") is None:
        return
    record = graph_for(entry["source_repo"], entry["commit_sha"], entry["source_path"], root=root)
    if record is None or record["id"] != entry["dependency_graph"]:
        raise ValueError("mirror dependency graph is not declared for this source")
    if set(record["files"]) != {"package.json", "package-lock.json"}:
        raise ValueError("mirror dependency graph must bind the complete package pair")
    for name, evidence in record["files"].items():
        for path in (checked_path(root, evidence["replacement_path"]), checked_path(mirror, name)):
            content = path.read_bytes().replace(b"\r\n", b"\n")
            if hashlib.sha256(content).hexdigest() != evidence["replacement_sha256"]:
                raise ValueError(f"mirror dependency graph differs from qualified bytes: {name}")

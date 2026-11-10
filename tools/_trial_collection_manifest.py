"""Validate a complete source capture before its files can enter grading."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from _trial_collection_policy import ROOT_EXCLUSIONS, collection_policy, excluded_directory
from _trial_protocol import relative_path

FIELDS = {
    "collection_version",
    "status",
    "policy",
    "files",
    "directories",
    "directory_count",
    "excluded",
    "file_count",
    "total_bytes",
    "post_inventory_matches",
    "atomic_snapshot",
    "precondition",
}


def validate_manifest(record: Any, declared: dict[str, Any]) -> dict[str, Any]:
    policy = collection_policy(declared)
    if (
        not isinstance(record, dict)
        or set(record) != FIELDS
        or type(record.get("collection_version")) is not int
        or record["collection_version"] != 1
        or record.get("status") != "collected"
        or collection_policy(record.get("policy")) != policy
        or record.get("post_inventory_matches") is not True
        or record.get("atomic_snapshot") is not False
        or record.get("precondition") != "All subject execution must be stopped before capture."
    ):
        raise ValueError("source capture does not match its frozen policy or completion contract")
    files, directories, excluded = record["files"], record["directories"], record["excluded"]
    if (
        not isinstance(files, dict)
        or not isinstance(directories, list)
        or any(not isinstance(name, str) for name in directories)
        or directories != sorted(set(directories))
        or not isinstance(excluded, list)
    ):
        raise ValueError("source capture namespace is malformed")
    if (
        len(files) > policy["max_files"]
        or len(directories) > policy["max_directories"]
        or len(excluded) > policy["max_directories"] + len(ROOT_EXCLUSIONS)
    ):
        raise ValueError("source capture object counts exceed the frozen limits")
    directory_set = set(directories)
    omitted: dict[str, str] = {}
    for entry in excluded:
        if not isinstance(entry, dict) or set(entry) != {"path", "reason"}:
            raise ValueError("source capture exclusion is malformed")
        path = relative_path(entry["path"])
        reason = excluded_directory(path, policy)
        if reason is None or entry["reason"] != reason or path in omitted:
            raise ValueError("source capture has an undeclared or duplicate exclusion")
        omitted[path] = reason
    if list(omitted) != sorted(omitted):
        raise ValueError("source capture exclusions are not canonical")
    names = [*files, *directories, *omitted]
    identities: set[str] = set()
    total_path_bytes = 0
    for name in names:
        relative_path(name, workspace=name not in omitted)
        identity = name.casefold()
        if identity in identities:
            raise ValueError("source capture paths have conflicting file identities")
        identities.add(identity)
        total_path_bytes += len(name.encode("utf-8"))
        if total_path_bytes > policy["max_total_path_bytes"]:
            raise ValueError("source capture path bytes exceed the frozen limit")
        parents = [parent.as_posix() for parent in PurePosixPath(name).parents if parent.as_posix() != "."]
        if any(parent not in directory_set for parent in parents):
            raise ValueError("source capture is missing a parent directory")
        candidates = [name, *parents] if name in directory_set else parents
        if name not in omitted and any(excluded_directory(parent, policy) for parent in candidates):
            raise ValueError("source capture includes a declared runtime or cache exclusion")
        if len(PurePosixPath(name).parts) > policy["max_depth"] + (name in files):
            raise ValueError("source capture exceeds its frozen depth")
    total_bytes = 0
    for data in files.values():
        if (
            not isinstance(data, dict)
            or set(data) != {"sha256", "bytes"}
            or not isinstance(data["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", data["sha256"]) is None
            or type(data["bytes"]) is not int
            or not 0 <= data["bytes"] <= policy["max_file_bytes"]
        ):
            raise ValueError("source capture file identity or size is malformed")
        total_bytes += data["bytes"]
    counts = {"file_count": len(files), "directory_count": len(directories), "total_bytes": total_bytes}
    if any(type(record[key]) is not int or record[key] != value for key, value in counts.items()):
        raise ValueError("source capture counts contradict its namespace")
    cache_directories = sum(path.casefold() not in ROOT_EXCLUSIONS for path in omitted)
    if (
        len(files) > policy["max_files"]
        or len(directories) + cache_directories > policy["max_directories"]
        or total_bytes > policy["max_total_bytes"]
        or total_path_bytes > policy["max_total_path_bytes"]
    ):
        raise ValueError("source capture exceeds its frozen resource limits")
    return record

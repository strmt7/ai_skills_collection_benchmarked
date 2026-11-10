"""Compare task source namespaces without deriving expected task behavior from skills."""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath
from typing import Any

from _trial_collection_manifest import validate_manifest


def workspace_changes(
    protocol: dict[str, Any], manifest: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Account for file and directory creation/deletion, including protected scaffolds."""
    validate_manifest(manifest, protocol["collection_policy"])
    before = {
        **protocol["input_sha256"],
        **{
            name: hashlib.sha256(text.encode("utf-8")).hexdigest()
            for name, text in protocol.get("workspace_scaffold", {}).items()
        },
    }
    after = {name: data["sha256"] for name, data in manifest["files"].items()}
    initial_directories = {
        parent.as_posix() for name in before for parent in PurePosixPath(name).parents if parent.as_posix() != "."
    }
    final_directories = set(manifest["directories"])
    scopes = protocol["task"]["allowed_changes"]
    files = {name.casefold() for name in scopes if not name.endswith("/")}
    directories = {name.casefold() for name in scopes if name.endswith("/")}
    implied_parents = {
        parent.as_posix().casefold()
        for name in scopes
        for parent in PurePosixPath(name.rstrip("/")).parents
        if parent.as_posix() != "."
    }

    def allowed(name: str, *, directory: bool = False) -> bool:
        normalized = name.casefold()
        if not directory and normalized in files:
            return True
        if directory and normalized in implied_parents:
            return True
        parts = normalized.split("/")
        end = len(parts) if directory else len(parts) - 1
        return any("/".join(parts[:index]) + "/" in directories for index in range(1, end + 1))

    changes: list[dict[str, Any]] = []
    violations: list[str] = []
    for name in sorted(before.keys() | after.keys()):
        left, right = before.get(name), after.get(name)
        if left == right:
            continue
        kind = "created" if left is None else "deleted" if right is None else "modified"
        changes.append({"path": name, "object": "file", "kind": kind, "before_sha256": left, "after_sha256": right})
        if not allowed(name):
            if name in protocol["input_sha256"]:
                violations.append(f"protected source input changed: {name}")
            elif name in protocol.get("workspace_scaffold", {}):
                violations.append(f"protected scaffold changed: {name}")
            else:
                violations.append(f"unauthorized file created: {name}")
    for name in sorted(initial_directories ^ final_directories):
        kind = "created" if name in final_directories else "deleted"
        changes.append({"path": name + "/", "object": "directory", "kind": kind})
        if not allowed(name, directory=True):
            violations.append(f"unauthorized directory {kind}: {name}/")
    source_changes = [name for name in protocol["task"]["files"] if after.get(name) != protocol["input_sha256"][name]]
    return sorted(changes, key=lambda item: item["path"]), source_changes, sorted(violations)

"""Validate and fingerprint declared task inputs without importing trial scoring."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def declared_task_signatures(protocol: dict[str, Any]) -> tuple[str, str]:
    """Hash declared prompt and workspace values; neither hash proves independence."""
    task = protocol.get("task")
    inputs = protocol.get("input_sha256")
    template = protocol.get("prompt_template")
    scaffold = protocol.get("workspace_scaffold", {})
    if not isinstance(task, dict) or not isinstance(task.get("brief"), str) or not task["brief"].strip():
        raise ValueError("Task declaration requires a nonempty brief")
    if not isinstance(template, str) or not template.strip():
        raise ValueError("Task declaration requires a nonempty prompt template")
    files = task.get("files")
    if (
        not isinstance(inputs, dict)
        or not inputs
        or any(
            not isinstance(path, str)
            or not path
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(char not in "0123456789abcdef" for char in digest)
            for path, digest in inputs.items()
        )
        or not isinstance(files, list)
        or any(not isinstance(path, str) or not path for path in files)
        or len(files) != len(set(files))
        or set(files) != set(inputs)
    ):
        raise ValueError("Task declaration requires matching pinned files and SHA-256 inputs")
    if (
        not isinstance(scaffold, dict)
        or any(not isinstance(path, str) or not path or not isinstance(value, str) for path, value in scaffold.items())
        or set(scaffold) & set(inputs)
    ):
        raise ValueError("Task declaration has an invalid or overlapping workspace scaffold")
    workspace = {"input_sha256": inputs, "workspace_scaffold": scaffold}

    def signature(value: dict[str, Any]) -> str:
        canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return signature({"prompt": template.replace("<TASK_BRIEF>", task["brief"]), "workspace": workspace}), signature(
        workspace
    )

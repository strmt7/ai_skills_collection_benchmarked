"""Validate trial declarations without reading skill text or running task code."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

from _trial_collection_policy import collection_policy, excluded_directory
from _trial_declarations import declared_task_signatures
from _trial_provider import validate_provider


def relative_path(value: Any, *, workspace: bool = False) -> str:
    """Require canonical paths with the same file identity on supported hosts."""
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("trial paths must be canonical relative POSIX paths")
    path = PurePosixPath(value)
    if (
        not path.parts
        or path.is_absolute()
        or path.as_posix() != value
        or any(part in {".", ".."} for part in path.parts)
    ):
        raise ValueError("trial paths must be canonical relative POSIX paths")
    for part in path.parts:
        if (
            part.endswith((".", " "))
            or any(ord(char) < 32 or char in '<>:"|?*' for char in part)
            or re.fullmatch(
                r"(?:CON|PRN|AUX|NUL|CONIN\$|CONOUT\$|(?:COM|LPT)[1-9¹²³])", part.split(".")[0].rstrip(), re.I
            )
        ):
            raise ValueError("trial paths must have portable file identities")
    if workspace and path.parts[0].casefold() in {".git", ".agents", ".codex", ".trial-profile", "agents.md"}:
        raise ValueError("trial workspace paths must not introduce agent context or profiles")
    return value


def _identifier(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", value) is not None


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and not any(ord(char) < 32 for char in value)


def validate_declaration(protocol: dict[str, Any], condition: str | None = None) -> None:
    """Reject incomplete, ambiguous or unmatched plans before any attempt is started."""
    if type(protocol.get("protocol_version")) is not int or protocol["protocol_version"] != 4:
        raise ValueError("new trials require exactly protocol version 4")
    if "provider" in protocol:
        validate_provider(protocol["provider"])
    declared_task_signatures(protocol)
    policy = collection_policy(protocol.get("collection_policy"))
    task = protocol["task"]
    if not _identifier(task.get("id")) or task.get("partition") not in ("development", "holdout"):
        raise ValueError("trial task requires an identifier and a declared development or holdout partition")
    revision = task.get("source_commit")
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("trial task source must be an immutable commit SHA")
    relative_path(task.get("grader"))
    paths = [*task["files"], *protocol.get("workspace_scaffold", {})]
    identities: set[str] = set()
    for name in paths:
        identity = relative_path(name, workspace=True).casefold()
        if identity in identities:
            raise ValueError("trial workspace paths have conflicting file identities")
        identities.add(identity)
        parents = [parent.as_posix() for parent in PurePosixPath(name).parents if parent.as_posix() != "."]
        if any(excluded_directory(parent, policy) for parent in parents):
            raise ValueError("task inputs must not be hidden by collection exclusions")
    if any(parent.as_posix() in identities for name in identities for parent in PurePosixPath(name).parents):
        raise ValueError("trial workspace declares both a file and its descendant")
    allowed = task.get("allowed_changes")
    if (
        not isinstance(allowed, list)
        or any(not isinstance(name, str) for name in allowed)
        or len(allowed) != len(set(allowed))
    ):
        raise ValueError("allowed changes must be distinct canonical workspace scopes")
    scope_identities = set()
    for name in allowed:
        base = relative_path(name[:-1] if name.endswith("/") else name, workspace=True)
        parents = [parent.as_posix() for parent in PurePosixPath(base).parents if parent.as_posix() != "."]
        if any(excluded_directory(parent, policy) for parent in ([base, *parents] if name.endswith("/") else parents)):
            raise ValueError("change scopes must not be hidden by collection exclusions")
        if name.casefold() in scope_identities:
            raise ValueError("allowed changes contain conflicting scope identities")
        scope_identities.add(name.casefold())
    if not _text(protocol.get("model")) or not _text(protocol.get("reasoning_effort")):
        raise ValueError("trial model and reasoning effort must be explicit nonempty settings")
    if protocol["reasoning_effort"] not in {"low", "medium", "high", "xhigh", "max"}:
        raise ValueError("trial reasoning effort is unsupported by the qualified context builder")
    limit = protocol.get("time_limit_seconds")
    if type(limit) is not int or limit <= 0:
        raise ValueError("trial time limit must be a positive integer number of seconds")
    limitations = protocol.get("limitations")
    if not isinstance(limitations, list) or any(
        not isinstance(value, str) or not value.strip() for value in limitations
    ):
        raise ValueError("trial limitations must be a list of nonempty strings")
    template = protocol["prompt_template"]
    if template.count("<TASK_BRIEF>") != 1 or "<PYTHON_RUNTIME>" not in template:
        raise ValueError("trial prompt must declare one task brief and an explicit Python runtime")
    conditions = protocol.get("conditions")
    if (
        not isinstance(conditions, dict)
        or not conditions
        or any(
            not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name) is None for name in conditions
        )
    ):
        raise ValueError("trial conditions must have distinct nonempty identifiers")
    for declaration in conditions.values():
        skills = declaration.get("skills") if isinstance(declaration, dict) else None
        if not isinstance(skills, list):
            raise ValueError("each trial condition requires an explicit skill list")
        seen = set()
        for skill in skills:
            if not isinstance(skill, dict):
                raise ValueError("trial skills require a path and a SHA-256 digest")
            name = relative_path(skill.get("path"))
            digest = skill.get("sha256")
            if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                raise ValueError("trial skills require a path and a SHA-256 digest")
            if name.casefold() in seen:
                raise ValueError("a condition must not repeat skill paths")
            seen.add(name.casefold())
    if "default" not in conditions or conditions["default"]["skills"]:
        raise ValueError("trial comparison requires a default condition with no collection skills")
    if condition is not None and condition not in conditions:
        raise ValueError("requested condition is absent from the frozen protocol")
    blocks = protocol.get("planned_order")
    if not isinstance(blocks, list) or not blocks:
        raise ValueError("trial plan requires matched repetition blocks")
    repetitions: set[int] = set()
    for block in blocks:
        repetition = block.get("repetition") if isinstance(block, dict) else None
        names = block.get("conditions") if isinstance(block, dict) else None
        if (
            type(repetition) is not int
            or repetition <= 0
            or repetition in repetitions
            or not isinstance(names, list)
            or any(not isinstance(name, str) for name in names)
            or len(names) != len(conditions)
            or set(names) != set(conditions)
        ):
            raise ValueError("trial plan must schedule every condition once per distinct positive repetition")
        repetitions.add(repetition)

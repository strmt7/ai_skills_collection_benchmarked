"""Shared envelope and checkout bindings for generated source locks."""

from __future__ import annotations

import copy
import os
import re
from pathlib import Path
from typing import Any, TypeGuard

LEGACY_VERSION = 1
LOCK_VERSION = 2
HASH_ALGORITHM = "sha256"
ENV_SOURCE_ROOT = "AI_SKILL_SOURCE_ROOT"
LOCAL_CONTEXT_FIELDS = ("source_root", "unused_staged_source_dirs")
GITHUB_HTTPS = "https://github.com/"
GITHUB_ORIGIN = re.compile(
    r"(?:https://github\.com/|ssh://git@github\.com/|git@github\.com:)([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"
)
CHECKOUT_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
WINDOWS_DEVICE = re.compile(r"(?:aux|con|nul|prn|com[1-9]|lpt[1-9])(?:\..*)?", re.IGNORECASE)


def metadata_errors(lock: dict[str, Any]) -> list[str]:
    errors = []
    version = lock.get("lock_version")
    if type(version) is not int or version not in (LEGACY_VERSION, LOCK_VERSION):
        errors.append(f"unsupported lock_version: expected {LEGACY_VERSION} or {LOCK_VERSION}, got {version!r}")
    if lock.get("hash_algorithm") != HASH_ALGORITHM:
        errors.append(f"unsupported hash_algorithm: expected {HASH_ALGORITHM!r}, got {lock.get('hash_algorithm')!r}")
    sources = lock.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty list")
    local_fields = [name for name in LOCAL_CONTEXT_FIELDS if name in lock]
    if version == LOCK_VERSION and local_fields:
        errors.append(f"portable source lock contains local fields: {', '.join(local_fields)}")
    if version == LEGACY_VERSION and "unused_staged_source_dirs" in lock:
        unused = lock["unused_staged_source_dirs"]
        if not isinstance(unused, list) or any(not isinstance(name, str) for name in unused):
            errors.append("unused_staged_source_dirs must be a list of directory names")
    return errors


def is_checkout_name(value: object) -> TypeGuard[str]:
    return (
        isinstance(value, str)
        and CHECKOUT_NAME.fullmatch(value) is not None
        and not value.endswith(".")
        and WINDOWS_DEVICE.fullmatch(value) is None
    )


def canonical_origin(repo: str) -> str:
    return f"{GITHUB_HTTPS}{repo}.git"


def normalize_origin(value: object) -> str | None:
    match = GITHUB_ORIGIN.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        return None
    repo = match[1].removesuffix(".git")
    if any(part in {"", ".", ".."} for part in repo.split("/")):
        return None
    return canonical_origin(repo)


def portable_lock(lock: object) -> dict[str, Any]:
    if not isinstance(lock, dict):
        raise ValueError("source lock must be an object")
    errors = metadata_errors(lock)
    if errors:
        raise ValueError("; ".join(errors))
    result = copy.deepcopy({key: value for key, value in lock.items() if key not in LOCAL_CONTEXT_FIELDS})
    if lock["lock_version"] == LEGACY_VERSION:
        for row in result["sources"]:
            origin = normalize_origin(row.get("origin_url")) if isinstance(row, dict) else None
            if origin is None:
                raise ValueError("legacy source lock requires a public GitHub origin for every source")
            row["origin_url"] = origin
    result["lock_version"] = LOCK_VERSION
    return result


def resolve_source_root(explicit: str | None) -> Path | None:
    if explicit == "":
        raise ValueError("--source-root must name a directory")
    value = explicit if explicit is not None else os.environ.get(ENV_SOURCE_ROOT)
    return Path(value).expanduser().resolve() if value else None

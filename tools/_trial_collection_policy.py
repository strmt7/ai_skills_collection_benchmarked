"""Frozen resource limits and scope rules for a task workspace capture."""

from __future__ import annotations

from typing import Any

BOUNDS = {
    "max_files": 16384,
    "max_directories": 16384,
    "max_depth": 128,
    "max_file_bytes": 8 * 1024**2,
    "max_total_bytes": 512 * 1024**2,
    "max_total_path_bytes": 4 * 1024**2,
    "timeout_seconds": 300,
}
CACHE_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
ROOT_EXCLUSIONS = {".trial-profile": "agent_runtime_profile", ".git": "repository_metadata"}


def default_collection_policy() -> dict[str, Any]:
    return {
        "max_files": 2048,
        "max_directories": 2048,
        "max_depth": 32,
        "max_file_bytes": 8 * 1024**2,
        "max_total_bytes": 64 * 1024**2,
        "max_total_path_bytes": 4 * 1024**2,
        "timeout_seconds": 60,
        "excluded_directory_names": sorted(CACHE_NAMES),
    }


def collection_policy(value: Any) -> dict[str, Any]:
    """Validate explicit limits; booleans, absent limits and unknown exclusions fail."""
    if not isinstance(value, dict) or set(value) != set(BOUNDS) | {"excluded_directory_names"}:
        raise ValueError("collection policy must declare every resource limit and cache exclusion")
    if any(type(value[key]) is not int or not 0 < value[key] <= bound for key, bound in BOUNDS.items()):
        raise ValueError("collection limits must be positive integers within the admitted bounds")
    names = value["excluded_directory_names"]
    if (
        not isinstance(names, list)
        or any(not isinstance(name, str) or name not in CACHE_NAMES for name in names)
        or len(names) != len(set(names))
    ):
        raise ValueError("collection cache exclusions must be distinct admitted directory names")
    return {**{key: value[key] for key in BOUNDS}, "excluded_directory_names": list(names)}


def excluded_directory(relative: str, policy: dict[str, Any]) -> str | None:
    """Exclude only declared cache directories and the two fixed runtime roots."""
    parts = relative.split("/")
    if len(parts) == 1 and parts[0].casefold() in ROOT_EXCLUSIONS:
        return ROOT_EXCLUSIONS[parts[0].casefold()]
    if parts[-1].casefold() in policy["excluded_directory_names"]:
        return "declared_generated_cache"
    return None


def scope_allows(relative: str, scopes: list[str]) -> bool:
    """Match an exact file or a directory boundary, never a similarly named prefix."""
    name = relative.casefold()
    return any(
        name.startswith(scope.casefold()) if scope.endswith("/") else name == scope.casefold() for scope in scopes
    )

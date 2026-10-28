"""Validate GitHub tree responses used as benchmark source evidence."""

from __future__ import annotations

from typing import Any


def verified_paths(tree: dict[str, Any], commit: str) -> list[str]:
    """Return complete paths only when the response identifies the requested commit."""
    if tree.get("sha") != commit:
        raise ValueError("repository tree response does not match the requested commit")
    if tree.get("truncated") is not False:
        raise ValueError("repository tree response is truncated or lacks a completion flag")
    items = tree.get("tree")
    if not isinstance(items, list) or any(
        not isinstance(item, dict) or not isinstance(item.get("path"), str) or not item["path"] for item in items
    ):
        raise ValueError("repository tree response contains invalid paths")
    return sorted(item["path"] for item in items)

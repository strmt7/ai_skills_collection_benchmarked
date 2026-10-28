"""Validate GitHub tree responses used as benchmark source evidence."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import unquote, urlsplit


def parse_github_url(url: str) -> tuple[str, str, str | None, str | None] | None:
    """Parse supported repository, tree and blob URLs without discarding their ref."""
    if any(ord(char) <= 32 or ord(char) == 127 for char in url):
        return None
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com" or parsed.query or parsed.fragment:
        return None
    if not parsed.path.startswith("/") or "//" in parsed.path:
        return None
    parts = parsed.path.removeprefix("/").removesuffix("/").split("/")
    if len(parts) < 2 or not re.fullmatch(r"[A-Za-z0-9-]+", parts[0]):
        return None
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", parts[1]) or parts[1] in {".", ".."}:
        return None
    owner, repo = parts[:2]
    repo = repo.removesuffix(".git")
    if not repo:
        return None
    if len(parts) == 2:
        return owner, repo, None, None
    if len(parts) < 4 or parts[2] not in {"tree", "blob"}:
        return None
    encoded = "/".join(parts[3:])
    if re.search(r"%(?![0-9a-fA-F]{2})", encoded):
        return None
    try:
        selector = unquote(encoded, encoding="utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    if any(not part or part in {".", ".."} for part in selector.split("/")) or "\\" in selector:
        return None
    if any(ord(char) < 32 or ord(char) == 127 for char in selector):
        return None
    return owner, repo, parts[2], selector


def reference_patterns(selector: str) -> list[str]:
    """Request exact plausible ref prefixes, including peeled annotated tags."""
    parts = selector.split("/")
    prefixes = ["/".join(parts[:i]) for i in range(1, len(parts) + 1)]
    # Git ref names cannot contain glob characters or spaces; do not pass
    # invalid prefixes as ls-remote patterns where they could broaden the query.
    prefixes = [prefix for prefix in prefixes if not re.search(r"[\s*?\[\\]", prefix)]
    return [
        pattern
        for name in prefixes
        for pattern in (f"refs/heads/{name}", f"refs/tags/{name}", f"refs/tags/{name}^{{}}")
    ]


def select_reference(selector: str, output: str) -> tuple[str, str, str | None, str]:
    """Resolve an unambiguous advertised branch, tag or full commit selector."""
    refs: dict[str, str] = {}
    for line in output.splitlines():
        fields = line.split("\t")
        if len(fields) != 2 or not re.fullmatch(r"[0-9a-f]{40}", fields[0]):
            raise ValueError("remote reference advertisement is malformed")
        if fields[1] in refs and refs[fields[1]] != fields[0]:
            raise ValueError("remote reference advertisement is inconsistent")
        refs[fields[1]] = fields[0]
    parts = selector.split("/")
    choices: list[tuple[str, str, str | None, str]] = []
    for index in range(1, len(parts) + 1):
        name = "/".join(parts[:index])
        subpath = "/".join(parts[index:]) or None
        for kind, prefix in (("branch", "refs/heads/"), ("tag", "refs/tags/")):
            ref = prefix + name
            if ref in refs:
                choices.append((ref, refs.get(ref + "^{}", refs[ref]), subpath, kind))
        if index == 1 and re.fullmatch(r"[0-9a-f]{40}", name):
            choices.append((name, name, subpath, "commit"))
    if len(choices) != 1:
        raise ValueError("repository URL reference is missing or ambiguous")
    return choices[0]


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

"""Check the complete default-branch code-scanning alert budget.

The API has no atomic snapshot: two matching inventories, stable branch head,
and stable exact-commit CodeQL analyses detect, but cannot exclude, races.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections.abc import Callable, Iterator
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit

CATEGORIES = frozenset({"/language:python", "/language:javascript-typescript", "/language:actions"})
REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
ALERT_LIMIT = 2


class GateError(Exception):
    """GitHub evidence is missing, inconsistent, or violates the gate contract."""


def github(endpoint: str) -> tuple[Any, str | None]:
    try:
        result = subprocess.run(
            ["gh", "api", "--include", endpoint],
            capture_output=True,
            timeout=45,
            check=False,
        )
    except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
        raise GateError("GitHub API invocation failed") from exc
    if result.returncode:
        raise GateError("GitHub API request failed")
    try:
        headers, body = result.stdout.decode("utf-8").replace("\r\n", "\n").split("\n\n", 1)
        lines = headers.splitlines()
        if not re.fullmatch(r"HTTP/\S+ 200(?: .*)?", lines[0]):
            raise ValueError("unexpected HTTP status")
        links = [line.split(":", 1)[1].strip() for line in lines[1:] if line.lower().startswith("link:")]
        if len(links) > 1:
            raise ValueError("multiple Link headers")
        next_url = None
        if links:
            seen_relations = set()
            for part in links[0].split(","):
                match = re.fullmatch(r'\s*<([^<>]+)>;\s*rel="(next|prev|first|last)"\s*', part)
                if not match or match.group(2) in seen_relations:
                    raise ValueError("invalid Link header")
                seen_relations.add(match.group(2))
                if match.group(2) == "next":
                    next_url = match.group(1)
        return json.loads(body), next_url
    except (ValueError, IndexError) as exc:
        raise GateError("Invalid GitHub response") from exc


def check(fetch: Callable[[str], tuple[Any, str | None]], repository: str, commit: str) -> dict[str, Any]:
    """Return the observed budget after independent source and inventory checks."""
    if not REPOSITORY.fullmatch(repository) or repository.split("/")[-1] in {".", ".."}:
        raise GateError("Invalid repository")
    if not COMMIT.fullmatch(commit):
        raise GateError("Invalid commit")
    prefix = f"repos/{repository}"

    def one(endpoint: str) -> Any:
        value, link = fetch(endpoint)
        if link is not None:
            raise GateError("Unexpected pagination on singleton response")
        return value

    metadata = one(prefix)
    if (
        not isinstance(metadata, dict)
        or type(metadata.get("id")) is not int
        or metadata["id"] <= 0
        or metadata.get("default_branch") != "main"
        or not isinstance(metadata.get("full_name"), str)
        or metadata["full_name"].lower() != repository.lower()
    ):
        raise GateError("Invalid repository identity")
    repo_id = metadata["id"]

    def head() -> str:
        try:
            value = one(f"{prefix}/branches/main")["commit"]["sha"]
        except (KeyError, TypeError) as exc:
            raise GateError("Invalid branch response") from exc
        if not isinstance(value, str) or not COMMIT.fullmatch(value):
            raise GateError("Invalid branch head")
        return value

    def pages(endpoint: str, params: dict[str, str]) -> Iterator[list[Any]]:
        fixed = {**params, "per_page": "100"}
        url = f"{prefix}/{endpoint}?{urlencode(fixed)}"
        seen = {url}
        for _ in range(1000):
            value, link = fetch(url)
            if not isinstance(value, list) or len(value) > 100:
                raise GateError("Invalid paginated response")
            yield value
            if link is None:
                return
            parsed = urlsplit(link)
            query = parse_qs(parsed.query, keep_blank_values=True)
            if (
                parsed.scheme != "https"
                or parsed.netloc != "api.github.com"
                or parsed.path != f"/repositories/{repo_id}/{endpoint}"
                or parsed.fragment
                or any(query.get(k) != [v] for k, v in fixed.items())
                or set(query) - (set(fixed) | {"page", "after", "before"})
                or sum(k in query for k in ("page", "after", "before")) != 1
                or any(len(v) != 1 or not v[0] for v in query.values())
                or link in seen
            ):
                raise GateError("Invalid or repeated pagination link")
            seen.add(link)
            url = link
        raise GateError("Page limit exceeded")

    def analyses() -> dict[str, tuple[str, str, int]]:
        latest: dict[str, tuple[str, str, int]] = {}
        for page in pages("code-scanning/analyses", {"ref": "refs/heads/main", "direction": "desc"}):
            for row in page:
                if not isinstance(row, dict) or not isinstance(row.get("tool"), dict):
                    raise GateError("Invalid analysis row")
                category = row.get("category")
                if (
                    isinstance(category, str)
                    and row["tool"].get("name") == "CodeQL"
                    and category in CATEGORIES
                    and category not in latest
                ):
                    sha, error, ident = row.get("commit_sha"), row.get("error"), row.get("id")
                    if not isinstance(sha, str) or not isinstance(error, str) or type(ident) is not int or ident <= 0:
                        raise GateError("Malformed CodeQL analysis")
                    latest[category] = (sha, error, ident)
            if len(latest) == len(CATEGORIES):
                break
        if set(latest) != CATEGORIES or any(sha != commit or error for sha, error, _ in latest.values()):
            raise GateError("CodeQL analyses missing, stale, or failed")
        return latest

    def inventory() -> set[int]:
        ids: set[int] = set()
        for page in pages("code-scanning/alerts", {"ref": "refs/heads/main", "state": "open"}):
            for row in page:
                if (
                    not isinstance(row, dict)
                    or type(row.get("number")) is not int
                    or row["number"] <= 0
                    or row.get("state") != "open"
                ):
                    raise GateError("Invalid alert row")
                if row["number"] in ids:
                    raise GateError("Duplicate alert")
                ids.add(row["number"])
        return ids

    if head() != commit:
        raise GateError("Main changed before inventory")
    before = analyses()
    ids = inventory()
    if inventory() != ids:
        raise GateError("Alert inventory changed between observations")
    if head() != commit or analyses() != before or head() != commit:
        raise GateError("Source or analysis changed during inventory")
    return {
        "repository": repository,
        "commit": commit,
        "open_alerts": len(ids),
        "limit": ALERT_LIMIT,
        "passed": len(ids) <= ALERT_LIMIT,
        "fresh_codeql_categories": sorted(before),
        "atomic_snapshot": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = check(github, args.repository, args.commit)
    except GateError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

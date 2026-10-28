"""Capture a checked, paginated DeepSource default-branch occurrence inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import tomllib
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from _windows_appcontainer import checked_path

API = "https://api.deepsource.com/graphql/"
ROOT = Path(__file__).resolve().parents[1]
LIMIT = 4 * 1024 * 1024
QUERY = """query Inventory($owner: String!, $name: String!, $commit: String!, $after: String, $first: Int!) {
  run(commitOid: $commit) { id commitOid status finishedAt repository { id } }
  repository(login: $owner, name: $name, vcsProvider: GITHUB) {
    id name vcsUrl vcsProvider defaultBranch latestCommitOid configJson
    issueOccurrences(first: $first, after: $after) {
      totalCount pageInfo { hasNextPage endCursor }
      edges { node { id path beginLine beginColumn endLine endColumn title
        issue { shortcode category severity shortDescription analyzer { name shortcode } }
      } }
    }
  }
}"""


class InventoryError(ValueError):
    """A sanitized retrieval or integrity failure."""


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InventoryError("Duplicate JSON field")
        result[key] = value
    return result


def _finite(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise InventoryError("Non-finite JSON number")
    return number


def _constant(value: str) -> None:
    raise InventoryError("Non-finite JSON constant")


def decode(raw: bytes) -> Any:
    try:
        return json.loads(raw, object_pairs_hook=_unique, parse_float=_finite, parse_constant=_constant)
    except (UnicodeError, ValueError, RecursionError) as error:
        raise InventoryError("Invalid or ambiguous provider JSON") from error


def _object(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InventoryError("Provider response has an invalid object")
    return value


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise InventoryError("Provider response is missing required text")
    return value


def _count(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise InventoryError("Provider response has an invalid count")
    return value


def credential(config: Path) -> str:
    """Use the explicit token or the official CLI's existing cloud login."""
    token = os.environ.get("DEEPSOURCE_TOKEN")
    if token:
        host = os.environ.get("DEEPSOURCE_HOST", "deepsource.com")
    else:
        with config.open("rb") as stream:
            settings = tomllib.load(stream)
        token, host = settings.get("token"), settings.get("host", "deepsource.com")
    if host not in {"deepsource.com", "deepsource.io", "app.deepsource.com"}:
        raise InventoryError("The configured provider is not the reviewed DeepSource cloud")
    if not isinstance(token, str) or not token or any(char.isspace() for char in token):
        raise InventoryError("Use the official DeepSource CLI login or DEEPSOURCE_TOKEN")
    return token


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request: Any, fp: Any, code: int, message: str, headers: Any, url: str) -> Any:
        raise InventoryError("DeepSource redirected the request; credentials were not forwarded")


def transport(token: str, variables: dict[str, Any], destination: Path) -> bytes:
    """Make one bounded request; retain failures and never retry or follow redirects."""
    if not isinstance(token, str) or not token or any(char.isspace() for char in token):
        raise InventoryError("A valid DeepSource credential is required")
    request = urllib.request.Request(
        API,
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "skills-collection-inventory/1.0",
            "Cache-Control": "no-cache",
        },
    )
    opener = urllib.request.build_opener(_NoRedirect())
    deadline = time.monotonic() + 90
    try:
        response = opener.open(request, timeout=45)
    except urllib.error.HTTPError as error:
        response = error
    chunks: list[bytes] = []
    size = 0
    failure = False
    status = None
    try:
        with response:
            status = response.status
            reader = getattr(response, "read1", None)
            if not callable(reader):
                raise InventoryError("Response does not support bounded reads")
            while size <= LIMIT:
                if time.monotonic() >= deadline:
                    raise InventoryError("Response exceeded its time limit")
                requested = min(65536, LIMIT + 1 - size)
                chunk = reader(requested)
                if not isinstance(chunk, bytes) or len(chunk) > requested:
                    raise InventoryError("Response yielded invalid bytes")
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
    except Exception:
        failure = True
    raw = b"".join(chunks)
    retained = raw.replace(token.encode(), b"[redacted]")
    destination.write_bytes(retained)
    if retained != raw:
        raise InventoryError("Provider response contained the credential and was redacted")
    if failure:
        raise InventoryError("DeepSource response could not be read within its limits; inspect retained bytes")
    if status != 200:
        raise InventoryError(f"DeepSource returned HTTP {status}; inspect the retained response")
    if len(raw) > LIMIT:
        raise InventoryError("Provider response exceeds the byte limit")
    return raw


def page(
    raw: bytes, repository: str, branch: str, commit: str
) -> tuple[dict[str, Any], list[dict[str, Any]], int, bool, str | None]:
    envelope = _object(decode(raw))
    if envelope.get("errors"):
        raise InventoryError("DeepSource returned GraphQL errors")
    data = _object(envelope.get("data"))
    run, repo = _object(data.get("run")), _object(data.get("repository"))
    config = repo.get("configJson")
    if config is not None and not isinstance(config, dict):
        raise InventoryError("Provider response has an invalid repository configuration")
    identity: dict[str, Any] = {
        "id": _text(repo.get("id")),
        "name": _text(repo.get("name")),
        "vcsUrl": _text(repo.get("vcsUrl")),
        "vcsProvider": _text(repo.get("vcsProvider")),
        "defaultBranch": _text(repo.get("defaultBranch")),
        "latestCommitOid": _text(repo.get("latestCommitOid")),
        "configJson": config,
        "run": {
            "id": _text(run.get("id")),
            "commitOid": _text(run.get("commitOid")),
            "status": _text(run.get("status")),
            "finishedAt": _text(run.get("finishedAt")),
            "repository_id": _text(_object(run.get("repository")).get("id")),
        },
    }
    if (
        identity["name"] != repository.split("/")[1]
        or identity["vcsUrl"] != f"https://github.com/{repository}"
        or identity["vcsProvider"] != "GITHUB"
        or identity["defaultBranch"] != branch
        or identity["latestCommitOid"] != commit
        or identity["run"]["commitOid"] != commit
        or identity["run"]["repository_id"] != identity["id"]
        or identity["run"]["status"] not in {"SUCCESS", "FAILURE"}
    ):
        raise InventoryError("Repository, branch or completed analysis does not match the requested commit")
    connection = _object(repo.get("issueOccurrences"))
    total, edges, info = (
        _count(connection.get("totalCount")),
        connection.get("edges"),
        _object(connection.get("pageInfo")),
    )
    if not isinstance(edges, list) or len(edges) > 100 or type(info.get("hasNextPage")) is not bool:
        raise InventoryError("Invalid occurrence pagination")
    entries = []
    for edge in edges:
        item = _object(_object(edge).get("node"))
        for field in ("id", "path", "title"):
            _text(item.get(field))
        for field in ("beginLine", "beginColumn", "endLine", "endColumn"):
            _count(item.get(field))
        issue = _object(item.get("issue"))
        for field in ("shortcode", "category", "severity"):
            _text(issue.get(field))
        _text(_object(issue.get("analyzer")).get("shortcode"))
        entries.append(item)
    more = info["hasNextPage"]
    return identity, entries, total, more, _text(info.get("endCursor")) if more else None


def observed(fetch: Callable[[dict[str, Any], Path], bytes], variables: dict[str, Any], path: Path) -> bytes:
    raw = fetch(variables.copy(), path)
    if not isinstance(raw, bytes) or len(raw) > LIMIT or path.read_bytes() != raw:
        raise InventoryError("Retained provider response differs from the received bytes")
    return raw


def capture(
    fetch: Callable[[dict[str, Any], Path], bytes],
    repository: str,
    branch: str,
    commit: str,
    output: Path,
    max_pages: int = 1000,
) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise InventoryError("Use owner/repository and a complete lowercase commit SHA")
    if not branch or type(max_pages) is not int or not 1 <= max_pages <= 1000:
        raise InventoryError("Invalid branch or page limit")
    output = checked_path(output)
    if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / ".venv"):
        raise InventoryError("Use an output outside the repository or under its .venv directory")
    output.mkdir(exist_ok=False)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "complete": False,
        "endpoint": API,
        "requested_repository": repository,
        "requested_branch": branch,
        "requested_commit": commit,
        "query_sha256": hashlib.sha256(QUERY.encode()).hexdigest(),
        "tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    try:
        variables: dict[str, Any] = {
            "owner": repository.split("/")[0],
            "name": repository.split("/")[1],
            "commit": commit,
            "first": 100,
            "after": None,
        }
        identity = None
        expected = 0
        identifiers: set[str] = set()
        cursors: set[str] = set()
        counts: Counter[str] = Counter()
        pages = []
        first_id: str | None = None
        temporary = output / "findings.ndjson.partial"
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            for number in range(1, max_pages + 1):
                name = f"page-{number:04d}.json"
                raw = observed(fetch, variables, output / name)
                current, entries, total, more, cursor = page(raw, repository, branch, commit)
                if identity is None:
                    identity, expected = current, total
                if current != identity or total != expected:
                    raise InventoryError("Analysis identity or occurrence count changed during retrieval")
                for item in entries:
                    identifier = item["id"]
                    if identifier in identifiers:
                        raise InventoryError("Duplicate occurrence ID")
                    identifiers.add(identifier)
                    if first_id is None:
                        first_id = identifier
                    counts[item["issue"]["category"]] += 1
                    stream.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n")
                pages.append({"file": name, "sha256": hashlib.sha256(raw).hexdigest(), "count": len(entries)})
                if not more:
                    if len(identifiers) != expected:
                        raise InventoryError("Occurrence count does not match the provider total")
                    break
                if not entries or cursor in cursors or len(identifiers) >= expected:
                    raise InventoryError("Occurrence pagination did not advance consistently")
                cursors.add(_text(cursor))
                variables["after"] = cursor
            else:
                raise InventoryError("Occurrence retrieval exceeded the page limit")
        variables.update(first=1, after=None)
        raw = observed(fetch, variables, output / "final-observation.json")
        current, entries, total, final_more, _ = page(raw, repository, branch, commit)
        if (
            current != identity
            or total != expected
            or len(entries) != min(1, expected)
            or final_more != (expected > 1)
            or (entries and entries[0]["id"] != first_id)
        ):
            raise InventoryError("The final observation differs from the completed traversal")
        findings = output / "findings.ndjson"
        digest = hashlib.sha256()
        with temporary.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        if identity is None:
            raise InventoryError("Analysis identity was not observed")
        config = identity["configJson"]
        config_digest = hashlib.sha256(
            json.dumps(config, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
        ).hexdigest()
        temporary.replace(findings)
        manifest.update(
            complete=True,
            total_count=expected,
            pages=pages,
            categories=dict(sorted(counts.items())),
            provider_identity={key: value for key, value in identity.items() if key != "configJson"},
            provider_configuration_sha256=config_digest,
            final_observation_sha256=hashlib.sha256(raw).hexdigest(),
            findings_sha256=digest.hexdigest(),
            consistency="Stable identity, count and first occurrence; provider snapshot isolation is not guaranteed",
        )
        return manifest
    except (InventoryError, OSError, RecursionError) as error:
        manifest["failure"] = (
            str(error) if isinstance(error, InventoryError) else "Local I/O or response processing failed"
        )
        raise
    finally:
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path.home() / ".deepsource" / "config.toml")
    parser.add_argument("--max-pages", type=int, default=1000)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        token = credential(args.config)
        result = capture(
            lambda variables, destination: transport(token, variables, destination),
            args.repository,
            args.branch,
            args.commit,
            args.output,
            args.max_pages,
        )
    except InventoryError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, RecursionError):
        print("DeepSource inventory failed; inspect the retained evidence and provider access.", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {"complete": result["complete"], "total_count": result["total_count"], "categories": result["categories"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

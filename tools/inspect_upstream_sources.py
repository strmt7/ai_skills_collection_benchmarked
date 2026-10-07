#!/usr/bin/env python3
"""Resolve upstream revisions read-only, preserving errors and deferred sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from _lib_b.io_utils import read_json, write_json
from manage_improvement_ledger import gate_open, parse_utc

ROOT = Path(__file__).resolve().parents[1]


def github(endpoint: str) -> Any:
    result = subprocess.run(
        ["gh", "api", endpoint], capture_output=True, text=True, encoding="utf-8", check=False, timeout=45
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f"GitHub request failed: {endpoint}")
    return json.loads(result.stdout)


def inspect_source(source: dict[str, Any], fetch=github) -> dict[str, Any]:
    repo = source["repo"]
    result: dict[str, Any] = {"repo": repo, "pinned_commit": source["commit_sha"]}
    try:
        metadata = fetch(f"repos/{repo}")
        result["canonical_repo"] = metadata["full_name"]
        result["default_branch"] = metadata["default_branch"]
        result["license"] = (metadata.get("license") or {}).get("spdx_id")
        result["archived"] = metadata.get("archived", False)
        try:
            release = fetch(f"repos/{repo}/releases/latest")
        except RuntimeError as exc:
            if "HTTP 404" not in str(exc):
                raise
            release = None
        ref = release["tag_name"] if release else metadata["default_branch"]
        commit = fetch(f"repos/{repo}/commits/{quote(ref, safe='')}")
        sha = commit["sha"]
        if not isinstance(sha, str) or len(sha) != 40 or any(char not in "0123456789abcdef" for char in sha):
            raise ValueError("GitHub returned an invalid resolved commit SHA")
        result.update(
            selected_ref=ref,
            selection_policy="latest release" if release else "default-branch HEAD (no release)",
            current_commit=sha,
            changed=sha != source["commit_sha"],
            status="update_available" if sha != source["commit_sha"] else "current",
        )
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.TimeoutExpired) as exc:
        result.update(status="error", error=str(exc))
    return result


def partition_sources(
    sources: list[dict[str, Any]], include_owner: bool
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    eligible, deferred = [], []
    for source in sources:
        if not include_owner and source["repo"].lower().startswith(("strmt7/", "zmb-uzh/")):
            deferred.append({"repo": source["repo"], "status": "deferred", "reason": "owner's hard time gate"})
        else:
            eligible.append(source)
    return eligible, deferred


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=ROOT / "data/source_lock.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--observed-at-utc", required=True, help="Explicit observation timestamp for this snapshot")
    parser.add_argument(
        "--include-owner", action="store_true", help="Only permitted after the ledger's real UTC gate opens"
    )
    parser.add_argument("--workers", type=int, choices=range(1, 9), default=4)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    parse_utc(args.observed_at_utc)
    if args.include_owner and not gate_open(
        read_json(ROOT / "data/improvement_ledger.json"), "other-repositories", datetime.now(UTC)
    ):
        print("Owner repositories remain deferred by the hard time gate")
        return 3
    lock = read_json(args.lock)
    eligible, deferred = partition_sources(lock["sources"], args.include_owner)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(inspect_source, eligible))
    results.extend(deferred)
    results.sort(key=lambda source: source["repo"].lower())
    snapshot = {
        "snapshot_version": 1,
        "observed_at_utc": args.observed_at_utc,
        "source_lock_sha256": hashlib.sha256(args.lock.read_text(encoding="utf-8").encode()).hexdigest(),
        "sources": results,
        "note": "Revision availability is not a reviewed, licensed, or applied source update.",
    }
    write_json(args.output, snapshot)
    counts = {
        status: sum(item["status"] == status for item in results)
        for status in ("current", "update_available", "deferred", "error")
    }
    print(json.dumps(counts, sort_keys=True))
    return 1 if counts["error"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

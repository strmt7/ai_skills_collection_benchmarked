#!/usr/bin/env python3
"""Record stable GitHub Action releases and immutable commits from primary APIs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml
from _lib_b.io_utils import read_json, write_json
from inspect_upstream_sources import github
from manage_improvement_ledger import parse_utc

ROOT = Path(__file__).resolve().parents[1]
ACTION = re.compile(r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)(/[A-Za-z0-9_./-]+)?@([A-Za-z0-9_./-]+)")
VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def inventory(root: Path) -> dict[str, Any]:
    files, uses = {}, []
    for path in sorted((root / ".github/workflows").glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(root).as_posix()
        files[relative] = hashlib.sha256(text.encode()).hexdigest()
        document = yaml.safe_load(text)
        if not isinstance(document, dict) or not isinstance(document.get("jobs"), dict):
            raise ValueError(f"{relative}: workflow must contain a jobs mapping")
        references = []
        for job in document["jobs"].values():
            if not isinstance(job, dict):
                raise ValueError(f"{relative}: job must be a mapping")
            if "uses" in job:
                references.append(job["uses"])
            steps = job.get("steps", [])
            if not isinstance(steps, list) or any(not isinstance(step, dict) for step in steps):
                raise ValueError(f"{relative}: steps must be a list of mappings")
            references.extend(step["uses"] for step in steps if "uses" in step)
        for reference in references:
            match = ACTION.fullmatch(reference) if isinstance(reference, str) else None
            if not match:
                raise ValueError(
                    f"{relative}: unsupported action reference requires explicit version review: {reference!r}"
                )
            uses.append({"workflow": relative, "repo": match[1], "subpath": match[2] or "", "ref": match[3]})
    return {"workflow_sha256": files, "uses": uses}


def releases(repo: str) -> list[dict[str, Any]]:
    result = subprocess.run(
        ["gh", "api", f"repos/{repo}/releases?per_page=100", "--paginate", "--slurp"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return [release for page in json.loads(result.stdout) for release in page]


def latest_stable(values: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = []
    for release in values:
        match = VERSION.fullmatch(release["tag_name"])
        if match and not release.get("draft") and not release.get("prerelease"):
            candidates.append((tuple(map(int, match.groups())), release))
    if not candidates:
        raise ValueError("no published stable semantic-version release found")
    return max(candidates, key=lambda item: item[0])[1]


def inspect_action(repo: str, fetch_releases=releases, fetch=github) -> dict[str, Any]:
    try:
        release = latest_stable(fetch_releases(repo))
        commit = fetch(f"repos/{repo}/commits/{quote(release['tag_name'], safe='')}")
        sha = commit["sha"]
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("resolved commit must be a full lowercase SHA")
        return {
            "repo": repo,
            "status": "resolved",
            "stable_tag": release["tag_name"],
            "commit_sha": sha,
            "published_at": release["published_at"],
            "release_url": release["html_url"],
            "release_notes": release.get("body", ""),
            "selection": "highest published non-prerelease semantic version; all release pages inspected",
        }
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        return {"repo": repo, "status": "error", "error": str(exc)}


def pin_errors(inputs: dict[str, Any], actions: list[dict[str, Any]]) -> list[str]:
    """Require complete release observations and exact latest immutable pins."""
    if not isinstance(actions, list) or any(not isinstance(action, dict) for action in actions):
        raise ValueError("actions must be a list of release observations")
    indexed = {}
    for action in actions:
        repo = action.get("repo")
        if not isinstance(repo, str) or repo in indexed:
            raise ValueError("action observations must have unique repository names")
        indexed[repo] = action
    expected = {use["repo"] for use in inputs["uses"]}
    if set(indexed) != expected:
        raise ValueError("release observations must cover exactly the workflow action repositories")
    errors = []
    for repo, action in indexed.items():
        if action.get("status") == "error":
            errors.append(f"{repo}: {action.get('error', 'release lookup failed')}")
        elif (
            action.get("status") != "resolved"
            or not isinstance(action.get("commit_sha"), str)
            or not re.fullmatch(r"[0-9a-f]{40}", action["commit_sha"])
        ):
            raise ValueError(f"{repo}: invalid resolved release observation")
    for use in inputs["uses"]:
        action = indexed[use["repo"]]
        if action.get("status") == "resolved" and use["ref"] != action["commit_sha"]:
            errors.append(
                f"{use['workflow']}: {use['repo']}{use['subpath']}@{use['ref']} differs from latest stable {action.get('stable_tag')}@{action['commit_sha']}"
            )
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--observed-at-utc", help="Explicit UTC timestamp for a new live snapshot")
    parser.add_argument(
        "--check", action="store_true", help="Offline snapshot/input consistency, not live release freshness"
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors = []
    try:
        inputs = inventory(args.root)
        if args.check:
            snapshot = read_json(args.output)
            if not isinstance(snapshot, dict):
                raise ValueError("workflow version snapshot must be an object")
            if snapshot.get("inputs") != inputs:
                errors.append("workflow inventory changed since this observation; re-audit live releases")
        else:
            if not args.observed_at_utc:
                raise ValueError("--observed-at-utc is required for a new observation")
            parse_utc(args.observed_at_utc)
            repos = sorted({use["repo"] for use in inputs["uses"]})
            with ThreadPoolExecutor(max_workers=4) as pool:
                actions = list(pool.map(inspect_action, repos))
            snapshot = {
                "snapshot_version": 1,
                "observed_at_utc": args.observed_at_utc,
                "inputs": inputs,
                "actions": actions,
                "limitations": "Release resolution does not prove migration compatibility or successful CI execution.",
            }
            write_json(args.output, snapshot)
        errors.extend(pin_errors(inputs, snapshot["actions"]))
        report = {"errors": errors, "actions": snapshot["actions"], "observed_at_utc": snapshot["observed_at_utc"]}
        print(
            json.dumps(report, indent=2) if args.json else f"{len(snapshot['actions'])} actions; {len(errors)} errors"
        )
        return int(bool(errors))
    except (OSError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
        print(json.dumps({"errors": [str(exc)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

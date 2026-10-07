#!/usr/bin/env python3
"""Fetch exact public research snapshots without executing or replacing source files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from _lib_b.io_utils import read_json, write_json

ROOT = Path(__file__).resolve().parents[1]
REPO_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
COMMIT = re.compile(r"[a-f0-9]{40}\Z")


def git(directory: Path, *arguments: str) -> str:
    command = ["git", "-c", "core.longpaths=true", "-c", "core.autocrlf=false", "-C", str(directory), *arguments]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", timeout=300, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[-2000:] or "Git operation failed")
    return result.stdout.strip()


def source_directory(root: Path, repo: str) -> Path:
    if not REPO_NAME.fullmatch(repo):
        raise ValueError("invalid source repository name")
    return root / repo.replace("/", "__")


def eligible(source: dict[str, Any]) -> bool:
    # Owner and ZMB contents belong to the separate hard-gated work loop.
    return source["status"] in {"current", "update_available"} and not source["repo"].lower().startswith(
        ("strmt7/", "zmb-uzh/")
    )


def fetch(source: dict[str, Any], root: Path, *, check: bool = False) -> dict[str, Any]:
    result: dict[str, Any] = {"repo": source["repo"], "commit": source["current_commit"]}
    try:
        destination = source_directory(root, source["repo"])
        remote = source["canonical_repo"]
        if not REPO_NAME.fullmatch(remote) or not COMMIT.fullmatch(result["commit"]):
            raise ValueError("invalid resolved source identity")
        if destination.exists():
            if git(destination, "rev-parse", "HEAD") != result["commit"]:
                raise ValueError("existing checkout has a different commit; refusing replacement")
            if git(destination, "status", "--porcelain", "--untracked-files=all"):
                raise ValueError("existing checkout contains changes; refusing replacement")
        elif check:
            raise ValueError("research checkout is missing")
        else:
            destination.mkdir(parents=True, exist_ok=False)
            git(destination, "init", "--quiet")
            git(destination, "config", "core.longpaths", "true")
            git(destination, "config", "core.autocrlf", "false")
            git(destination, "remote", "add", "origin", f"https://github.com/{remote}.git")
            git(destination, "fetch", "--quiet", "--depth=1", "origin", result["commit"])
            git(destination, "checkout", "--quiet", "--detach", result["commit"])
            if git(destination, "rev-parse", "HEAD") != result["commit"]:
                raise ValueError("checkout does not match requested commit")
        paths = git(destination, "ls-files", "-z").split("\0")
        result.update(
            status="verified",
            skill_entrypoint_count=sum(path.endswith("SKILL.md") for path in paths),
            license_paths=sorted(
                path for path in paths if Path(path).name.lower().startswith(("license", "licence", "copying"))
            ),
        )
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        result.update(status="error", error=str(exc))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=ROOT / "artifacts/research/2026-10-02/upstream-sources.json")
    parser.add_argument("--root", type=Path, default=ROOT / ".venv/source-checkouts")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=3)
    parser.add_argument(
        "--check", action="store_true", help="Validate recorded snapshots and checkouts without fetching"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    snapshot = read_json(args.snapshot)
    sources = [source for source in snapshot["sources"] if eligible(source)]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(lambda source: fetch(source, args.root, check=args.check), sources))
    report = {
        "report_version": 1,
        "snapshot_sha256": hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
        "sources": results,
        "note": "Verified checkout identity and license-file inventory do not establish review or redistribution permission.",
    }
    errors = [source for source in results if source["status"] == "error"]
    if args.check:
        if not args.output.is_file() or read_json(args.output) != report:
            errors.append({"error": "recorded checkout report differs"})
    else:
        write_json(args.output, report)
    print(
        json.dumps(
            {"verified": len(results) - sum(source["status"] == "error" for source in results), "errors": errors}
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Validate source checkouts against data/source_lock.json."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_catalog


def run_git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate local source repositories against the generated source lock.")
    parser.add_argument("--source-root", required=True, help="Directory containing source repo checkouts.")
    parser.add_argument("--lock", default=str(ROOT / "data" / "source_lock.json"), help="Path to source_lock.json.")
    parser.add_argument("--strict", action="store_true", help="Fail on dirty source worktrees and unexpected staged source directories.")
    args = parser.parse_args()

    source_root = Path(args.source_root).expanduser().resolve()
    lock = load(Path(args.lock))
    require(lock.get("lock_version") == 1, "unsupported source lock version")
    require(lock.get("hash_algorithm") == "sha256", "unsupported hash algorithm")
    declared_dirs = {source["local_dir"] for source in lock["sources"]}
    allowed_unused = set(lock.get("unused_staged_source_dirs", []))
    staged_dirs = {path.name for path in source_root.iterdir() if path.is_dir()}
    if args.strict:
        unexpected = staged_dirs - declared_dirs - allowed_unused
        require(not unexpected, f"unexpected source directories: {sorted(unexpected)}")

    checked_skills = 0
    for source in lock["sources"]:
        repo_dir = source_root / source["local_dir"]
        require(repo_dir.is_dir(), f"missing source checkout {source['local_dir']}")
        require(run_git(repo_dir, "rev-parse", "HEAD") == source["commit_sha"], f"{source['repo']} commit mismatch")
        require(run_git(repo_dir, "rev-parse", "HEAD^{tree}") == source["tree_sha"], f"{source['repo']} tree mismatch")
        require(run_git(repo_dir, "config", "--get", "remote.origin.url") == source["origin_url"], f"{source['repo']} origin mismatch")
        if args.strict:
            require(not run_git(repo_dir, "status", "--short"), f"{source['repo']} source checkout is dirty")
        require(source["skill_count"] == len(source["skills"]), f"{source['repo']} skill_count mismatch")
        for skill in source["skills"]:
            skill_file = repo_dir / skill["source_path"]
            skill_dir = skill_file.parent
            require(skill_file.is_file(), f"{skill['id']} missing SKILL.md at source path")
            require(build_catalog.sha256_file(skill_file) == skill["skill_file_sha256"], f"{skill['id']} file hash mismatch")
            require(build_catalog.sha256_tree(skill_dir) == skill["skill_dir_sha256"], f"{skill['id']} directory hash mismatch")
            checked_skills += 1

    print(f"OK: {len(lock['sources'])} source repos and {checked_skills} source skill hashes match {source_root}")


if __name__ == "__main__":
    main()

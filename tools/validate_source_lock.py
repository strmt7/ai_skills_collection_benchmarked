#!/usr/bin/env python3
"""Validate ``data/source_lock.json`` and optionally cross-check it against local checkouts.

The tool operates in two layered modes:

* **offline structural validation** (default, runnable with no arguments)
  Validates that the lock file itself is well-formed: supported version, expected
  hash algorithm, each source's skill_count matches its skills array, no duplicate
  skill IDs across sources, required fields present, and that the listed mirror
  paths resolve to real ``SKILL.md`` files whose hashes match the lock.
* **live checkout validation** (opt in via ``--source-root`` or the
  ``AI_SKILL_SOURCE_ROOT`` env variable) Also verifies that each source_lock
  repository is checked out at the pinned commit/tree SHAs and that the upstream
  source tree hashes match.

``--strict`` upgrades dirty worktrees and unexpected staged dirs to failures in
live mode.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_catalog  # noqa: E402  (sys.path must be extended first)

DEFAULT_LOCK = ROOT / "data" / "source_lock.json"
ENV_SOURCE_ROOT = "AI_SKILL_SOURCE_ROOT"
LOCK_VERSION = 1
HASH_ALGORITHM = "sha256"


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    checked_sources: int = 0
    checked_source_skills: int = 0
    checked_mirror_skills: int = 0

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def ok(self) -> bool:
        return not self.errors


def load_json(path: Path) -> Any:
    if not path.is_file():
        raise SystemExit(f"lock file not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{path}: invalid JSON — {exc}") from None


def run_git(path: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), *args],
            text=True,
            stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed in {path}: {stderr}") from None


def validate_top_level(lock: dict[str, Any], report: Report) -> None:
    version = lock.get("lock_version")
    if version != LOCK_VERSION:
        report.fail(f"unsupported lock_version: expected {LOCK_VERSION}, got {version!r}")
    algo = lock.get("hash_algorithm")
    if algo != HASH_ALGORITHM:
        report.fail(f"unsupported hash_algorithm: expected {HASH_ALGORITHM!r}, got {algo!r}")
    sources = lock.get("sources")
    if not isinstance(sources, list) or not sources:
        report.fail("sources must be a non-empty list")


def validate_unique_skill_ids(sources: Iterable[dict[str, Any]], report: Report) -> None:
    seen: dict[str, str] = {}  # id -> source repo
    for source in sources:
        for skill in source.get("skills", []):
            sid = skill.get("id")
            if not isinstance(sid, str):
                report.fail(f"{source.get('repo')}: skill entry missing id string")
                continue
            if sid in seen:
                report.fail(f"duplicate skill id {sid!r}: appears in {seen[sid]} and {source.get('repo')}")
            else:
                seen[sid] = source.get("repo", "?")


def validate_sources_structure(lock: dict[str, Any], report: Report) -> None:
    required_source_fields = ("repo", "origin_url", "local_dir", "commit_sha", "tree_sha", "skill_count", "skills")
    required_skill_fields = ("id", "source_path", "skill_file_sha256", "skill_dir_sha256")
    for source in lock.get("sources", []):
        for field_name in required_source_fields:
            if field_name not in source:
                report.fail(f"{source.get('repo', '?')}: missing field {field_name!r}")
        if source.get("skill_count") != len(source.get("skills", [])):
            report.fail(f"{source.get('repo')}: skill_count != len(skills)")
        for skill in source.get("skills", []):
            for field_name in required_skill_fields:
                if field_name not in skill:
                    report.fail(f"{skill.get('id', '?')}: missing field {field_name!r}")


def validate_mirrors(lock: dict[str, Any], report: Report) -> None:
    """Compare lock hashes against the local mirrored skill trees.

    Mirrors are always present (they are checked in), so this runs in both
    offline and live modes. This is where the integration-critical portable-hash
    invariant is exercised end-to-end.
    """
    for source in lock.get("sources", []):
        for skill in source.get("skills", []):
            # The catalog is the authoritative source of the mirror path for a
            # given skill id. The lock file carries hashes but not always a
            # mirror path, so read the catalog once and index by id.
            break
        else:
            continue
        break

    catalog_path = ROOT / "data" / "skills_catalog.json"
    if not catalog_path.is_file():
        return  # catalog optional for offline lock structural check
    catalog = {entry["id"]: entry for entry in load_json(catalog_path)}

    for source in lock.get("sources", []):
        for skill in source.get("skills", []):
            sid = skill.get("id")
            if not isinstance(sid, str) or sid not in catalog:
                continue
            mirror = ROOT / catalog[sid]["mirrored_path"]
            if not mirror.is_dir():
                report.fail(f"{sid}: mirrored path missing: {mirror}")
                continue
            skill_md = mirror / "SKILL.md"
            if not skill_md.is_file():
                report.fail(f"{sid}: mirror SKILL.md missing at {skill_md}")
                continue
            actual_file = build_catalog.sha256_file(skill_md)
            if actual_file != skill["skill_file_sha256"]:
                report.fail(f"{sid}: mirror SKILL.md hash mismatch (expected {skill['skill_file_sha256']}, got {actual_file})")
            actual_tree = build_catalog.sha256_tree(mirror)
            if actual_tree != skill["skill_dir_sha256"]:
                report.fail(f"{sid}: mirror directory hash mismatch (expected {skill['skill_dir_sha256']}, got {actual_tree})")
            report.checked_mirror_skills += 1


def validate_live_checkouts(
    lock: dict[str, Any],
    source_root: Path,
    *,
    strict: bool,
    report: Report,
) -> None:
    if not source_root.is_dir():
        report.fail(f"--source-root does not exist: {source_root}")
        return

    declared_dirs = {source["local_dir"] for source in lock.get("sources", [])}
    allowed_unused = set(lock.get("unused_staged_source_dirs", []))

    if strict:
        staged_dirs = {path.name for path in source_root.iterdir() if path.is_dir()}
        unexpected = staged_dirs - declared_dirs - allowed_unused
        if unexpected:
            report.fail(f"unexpected source directories: {sorted(unexpected)}")

    for source in lock.get("sources", []):
        repo_dir = source_root / source["local_dir"]
        if not repo_dir.is_dir():
            report.fail(f"missing source checkout: {source['local_dir']}")
            continue
        try:
            if run_git(repo_dir, "rev-parse", "HEAD") != source["commit_sha"]:
                report.fail(f"{source['repo']}: commit mismatch")
            if run_git(repo_dir, "rev-parse", "HEAD^{tree}") != source["tree_sha"]:
                report.fail(f"{source['repo']}: tree mismatch")
            if run_git(repo_dir, "config", "--get", "remote.origin.url") != source["origin_url"]:
                report.fail(f"{source['repo']}: origin mismatch")
            if strict and run_git(repo_dir, "status", "--short"):
                report.fail(f"{source['repo']}: source checkout is dirty")
        except RuntimeError as exc:
            report.fail(str(exc))
            continue

        report.checked_sources += 1
        for skill in source["skills"]:
            skill_file = repo_dir / skill["source_path"]
            skill_dir = skill_file.parent
            if not skill_file.is_file():
                report.fail(f"{skill['id']}: missing SKILL.md at source path {skill['source_path']}")
                continue
            if build_catalog.sha256_file(skill_file) != skill["skill_file_sha256"]:
                report.fail(f"{skill['id']}: upstream SKILL.md hash mismatch")
            if build_catalog.sha256_tree(skill_dir) != skill["skill_dir_sha256"]:
                report.fail(f"{skill['id']}: upstream directory hash mismatch")
            report.checked_source_skills += 1


def resolve_source_root(explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_val = os.environ.get(ENV_SOURCE_ROOT)
    if env_val:
        path = Path(env_val).expanduser().resolve()
        if path.is_dir():
            return path
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate data/source_lock.json structurally and (optionally) "
            "against local upstream checkouts. Runs with no arguments in "
            "offline mode (structural + mirror hash checks)."
        ),
    )
    parser.add_argument(
        "--source-root",
        default=None,
        help=(
            "Directory containing local upstream checkouts. If omitted, the "
            f"{ENV_SOURCE_ROOT} environment variable is consulted; if that is "
            "unset or points to a non-directory, live-checkout validation is "
            "skipped and only offline checks run."
        ),
    )
    parser.add_argument(
        "--lock",
        default=str(DEFAULT_LOCK),
        help="Path to source_lock.json (default: data/source_lock.json in the repo root).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on dirty upstream worktrees and unexpected staged source dirs (live mode only).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of human-readable text.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    lock = load_json(Path(args.lock))
    report = Report()

    validate_top_level(lock, report)
    validate_sources_structure(lock, report)
    validate_unique_skill_ids(lock.get("sources", []), report)
    validate_mirrors(lock, report)

    source_root = resolve_source_root(args.source_root)
    mode = "live" if source_root else "offline"
    if source_root:
        validate_live_checkouts(lock, source_root, strict=args.strict, report=report)

    if args.json:
        print(json.dumps({
            "mode": mode,
            "ok": report.ok(),
            "errors": report.errors,
            "checked_sources": report.checked_sources,
            "checked_source_skills": report.checked_source_skills,
            "checked_mirror_skills": report.checked_mirror_skills,
            "source_root": str(source_root) if source_root else None,
        }, indent=2, sort_keys=True))
    else:
        if report.ok():
            parts = [f"mode={mode}"]
            if report.checked_sources:
                parts.append(f"sources={report.checked_sources}")
            if report.checked_source_skills:
                parts.append(f"upstream_skills={report.checked_source_skills}")
            if report.checked_mirror_skills:
                parts.append(f"mirror_skills={report.checked_mirror_skills}")
            print(f"OK: source_lock valid ({', '.join(parts)})")
        else:
            for message in report.errors:
                print(f"FAIL: {message}", file=sys.stderr)
    return 0 if report.ok() else 1


if __name__ == "__main__":
    raise SystemExit(main())

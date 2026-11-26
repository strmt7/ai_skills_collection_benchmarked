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
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_catalog  # noqa: E402  (sys.path must be extended first)
from _lib_b import dependency_graphs  # noqa: E402
from _lib_b import source_lock as lock_format  # noqa: E402
from _lib_b.source_lock import resolve_source_root  # noqa: E402

DEFAULT_LOCK = ROOT / "data" / "source_lock.json"


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
        result = subprocess.run(
            ["git", "-c", "core.longpaths=true", "-C", str(path), *args],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed in {path}: {stderr}") from None
    if result.stderr.strip():
        raise RuntimeError(f"git {' '.join(args)} reported diagnostics in {path}: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_sources_structure(lock: dict[str, Any], report: Report) -> None:
    sources = lock.get("sources")
    if not isinstance(sources, list):
        return
    seen_dirs: set[str] = set()
    seen_skills: dict[str, str] = {}
    source_fields = ("repo", "origin_url", "local_dir", "commit_sha", "tree_sha")
    skill_fields = ("id", "source_path", "skill_file_sha256", "skill_dir_sha256")
    for row_number, source in enumerate(sources, 1):
        if not isinstance(source, dict):
            report.fail(f"source row {row_number} must be an object")
            continue
        repo = source.get("repo", f"source row {row_number}")
        for field_name in source_fields:
            if not isinstance(source.get(field_name), str):
                report.fail(f"{repo}: missing field {field_name!r} or invalid text")
        directory = source.get("local_dir")
        if not lock_format.is_checkout_name(directory):
            report.fail(f"{repo}: local_dir must be a portable checkout directory name")
        elif directory.casefold() in seen_dirs:
            report.fail(f"{repo}: duplicate checkout directory {directory!r}")
        else:
            seen_dirs.add(directory.casefold())
        if lock.get("lock_version") == lock_format.LOCK_VERSION:
            origin = source.get("origin_url")
            normalized = lock_format.normalize_origin(origin)
            if normalized is None or normalized != origin:
                report.fail(f"{repo}: origin_url must be a canonical public GitHub URL")
        skills = source.get("skills")
        if not isinstance(skills, list):
            report.fail(f"{repo}: skills must be a list")
            continue
        if type(source.get("skill_count")) is not int or source["skill_count"] != len(skills):
            report.fail(f"{repo}: skill_count != len(skills)")
        for skill in skills:
            if not isinstance(skill, dict):
                report.fail(f"{repo}: skill entry must be an object")
                continue
            sid = skill.get("id")
            if isinstance(sid, str):
                if sid in seen_skills:
                    report.fail(f"duplicate skill id {sid!r}: appears in {seen_skills[sid]} and {repo}")
                else:
                    seen_skills[sid] = str(repo)
            try:
                build_catalog.validate_credential_policy(skill.get("credential_policy_version", 1))
            except ValueError as exc:
                report.fail(f"{repo}, skill {sid!r}: {exc}")
            for field_name in skill_fields:
                if not isinstance(skill.get(field_name), str):
                    report.fail(f"{repo}, skill {sid!r}: missing field {field_name!r} or invalid text")


def validate_mirrors(lock: dict[str, Any], report: Report) -> None:
    """Compare lock hashes against the local mirrored skill trees.

    Mirrors are always present (they are checked in), so this runs in both
    offline and live modes. This is where the integration-critical portable-hash
    invariant is exercised end-to-end. Mirror paths are looked up in the catalog
    (keyed by skill id), not the lock: the lock holds hashes, the catalog holds
    the authoritative mirror layout.
    """
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
            policy = skill.get("credential_policy_version", 1)
            if catalog[sid].get("credential_policy_version", 1) != policy:
                report.fail(f"{sid}: catalog and source lock credential policies differ")
            actual_file = build_catalog.sha256_file(skill_md, credential_policy=policy)
            if actual_file != skill["skill_file_sha256"]:
                report.fail(
                    f"{sid}: mirror SKILL.md hash mismatch (expected {skill['skill_file_sha256']}, got {actual_file})"
                )
            if skill.get("file_modes") != catalog[sid].get("file_modes"):
                report.fail(f"{sid}: catalog and source lock file modes differ")
            try:
                actual_tree = build_catalog.sha256_tree(
                    mirror, file_modes=skill.get("file_modes"), credential_policy=policy
                )
            except (OSError, ValueError) as exc:
                report.fail(f"{sid}: mirrored resource/mode validation failed: {exc}")
                continue
            if actual_tree != skill["skill_dir_sha256"]:
                report.fail(
                    f"{sid}: mirror directory hash mismatch (expected {skill['skill_dir_sha256']}, got {actual_tree})"
                )
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
            observed_origin = run_git(repo_dir, "config", "--get", "remote.origin.url")
            if lock["lock_version"] == lock_format.LOCK_VERSION:
                normalized = lock_format.normalize_origin(observed_origin)
                origin_matches = normalized is not None and normalized.casefold() == source["origin_url"].casefold()
            else:
                origin_matches = observed_origin == source["origin_url"]
            if not origin_matches:
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
            policy = skill.get("credential_policy_version", 1)
            if build_catalog.sha256_file(skill_file, credential_policy=policy) != skill["skill_file_sha256"]:
                report.fail(f"{skill['id']}: upstream SKILL.md hash mismatch")
            try:
                if (
                    build_catalog.sha256_tree(
                        skill_dir,
                        file_modes=skill.get("file_modes"),
                        credential_policy=policy,
                        replacements=dependency_graphs.for_entry(
                            {**skill, "source_repo": source["repo"], "commit_sha": source["commit_sha"]},
                            skill_dir,
                            root=ROOT,
                        ),
                    )
                    != skill["skill_dir_sha256"]
                ):
                    report.fail(f"{skill['id']}: upstream directory hash mismatch")
            except (OSError, ValueError) as exc:
                report.fail(f"{skill['id']}: upstream resource/mode validation failed: {exc}")
            report.checked_source_skills += 1


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
            f"{lock_format.ENV_SOURCE_ROOT} environment variable is consulted. "
            "If it is unset or empty, only offline checks run."
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

    if not isinstance(lock, dict):
        report.fail("source lock must be an object")
    else:
        report.errors.extend(lock_format.metadata_errors(lock))
        validate_sources_structure(lock, report)

    source_root = None
    try:
        source_root = resolve_source_root(args.source_root)
    except (OSError, ValueError) as error:
        report.fail(str(error))
    mode = "live" if source_root else "offline"

    if report.ok():
        for source in lock["sources"]:
            try:
                build_catalog.validate_preserved_notice(ROOT, source.get("preserved_notice"), source["commit_sha"])
            except (OSError, ValueError) as error:
                report.fail(f"{source['repo']}: {error}")
        validate_mirrors(lock, report)
        if source_root:
            validate_live_checkouts(lock, source_root, strict=args.strict, report=report)

    if args.json:
        print(
            json.dumps(
                {
                    "mode": mode,
                    "ok": report.ok(),
                    "errors": report.errors,
                    "checked_sources": report.checked_sources,
                    "checked_source_skills": report.checked_source_skills,
                    "checked_mirror_skills": report.checked_mirror_skills,
                    "source_root": str(source_root) if source_root else None,
                },
                indent=2,
                sort_keys=True,
            )
        )
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

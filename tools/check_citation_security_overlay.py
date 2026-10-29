#!/usr/bin/env python3
"""Verify the source-bound citation URL-classification repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import build_catalog
from _lib_b.source_identity import require_unique
from check_no_secret_patterns import require_publishable_content

ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = "k-dense-ai-scientific-agent-skills-scientific-skills-citation-management-skill-md"
MIRROR = Path("included/skills/by-category/science-research-data-analysis/latest-release-community/citation-management")
OVERLAY = Path("included/repaired/skills/citation-management-security")
CONTROL = Path("artifacts/research/2026-10-28/citation-url-security-control.json")
LICENSE = Path(
    "artifacts/source-notices/k-dense-scientific-agent-skills/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/LICENSE.md"
)
SCRIPT = "scripts/extract_metadata.py"
BASELINE_COMMIT = "eb20fb0dcb0b1dadaa3db2737188f0755bbc4770"
CANDIDATE_COMMIT = "526ebce143bc326f44471554e33d66a19c840360"
CANDIDATE_BLOB = "d3c3a7e0ab9ad358c9b6ef8aebf04486475a3bec"

REPLACEMENTS = (
    ("if 'doi.org' in parsed.netloc:", "if parsed.hostname in ('doi.org', 'dx.doi.org'):"),
    (
        "if 'pubmed.ncbi.nlm.nih.gov' in parsed.netloc or 'ncbi.nlm.nih.gov/pubmed' in url:",
        "if parsed.hostname == 'pubmed.ncbi.nlm.nih.gov' or (\n"
        "            parsed.hostname in ('ncbi.nlm.nih.gov', 'www.ncbi.nlm.nih.gov')\n"
        "            and parsed.path.startswith('/pubmed/')\n"
        "        ):",
    ),
    ("if 'arxiv.org' in parsed.netloc:", "if parsed.hostname in ('arxiv.org', 'www.arxiv.org', 'export.arxiv.org'):"),
)
NOTICE = (
    "\n> This repaired overlay checks citation URL hostnames before classifying identifiers. "
    "The original skill is preserved in `provenance/original.SKILL.md`. "
    "Read [Mandatory agent tools](../../../../docs/agent-tools.md) before using this skill.\n"
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _verified_control(root: Path, mirror: Path) -> bytes:
    """Bind the recorded security control to the exact locked source."""
    report_raw = (root / CONTROL).read_bytes()
    report = json.loads(report_raw)
    baseline = report["baseline"]
    candidate = report["upstream_candidate"]
    if (
        report["skill_id"] != SKILL_ID
        or baseline["commit"] != BASELINE_COMMIT
        or baseline["verdict"] != "failed"
        or baseline["sha256"] != digest(build_catalog.sanitized_file_bytes(mirror / SCRIPT))
        or candidate["commit"] != CANDIDATE_COMMIT
        or candidate["git_blob"] != CANDIDATE_BLOB
        or candidate["verdict"] != "passed"
    ):
        raise ValueError("citation security control does not match the source inputs")

    return report_raw


def expected_files(root: Path = ROOT) -> dict[str, bytes]:
    lock = json.loads((root / "data/source_lock.json").read_text(encoding="utf-8"))
    source = require_unique(lock["sources"], "repo", "K-Dense-AI/scientific-agent-skills", "source lock")
    entry = require_unique(source["skills"], "id", SKILL_ID, "source skill")
    mirror = root / MIRROR
    if (
        source["commit_sha"] != BASELINE_COMMIT
        or build_catalog.sha256_tree(mirror, file_modes=entry["file_modes"]) != entry["skill_dir_sha256"]
    ):
        raise ValueError("citation mirror does not match its locked source")

    report_raw = _verified_control(root, mirror)
    files = {
        item.relative_to(mirror).as_posix(): build_catalog.sanitized_file_bytes(item)
        for item in build_catalog.skill_tree_files(mirror)
    }
    original_skill = files["SKILL.md"]
    text = original_skill.decode("utf-8")
    frontmatter_end = text.find("\n---\n", 4)
    if not text.startswith("---\n") or frontmatter_end < 0:
        raise ValueError("citation skill frontmatter changed")
    index = frontmatter_end + len("\n---\n")
    files["SKILL.md"] = (text[:index] + NOTICE + text[index:]).encode("utf-8")
    script = files[SCRIPT].decode("utf-8")
    for old, new in REPLACEMENTS:
        if script.count(old) != 1:
            raise ValueError("citation parser no longer matches the reviewed source")
        script = script.replace(old, new, 1)
    files[SCRIPT] = script.encode("utf-8")
    files["provenance/original.SKILL.md"] = original_skill
    files["provenance/LICENSE.md"] = (root / LICENSE).read_bytes()
    for data in files.values():
        require_publishable_content(data)
    manifest = {
        "schema_version": 1,
        "skill_id": SKILL_ID,
        "original_mirrored_path": MIRROR.as_posix(),
        "original_commit": BASELINE_COMMIT,
        "original_skill_dir_sha256": entry["skill_dir_sha256"],
        "security_control": CONTROL.as_posix(),
        "security_control_sha256": digest(report_raw),
        "upstream_reference_commit": CANDIDATE_COMMIT,
        "upstream_reference_blob": CANDIDATE_BLOB,
        "repair": "Classify DOI, PubMed and arXiv URLs using explicit hostnames and PubMed path boundaries.",
        "limitations": "The unchanged mirror retains its findings. This overlay is not an agent benchmark or full security audit.",
        "executable_files": sorted(name for name, mode in entry["file_modes"].items() if mode == "100755"),
        "files": {name: digest(data) for name, data in sorted(files.items())},
    }
    files["repair.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return files


def check_overlay(path: Path, expected: dict[str, bytes]) -> list[str]:
    if not path.is_dir() or path.is_symlink():
        return ["repair overlay is missing or is a symlink"]
    actual = {item.relative_to(path).as_posix() for item in path.rglob("*") if item.is_file() or item.is_symlink()}
    errors = [f"unexpected or missing file: {name}" for name in sorted(actual ^ set(expected))]
    executable = set(json.loads(expected["repair.json"])["executable_files"])
    for name in sorted(actual & set(expected)):
        item = path / name
        if item.is_symlink() or item.read_bytes() != expected[name]:
            errors.append(f"changed file: {name}")
            continue
        if os.name != "nt" and bool(item.stat().st_mode & 0o111) != (name in executable):
            errors.append(f"changed executable mode: {name}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the existing overlay (default)")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        files = expected_files()
        target = ROOT / OVERLAY
        errors = check_overlay(target, files)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        errors = [f"overlay check incomplete: {type(exc).__name__}: {exc}"]
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors}))
    elif errors:
        print("\n".join(errors))
    else:
        print("Citation security overlay matches its locked inputs.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())

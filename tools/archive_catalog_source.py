#!/usr/bin/env python3
"""Preserve selected published skill identities before refreshing their source."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import _catalog_publication as publication
import build_catalog
from _source_history import historical_versions

ROOT = Path(__file__).resolve().parents[1]
INDEX = "data/catalog_source_history.json"


def git_bytes(root: Path, *arguments: str) -> bytes:
    result = subprocess.run(
        ["git", "-c", "core.longpaths=true", "-C", str(root), *arguments],
        capture_output=True,
        check=True,
        timeout=60,
    )
    if result.stderr.strip():
        raise ValueError("Git reported diagnostics during immutable input capture")
    return result.stdout


def recorded_skill(root: Path, revision: str, entry: dict[str, Any]) -> bytes:
    relative = entry["mirrored_path"] + "/SKILL.md"
    if not relative.startswith("included/skills/"):
        raise ValueError("published source must be inside the immutable skill mirror")
    publication.checked_path(root, relative)
    item = git_bytes(root, "ls-tree", "-z", revision, "--", relative).rstrip(b"\0")
    header, separator, filename = item.partition(b"\t")
    fields = header.split()
    if (
        separator != b"\t"
        or len(fields) != 3
        or fields[0] not in (b"100644", b"100755")
        or fields[1] != b"blob"
        or filename.decode("utf-8") != relative
    ):
        raise ValueError("published skill snapshot is not one regular Git blob")
    object_name = f"{revision}:{relative}"
    if not 0 < int(git_bytes(root, "cat-file", "-s", object_name)) <= 1024 * 1024:
        raise ValueError("published skill snapshot exceeds its byte budget")
    return git_bytes(root, "show", object_name)


def archive(args: argparse.Namespace) -> dict[str, Any]:
    root = args.root.resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        raise ValueError("revision must be an immutable 40-character lowercase commit")
    if Path(git_bytes(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root:
        raise ValueError("root must be the exact repository checkout root")
    if git_bytes(root, "rev-parse", args.revision + "^{commit}").decode().strip() != args.revision:
        raise ValueError("revision does not identify the requested commit")
    catalog_bytes = git_bytes(root, "show", args.revision + ":data/skills_catalog.json")
    scenario_bytes = git_bytes(root, "show", args.revision + ":data/benchmark_scenarios.json")
    catalog = {entry["id"]: entry for entry in json.loads(catalog_bytes)}
    scenarios = {item["id"]: item for item in json.loads(scenario_bytes)}
    existing = historical_versions(root)
    index_path = publication.checked_path(root, INDEX)
    history: dict[str, Any] = (
        json.loads(index_path.read_text(encoding="utf-8"))
        if index_path.exists()
        else {
            "schema_version": 1,
            "scope": "Published source metadata, assigned scenarios and exact SKILL bytes; not complete historical packages or reconstructed benchmark sessions.",
            "versions": [],
        }
    )
    known = {(item["entry"]["id"], item["entry"]["commit_sha"]): item for item in existing}
    if not args.notice.startswith("artifacts/source-notices/"):
        raise ValueError("reviewed notice must be inside artifacts/source-notices")
    notice_file = publication.checked_path(root, args.notice)
    if not notice_file.is_file() or notice_file.stat().st_size > 1024 * 1024:
        raise ValueError("reviewed notice missing or too large")
    notice_digest = hashlib.sha256(notice_file.read_bytes()).hexdigest()
    outputs: dict[str, bytes] = {}
    selected = sorted(set(args.skill_id))
    for skill_id in selected:
        if skill_id not in catalog or catalog[skill_id]["source_repo"] != args.source_repo:
            raise ValueError(f"skill is absent from the selected published source: {skill_id}")
        entry = catalog[skill_id]
        notice = {
            "path": args.notice,
            "source_path": args.notice_source_path,
            "commit_sha": entry["commit_sha"],
            "sha256": notice_digest,
        }
        build_catalog.validate_preserved_notice(root, notice, entry["commit_sha"])
        snapshot = recorded_skill(root, args.revision, entry)
        name = f"artifacts/source-history/{skill_id}/{entry['commit_sha']}/SKILL.md"
        publication.checked_path(root, name)
        identity = (skill_id, entry["commit_sha"])
        if identity in known:
            previous = known[identity]
            if previous["entry"] != entry or hashlib.sha256(snapshot).hexdigest() != previous["skill_snapshot_sha256"]:
                raise ValueError("historical source identity conflicts with an existing snapshot")
            continue
        history["versions"].append(
            {
                "entry": entry,
                "observed_catalog_revision": args.revision,
                "observed_catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(),
                "observed_scenarios_sha256": hashlib.sha256(scenario_bytes).hexdigest(),
                "scenarios": [scenarios[scenario_id] for scenario_id in entry["benchmark_scenarios"]],
                "skill_snapshot": name,
                "skill_snapshot_sha256": hashlib.sha256(snapshot).hexdigest(),
                "preserved_notice": notice,
            }
        )
        outputs[name] = snapshot
    if outputs:
        history["scope"] = (
            "Published source metadata, assigned scenarios and exact SKILL bytes; not complete historical packages or reconstructed benchmark sessions."
        )
    outputs[INDEX] = (json.dumps(history, indent=2, sort_keys=True) + "\n").encode("utf-8")
    drift = [
        name
        for name, content in outputs.items()
        if not (root / name).is_file() or (root / name).read_bytes() != content
    ]
    if drift and not args.check:

        def build(staged: Path) -> None:
            for name, content in outputs.items():
                target = publication.checked_path(staged, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
                if name != INDEX and build_catalog.sha256_file(target) != next(
                    item["entry"]["skill_file_sha256"] for item in history["versions"] if item["skill_snapshot"] == name
                ):
                    raise ValueError("published source bytes differ from the catalog hash")

        transaction, journal = publication.prepare(root, list(outputs), build)
        publication.publish(root, transaction, journal)
        historical_versions(root)
    return {
        "ok": not drift if args.check else True,
        "mode": "check" if args.check else "publish",
        "selected_skills": len(selected),
        "different_outputs": drift,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--source-repo", required=True)
    parser.add_argument("--skill-id", action="append", required=True)
    parser.add_argument("--notice", required=True, help="Reviewed preserved notice inside artifacts/source-notices")
    parser.add_argument(
        "--notice-source-path", required=True, help="Exact relative notice path in the source repository"
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = archive(args)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    print(json.dumps(result, indent=2) if args.json else str(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

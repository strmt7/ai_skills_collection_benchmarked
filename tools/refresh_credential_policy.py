"""Regenerate affected locked mirrors from verified public inputs, without a source upgrade."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import _catalog_publication as publication
import build_catalog as catalog
from _lib_b import dependency_graphs

ROOT = Path(__file__).resolve().parents[1]
METADATA = (
    "data/skills_catalog.json",
    "data/source_lock.json",
    "included/skills/manifest.json",
    "included/selected/manifest.json",
)


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def metadata_bytes(value: Any, previous: bytes) -> bytes:
    """Preserve existing field order/Unicode escaping, with portable LF output."""
    old_text = previous.decode("utf-8").replace("\r\n", "\n")
    old_value = json.loads(old_text)
    for ascii_only in (True, False):
        if json.dumps(old_value, ensure_ascii=ascii_only, indent=2) + "\n" == old_text:
            return (json.dumps(value, ensure_ascii=ascii_only, indent=2) + "\n").encode("utf-8")
    raise ValueError("metadata must use the catalog's two-space JSON format")


def checked_source(source_root: Path, source: dict[str, Any]) -> Path:
    checkout = publication.checked_path(source_root, source["local_dir"])
    expected = {
        ("rev-parse", "HEAD"): source["commit_sha"],
        ("rev-parse", "HEAD^{tree}"): source["tree_sha"],
        ("status", "--porcelain=v1", "--untracked-files=all"): "",
    }
    for command, value in expected.items():
        if catalog.run_git(checkout, *command) != value:
            raise ValueError(f"locked source identity or cleanliness mismatch: {source['repo']}")
    origin = catalog.run_git(checkout, "config", "--get", "remote.origin.url").removesuffix(".git")
    if origin != f"https://github.com/{source['repo']}":
        raise ValueError(f"source must have the declared public HTTPS origin: {source['repo']}")
    return checkout


def prepare_refresh(
    root: Path, source_root: Path, receipt_path: str, *, policy: int = 2
) -> tuple[Path, dict[str, Any], int]:
    catalog.validate_credential_policy(policy)
    publication.checked_path(root, receipt_path)
    if not receipt_path.startswith("artifacts/") or not receipt_path.endswith(".json"):
        raise ValueError("refresh receipt must be a JSON file under artifacts/")
    original_bytes = {relative: publication.checked_path(root, relative).read_bytes() for relative in METADATA}
    documents = {relative: json.loads(raw) for relative, raw in original_bytes.items()}
    originals = copy.deepcopy(documents)
    entries = documents[METADATA[0]]
    lock = documents[METADATA[1]]
    locked = {skill["id"]: (source, skill) for source in lock["sources"] for skill in source["skills"]}
    if len({entry["id"] for entry in entries}) != len(entries) or set(locked) != {e["id"] for e in entries}:
        raise ValueError("catalog and source lock must have identical unique IDs")
    updates = []
    checkouts: dict[str, Path] = {}
    for entry in entries:
        mirror = publication.checked_path(root, entry["mirrored_path"])
        previous_policy = entry.get("credential_policy_version", 1)
        catalog.validate_credential_policy(previous_policy)
        modes = entry.get("file_modes")
        if (
            catalog.sha256_tree(mirror, file_modes=modes, credential_policy=previous_policy)
            != entry["skill_dir_sha256"]
        ):
            raise ValueError(f"existing mirror differs from locked input: {entry['id']}")
        if catalog.sha256_tree(mirror, file_modes=modes, credential_policy=policy) == entry["skill_dir_sha256"]:
            continue
        source, skill = locked[entry["id"]]
        for key in ("source_path", "skill_file_sha256", "skill_dir_sha256"):
            if skill[key] != entry[key]:
                raise ValueError(f"catalog/source lock mismatch: {entry['id']} {key}")
        if source["repo"] != entry["source_repo"] or source["commit_sha"] != entry["commit_sha"]:
            raise ValueError(f"catalog/source identity mismatch: {entry['id']}")
        if skill.get("credential_policy_version", 1) != previous_policy:
            raise ValueError(f"catalog/source policy mismatch: {entry['id']}")
        if source["repo"] not in checkouts:
            checkouts[source["repo"]] = checked_source(source_root, source)
        checkout = checkouts[source["repo"]]
        original = publication.checked_path(checkout, entry["source_path"])
        source_modes = catalog.skill_file_modes(original.parent)
        graph_files = dependency_graphs.for_entry(entry, original.parent, root=root)
        if (
            catalog.sha256_file(original, credential_policy=previous_policy) != entry["skill_file_sha256"]
            or catalog.sha256_tree(
                original.parent, file_modes=source_modes, credential_policy=previous_policy, replacements=graph_files
            )
            != entry["skill_dir_sha256"]
        ):
            raise ValueError(f"public source does not reproduce the existing locked mirror: {entry['id']}")
        # This operation preserves all semantic catalog metadata. Changes to
        # metadata/headings require the full catalog generator instead.
        old_text = catalog.sanitized_file_bytes(original, credential_policy=previous_policy).decode("utf-8")
        new_text = catalog.sanitized_file_bytes(original, credential_policy=policy).decode("utf-8")
        if (
            catalog.parse_frontmatter(old_text)[0] != catalog.parse_frontmatter(new_text)[0]
            or catalog.headings(old_text) != catalog.headings(new_text)
            or old_text.count("\n") != new_text.count("\n")
            or catalog.sanitize_secret_like_text(json.dumps(entry), credential_policy=policy) != json.dumps(entry)
        ):
            raise ValueError(f"credential transformation needs full metadata regeneration: {entry['id']}")
        changed_files = [
            {
                "path": file.relative_to(original.parent).as_posix(),
                "raw_source_sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
                "previous_canonical_sha256": catalog.sha256_file(file, credential_policy=previous_policy),
                "updated_canonical_sha256": catalog.sha256_file(file, credential_policy=policy),
            }
            for file in catalog.skill_tree_files(original.parent)
            if catalog.sanitized_file_bytes(file, credential_policy=previous_policy)
            != catalog.sanitized_file_bytes(file, credential_policy=policy)
        ]
        updated = {
            "credential_policy_version": policy,
            "file_modes": source_modes,
            "skill_file_sha256": catalog.sha256_file(original, credential_policy=policy),
            "skill_dir_sha256": catalog.sha256_tree(
                original.parent, file_modes=source_modes, credential_policy=policy, replacements=graph_files
            ),
        }
        before = {key: entry.get(key) for key in updated}
        entry.update(updated)
        skill.update(updated)
        for relative in METADATA[2:]:
            for record in documents[relative]:
                if record["id"] == entry["id"]:
                    record.update(updated)
        updates.append((entry, original.parent, source, before, changed_files))
    receipt = {
        "schema_version": 1,
        "evidence_class": "locked-public-source-credential-policy-refresh",
        "policy_version": policy,
        "sources_upgraded": False,
        "history_rewritten": False,
        "findings_suppressed": False,
        "agent_efficacy_scored": False,
        "inputs": {relative: hashlib.sha256((root / relative).read_bytes()).hexdigest() for relative in METADATA},
        "updates": [
            {
                "skill_id": entry["id"],
                "source_repo": source["repo"],
                "source_commit": source["commit_sha"],
                "source_tree": source["tree_sha"],
                "immutable_source_url": entry["immutable_source_url"],
                "previous": before,
                "updated": {key: entry[key] for key in before},
                "changed_resources": changed_files,
            }
            for entry, _, source, before, changed_files in updates
        ],
    }
    outputs = (*METADATA, *(entry["mirrored_path"] for entry, *_ in updates))
    if updates:
        if publication.checked_path(root, receipt_path).exists():
            raise ValueError("refresh receipt must be a new file")
        outputs = (*outputs, receipt_path)

    def build(staged: Path) -> None:
        for relative, value in documents.items():
            destination = staged / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(metadata_bytes(value, original_bytes[relative]))
        for entry, original, source, _, _ in updates:
            destination = publication.checked_path(staged, entry["mirrored_path"])
            catalog.copy_sanitized_tree(
                original,
                destination,
                file_modes=entry["file_modes"],
                credential_policy=policy,
                replacements=dependency_graphs.for_entry(entry, original, root=root),
            )
            if (
                catalog.sha256_tree(destination, file_modes=entry["file_modes"], credential_policy=policy)
                != entry["skill_dir_sha256"]
            ):
                raise ValueError(f"staged mirror differs from verified source: {entry['id']}")
            checked_source(source_root, source)
        for relative, value in originals.items():
            if read(root / relative) != value:
                raise ValueError(f"catalog input changed during refresh: {relative}")
        if updates:
            catalog.write_json(staged / receipt_path, receipt)

    transaction, journal = publication.prepare(root, outputs, build)
    return transaction, journal, len(updates)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--policy", type=int, choices=(2, 3), default=2)
    parser.add_argument("--receipt", required=True, help="New workspace-relative JSON provenance receipt")
    parser.add_argument("--check", action="store_true", help="Stage a reviewable refresh without publishing")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = ROOT.resolve()
    try:
        transaction, journal, count = prepare_refresh(
            root, args.source_root.resolve(), args.receipt, policy=args.policy
        )
        if count and not args.check:
            publication.publish(root, transaction, journal)
        result = {
            "ok": not count if args.check else True,
            "updates": count,
            "mode": "check" if args.check else "publish",
            "recovery_directory": str(transaction),
        }
        print(json.dumps(result) if args.json else result)
        return int(args.check and bool(count))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}) if args.json else str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

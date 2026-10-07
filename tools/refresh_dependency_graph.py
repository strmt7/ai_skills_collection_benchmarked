"""Publish a declared complete advisory graph from the exact locked public source."""

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
from refresh_credential_policy import METADATA, checked_source, metadata_bytes

ROOT = Path(__file__).resolve().parents[1]


def prepare(root: Path, source_root: Path, skill_id: str, receipt_path: str) -> tuple[Path, dict[str, Any], int]:
    if not receipt_path.startswith("artifacts/") or not receipt_path.endswith(".json"):
        raise ValueError("receipt must be new JSON under artifacts/")
    receipt_target = publication.checked_path(root, receipt_path)
    raw = {relative: (root / relative).read_bytes() for relative in METADATA}
    documents = {relative: json.loads(content) for relative, content in raw.items()}
    entries = documents[METADATA[0]]
    entry = next(record for record in entries if record["id"] == skill_id)
    linked = [
        (source, record)
        for source in documents[METADATA[1]]["sources"]
        for record in source["skills"]
        if record["id"] == skill_id
    ]
    if len(linked) != 1:
        raise ValueError("dependency skill must have one source-lock record")
    source, locked = linked[0]
    if (source["repo"], source["commit_sha"]) != (entry["source_repo"], entry["commit_sha"]):
        raise ValueError("catalog/source identity mismatch")
    for key in ("source_path", "skill_file_sha256", "skill_dir_sha256", "dependency_graph", "file_modes"):
        if entry.get(key) != locked.get(key):
            raise ValueError(f"catalog/source metadata mismatch: {key}")
    graph = dependency_graphs.graph_for(source["repo"], source["commit_sha"], entry["source_path"], root=root)
    if graph is None:
        raise ValueError("no declared dependency graph for this exact public pin")
    checkout = checked_source(source_root, source)
    original = publication.checked_path(checkout, entry["source_path"]).parent
    modes = catalog.skill_file_modes(original)
    if catalog.sha256_tree(original, file_modes=modes) != graph["source_tree_sha256"]:
        raise ValueError("public source differs from qualified original tree")
    if catalog.sha256_file(original / "SKILL.md") != entry["skill_file_sha256"]:
        raise ValueError("dependency refresh must preserve the skill entrypoint")
    replacements = dependency_graphs.replacements(original, graph, root=root)
    updated_hash = catalog.sha256_tree(original, file_modes=modes, replacements=replacements)
    mirror = publication.checked_path(root, entry["mirrored_path"])
    if catalog.sha256_tree(mirror, file_modes=entry.get("file_modes")) != entry["skill_dir_sha256"]:
        raise ValueError("existing mirror differs from catalog")
    if entry.get("dependency_graph") == graph["id"] and entry["skill_dir_sha256"] == updated_hash:
        return root, {}, 0
    if entry.get("dependency_graph") is not None or entry["skill_dir_sha256"] != graph["previous_mirror_sha256"]:
        raise ValueError("previous mirror differs from qualified migration baseline")
    for file in catalog.skill_tree_files(original):
        relative = file.relative_to(original).as_posix()
        if relative not in replacements and catalog.sanitized_file_bytes(file) != catalog.sanitized_file_bytes(
            mirror / relative
        ):
            raise ValueError(f"nondependency source resource differs: {relative}")
    if receipt_target.exists():
        raise ValueError("refresh receipt must be a new file")
    originals = copy.deepcopy(documents)
    previous = {key: entry.get(key) for key in ("dependency_graph", "skill_dir_sha256", "file_modes")}
    updated = {"dependency_graph": graph["id"], "skill_dir_sha256": updated_hash, "file_modes": modes}
    entry.update(updated)
    locked.update(updated)
    for relative in METADATA[2:]:
        for record in documents[relative]:
            if record["id"] == skill_id:
                record.update(updated)
    receipt = {
        "schema_version": 1,
        "evidence_class": "locked-public-source-complete-dependency-graph-refresh",
        "skill_id": skill_id,
        "graph": graph,
        "previous": previous,
        "updated": updated,
        "sources_upgraded": False,
        "skill_text_changed": False,
        "findings_suppressed": False,
        "agent_efficacy_scored": False,
        "previous_graph_sha256": {
            name: hashlib.sha256((mirror / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for name in replacements
        },
    }

    def build(stage: Path) -> None:
        for relative, value in documents.items():
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(metadata_bytes(value, raw[relative]))
        destination = stage / entry["mirrored_path"]
        catalog.copy_sanitized_tree(original, destination, file_modes=modes, replacements=replacements)
        if catalog.sha256_tree(destination, file_modes=modes) != updated_hash:
            raise ValueError("staged dependency mirror differs from qualification")
        checked_source(source_root, source)
        if dependency_graphs.replacements(original, graph, root=root) != replacements:
            raise ValueError("dependency graph changed while staging")
        for relative, value in originals.items():
            if json.loads((root / relative).read_bytes()) != value:
                raise ValueError("catalog input changed while staging")
        catalog.write_json(stage / receipt_path, receipt)

    transaction, journal = publication.prepare(root, (*METADATA, entry["mirrored_path"], receipt_path), build)
    return transaction, journal, 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--skill-id", required=True)
    parser.add_argument("--receipt", required=True)
    parser.add_argument("--check", action="store_true", help="Stage without publication; fail on pending changes")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        transaction, journal, count = prepare(ROOT, args.source_root.resolve(), args.skill_id, args.receipt)
        if count and not args.check:
            publication.publish(ROOT, transaction, journal)
        result = {
            "ok": not count if args.check else True,
            "updates": count,
            "mode": "check" if args.check else "publish",
            "recovery_directory": str(transaction),
        }
        print(json.dumps(result) if args.json else result)
        return int(args.check and bool(count))
    except (OSError, ValueError, KeyError, StopIteration, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}) if args.json else str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

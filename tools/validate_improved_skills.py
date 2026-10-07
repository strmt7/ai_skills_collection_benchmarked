#!/usr/bin/env python3
"""Validate experimental overlays, original provenance, and recorded hashes."""

from __future__ import annotations

import argparse
import re
from pathlib import Path, PurePosixPath
from typing import Any

from _lib_b.frontmatter_utils import parse
from _lib_b.io_utils import read_json
from build_catalog import sha256_file

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


def inside(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        raise ValueError("manifest paths must be nonempty relative strings")
    path = root / value
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("manifest path escapes the repository")
    return path.resolve()


def validate(manifest: Any, catalog: list[dict[str, Any]], root: Path) -> list[str]:
    errors = []
    if not isinstance(manifest, dict):
        return ["overlay manifest must be an object"]
    if manifest.get("manifest_version") != 1:
        errors.append("unsupported manifest_version")
    by_id = {entry["id"]: entry for entry in catalog}
    seen = set()
    items = manifest.get("skills")
    if not isinstance(items, list) or not items:
        return [*errors, "overlay manifest must contain a nonempty skills list"]
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get("skill_id"), str):
            errors.append("each overlay record must be an object with a string skill_id")
            continue
        skill_id = item.get("skill_id")
        if skill_id in seen:
            errors.append(f"duplicate overlay: {skill_id}")
        seen.add(skill_id)
        source = by_id.get(skill_id)
        if not source:
            errors.append(f"unknown source skill: {skill_id}")
            continue
        try:
            overlay = inside(root, item["overlay_path"])
            original = inside(root, item["original_path"])
            mirror = inside(root, source["mirrored_path"])
            if overlay == mirror or overlay.is_relative_to(mirror) or mirror.is_relative_to(overlay):
                errors.append(f"{skill_id}: overlay overlaps immutable source mirror")
            if not original.resolve().is_relative_to(overlay.resolve()):
                errors.append(f"{skill_id}: original provenance must be inside overlay")
            expected = source["skill_file_sha256"]
            if item.get("source_file_sha256") != expected or sha256_file(original) != expected:
                errors.append(f"{skill_id}: original provenance differs from locked source")
            if sha256_file(mirror / "SKILL.md") != expected:
                errors.append(f"{skill_id}: immutable source mirror was changed")
            if item.get("source_commit") != source["commit_sha"]:
                errors.append(f"{skill_id}: source commit differs from catalog")
            if item.get("source_url") != source["immutable_source_url"]:
                errors.append(f"{skill_id}: source URL differs from catalog")
            skill_file = overlay / "SKILL.md"
            if sha256_file(skill_file) != item.get("overlay_sha256"):
                errors.append(f"{skill_id}: overlay hash mismatch")
            meta, _ = parse(skill_file.read_text(encoding="utf-8"))
            if not meta:
                errors.append(f"{skill_id}: missing YAML frontmatter")
                continue
            name = meta.get("name")
            if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
                errors.append(f"{skill_id}: invalid skill name")
            elif name != overlay.name:
                errors.append(f"{skill_id}: skill name differs from directory")
            description = meta.get("description")
            if not isinstance(description, str) or not 1 <= len(description.strip()) <= 1024:
                errors.append(f"{skill_id}: invalid description")
            if meta.keys() - ALLOWED_FIELDS:
                errors.append(f"{skill_id}: unsupported frontmatter fields")
            metadata = meta.get("metadata", {})
            if not isinstance(metadata, dict) or not all(
                isinstance(key, str) and isinstance(value, str) for key, value in metadata.items()
            ):
                errors.append(f"{skill_id}: metadata must contain string keys and values")
            if meta.get("license") != item.get("license") or not (overlay / "LICENSE").is_file():
                errors.append(f"{skill_id}: missing or inconsistent license notice")
            elif sha256_file(overlay / "LICENSE") != item.get("license_file_sha256"):
                errors.append(f"{skill_id}: license notice hash mismatch")
            package_files = item.get("package_file_sha256")
            if not isinstance(package_files, dict) or not package_files:
                errors.append(f"{skill_id}: complete package file hashes required")
            else:
                actual_files = {}
                for file in overlay.rglob("*"):
                    if file.is_symlink() or not file.resolve().is_relative_to(overlay.resolve()):
                        errors.append(f"{skill_id}: linked or escaping package input")
                    elif file.is_file():
                        actual_files[file.relative_to(overlay).as_posix()] = sha256_file(file)
                for name, digest in package_files.items():
                    if (
                        not isinstance(name, str)
                        or "\\" in name
                        or ":" in name
                        or PurePosixPath(name).is_absolute()
                        or PurePosixPath(name).as_posix() != name
                        or ".." in PurePosixPath(name).parts
                        or not isinstance(digest, str)
                        or not re.fullmatch(r"[0-9a-f]{64}", digest)
                    ):
                        errors.append(f"{skill_id}: invalid package hash record")
                if actual_files != package_files:
                    errors.append(f"{skill_id}: package file coverage or hash mismatch")
            if item.get("performance_status") != "unbenchmarked":
                errors.append(f"{skill_id}: performance claims require the separate agent-trial evidence system")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{skill_id}: {exc}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data/improved_skills_manifest.json")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    import json

    args = build_parser().parse_args(argv)
    try:
        manifest = read_json(args.manifest)
        errors = validate(manifest, read_json(ROOT / "data/skills_catalog.json"), ROOT)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors = [str(exc)]
    print(
        json.dumps({"errors": errors}, indent=2) if args.json else f"Improved overlay validation: {len(errors)} errors"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

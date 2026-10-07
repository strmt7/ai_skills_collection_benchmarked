#!/usr/bin/env python3
"""Stage pinned source and a complete current dependency graph for offline controls."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
from pathlib import Path

import _catalog_publication as publication
from _lib_b.io_utils import read_json
from build_catalog import sha256_tree

ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = "varnan-tech-opendirectory-packages-cli-skills-blog-cover-image-cli-skill-md"
FIXTURE = "benchmarks/dependency-regressions/fixtures/image-cli-current"


def files(path: Path) -> dict[str, str]:
    result = {}

    def fail(error: OSError) -> None:
        raise error

    for directory, directories, names in os.walk(path, followlinks=False, onerror=fail):
        if Path(directory) == path:
            directories[:] = [name for name in directories if name != "node_modules"]
        for name in directories + names:
            item = Path(directory) / name
            info = item.lstat()
            if item.is_symlink() or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError("control inputs must not contain links/reparse points")
            if name in names:
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("control inputs must be regular files")
                result[item.relative_to(path).as_posix()] = hashlib.sha256(item.read_bytes()).hexdigest()
    return result


def prepare(root: Path, target: Path, *, check: bool = False) -> dict[str, object]:
    root, target = root.resolve(), target.absolute()
    # Provision only an explicitly requested directory within this workspace.
    if not target.is_relative_to(root) or target == root:
        raise ValueError("control stage must be inside the workspace")
    target = publication.checked_path(root, target.relative_to(root).as_posix())
    source = next(entry for entry in read_json(root / "data/skills_catalog.json") if entry["id"] == SKILL_ID)
    mirror = publication.checked_path(root, source["mirrored_path"])
    if target == mirror or target.is_relative_to(mirror) or mirror.is_relative_to(target):
        raise ValueError("control stage cannot overlap the immutable source mirror")
    fixture = publication.checked_path(root, FIXTURE)
    if target == fixture or target.is_relative_to(fixture) or fixture.is_relative_to(target):
        raise ValueError("control stage cannot overlap the pinned dependency fixture")
    if sha256_tree(mirror, file_modes=source.get("file_modes")) != source["skill_dir_sha256"]:
        raise ValueError("immutable source mirror differs from catalog")
    originals = files(mirror)
    expected = originals.copy()
    for name in ("package.json", "package-lock.json", "LICENSE"):
        expected[name] = hashlib.sha256((fixture / name).read_bytes()).hexdigest()
    package, lock = read_json(fixture / "package.json"), read_json(fixture / "package-lock.json")
    if package["dependencies"] != lock["packages"][""]["dependencies"]:
        raise ValueError("package declaration and complete lockfile disagree")
    if any(
        lock["packages"][f"node_modules/{name}"]["version"] != version
        for name, version in package["dependencies"].items()
    ):
        raise ValueError("direct dependency resolutions differ from pinned versions")
    if not check:
        if target.exists():
            raise ValueError("control stage already exists; refusing replacement")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.mkdir()
        for relative in files(mirror):
            destination = publication.checked_path(target, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(mirror / relative, destination)
        for name in ("package.json", "package-lock.json", "LICENSE"):
            (target / name).write_bytes((fixture / name).read_bytes())
    if not target.is_dir() or files(target) != expected:
        raise ValueError("control stage input files differ from pinned source/fixture")
    return {
        "ok": True,
        "evidence_class": "control-stage-source-and-graph-provenance",
        "skill_id": SKILL_ID,
        "source_commit": source["commit_sha"],
        "source_url": source["immutable_source_url"],
        "original_source_file_sha256": originals,
        "staged_file_sha256": expected,
        "stage": target.relative_to(root).as_posix(),
        "dependencies_installed_by_this_tool": False,
        "runtime_controls_executed_by_this_tool": False,
        "performance_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=Path, required=True, help="New workspace directory (or existing with --check)")
    parser.add_argument("--check", action="store_true", help="Verify source and graph files without replacing them")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = prepare(ROOT, args.stage, check=args.check)
    except (OSError, ValueError, KeyError, StopIteration, TypeError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    print(json.dumps(result, indent=2) if args.json else result)
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

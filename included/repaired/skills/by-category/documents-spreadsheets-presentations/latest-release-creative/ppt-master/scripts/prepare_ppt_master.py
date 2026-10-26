"""Create an independent, source-checked PPT Master copy with a repaired editor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

SOURCE_TREE = "875410619eee330cedb49cab986adbc0fa0722c62bfc0a584352b5b678d6ed76"
ORIGINAL_SCRIPT_LF = "57b6139bfab8be058e8ced99e47dde86a89dddcc58bfb9cc53baa9ab175c747a"
REPAIRED_SCRIPT = "25aad0d453babd2df3c4f3b9185308a5b94bae738868ad520044f55792b74cb7"
RELATIVE = "scripts/svg_editor/static/app.js"
SOURCE = "included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master"


def source_script_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def no_links(root: Path) -> None:
    def fail_on_error(error: OSError) -> None:
        raise error

    for current, directories, files in os.walk(root, followlinks=False, onerror=fail_on_error):
        for name in [*directories, *files]:
            path = Path(current) / name
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(
                stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
            ):
                raise ValueError(f"link or reparse point in source: {path.relative_to(root)}")


def prepare(repo: Path, candidate: Path, destination: Path) -> dict[str, str]:
    repo = repo.resolve(strict=True)
    source = repo
    for part in Path(SOURCE).parts:
        source = source / part
        info = source.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
        ):
            raise ValueError("source path contains a link or reparse point")
    source = source.resolve(strict=True)
    if not source.is_relative_to(repo):
        raise ValueError("source path escapes the repository")
    candidate = candidate.resolve(strict=True)
    destination = destination.absolute()
    if not destination.parent.is_dir():
        raise ValueError("destination parent must exist")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError("destination already exists")
    resolved_destination = destination.resolve()
    if (
        resolved_destination == repo
        or repo.is_relative_to(resolved_destination)
        or resolved_destination.is_relative_to(source)
    ):
        raise ValueError("destination overlaps source or repository root")
    repaired = candidate.read_bytes()
    if hashlib.sha256(repaired).hexdigest() != REPAIRED_SCRIPT:
        raise ValueError("repair bytes do not match their qualified digest")
    sys.path.insert(0, str(repo / "tools"))
    import build_catalog

    lock = json.loads((repo / "data/source_lock.json").read_bytes())
    matches = [
        (s, entry)
        for s in lock["sources"]
        for entry in s["skills"]
        if s["repo"] == "hugohe3/ppt-master" and entry["install_name"] == "ppt-master"
    ]
    if len(matches) != 1:
        raise ValueError("source lock must contain exactly one PPT Master entry")
    _, entry = matches[0]
    if entry["skill_dir_sha256"] != SOURCE_TREE:
        raise ValueError("source lock changed; requalify this repair")
    modes = entry["file_modes"]
    policy = entry["credential_policy_version"]
    no_links(source)
    if source_script_sha256(source / RELATIVE) != ORIGINAL_SCRIPT_LF:
        raise ValueError("original editor bytes differ from the qualified source")
    observed = build_catalog.sha256_tree(source, file_modes=modes, credential_policy=policy)
    if observed != SOURCE_TREE:
        raise ValueError("source tree differs from its lock")
    replacement = {RELATIVE: repaired}
    expected = build_catalog.sha256_tree(source, file_modes=modes, credential_policy=policy, replacements=replacement)
    destination.mkdir()
    try:
        build_catalog.copy_sanitized_tree(
            source, destination, file_modes=modes, credential_policy=policy, replacements=replacement
        )
        if build_catalog.sha256_tree(destination, file_modes=modes, credential_policy=policy) != expected:
            raise ValueError("prepared tree failed digest verification")
        if build_catalog.sha256_tree(source, file_modes=modes, credential_policy=policy) != SOURCE_TREE:
            raise ValueError("source changed during preparation")
    except Exception as error:
        raise RuntimeError(f"preparation failed; inspect the new incomplete directory {destination}") from error
    return {
        "source_tree": SOURCE_TREE,
        "prepared_tree": expected,
        "repaired_script_sha256": REPAIRED_SCRIPT,
        "destination": str(destination),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.repo, Path(__file__).with_name("app.js"), args.destination)
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

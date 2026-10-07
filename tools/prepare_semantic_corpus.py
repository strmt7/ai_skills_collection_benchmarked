#!/usr/bin/env python3
"""Prepare a bound, verifiable UTF-8 corpus without executing or indexing inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

MAX_FILE_BYTES = 4 * 1024 * 1024


def canonical_name(name: str) -> str:
    path = PurePosixPath(name)
    if (
        not name
        or name == "."
        or ":" in name
        or "\\" in name
        or path.is_absolute()
        or path.as_posix() != name
        or ".." in path.parts
    ):
        raise ValueError("input paths must be canonical relative POSIX paths")
    return name


def regular_file(root: Path, name: str) -> Path:
    path = root / canonical_name(name)
    for part in (path, *path.parents):
        if part == root:
            break
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"symlink or reparse-point resource: {name}")
    if not path.resolve().is_relative_to(root) or not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"nonregular or external resource: {name}")
    return path


def fingerprint(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


def git_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        capture_output=True,
        timeout=60,
        check=True,
    )
    return sorted({canonical_name(name.decode("utf-8")) for name in result.stdout.split(b"\0") if name})


def inventory(root: Path, prefixes: list[str]) -> dict[str, Any]:
    prefixes = sorted({canonical_name(prefix) for prefix in prefixes})
    if not prefixes:
        raise ValueError("select at least one explicit input prefix")
    if any(prefix == ".venv" or prefix.startswith(".venv/") for prefix in prefixes):
        raise ValueError("corpus inputs may not include local .venv state")
    records: dict[str, Any] = {}
    for name in git_files(root):
        if not any(name == prefix or name.startswith(prefix + "/") for prefix in prefixes):
            continue
        path = regular_file(root, name)
        digest, size = fingerprint(path)
        reason = None
        if size > MAX_FILE_BYTES:
            reason = "larger_than_4_mib"
        else:
            with path.open("rb") as stream:
                data = stream.read(MAX_FILE_BYTES + 1)
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError(f"input changed while reading: {name}")
            if b"\0" in data:
                reason = "contains_nul"
            else:
                try:
                    data.decode("utf-8")
                except UnicodeDecodeError:
                    reason = "not_utf8"
        records[name] = {"sha256": digest, "bytes": size, "excluded_reason": reason}
    if not records or not any(record["excluded_reason"] is None for record in records.values()):
        raise ValueError("the selected corpus contains no indexable text")
    return {"schema_version": 1, "source_root": str(root), "prefixes": prefixes, "files": records}


def checked_output(root: Path, output: Path) -> Path:
    # Corpus state is local and deliberately outside the selected source inputs.
    # Restrict it to the repository's ignored workspace, never a home/global index.
    destination = output.resolve()
    state_root = root / ".venv"
    if not destination.is_relative_to(state_root) or destination == state_root:
        raise ValueError("output must be a child of the source repository's .venv directory")
    cursor = output.absolute()
    while cursor != root and cursor != cursor.parent:
        if cursor.exists() and (cursor.is_symlink() or getattr(cursor.lstat(), "st_file_attributes", 0) & 0x400):
            raise ValueError("output may not traverse symlinks or reparse points")
        cursor = cursor.parent
    return destination


def corpus_errors(output: Path, expected: dict[str, Any]) -> list[str]:
    errors = []
    tree = output / "tree"
    names: set[str] = set()
    if not tree.is_dir() or tree.is_symlink():
        return ["corpus tree is missing or is a symlink"]

    def walk_error(error: OSError) -> None:
        raise error

    for directory, children, files in os.walk(tree, followlinks=False, onerror=walk_error):
        # CocoIndex owns only this explicit state directory, not source resources.
        if Path(directory) == tree:
            children[:] = [name for name in children if name != ".cocoindex_code"]
        for child in tuple(children):
            child_path = Path(directory) / child
            if child_path.is_symlink() or getattr(child_path.lstat(), "st_file_attributes", 0) & 0x400:
                errors.append(f"nonregular corpus directory: {child_path.relative_to(tree).as_posix()}")
                children.remove(child)
        names.update((Path(directory) / name).relative_to(tree).as_posix() for name in files)
    wanted = {name for name, record in expected["files"].items() if record["excluded_reason"] is None}
    errors.extend(f"missing corpus resource: {name}" for name in sorted(wanted - names))
    errors.extend(f"unexpected corpus resource: {name}" for name in sorted(names - wanted))
    for name in sorted(names & wanted):
        try:
            digest, size = fingerprint(regular_file(tree, name))
            if (digest, size) != (expected["files"][name]["sha256"], expected["files"][name]["bytes"]):
                errors.append(f"changed corpus resource: {name}")
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    return errors


def prepare(root: Path, output: Path, prefixes: list[str], *, check: bool) -> dict[str, Any]:
    root = root.resolve(strict=True)
    output = checked_output(root, output)
    expected = inventory(root, prefixes)
    errors = []
    if check:
        manifest_path = regular_file(output, "manifest.json")
        recorded = json.loads(manifest_path.read_text(encoding="utf-8"))
        if recorded != expected:
            errors.append("source inventory or binding changed; prepare a new corpus")
    else:
        output.mkdir(parents=True, exist_ok=False)
        tree = output / "tree"
        tree.mkdir()
        for name, record in expected["files"].items():
            if record["excluded_reason"] is not None:
                continue
            with regular_file(root, name).open("rb") as stream:
                data = stream.read(MAX_FILE_BYTES + 1)
            if hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise ValueError(f"input changed before copying: {name}")
            target = tree / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        if inventory(root, prefixes) != expected:
            raise ValueError("source inventory changed during preparation")
    errors.extend(corpus_errors(output, expected))
    if not check and not errors:
        (output / "manifest.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": not errors,
        "errors": errors,
        "selected_files": len(expected["files"]),
        "text_files": sum(record["excluded_reason"] is None for record in expected["files"].values()),
        "excluded_files": {
            name: record["excluded_reason"] for name, record in expected["files"].items() if record["excluded_reason"]
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--prefix", action="append", required=True, help="Explicit repository-relative input path; repeatable."
    )
    parser.add_argument(
        "--check", action="store_true", help="Verify binding, full selected inventory and copied bytes without writing."
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = prepare(args.root, args.output, args.prefix, check=args.check)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    print(
        json.dumps(result, indent=2)
        if args.json
        else ("OK: verified corpus" if result["ok"] else "ERROR: " + "; ".join(result["errors"]))
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

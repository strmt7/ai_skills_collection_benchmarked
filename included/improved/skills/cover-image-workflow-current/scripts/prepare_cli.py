#!/usr/bin/env python3
"""Prepare a source-locked CLI repair in a new directory without installing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
from pathlib import Path, PurePosixPath

OVERLAY = Path(__file__).resolve().parents[1]


def digest(data: bytes, *, text: bool = False) -> str:
    if text:
        data = data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def linked(path: Path) -> bool:
    info = path.lstat()
    return path.is_symlink() or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def prepare(source: Path, output: Path) -> dict:
    if linked(source) or not source.is_dir():
        raise ValueError("source must be an unlinked directory")
    source, output = source.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("output must be new and must not overlap source")
    if output.is_relative_to(OVERLAY) or OVERLAY.is_relative_to(output):
        raise ValueError("output must not overlap the repair overlay")
    lock = json.loads((OVERLAY / "references/source-files.json").read_text(encoding="utf-8"))
    expected = {item["path"]: item for item in lock["source_files"]}
    inputs = {}
    for file in source.rglob("*"):
        if linked(file):
            raise ValueError("linked source entry is not allowed")
        if file.is_dir():
            continue
        if not stat.S_ISREG(file.stat().st_mode):
            raise ValueError("source entries must be regular files or directories")
        relative = file.relative_to(source).as_posix()
        if relative not in expected:
            raise ValueError(f"unexpected source file: {relative}")
        data = file.read_bytes()
        if digest(data, text=expected[relative]["text"]) != expected[relative]["sha256"]:
            raise ValueError(f"source hash mismatch: {relative}")
        inputs[relative] = data
    if inputs.keys() != expected.keys():
        raise ValueError("source inventory is incomplete")
    replacements = {}
    for item in lock["replacements"]:
        name = item["path"]
        if name not in inputs or PurePosixPath(name).as_posix() != name:
            raise ValueError("replacement must name a locked source file")
        data = (OVERLAY / "assets" / PurePosixPath(name).name).read_bytes()
        if digest(data, text=True) != item["sha256"]:
            raise ValueError(f"replacement hash mismatch: {name}")
        replacements[name] = data
    # Validate every input before creating output. Write the same bytes we checked.
    output.mkdir(parents=True)
    for relative, data in (inputs | replacements).items():
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(data)
    receipt = {
        "schema_version": 1,
        "source_commit": lock["source_commit"],
        "source_files": [{"path": name, "sha256": digest(data)} for name, data in sorted(inputs.items())],
        "replacements": lock["replacements"],
        "preparer_sha256": digest(Path(__file__).read_bytes()),
        "source_lock_sha256": digest((OVERLAY / "references/source-files.json").read_bytes()),
        "dependencies_installed": False,
        "real_provider_qualified": False,
        "agent_efficacy_scored": False,
    }
    with (output / "repair-preparation.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True, help="exact mirrored package, without node_modules")
    parser.add_argument("--output", type=Path, required=True, help="new, separate staging directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        receipt = prepare(args.source, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"prepared": False, "error": str(error)}))
        return 1
    print(json.dumps({"prepared": True, "files": len(receipt["source_files"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

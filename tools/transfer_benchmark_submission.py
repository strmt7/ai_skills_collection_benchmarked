#!/usr/bin/env python3
"""Seal changes between complete benchmark captures and rebuild the submitted tree."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import stat
import tarfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO

from _trial_collection_manifest import validate_manifest
from _trial_collection_policy import collection_policy
from _trial_transcript import strict_json

MAX_MANIFEST_BYTES = 16 * 1024**2


@dataclass(frozen=True, slots=True)
class Handoff:
    baseline: dict[str, Any]
    submission: dict[str, Any]
    delta: dict[str, Any]

    @property
    def max_archive_bytes(self) -> int:
        policy = self.submission["policy"]
        return policy["max_total_bytes"] + policy["max_files"] * 4096 + 2 * MAX_MANIFEST_BYTES


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def plan_handoff(baseline: bytes, submission: bytes) -> Handoff:
    if any(not 0 < len(raw) <= MAX_MANIFEST_BYTES for raw in (baseline, submission)):
        raise ValueError("Capture manifest is empty or exceeds its size bound")
    original = strict_json(baseline.decode("utf-8"))
    if not isinstance(original, dict):
        raise ValueError("Baseline capture is not a complete manifest")
    policy = collection_policy(original.get("policy"))
    before = validate_manifest(original, policy)
    after = validate_manifest(strict_json(submission.decode("utf-8")), policy)
    previous, current = before["files"], after["files"]
    delta = {
        "handoff_version": 1,
        "baseline_manifest_sha256": _sha(baseline),
        "submission_manifest_sha256": _sha(submission),
        "writes": {name: current[name] for name in sorted(current) if current[name] != previous.get(name)},
        "deletes": sorted(previous.keys() - current.keys()),
    }
    return Handoff(before, after, delta)


def _encoded(delta: Mapping[str, Any]) -> bytes:
    return (json.dumps(delta, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def _ordinary(path: Path, *, directory: bool) -> None:
    info = path.lstat()
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected_type(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError(f"Captured object has an unexpected file type: {path.name}")


def _inventory(root: Path, manifest: dict[str, Any]) -> None:
    """Check the closed, controller-owned copy against its exact declared namespace."""
    _ordinary(root, directory=True)
    directories = set(manifest["directories"])
    files = manifest["files"]
    pending = [root]
    directory_count = file_count = 0
    while pending:
        for path in pending.pop().iterdir():
            name = path.relative_to(root).as_posix()
            if name in directories:
                _ordinary(path, directory=True)
                pending.append(path)
                directory_count += 1
            elif name in files:
                _ordinary(path, directory=False)
                file_count += 1
            else:
                raise ValueError(f"Capture contains an undeclared entry: {name}")
    if directory_count != len(directories) or file_count != len(files):
        raise ValueError("Capture is missing declared directories or files")


def _read_file(root: Path, name: str, identity: dict[str, Any]) -> bytes:
    path = root / name
    _ordinary(path, directory=False)
    with path.open("rb") as stream:
        data = stream.read(identity["bytes"] + 1)
    if len(data) != identity["bytes"] or _sha(data) != identity["sha256"]:
        raise ValueError(f"Captured bytes differ from the receipt: {name}")
    return data


def _disjoint(first: Path, second: Path) -> None:
    a, b = first.resolve(), second.resolve()
    if a.is_relative_to(b) or b.is_relative_to(a):
        raise ValueError("Handoff inputs and output must be disjoint")


def _add(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    member = tarfile.TarInfo(name)
    member.size, member.mode = len(data), 0o444
    archive.addfile(member, io.BytesIO(data))


def _archive_digest(stream: BinaryIO, maximum: int) -> str:
    stream.seek(0)
    digest = hashlib.sha256()
    size = 0
    while chunk := stream.read(1024**2):
        size += len(chunk)
        if size > maximum:
            raise ValueError("Handoff archive exceeds its size bound")
        digest.update(chunk)
    if not size:
        raise ValueError("Handoff archive is empty")
    stream.seek(0)
    return digest.hexdigest()


def seal(handoff: Handoff, submission_tree: Path, bundle: Path) -> dict[str, Any]:
    """Verify the entire capture and export only changed file bytes."""
    _disjoint(submission_tree, bundle)
    _inventory(submission_tree, handoff.submission)
    writes = handoff.delta["writes"]
    output = bundle.open("x+b")
    try:
        with output:
            with tarfile.open(fileobj=output, mode="w:", format=tarfile.PAX_FORMAT) as archive:
                _add(archive, "manifest.json", _encoded(handoff.delta))
                for name, identity in sorted(handoff.submission["files"].items()):
                    raw = _read_file(submission_tree, name, identity)
                    if name in writes:
                        _add(archive, "payload/" + name, raw)
            output.flush()
            digest = _archive_digest(output, handoff.max_archive_bytes)
    except BaseException:
        bundle.unlink(missing_ok=True)
        raise
    return {"status": "handoff_sealed", "archive_sha256": digest, **handoff.delta}


def _member(archive: tarfile.TarFile, name: str, size: int) -> bytes:
    info = archive.next()
    if (
        info is None
        or info.type != tarfile.REGTYPE
        or info.name != name
        or info.size != size
        or info.linkname
        or info.sparse is not None
        or set(info.pax_headers) - {"path"}
    ):
        raise ValueError(f"Archive member does not match the declared inventory: {name}")
    stream = archive.extractfile(info)
    if stream is None:
        raise ValueError(f"Archive has no bytes for {name}")
    with stream:
        data = stream.read(size + 1)
    if len(data) != size:
        raise ValueError(f"Archive member is incomplete: {name}")
    return data


def restore(handoff: Handoff, baseline_tree: Path, bundle: Path, digest: str, output: Path) -> dict[str, Any]:
    """Rebuild a fresh grader tree from the admitted baseline and exact delta."""
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError("Expected the controller's lowercase archive SHA-256")
    _disjoint(baseline_tree, output)
    _disjoint(bundle, output)
    _ordinary(bundle, directory=False)
    _inventory(baseline_tree, handoff.baseline)
    previous = handoff.baseline["files"]
    writes = handoff.delta["writes"]
    for name in handoff.delta["deletes"] + list(writes.keys() & previous.keys()):
        _read_file(baseline_tree, name, previous[name])
    with bundle.open("rb") as source:
        if _archive_digest(source, handoff.max_archive_bytes) != digest:
            raise ValueError("Archive bytes differ from the controller's digest")
        with tarfile.open(fileobj=source, mode="r:") as archive:
            expected = _encoded(handoff.delta)
            if _member(archive, "manifest.json", len(expected)) != expected:
                raise ValueError("Archive manifest differs from the two complete captures")
            output.mkdir()
            try:
                for name in handoff.submission["directories"]:
                    (output / name).mkdir()
                for name, identity in sorted(handoff.submission["files"].items()):
                    if name in writes:
                        data = _member(archive, "payload/" + name, identity["bytes"])
                        if _sha(data) != identity["sha256"]:
                            raise ValueError(f"Archive payload differs from the submitted bytes: {name}")
                    else:
                        data = _read_file(baseline_tree, name, identity)
                    (output / name).write_bytes(data)
                if archive.next() is not None:
                    raise ValueError("Archive has an undeclared payload")
            except BaseException:
                shutil.rmtree(output)
                raise
    return {
        "status": "grader_tree_rebuilt",
        "archive_sha256": digest,
        "file_count": handoff.submission["file_count"],
        "directory_count": handoff.submission["directory_count"],
        "total_bytes": handoff.submission["total_bytes"],
        **handoff.delta,
    }


def _read_manifest(path: Path) -> bytes:
    _ordinary(path, directory=False)
    with path.open("rb") as stream:
        return stream.read(MAX_MANIFEST_BYTES + 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-manifest", required=True, type=Path)
    parser.add_argument("--submission-manifest", required=True, type=Path)
    subcommands = parser.add_subparsers(dest="operation", required=True)
    prepare = subcommands.add_parser("seal", help="Verify a completed capture and export its changes")
    prepare.add_argument("--submission-tree", required=True, type=Path)
    prepare.add_argument("--bundle", required=True, type=Path)
    replay = subcommands.add_parser("restore", help="Rebuild a fresh tree using the controller's archive digest")
    replay.add_argument("--baseline-tree", required=True, type=Path)
    replay.add_argument("--bundle", required=True, type=Path)
    replay.add_argument("--archive-sha256", required=True)
    replay.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        handoff = plan_handoff(_read_manifest(args.baseline_manifest), _read_manifest(args.submission_manifest))
        if args.operation == "seal":
            report = seal(handoff, args.submission_tree, args.bundle)
        else:
            report = restore(handoff, args.baseline_tree, args.bundle, args.archive_sha256, args.output)
    except (OSError, ValueError, tarfile.TarError) as exc:
        print(json.dumps({"status": "handoff_unverified", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

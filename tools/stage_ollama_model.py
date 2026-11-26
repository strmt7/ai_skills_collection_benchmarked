"""Stage an exact Ollama model in a private, independently writable store."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import time
from pathlib import Path
from typing import Any

from _trial_transcript import strict_json
from _windows_appcontainer import checked_path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_LIMIT = 1024**2
CHUNK_BYTES = 4 * 1024**2
COPY_BYTES_PER_SECOND = 64 * 1024**2


def manifest_blobs(manifest: object) -> dict[str, int]:
    """Return unique content identities and lengths from a publisher manifest."""
    if (
        not isinstance(manifest, dict)
        or type(manifest.get("schemaVersion")) is not int
        or manifest["schemaVersion"] != 2
        or not isinstance(manifest.get("layers"), list)
        or not manifest["layers"]
    ):
        raise ValueError("Expected a schema-2 Ollama model manifest with layers")
    blobs: dict[str, int] = {}
    for entry in [manifest.get("config"), *manifest["layers"]]:
        if not isinstance(entry, dict):
            raise ValueError("Each model descriptor must declare a digest and size")
        digest, size = entry.get("digest"), entry.get("size")
        if (
            not isinstance(digest, str)
            or re.fullmatch(r"sha256:[a-f0-9]{64}", digest) is None
            or type(size) is not int
            or not 0 <= size <= 2**63 - 1
            or blobs.get(digest, size) != size
        ):
            raise ValueError("A model descriptor has an invalid digest or conflicting size")
        blobs[digest] = size
    return blobs


def fingerprint(info: os.stat_result) -> tuple[int, int, int, int]:
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def copy_verified_blob(source: Path, target: Path, expected: str, size: int) -> None:
    """Copy model bytes at a limited rate and verify their source state."""
    source = checked_path(source)
    before = source.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size != size:
        raise ValueError("Cached model blob has the wrong type or size")
    digest = hashlib.sha256()
    total = 0
    started = time.monotonic()
    with source.open("rb") as reader, target.open("xb") as writer:
        while block := reader.read(min(CHUNK_BYTES, size + 1 - total)):
            total += len(block)
            if total > size:
                raise ValueError("Cached model blob grew during staging")
            digest.update(block)
            writer.write(block)
            delay = started + total / COPY_BYTES_PER_SECOND - time.monotonic()
            if delay > 0:
                time.sleep(delay)
    if total != size or "sha256:" + digest.hexdigest() != expected or fingerprint(source.stat()) != fingerprint(before):
        raise ValueError("Cached model blob differs from its frozen identity")


def stage_model(model: str, manifest: Path, manifest_sha256: str, cached_blobs: Path, output: Path) -> dict[str, Any]:
    """Create a fresh local store and install its manifest after all copies verify."""
    match = re.fullmatch(r"([a-z0-9][a-z0-9_.-]*):([a-zA-Z0-9_][a-zA-Z0-9_.-]*)", model)
    if match is None:
        raise ValueError("Use an explicit library model and tag, such as qwen3:4b")
    name, tag = match.groups()
    devices = re.compile(r"(?i:con|prn|aux|nul|com[0-9]|lpt[0-9])")
    if any(part.endswith(".") or devices.fullmatch(part.split(".", 1)[0]) for part in (name, tag)):
        raise ValueError("The model and tag must be portable path components")
    with checked_path(manifest).open("rb") as stream:
        raw = stream.read(MANIFEST_LIMIT + 1)
    if len(raw) > MANIFEST_LIMIT or hashlib.sha256(raw).hexdigest() != manifest_sha256:
        raise ValueError("Model manifest differs from its frozen identity")
    blobs = manifest_blobs(strict_json(raw.decode("utf-8")))
    base = checked_path(cached_blobs)
    target = checked_path(output)
    if target.is_relative_to(base) or not base.is_dir():
        raise ValueError("Use an existing cache and a separate destination")
    size = sum(blobs.values())
    if shutil.disk_usage(target.parent).free < size + len(raw):
        raise ValueError("Insufficient space for an independently writable model store")
    target.mkdir()
    created = target.stat()
    try:
        (target / "blobs").mkdir()
        for digest, length in blobs.items():
            filename = digest.replace(":", "-")
            copy_verified_blob(base / filename, target / "blobs" / filename, digest, length)
        installed = target / "manifests/registry.ollama.ai/library" / name / tag
        installed.parent.mkdir(parents=True)
        installed.write_bytes(raw)
    except BaseException as failure:
        try:
            current = checked_path(target).stat()
            if (created.st_dev, created.st_ino) != (current.st_dev, current.st_ino):
                raise ValueError("The failed destination was replaced")
            shutil.rmtree(target)
        except (OSError, ValueError) as cleanup:
            failure.add_note(f"Staging cleanup failed: {cleanup}")
        raise
    return {
        "model": model,
        "manifest_sha256": manifest_sha256,
        "root": str(target),
        "verified": True,
        "storage": "independent_copies",
        "copied_bytes": size,
        "records": [{"digest": digest, "size": length} for digest, length in blobs.items()],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--cached-blobs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output = checked_path(args.output)
        if not output.is_relative_to(ROOT / ".venv") or output == ROOT / ".venv":
            raise ValueError("Stage model copies in a new directory under the checkout's .venv")
        receipt = stage_model(args.model, args.manifest, args.manifest_sha256, args.cached_blobs, output)
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    print(json.dumps({"ok": True, **receipt}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

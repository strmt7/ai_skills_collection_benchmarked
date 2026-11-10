"""Admit a complete pinned Python archive before writing its private payload."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any


def ordinary(path: Path) -> None:
    for part in (path, *path.parents):
        try:
            status = part.lstat()
        except FileNotFoundError:
            continue
        if part.is_symlink() or getattr(status, "st_file_attributes", 0) & 0x400:
            raise ValueError("Archive paths must not traverse a link or junction")


def snapshot(archive: Path, pin: dict[str, Any]) -> bytes:
    ordinary(archive)
    if not 0 < pin["archive_bytes"] <= 80_000_000 or archive.stat().st_size != pin["archive_bytes"]:
        raise ValueError("Archive size is outside its pinned bounds")
    raw = archive.read_bytes()
    if len(raw) != pin["archive_bytes"] or hashlib.sha256(raw).hexdigest() != pin["archive_sha256"]:
        raise ValueError("Archive size or SHA256 changed")
    return raw


def inspect(raw: bytes, pin: dict[str, Any]) -> dict[str, dict[str, Any]]:
    seen: set[str] = set()
    observed: dict[str, dict[str, Any]] = {}
    total = 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as stream:
        for member in stream:
            parts = member.name.split("/")
            if (
                not member.isfile()
                or member.name != PurePosixPath(member.name).as_posix()
                or parts[0] != "python"
                or len(parts) < 2
                or any(
                    part in {"", ".", ".."}
                    or part.endswith((".", " "))
                    or re.search(r'[<>:"\\|?*\x00-\x1f]', part)
                    or re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(\..*)?", part)
                    for part in parts
                )
                or member.name.casefold() in seen
            ):
                raise ValueError("Unsupported or noncanonical archive member")
            seen.add(member.name.casefold())
            expected = pin["archive_files"].get(member.name)
            if expected is None or member.size != expected["bytes"] or not 0 <= member.size <= 64 * 1024 * 1024:
                raise ValueError("Archive member is outside its pinned bounds")
            total += member.size
            if total > 256 * 1024 * 1024 or len(observed) >= 10000:
                raise ValueError("Archive exceeds its total declared bounds")
            source = stream.extractfile(member)
            if source is None:
                raise ValueError("An admitted regular member has no file contents")
            with source:
                content = source.read(member.size + 1)
            digest = hashlib.sha256(content).hexdigest()
            if len(content) != member.size or digest != expected["sha256"]:
                raise ValueError("Archive member content changed")
            observed[member.name] = {"bytes": len(content), "sha256": digest}
    if observed != pin["archive_files"]:
        raise ValueError("The complete archive inventory differs from its source pin")
    if any(
        "/".join(name.split("/")[:index]) in observed for name in observed for index in range(1, len(name.split("/")))
    ):
        raise ValueError("Archive members collide with parent directories")
    return observed


def extract(archive: Path, pin: dict[str, Any], output: Path) -> int:
    raw = snapshot(archive, pin)
    observed = inspect(raw, pin)
    ordinary(output)
    output.mkdir(exist_ok=False)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as stream:
        for member in stream:
            target = output.joinpath(*PurePosixPath(member.name).parts[1:])
            ordinary(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            source = stream.extractfile(member)
            if source is None:
                raise ValueError("An admitted regular member has no file contents")
            with source:
                content = source.read(member.size + 1)
            if len(content) != member.size or hashlib.sha256(content).hexdigest() != observed[member.name]["sha256"]:
                raise ValueError("Archive changed between admission and extraction")
            with target.open("xb") as writer:
                writer.write(content)
    return len(observed)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        pin = json.loads(args.manifest.read_bytes())["pythons"][args.python]
        if pin["format"] != "tar-gzip":
            raise ValueError("The selected interpreter is not a qualified tar-gzip payload")
        result: dict[str, Any] = {"ok": True, "admitted_files": extract(args.archive, pin, args.output)}
    except (OSError, ValueError, TypeError, KeyError, tarfile.TarError) as error:
        result = {"ok": False, "errors": [str(error)]}
    print(json.dumps(result))
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

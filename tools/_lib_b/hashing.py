"""SHA-256 helpers: file, text, and deterministic directory tree digests.

A sorted tree digest gives us content-addressable identity for generated
directory layouts, independent of filesystem walk order.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

_CHUNK = 65536


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_sorted_tree(root: Path) -> str:
    """Digest over the sorted list of (relative-posix-path, file-sha256) pairs.

    Directory entries are ignored except for the files they contain. The
    enumeration order is `sorted(root.rglob('*'))` to match the stable-outputs
    guidance from reproducible-builds.org.
    """
    digest = hashlib.sha256()
    for item in sorted(root.rglob("*")):
        if not item.is_file():
            continue
        rel = item.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\x00")
        digest.update(bytes.fromhex(sha256_file(item)))
        digest.update(b"\x00")
    return digest.hexdigest()

"""Validate grading-case manifests without executing grader or candidate code."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from _trial_transcript import strict_json


def case_digest(cases: list[str]) -> str:
    """Hash a canonical unordered case set for a protocol's advance commitment."""
    encoded = json.dumps(sorted(cases), ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_grading_manifest(
    protocol_path: Path, protocol: dict[str, Any], protocol_hash: str
) -> tuple[frozenset[str], str]:
    """Bind the expected denominator to the protocol and its recorded grader."""
    path = protocol_path.with_name(protocol_path.stem + ".grading.json")
    if path.is_symlink() or not path.is_file():
        raise ValueError("an adjacent grading manifest is required")
    with path.open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError("grading manifest is too large")
    manifest = strict_json(raw.decode("utf-8"))
    grader_hash = protocol.get("grader_sha256")
    version = protocol.get("protocol_version")
    if (
        not isinstance(manifest, dict)
        or manifest.get("manifest_version") != 1
        or type(manifest.get("manifest_version")) is not int
        or manifest.get("protocol_sha256") != protocol_hash
        or not isinstance(grader_hash, str)
        or len(grader_hash) != 64
        or any(character not in "0123456789abcdef" for character in grader_hash)
        or manifest.get("grader_sha256") != grader_hash
        or type(version) is not int
        or version < 2
    ):
        raise ValueError("grading manifest does not match the protocol and grader")
    cases = manifest.get("cases")
    if (
        not isinstance(cases, list)
        or not cases
        or any(not isinstance(case, str) or not case.strip() for case in cases)
        or len(cases) != len(set(cases))
    ):
        raise ValueError("grading manifest must contain unique nonempty case names")
    if version >= 3 and protocol.get("grading_cases_sha256") != case_digest(cases):
        raise ValueError("grading manifest differs from the protocol's committed case set")
    return frozenset(cases), hashlib.sha256(raw).hexdigest()

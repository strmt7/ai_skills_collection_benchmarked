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


def _check_header(manifest: Any, protocol: dict[str, Any], protocol_hash: str) -> int:
    """Validate the protocol version, manifest version and protocol binding."""
    version = protocol.get("protocol_version")
    if type(version) is not int or version < 2:
        raise ValueError("grading manifest does not match the protocol and grader")
    if not isinstance(manifest, dict):
        raise ValueError("grading manifest does not match the protocol and grader")
    if type(manifest.get("manifest_version")) is not int or manifest["manifest_version"] != 1:
        raise ValueError("grading manifest does not match the protocol and grader")
    if manifest.get("protocol_sha256") != protocol_hash:
        raise ValueError("grading manifest does not match the protocol and grader")
    return version


def _check_grader(manifest: dict[str, Any], protocol: dict[str, Any]) -> None:
    """Require an exact lowercase SHA-256 binding to the frozen grader."""
    grader_hash = protocol.get("grader_sha256")
    if not isinstance(grader_hash, str) or len(grader_hash) != 64:
        raise ValueError("grading manifest does not match the protocol and grader")
    if any(character not in "0123456789abcdef" for character in grader_hash):
        raise ValueError("grading manifest does not match the protocol and grader")
    if manifest.get("grader_sha256") != grader_hash:
        raise ValueError("grading manifest does not match the protocol and grader")


def _check_cases(manifest: dict[str, Any]) -> list[str]:
    """Require a nonempty list of distinct, nonblank case identifiers."""
    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("grading manifest must contain unique nonempty case names")
    if any(not isinstance(case, str) or not case.strip() for case in cases):
        raise ValueError("grading manifest must contain unique nonempty case names")
    if len(cases) != len(set(cases)):
        raise ValueError("grading manifest must contain unique nonempty case names")
    return cases


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
    version = _check_header(manifest, protocol, protocol_hash)
    _check_grader(manifest, protocol)
    cases = _check_cases(manifest)
    if version >= 3 and protocol.get("grading_cases_sha256") != case_digest(cases):
        raise ValueError("grading manifest differs from the protocol's committed case set")
    return frozenset(cases), hashlib.sha256(raw).hexdigest()

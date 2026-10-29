#!/usr/bin/env python3
"""Verify the source-bound Azure Key Vault Java security repair."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import build_catalog
from _lib_b.source_identity import require_unique
from check_no_secret_patterns import require_publishable_content

ROOT = Path(__file__).resolve().parents[1]
SKILL_ID = "microsoft-skills-github-plugins-azure-sdk-java-skills-azure-security-keyvault-secrets-java-skill-md"
MIRROR = Path(
    "included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-security-keyvault-secrets-java"
)
OVERLAY = Path("included/repaired/skills/azure-keyvault-java-security")
CONTROL = Path("artifacts/research/2026-10-28/azure-keyvault-output-security-control.json")
LICENSE = Path("artifacts/source-notices/microsoft-skills/a2c05249c4a20103dd954ca702467aa328aac031/LICENSE")
SOURCE_COMMIT = "a2c05249c4a20103dd954ca702467aa328aac031"
LICENSE_SHA256 = "d9a1b1e30d633d5732ea18e3cba9538d293ebc53e1a9e4e96ab739e0c5c4f1cb"
NOTICE = (
    "\n> Security repair: never print secret values or prefixes. The examples use placeholders; "
    "obtain real values through approved secure inputs and do not commit or log them. "
    "The preserved original is for audit only. "
    "Read [Mandatory agent tools](../../../../docs/agent-tools.md) before using this skill.\n"
)
REPAIRS = {
    "SKILL.md": (
        (77, 77, "// Use the value only for its intended operation; never print or log it.", "Secret value: "),
        (120, 120, '        System.out.println("Secret retrieved.");', "fullSecret.getValue()"),
        (210, 210, '    .subscribe(secret -> System.out.println("Secret retrieved."));', "secret.getValue()"),
        (279, 279, '    System.out.println("Secret retrieved.");', "secret.getValue()"),
    ),
    "references/examples.md": (
        (69, 70, 'System.out.println("Secret created.");', "secret.getValue()"),
        (83, 84, 'System.out.println("Secret created.");', "returnedSecret.getValue()"),
        (106, 107, 'System.out.println("Secret retrieved.");', "secret.getValue()"),
        (115, 116, 'System.out.println("Secret retrieved.");', "secretWithVersion.getValue()"),
        (146, 148, '    System.out.println("Secret retrieved.");', "secretWithValue.getValue()"),
        (178, 180, '    System.out.println("Secret version retrieved.");', "secret.getValue()"),
        (300, 300, '        secret -> System.out.println("Secret retrieved."),', "secret.getValue()"),
        (338, 338, '        System.out.println("Secret retrieved.");', "retrieved.getValue()"),
        (113, 113, 'String secretVersion = "<version-id>";', "String secretVersion ="),
        (124, 124, 'String secretVersion = "<version-id>";', "String secretVersion ="),
    ),
}
PLACEHOLDER_COUNTS = {"SKILL.md": 7, "references/examples.md": 5, "references/acceptance-criteria.md": 2}
_ticks = chr(96) * 3
JAVA_FENCE = re.compile(r"(^" + _ticks + r"java[^\n]*\n)(.*?)(^" + _ticks + r"[ \t]*(?:\n|$))", re.M | re.S)
SECRET_LITERAL = re.compile(
    r'(\b(?:setSecret|new\s+KeyVaultSecret)\s*\(\s*"(?:\\.|[^"\\\r\n])*"\s*,\s*)'
    r'"(?:\\.|[^"\\\r\n])*"',
    re.S,
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def repair_lines(data: bytes, changes: tuple[tuple[int, int, str, str], ...]) -> bytes:
    lines = data.decode("utf-8").splitlines(keepends=True)
    for start, end, replacement, expected in sorted(changes, reverse=True):
        old = "".join(lines[start - 1 : end])
        if expected not in old:
            raise ValueError(f"reviewed source no longer matches lines {start}-{end}")
        lines[start - 1 : end] = [replacement + "\n"]
    return "".join(lines).encode("utf-8")


def normalize_placeholders(data: bytes, expected_count: int) -> bytes:
    count = 0

    def fence(match: re.Match[str]) -> str:
        def literal(value: re.Match[str]) -> str:
            nonlocal count
            count += 1
            return value.group(1) + '"<secret-value>"'

        body = SECRET_LITERAL.sub(literal, match.group(2))
        return match.group(1) + body + match.group(3)

    text = JAVA_FENCE.sub(fence, data.decode("utf-8"))
    if count != expected_count:
        raise ValueError("the reviewed Java literal count changed")
    return text.encode("utf-8")


def _verified_control(root: Path, mirror: Path, entry: dict[str, Any]) -> tuple[bytes, dict[str, Any]]:
    """Bind the recorded security control to the exact locked source."""
    report_raw = (root / CONTROL).read_bytes()
    report = json.loads(report_raw)
    if (
        report["skill_id"] != SKILL_ID
        or report["source_commit"] != SOURCE_COMMIT
        or report["source_skill_sha256"] != entry["skill_file_sha256"]
        or report["source_tree_sha256"] != entry["skill_dir_sha256"]
        or report["source_examples_sha256"]
        != digest(build_catalog.sanitized_file_bytes(mirror / "references/examples.md"))
        or report["baseline_verdict"] != "failed"
        or report["repair_verdict"] != "passed"
        or len(report["controls"]) != 12
    ):
        raise ValueError("Key Vault control does not match the source inputs")
    return report_raw, report


def expected_files(root: Path = ROOT) -> dict[str, bytes]:
    lock = json.loads((root / "data/source_lock.json").read_text(encoding="utf-8"))
    source = require_unique(lock["sources"], "repo", "microsoft/skills", "source lock")
    entry = require_unique(source["skills"], "id", SKILL_ID, "source skill")
    mirror = root / MIRROR
    if (
        source["commit_sha"] != SOURCE_COMMIT
        or build_catalog.sha256_tree(mirror, file_modes=entry["file_modes"]) != entry["skill_dir_sha256"]
    ):
        raise ValueError("Key Vault mirror does not match its locked source")
    report_raw, report = _verified_control(root, mirror, entry)
    files = {
        item.relative_to(mirror).as_posix(): build_catalog.sanitized_file_bytes(item)
        for item in build_catalog.skill_tree_files(mirror)
    }
    original_skill = files["SKILL.md"]
    for name, changes in REPAIRS.items():
        files[name] = repair_lines(files[name], changes)
    for name, count in PLACEHOLDER_COUNTS.items():
        files[name] = normalize_placeholders(files[name], count)
    text = files["SKILL.md"].decode("utf-8")
    frontmatter_end = text.find("\n---\n", 4)
    if not text.startswith("---\n") or frontmatter_end < 0:
        raise ValueError("Key Vault skill frontmatter changed")
    index = frontmatter_end + len("\n---\n")
    files["SKILL.md"] = (text[:index] + NOTICE + text[index:]).encode("utf-8")
    files["provenance/original.SKILL.md"] = original_skill
    license_bytes = (root / LICENSE).read_bytes()
    if digest(license_bytes) != LICENSE_SHA256:
        raise ValueError("upstream license differs from the captured source")
    files["provenance/LICENSE"] = license_bytes
    if any(
        digest(files[name]) != report[key]
        for name, key in (
            ("SKILL.md", "repair_skill_sha256"),
            ("references/examples.md", "repair_examples_sha256"),
            ("references/acceptance-criteria.md", "repair_acceptance_sha256"),
        )
    ):
        raise ValueError("repair differs from the tested control inputs")
    for data in files.values():
        require_publishable_content(data)
    manifest = {
        "schema_version": 1,
        "skill_id": SKILL_ID,
        "original_mirrored_path": MIRROR.as_posix(),
        "original_commit": SOURCE_COMMIT,
        "original_skill_dir_sha256": entry["skill_dir_sha256"],
        "security_control": CONTROL.as_posix(),
        "security_control_sha256": digest(report_raw),
        "repair": "Avoid printing secret values or prefixes and label illustrative secret-value literals as placeholders.",
        "limitations": "The original mirror remains unchanged. These controls do not establish full skill security or agent efficacy.",
        "files": {name: digest(data) for name, data in sorted(files.items())},
    }
    files["repair.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    return files


def check_overlay(path: Path, expected: dict[str, bytes]) -> list[str]:
    if not path.is_dir() or path.is_symlink():
        return ["repair overlay is missing or is a symlink"]
    actual = {item.relative_to(path).as_posix() for item in path.rglob("*") if item.is_file() or item.is_symlink()}
    errors = [f"unexpected or missing file: {name}" for name in sorted(actual ^ set(expected))]
    for name in sorted(actual & set(expected)):
        item = path / name
        if item.is_symlink() or item.read_bytes() != expected[name]:
            errors.append(f"changed file: {name}")
            continue
        if os.name != "nt" and item.stat().st_mode & 0o111:
            errors.append(f"changed executable mode: {name}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify the existing overlay (default)")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        errors = check_overlay(ROOT / OVERLAY, expected_files())
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        errors = [f"overlay check incomplete: {type(exc).__name__}: {exc}"]
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors}))
    elif errors:
        print("\n".join(errors))
    else:
        print("Key Vault security overlay matches its locked inputs.")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())

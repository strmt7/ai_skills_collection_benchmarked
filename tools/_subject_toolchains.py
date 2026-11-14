"""Bind native subject command prefixes to complete, frozen read-only payloads."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _trial_protocol import relative_path
from _trial_transcript import strict_json
from _windows_appcontainer import checked_path
from grade_swe_skills_submission import asset

MAX_ENTRIES = 32000
MAX_BYTES = 4 * 1024**3


def _names(values: Any) -> list[str]:
    if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
        raise ValueError("Toolchain paths require a list of canonical relative names")
    names = [relative_path(value) for value in values]
    if len({name.casefold() for name in names}) != len(names):
        raise ValueError("Toolchain paths repeat a portable identity")
    return names


def _payload(value: Any) -> dict[str, Any]:
    fields = {"name", "version", "root", "files", "directories", "commands"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("Expected a complete native toolchain declaration")
    if (
        not isinstance(value["name"], str)
        or not re.fullmatch(r"[a-z][a-z0-9_-]{0,47}", value["name"])
        or not isinstance(value["version"], str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+_-]{0,95}", value["version"])
        or not isinstance(value["root"], str)
        or not Path(value["root"]).is_absolute()
    ):
        raise ValueError("Toolchain name, version and absolute root must be explicit")
    files, commands = value["files"], value["commands"]
    if not isinstance(files, dict) or not files or len(files) > MAX_ENTRIES:
        raise ValueError("Toolchain files require a bounded complete inventory")
    names = _names(list(files))
    directories = _names(value["directories"])
    if len(names) + len(directories) > MAX_ENTRIES:
        raise ValueError("Toolchain namespace exceeds its entry budget")
    if len({name.casefold() for name in [*names, *directories]}) != len(names) + len(directories):
        raise ValueError("Toolchain files and directories overlap")
    for identity in files.values():
        if (
            not isinstance(identity, dict)
            or set(identity) != {"bytes", "sha256"}
            or type(identity["bytes"]) is not int
            or not 0 <= identity["bytes"] <= MAX_BYTES
            or not isinstance(identity["sha256"], str)
            or not re.fullmatch(r"[a-f0-9]{64}", identity["sha256"])
        ):
            raise ValueError("Toolchain files need exact byte counts and SHA-256 identities")
    if sum(identity["bytes"] for identity in files.values()) > MAX_BYTES:
        raise ValueError("Toolchain payload exceeds its byte budget")
    if not isinstance(commands, dict) or not 1 <= len(commands) <= 8:
        raise ValueError("Toolchain commands require bounded explicit file prefixes")
    for name, prefix in commands.items():
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,47}", name):
            raise ValueError("Toolchain command names must be portable identifiers")
        if not isinstance(prefix, list) or not 1 <= len(prefix) <= 4:
            raise ValueError("Toolchain command prefixes must name declared files")
        if any(relative_path(part) not in files for part in prefix):
            raise ValueError("Toolchain command prefixes must name declared files")
    return value


@dataclass(frozen=True)
class NativeToolchains:
    """Recheck the declaration and its complete namespace before accepting results."""

    location: str
    sha256: str

    def asset(self) -> dict[str, str]:
        return {"path": self.location, "sha256": self.sha256}

    def payloads(self) -> list[dict[str, Any]]:
        value = strict_json(asset(self.asset()).decode("utf-8"))
        if (
            not isinstance(value, dict)
            or set(value) != {"schema_version", "toolchains"}
            or type(value["schema_version"]) is not int
            or value["schema_version"] != 1
            or not isinstance(value["toolchains"], list)
            or not 1 <= len(value["toolchains"]) <= 8
        ):
            raise ValueError("Expected a bounded native toolchain manifest")
        payloads = [_payload(item) for item in value["toolchains"]]
        names = [item["name"] for item in payloads]
        commands = [name for item in payloads for name in item["commands"]]
        if len(set(names)) != len(names) or len(set(commands)) != len(commands):
            raise ValueError("Toolchain or command identity is repeated")
        if sum(len(item["files"]) + len(item["directories"]) for item in payloads) > MAX_ENTRIES:
            raise ValueError("Combined toolchain namespace exceeds its entry budget")
        if sum(entry["bytes"] for item in payloads for entry in item["files"].values()) > MAX_BYTES:
            raise ValueError("Combined toolchain payload exceeds its byte budget")
        roots = [checked_path(Path(item["root"])) for item in payloads]
        if any(not root.is_dir() or root == Path(root.anchor) for root in roots):
            raise ValueError("Toolchains require scoped existing directories")
        if any(a.is_relative_to(b) or b.is_relative_to(a) for i, a in enumerate(roots) for b in roots[i + 1 :]):
            raise ValueError("Toolchain payload roots must be disjoint")
        return payloads

    def roots(self) -> tuple[Path, ...]:
        return tuple(checked_path(Path(item["root"])) for item in self.payloads())

    def instructions(self) -> str:
        commands = {
            name: [str(checked_path(Path(item["root"]) / part)) for part in prefix]
            for item in self.payloads()
            for name, prefix in item["commands"].items()
        }
        return "\nNative command prefixes for this attempt (use these full paths): " + json.dumps(commands) + "\n"

    def verify(self) -> None:
        for item in self.payloads():
            root = checked_path(Path(item["root"]))
            directories = set(item["directories"])
            pending, seen_files, seen_directories = [root], set(), set()
            while pending:
                for candidate in pending.pop().iterdir():
                    path = checked_path(candidate)
                    name = path.relative_to(root).as_posix()
                    if path.is_dir():
                        if name not in directories:
                            raise ValueError("Toolchain contains an undeclared directory")
                        seen_directories.add(name)
                        pending.append(path)
                    elif path.is_file():
                        if name not in item["files"]:
                            raise ValueError("Toolchain contains an undeclared file")
                        before = path.stat()
                        identity = item["files"][name]
                        if before.st_size != identity["bytes"]:
                            raise ValueError("Toolchain file size changed")
                        with path.open("rb") as stream:
                            digest = hashlib.file_digest(stream, "sha256").hexdigest()
                        after = path.stat()
                        if digest != identity["sha256"] or (
                            before.st_dev,
                            before.st_ino,
                            before.st_size,
                            before.st_mtime_ns,
                        ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
                            raise ValueError("Toolchain file identity changed")
                        seen_files.add(name)
                    else:
                        raise ValueError("Toolchain payloads admit only regular files and directories")
            if seen_files != set(item["files"]) or seen_directories != directories:
                raise ValueError("Toolchain is missing declared files or directories")


def load_toolchains(entry: Any) -> NativeToolchains:
    """Admit frozen payloads; provisioning remains the qualified setup frontend's job."""
    asset(entry)
    result = NativeToolchains(entry["path"], entry["sha256"])
    result.verify()
    return result

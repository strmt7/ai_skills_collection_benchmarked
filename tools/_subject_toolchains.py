"""Bind native subject command prefixes to complete, frozen read-only payloads."""

from __future__ import annotations

import hashlib
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
LAUNCHER_EVIDENCE = "native-tool-launcher.py.txt"
LAUNCHER = """
import os
import subprocess
import sys

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Choose a native tool and supply its arguments. Available tools: " + ", ".join(COMMANDS), file=sys.stderr)
        return 2
    name, *arguments = sys.argv[1:]
    environment = {**os.environ, **COMMON_ENVIRONMENT, **TOOL_ENVIRONMENTS.get(name, {})}
    return subprocess.run([*COMMANDS[name], *arguments], env=environment, check=False).returncode

raise SystemExit(main())
"""


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
    if not isinstance(commands, dict) or len(commands) > 8:
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
class PreparedNativeTools:
    launcher: Path
    source: bytes
    instructions: str

    def verify(self) -> None:
        with checked_path(self.launcher).open("rb") as stream:
            if stream.read(len(self.source) + 1) != self.source:
                raise ValueError("The prepared native tool launcher changed during execution")


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

    def prepare(self, workspace: Path, python: Path, temporary: Path) -> PreparedNativeTools | None:
        """Give declared commands a writable scratch directory inside the subject profile."""
        payloads = {item["name"]: item for item in self.payloads()}
        commands = {
            name: [str(checked_path(Path(item["root"]) / part)) for part in prefix]
            for item in payloads.values()
            for name, prefix in item["commands"].items()
        }
        if not commands:
            return None
        profile = checked_path(workspace / ".trial-profile")
        temporary = checked_path(temporary)
        if not temporary.is_relative_to(profile) or not temporary.is_dir():
            raise ValueError("Native tools require the runner's writable subject temporary directory")
        tool_environments = {}
        go = payloads.get("go")
        if go and "go" in go["commands"]:
            go_home = profile / "go"
            tool_environments["go"] = {
                "GOENV": "off",
                "GOTOOLCHAIN": "local",
                "GOTMPDIR": str(temporary),
                "GOPATH": str(go_home),
                "GOCACHE": str(go_home / "build"),
                "GOMODCACHE": str(go_home / "pkg/mod"),
            }
            if proxy := payloads.get("go-module-proxy"):
                tool_environments["go"]["GOPROXY"] = checked_path(Path(proxy["root"])).as_uri()
        source = (
            f"COMMANDS = {commands!r}\n"
            f"COMMON_ENVIRONMENT = {{'TEMP': {str(temporary)!r}, 'TMP': {str(temporary)!r}}}\n"
            f"TOOL_ENVIRONMENTS = {tool_environments!r}\n" + LAUNCHER
        ).encode("utf-8")
        launcher = checked_path(profile / "native-tools.py")
        with launcher.open("xb") as stream:
            stream.write(source)
        command = "& '{}' -I -B -S '{}'".format(str(python).replace("'", "''"), str(launcher).replace("'", "''"))
        invocation = "go test ./..." if "go" in tool_environments else "<tool> <arguments>"
        instructions = (
            "\nThe Windows PowerShell command tool starts in the task workspace. Use project-relative source paths.\n"
            "Run the declared native tools through this launcher. Supply the tool name and the arguments it expects.\n"
            f"Available native tools: {', '.join(commands)}\n"
            f"{command} {invocation}\n"
            "If a command returns a session ID, poll it until the exit status is available.\n"
        )
        return PreparedNativeTools(launcher, source, instructions)

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

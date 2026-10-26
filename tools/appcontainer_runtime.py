"""Provision or check the exact private CPython runtime used by native graders."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
import time
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from _windows_appcontainer import checked_path, checked_tree

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "toolchains/appcontainer/source.json"


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def verify(home: Path, specification: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    runtime = home / "runtime"
    if not runtime.is_dir():
        return ["runtime directory is missing"]
    try:
        actual = {file.relative_to(runtime).as_posix(): digest(file) for file in checked_tree(runtime)}
    except ValueError as error:
        return [str(error)]
    expected = specification["files"]
    errors.extend(
        f"missing or changed runtime file: {name}" for name, value in expected.items() if actual.get(name) != value
    )
    errors.extend(f"unexpected runtime file: {name}" for name in actual.keys() - expected.keys())
    return errors


def capture(home: Path, archive: Path | None, specification: dict[str, Any]) -> Path:
    captured = home / "python.zip"
    source = archive.open("rb") if archive else urllib.request.urlopen(specification["url"], timeout=30)
    deadline = time.monotonic() + 120
    with source as response, captured.open("xb") as destination:
        status = getattr(response, "status", None)
        if not archive and status != 200:
            raise ValueError(f"Runtime archive HTTP status: {status}")
        remaining = specification["archive_bytes"]
        while chunk := response.read(min(1024 * 1024, remaining + 1)):
            if time.monotonic() > deadline:
                raise TimeoutError("Runtime archive capture exceeded its wall-clock bound")
            remaining -= len(chunk)
            if remaining < 0:
                raise ValueError("Runtime archive exceeds the pinned byte count")
            destination.write(chunk)
    if captured.stat().st_size != specification["archive_bytes"] or digest(captured) != specification["archive_sha256"]:
        raise ValueError("Runtime archive differs from the official pinned release")
    return captured


def setup(home: Path, archive: Path | None, specification: dict[str, Any]) -> None:
    checked_path(home)
    home.mkdir(parents=True, exist_ok=False)
    captured = capture(home, archive, specification)
    runtime = home / "runtime"
    runtime.mkdir()
    with zipfile.ZipFile(captured) as package:
        if sum(item.file_size for item in package.infolist()) > 80 * 1024 * 1024:
            raise ValueError("Runtime archive expanded-size bound exceeded")
        for item in package.infolist():
            path = PurePosixPath(item.orig_filename)
            if path.is_absolute() or ".." in path.parts or ":" in item.orig_filename or "\\" in item.orig_filename:
                raise ValueError("Runtime archive has an escaping path")
            if stat.S_ISLNK(item.external_attr >> 16):
                raise ValueError("Runtime archive contains a symbolic link")
        package.extractall(runtime)
    errors = verify(home, specification)
    if errors:
        raise ValueError("; ".join(errors))
    (home / "source.json").write_text(json.dumps(specification, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "check"])
    parser.add_argument("--home", type=Path)
    parser.add_argument("--archive", type=Path, help="Optional existing exact archive for offline setup")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if sys.platform != "win32":
            raise ValueError("This runtime is qualified for Windows x64")
        specification = json.loads(SOURCE.read_bytes())
        cache = (ROOT / ".venv").resolve()
        home = checked_path(args.home or cache / ("appcontainer-" + specification["archive_sha256"][:16]))
        if home == cache or not home.is_relative_to(cache):
            raise ValueError("Runtime home must be a dedicated directory inside this clone's .venv")
        if args.command == "setup":
            setup(home, args.archive, specification)
        errors = verify(home, specification)
        print(
            json.dumps(
                {
                    "errors": errors,
                    "home": str(home),
                    "version": specification["version"],
                    "files": len(specification["files"]),
                }
            )
        )
        return int(bool(errors))
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(json.dumps({"errors": [str(error)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

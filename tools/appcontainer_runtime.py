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
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any

from _windows_appcontainer import Native, checked_path, checked_tree

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


def acl_graph(home: Path) -> list[dict[str, str]]:
    runtime = home / "runtime"
    files = checked_tree(runtime)
    directories = {
        parent for file in files for parent in file.parents if parent != runtime and parent.is_relative_to(runtime)
    }
    native = Native()
    return [
        {"path": path.relative_to(home).as_posix(), "sha256": hashlib.sha256(native.descriptor(path)).hexdigest()}
        for path in [home, runtime, *sorted(directories), *files]
    ]


def _prepare_private_home(home: Path, specification: dict[str, Any]) -> None:
    """Seal a newly created home before its ACL baseline is recorded."""
    home, cache = checked_path(home), checked_path(ROOT / ".venv")
    if home == cache or not home.is_relative_to(cache):
        raise ValueError("Private runtime home must be inside this clone's .venv")
    checked_tree(home)
    if (home / "isolation.json").exists() or (home / "isolation.lock").exists():
        raise ValueError("Private runtime home already has an isolation receipt or lock")
    if json.loads((home / "source.json").read_bytes()) != specification:
        raise ValueError("Private runtime source receipt differs from the selected specification")
    native = Native()
    native.grant(home, native.owner_sid(), None)
    record = {"schema_version": 1, "archive_sha256": specification["archive_sha256"], "descriptors": acl_graph(home)}
    (home / "isolation.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    (home / "isolation.lock").write_bytes(b"\0")


def verify_private_home(home: Path, specification: dict[str, Any]) -> list[str]:
    receipt = checked_path(home / "isolation.json")
    if not receipt.is_file():
        return ["Private runtime ACL receipt is missing; set up a new dedicated runtime home"]
    try:
        recorded = json.loads(receipt.read_bytes())
        expected = {
            "schema_version": 1,
            "archive_sha256": specification["archive_sha256"],
            "descriptors": acl_graph(home),
        }
    except (OSError, ValueError, KeyError) as error:
        return [f"Cannot verify private runtime ACLs: {error}"]
    if recorded != expected:
        return ["Private runtime ACL descriptors differ from the setup baseline"]
    return []


@contextmanager
def lease(home: Path, specification: dict[str, Any]) -> Iterator[None]:
    """Hold the runtime exclusively and verify its ACLs before and after use."""
    if sys.platform != "win32":
        raise ValueError("The private runtime lease requires Windows")
    import msvcrt

    lock = checked_path(home / "isolation.lock")
    if not lock.is_file() or lock.stat().st_size != 1 or lock.stat().st_nlink != 1:
        raise ValueError("The private runtime lock is missing or invalid; set up a new dedicated runtime home")
    with lock.open("r+b") as stream:
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as error:
            raise RuntimeError("The private runtime is in use; choose a dedicated runtime home") from error
        try:
            if errors := verify_private_home(home, specification):
                raise ValueError("; ".join(errors))
            try:
                yield
            finally:
                if errors := verify_private_home(home, specification):
                    raise RuntimeError("; ".join(errors))
        finally:
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


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
    _prepare_private_home(home, specification)


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
        if not errors:
            with lease(home, specification):
                pass
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
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        print(json.dumps({"errors": [str(error)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

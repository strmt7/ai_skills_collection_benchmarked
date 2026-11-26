"""Recoverable publication of a fixed set of generated catalog outputs.

Readers can observe intermediate renames; this is not an atomic filesystem
transaction. Retained originals, a durable journal and a process-owned guard
allow recovery after an interrupted writer.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import sys
import uuid
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import Any


def checked_path(root: Path, relative: str) -> Path:
    parts = PurePosixPath(relative).parts
    if not parts or PurePosixPath(relative).as_posix() != relative or "\\" in relative or ":" in relative:
        raise ValueError(f"noncanonical publication path: {relative}")
    if PurePosixPath(relative).is_absolute() or any(part in {".", ".."} for part in parts):
        raise ValueError(f"external publication path: {relative}")
    path = root.joinpath(*parts)
    for item in (path, *path.parents):
        if item == root:
            break
        if item.is_symlink() or (
            item.exists() and getattr(item.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
        ):
            raise ValueError(f"linked publication path: {relative}")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"publication path escapes root: {relative}")
    return path


def signature(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    items = [path]
    if path.is_dir():

        def fail(error: OSError) -> None:
            raise error

        for directory, directories, files in os.walk(path, onerror=fail, followlinks=False):
            items.extend(Path(directory) / name for name in sorted(directories + files))
        items[1:] = sorted(items[1:])
    for item in items:
        mode = item.lstat()
        if item.is_symlink() or getattr(mode, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f"linked generated resource: {item}")
        if not stat.S_ISREG(mode.st_mode) and not stat.S_ISDIR(mode.st_mode):
            raise ValueError(f"nonregular generated resource: {item}")
        kind = "directory" if item.is_dir() else "file"
        name = item.relative_to(path).as_posix()
        executable = bool(mode.st_mode & 0o111) if os.name != "nt" else False
        digest.update(json.dumps([name, kind, executable], separators=(",", ":")).encode())
        if item.is_file():
            file_digest = hashlib.sha256()
            size = 0
            with item.open("rb") as stream:
                while block := stream.read(1024 * 1024):
                    file_digest.update(block)
                    size += len(block)
            digest.update(f"\0{size}\0{file_digest.hexdigest()}\n".encode())
    return digest.hexdigest()


def prepare(root: Path, outputs: Sequence[str], build: Callable[[Path], None]) -> tuple[Path, dict[str, Any]]:
    root = root.resolve()
    if not outputs or len(set(outputs)) != len(outputs):
        raise ValueError("publication requires unique output paths")
    paths = [checked_path(root, relative) for relative in outputs]
    if any(a in b.parents or b in a.parents for i, a in enumerate(paths) for b in paths[i + 1 :]):
        raise ValueError("overlapping publication outputs")
    staging = checked_path(root, ".venv/generation-staging")
    staging.mkdir(parents=True, exist_ok=True)
    with _writer_guard(staging):
        if checked_path(staging, "publication.lock").exists():
            raise FileExistsError("catalog publication recovery is pending")
        _discard_build_in_progress(staging)
        originals = {relative: signature(path) for relative, path in zip(outputs, paths, strict=True)}
        building = checked_path(staging, "build-in-progress-v2")
        building.mkdir()
        transaction = checked_path(staging, "catalog-" + uuid.uuid4().hex)
        try:
            generated = building / "generated"
            generated.mkdir()
            build(generated)
            replacements = {relative: signature(checked_path(generated, relative)) for relative in outputs}
            unexpected = [
                item.relative_to(generated).as_posix()
                for item in generated.rglob("*")
                if item.is_file()
                and not item.relative_to(generated).as_posix().startswith(".venv/")
                and not any(
                    item == generated / relative or (generated / relative) in item.parents for relative in outputs
                )
            ]
            if unexpected:
                raise ValueError(f"undeclared generated outputs: {unexpected}")
            journal: dict[str, Any] = {
                "schema_version": 2,
                "root": str(root),
                "status": "prepared",
                "outputs": [
                    {"path": relative, "original": originals[relative], "replacement": replacements[relative]}
                    for relative in outputs
                ],
                "operations": [],
            }
            write_journal(building, journal)
            building.rename(transaction)
        except BaseException:
            _discard_build_in_progress(staging)
            raise
        return transaction, journal


def _discard_build_in_progress(staging: Path) -> bool:
    """Remove the reserved, incomplete build slot while holding the writer guard."""
    building = checked_path(staging, "build-in-progress-v2")
    if not building.exists():
        return False
    if not building.is_dir():
        raise ValueError("catalog build staging is not a directory")
    shutil.rmtree(building)
    return True


def write_journal(transaction: Path, journal: dict[str, Any]) -> None:
    _replace_text(transaction / "journal-next.json", transaction / "journal.json", json.dumps(journal, indent=2) + "\n")


def _replace_text(temporary: Path, target: Path, text: str) -> None:
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(target)


def differences(root: Path, transaction: Path, journal: dict[str, Any]) -> list[str]:
    return [
        item["path"]
        for item in journal["outputs"]
        if signature(checked_path(root, item["path"]))
        != signature(checked_path(transaction / "generated", item["path"]))
    ]


@contextmanager
def _writer_guard(staging: Path) -> Iterator[None]:
    """Use a process-owned kernel lock. Closing the handle releases it."""
    path = checked_path(staging, "publication.guard")
    with path.open("a+b") as stream:
        stream.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise FileExistsError(f"catalog publication guard unavailable: {path}") from error
        yield


def _require_transaction(staging: Path, transaction: Path) -> None:
    if (
        transaction.parent != staging
        or not transaction.name.startswith("catalog-")
        or checked_path(staging, transaction.name) != transaction
        or not transaction.is_dir()
    ):
        raise ValueError("transaction must be an owned staging directory")


def _locations(root: Path, transaction: Path, relative: str) -> tuple[Path, Path, Path]:
    return (
        checked_path(root, relative),
        checked_path(transaction, "generated/" + relative),
        checked_path(transaction, "previous/" + relative),
    )


def _state(locations: tuple[Path, Path, Path]) -> tuple[str | None, ...]:
    return tuple(signature(path) for path in locations)


def _original(item: dict[str, Any]) -> tuple[str | None, ...]:
    return item["original"], item["replacement"], None


def _installed(item: dict[str, Any]) -> tuple[str | None, ...]:
    return item["replacement"], None, item["original"]


def _rollback(root: Path, transaction: Path, journal: dict[str, Any]) -> None:
    """Preflight physical versions, then restore the recorded prefix in reverse."""
    actions = []
    count = len(journal["operations"])
    for item in journal["outputs"][:count]:
        relative = item["path"]
        paths = _locations(root, transaction, relative)
        observed = _state(paths)
        if observed == _original(item):
            continue
        backed_up = (None, item["replacement"], item["original"])
        if observed not in {backed_up, _installed(item)}:
            raise ValueError(f"unrecognized on-disk publication state: {relative}")
        actions.append((relative, paths, observed[0] is not None, observed[2] is not None))

    errors = []
    for relative, (target, replacement, backup), uninstall, restore in reversed(actions):
        try:
            if uninstall:
                replacement.parent.mkdir(parents=True, exist_ok=True)
                target.rename(replacement)
            if restore:
                target.parent.mkdir(parents=True, exist_ok=True)
                backup.rename(target)
        except (OSError, ValueError) as error:
            errors.append(f"{relative}: {error}")
    journal.update(status="rollback_failed" if errors else "rolled_back", rollback_errors=errors)
    write_journal(transaction, journal)
    if errors:
        raise RuntimeError(f"publication rollback failed; preserve {transaction}: {errors}")


def _read_recovery_journal(root: Path, transaction: Path, outputs: Sequence[str]) -> dict[str, Any]:
    path = checked_path(transaction, "journal.json")
    with path.open("rb") as stream:
        contents = stream.read(1024**2 + 1)
    if len(contents) > 1024**2:
        raise ValueError("catalog recovery journal exceeds the byte budget")
    journal = json.loads(contents)
    if (
        not isinstance(journal, dict)
        or type(journal.get("schema_version")) is not int
        or journal["schema_version"] != 2
        or journal.get("root") != str(root)
        or not isinstance(journal.get("status"), str)
        or journal.get("status") not in {"prepared", "publishing", "published", "rolled_back", "rollback_failed"}
        or not isinstance(journal.get("outputs"), list)
        or not isinstance(journal.get("operations"), list)
    ):
        raise ValueError("recovery requires a version-2 journal for this catalog root")
    records = journal["outputs"]
    if len(records) != len(outputs) or not records:
        raise ValueError("catalog recovery output scope differs")
    for relative, item in zip(outputs, records, strict=True):
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "original", "replacement"}
            or item["path"] != relative
            or any(
                value is not None and (not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None)
                for value in (item["original"], item["replacement"])
            )
        ):
            raise ValueError("catalog recovery output identities differ")
    operations = journal["operations"]
    if len(operations) > len(records) or any(
        not isinstance(entry, dict)
        or set(entry) != {"path", "backed_up", "installed"}
        or entry["path"] != records[index]["path"]
        or type(entry["backed_up"]) is not bool
        or type(entry["installed"]) is not bool
        for index, entry in enumerate(operations)
    ):
        raise ValueError("catalog recovery operations must match the declared output order")
    return journal


def recover(root: Path, outputs: Sequence[str]) -> dict[str, Any]:
    """Finish a completed transaction or restore an interrupted transaction."""
    root = root.resolve()
    staging = checked_path(root, ".venv/generation-staging")
    if not staging.is_dir():
        return {"status": "none", "recovery_directory": None, "partial_build_removed": False}
    with _writer_guard(staging):
        discarded = _discard_build_in_progress(staging)
        lock = checked_path(staging, "publication.lock")
        if not lock.exists():
            return {"status": "none", "recovery_directory": None, "partial_build_removed": discarded}
        if lock.stat().st_size > 64 * 1024:
            raise ValueError("catalog publication pointer exceeds the byte budget")
        transaction = Path(lock.read_text(encoding="utf-8"))
        _require_transaction(staging, transaction)
        journal = _read_recovery_journal(root, transaction, outputs)
        if journal["status"] == "published":
            if len(journal["operations"]) != len(journal["outputs"]) or any(
                _state(_locations(root, transaction, item["path"])) != _installed(item) for item in journal["outputs"]
            ):
                raise ValueError("completed catalog publication differs from its journal")
        else:
            if journal["status"] == "prepared" and journal["operations"]:
                raise ValueError("prepared catalog journal already records publication operations")
            _rollback(root, transaction, journal)
        lock.unlink()
        return {"status": journal["status"], "recovery_directory": str(transaction), "partial_build_removed": discarded}


def discard_prepared(root: Path, transaction: Path) -> None:
    """Remove an owned check-only stage after verifying its journal and lock."""
    root = root.resolve()
    staging = checked_path(root, ".venv/generation-staging")
    with _writer_guard(staging):
        _require_transaction(staging, transaction)
        lock = checked_path(staging, "publication.lock")
        if lock.exists():
            raise FileExistsError("catalog publication recovery is pending")
        state = json.loads(checked_path(transaction, "journal.json").read_bytes())
        if (
            not isinstance(state, dict)
            or state.get("schema_version") != 2
            or state.get("root") != str(root)
            or state.get("status") != "prepared"
            or state.get("operations") != []
        ):
            raise ValueError("can only discard a prepared, unused catalog transaction")
        shutil.rmtree(transaction)


def publish(root: Path, transaction: Path, journal: dict[str, Any]) -> None:
    root = root.resolve()
    staging = checked_path(root, ".venv/generation-staging")
    _require_transaction(staging, transaction)
    if journal.get("root") != str(root) or journal.get("status") != "prepared" or journal.get("schema_version") != 2:
        raise ValueError("journal is not a prepared transaction for this root")
    with _writer_guard(staging):
        lock = checked_path(staging, "publication.lock")
        if lock.exists():
            raise FileExistsError("catalog publication recovery is pending")
        for item in journal["outputs"]:
            target, replacement, backup = _locations(root, transaction, item["path"])
            if signature(target) != item["original"]:
                raise ValueError(f"publication target changed during generation: {item['path']}")
            if signature(replacement) != item["replacement"] or backup.exists():
                raise ValueError(f"staged output changed after generation: {item['path']}")
        _replace_text(checked_path(transaction, "lock-next.txt"), lock, str(transaction))
        try:
            journal["status"] = "publishing"
            write_journal(transaction, journal)
            for item in journal["outputs"]:
                relative = item["path"]
                target, replacement, backup = _locations(root, transaction, relative)
                if signature(target) != item["original"]:
                    raise ValueError(f"publication target changed before replacement: {relative}")
                operation = {"path": relative, "backed_up": False, "installed": False}
                journal["operations"].append(operation)
                write_journal(transaction, journal)
                if target.exists():
                    backup.parent.mkdir(parents=True, exist_ok=True)
                    target.rename(backup)
                    operation["backed_up"] = True
                    write_journal(transaction, journal)
                if replacement.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    replacement.rename(target)
                    operation["installed"] = True
                    write_journal(transaction, journal)
            journal["status"] = "published"
            write_journal(transaction, journal)
        except BaseException:
            _rollback(root, transaction, journal)
            lock.unlink()
            raise
        else:
            lock.unlink()

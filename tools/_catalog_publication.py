"""Recoverable publication of a fixed set of generated catalog outputs.

Readers can observe intermediate renames; this is not an atomic filesystem
transaction. Retained originals and a journal make failure recovery inspectable.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from collections.abc import Callable, Sequence
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
    originals = {relative: signature(path) for relative, path in zip(outputs, paths, strict=True)}
    staging = checked_path(root, ".venv/generation-staging")
    staging.mkdir(parents=True, exist_ok=True)
    transaction = Path(tempfile.mkdtemp(prefix="catalog-", dir=staging))
    generated = transaction / "generated"
    generated.mkdir()
    build(generated)
    replacements = {relative: signature(checked_path(generated, relative)) for relative in outputs}
    unexpected = [
        item.relative_to(generated).as_posix()
        for item in generated.rglob("*")
        if item.is_file()
        and not item.relative_to(generated).as_posix().startswith(".venv/")
        and not any(item == generated / relative or (generated / relative) in item.parents for relative in outputs)
    ]
    if unexpected:
        raise ValueError(f"undeclared generated outputs: {unexpected}")
    journal: dict[str, Any] = {
        "schema_version": 1,
        "root": str(root),
        "status": "prepared",
        "outputs": [
            {"path": relative, "original": originals[relative], "replacement": replacements[relative]}
            for relative in outputs
        ],
        "operations": [],
    }
    write_journal(transaction, journal)
    return transaction, journal


def write_journal(transaction: Path, journal: dict[str, Any]) -> None:
    temporary = transaction / "journal-next.json"
    temporary.write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(transaction / "journal.json")


def differences(root: Path, transaction: Path, journal: dict[str, Any]) -> list[str]:
    return [
        item["path"]
        for item in journal["outputs"]
        if signature(checked_path(root, item["path"]))
        != signature(checked_path(transaction / "generated", item["path"]))
    ]


def publish(root: Path, transaction: Path, journal: dict[str, Any]) -> None:
    root = root.resolve()
    staging = checked_path(root, ".venv/generation-staging")
    if transaction.parent != staging or transaction.is_symlink() or not transaction.is_dir():
        raise ValueError("transaction must be an owned staging directory")
    if journal.get("root") != str(root) or journal.get("status") != "prepared":
        raise ValueError("journal is not a prepared transaction for this root")
    # Freeze the staged replacements and detect modifications made during build.
    for item in journal["outputs"]:
        if signature(checked_path(root, item["path"])) != item["original"]:
            raise ValueError(f"publication target changed during generation: {item['path']}")
        if signature(checked_path(transaction / "generated", item["path"])) != item["replacement"]:
            raise ValueError(f"staged output changed after generation: {item['path']}")
    lock = checked_path(root, ".venv/generation-staging/publication.lock")
    # An interrupted publisher leaves this lock; inspect its retained journal
    # before removing it. Never guess that another process is safe to replace.
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(transaction))
    try:
        journal["status"] = "publishing"
        write_journal(transaction, journal)
        for item in journal["outputs"]:
            relative = item["path"]
            target = checked_path(root, relative)
            replacement = checked_path(transaction / "generated", relative)
            backup = checked_path(transaction / "previous", relative)
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
        errors = []
        for operation in reversed(journal["operations"]):
            relative = operation["path"]
            try:
                target = checked_path(root, relative)
                replacement = checked_path(transaction / "generated", relative)
                backup = checked_path(transaction / "previous", relative)
                if operation["installed"]:
                    replacement.parent.mkdir(parents=True, exist_ok=True)
                    target.rename(replacement)
                if operation["backed_up"]:
                    backup.rename(target)
            except (OSError, ValueError) as exc:
                errors.append(f"{relative}: {exc}")
        journal.update(status="rollback_failed" if errors else "rolled_back", rollback_errors=errors)
        write_journal(transaction, journal)
        if errors:
            raise RuntimeError(f"publication rollback failed; preserve {transaction}: {errors}") from None
        raise
    finally:
        if journal["status"] in {"published", "rolled_back"}:
            lock.unlink()

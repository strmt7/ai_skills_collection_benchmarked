"""Capture a bounded task source tree without executing files from that tree."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from _trial_collection_policy import collection_policy
from _trial_transcript import strict_json
from _windows_appcontainer import checked_path
from _windows_directory_reader import inventory
from _windows_submission_reader import WorkspaceReader


def capture(workspace: Path, output: Path, declared: dict[str, Any]) -> dict[str, Any]:
    """Copy held source files after inventory validation, then recheck the namespace."""
    policy = collection_policy(declared)
    workspace, output = checked_path(workspace), checked_path(output)
    if workspace.is_relative_to(output) or output.is_relative_to(workspace):
        raise ValueError("collected output and task workspace must be disjoint")
    if output.exists():
        raise ValueError("collected output already exists; refusing to overwrite")
    with WorkspaceReader(workspace, enumerate_directories=True) as reader:
        before, excluded, directories = inventory(reader, policy)
        for name, entry in before.items():
            _, _, size = reader.open_file(name, max_bytes=policy["max_file_bytes"])
            if size != entry.size:
                raise ValueError("workspace file changed before its handle was held")
        locked, omitted, locked_directories = inventory(reader, policy)
        if locked != before or omitted != excluded or locked_directories != directories:
            raise ValueError("workspace changed while its handle graph was established")
        output.mkdir(parents=True, exist_ok=False)
        for name in directories:
            (output / name).mkdir(parents=True, exist_ok=False)
        files = {}
        for name, entry in before.items():
            data = reader.read_file(name, max_bytes=policy["max_file_bytes"])
            if len(data) != entry.size:
                raise ValueError("workspace size changed during capture")
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            files[name] = {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
        after, omitted, after_directories = inventory(reader, policy)
        if after != before or omitted != excluded or after_directories != directories:
            raise ValueError("workspace changed during capture")
    return {
        "collection_version": 1,
        "status": "collected",
        "policy": policy,
        "files": files,
        "directories": directories,
        "directory_count": len(directories),
        "excluded": excluded,
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files.values()),
        "post_inventory_matches": True,
        "atomic_snapshot": False,
        "precondition": "All subject execution must be stopped before capture.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--policy-json", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    import sys

    args = build_parser().parse_args(argv)
    try:
        record = capture(args.workspace, args.output, strict_json(args.policy_json))
    except (OSError, ValueError) as exc:
        record = {
            "collection_version": 1,
            "status": "collection_error",
            "error_type": type(exc).__name__,
            **{key: getattr(exc, key, None) for key in ("errno", "winerror")},
        }
    sys.stdout.buffer.write((json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    return 0 if record["status"] == "collected" else 1


if __name__ == "__main__":
    raise SystemExit(main())

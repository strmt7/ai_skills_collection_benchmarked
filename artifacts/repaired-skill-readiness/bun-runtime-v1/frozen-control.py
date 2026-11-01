from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def run(bun: Path, scratch: Path, output: Path) -> dict[str, Any]:
    version = subprocess.run(
        [str(bun), "--version"], capture_output=True, text=True, timeout=20, check=True
    ).stdout.strip()
    if version != "1.4.4":
        raise ValueError(f"Expected Bun 1.4.4, got {version}")
    scratch.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix="bun-frozen-", dir=scratch))
    env = os.environ.copy()
    env["BUN_INSTALL_CACHE_DIR"] = str(scratch / "bun-cache")
    package = fixture / "package.json"
    package.write_text(
        json.dumps({"name": "bun-frozen-control", "private": True, "dependencies": {"is-number": "7.0.0"}}),
        encoding="utf-8",
    )

    def install(label: str, frozen: bool) -> dict[str, Any]:
        args = [str(bun), "install", "--no-progress"]
        if frozen:
            args.append("--frozen-lockfile")
        completed = subprocess.run(args, cwd=fixture, env=env, capture_output=True, text=True, timeout=90, check=False)
        (output / f"{label}.stdout.txt").write_text(completed.stdout, encoding="utf-8", newline="\n")
        (output / f"{label}.stderr.txt").write_text(completed.stderr, encoding="utf-8", newline="\n")
        lock = fixture / "bun.lock"
        return {
            "exit": completed.returncode,
            "lock_exists": lock.exists(),
            "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest() if lock.exists() else None,
        }

    no_lock = install("no-lock", True)
    created = install("create-lock", False)
    matching = install("matching-lock", True)
    package.write_text(
        json.dumps(
            {"name": "bun-frozen-control", "private": True, "dependencies": {"is-number": "7.0.0", "is-odd": "3.0.1"}}
        ),
        encoding="utf-8",
    )
    mismatch = install("mismatched-lock", True)
    with bun.open("rb") as binary:
        binary_digest = hashlib.file_digest(binary, "sha256").hexdigest()
    result = {
        "bun_version": version,
        "binary_sha256": binary_digest,
        "platform": platform.system(),
        "cases": {
            "no_lock_frozen": no_lock,
            "create_lock": created,
            "matching_frozen": matching,
            "mismatch_frozen": mismatch,
        },
        "agent_efficacy_scored": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    valid = (
        no_lock["exit"] == 0
        and not no_lock["lock_exists"]
        and created["exit"] == 0
        and created["lock_exists"]
        and matching["exit"] == 0
        and mismatch["exit"] != 0
        and created["lock_sha256"] == matching["lock_sha256"] == mismatch["lock_sha256"]
    )
    if not valid:
        raise ValueError("Observed behavior differs from the recorded Bun 1.4.4 control")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce Bun 1.4.4 frozen-lock behavior in a fresh fixture.")
    parser.add_argument("--bun", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.bun.resolve(), args.scratch.resolve(), args.output.resolve()), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

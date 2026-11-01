"""Compare two source-bound Anthropic DOCX helpers on Windows."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED = {
    "old": (
        "c7f7e3289fdff196399fd6f3d6668b9aa68eec87",
        "a3e21840e29e32f947d5286028931b96eaf2dee63f75d883b8eb19c943c80aa0",
    ),
    "new": (
        "0b4c99deca54013c550458c9244ee63eea748dca",
        "df2c8d7249c132a4512d744482e4b5ed0ecbe885f0bcfb1295e7e6a7ced0432c",
    ),
}


def git_blob(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def run(old: Path, new: Path) -> dict:
    if sys.platform != "win32" or hasattr(socket, "AF_UNIX"):
        raise ValueError("This control requires Windows Python without socket.AF_UNIX")
    results = []
    with tempfile.TemporaryDirectory(prefix="office-source-comparison-") as temporary:
        private = Path(temporary)
        profile = private / "profile"
        temp = private / "temp"
        empty_path = private / "empty-path"
        for directory in (profile, temp, empty_path):
            directory.mkdir()
        env = os.environ.copy()
        env.update(USERPROFILE=str(profile), TEMP=str(temp), TMP=str(temp), PATH=str(empty_path))
        for name, source in (("old", old), ("new", new)):
            source = source.resolve(strict=True)
            before = source.read_bytes()
            if (git_blob(before), hashlib.sha256(before).hexdigest()) != EXPECTED[name]:
                raise ValueError(f"Unexpected {name} helper bytes")
            completed = subprocess.run(
                [sys.executable, "-I", "-B", str(source), "--version"],
                env=env,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            if source.read_bytes() != before:
                raise ValueError(f"{name} helper changed during execution")
            stderr = completed.stderr.replace(str(source), f"<{name}-source>").replace(str(private), "<private>")
            if (
                completed.returncode != 1
                or "module 'socket' has no attribute 'AF_UNIX'" not in stderr
                or completed.stdout
            ):
                raise ValueError(f"Unexpected {name} outcome: exit {completed.returncode}, stderr: {stderr}")
            results.append(
                {
                    "source": name,
                    "git_blob_sha1": EXPECTED[name][0],
                    "sha256": hashlib.sha256(before).hexdigest(),
                    "exit_code": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": stderr,
                }
            )
        if any(any(directory.iterdir()) for directory in (profile, temp, empty_path)):
            raise ValueError("Isolated profile or temporary directory is not empty")
    return {
        "platform": platform.system(),
        "python": platform.python_version(),
        "source_comparison": results,
        "child_path": "empty-directory",
        "document_conversion_tested": False,
        "agent_evaluated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", type=Path, required=True)
    parser.add_argument("--new", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.old, args.new), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

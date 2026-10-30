"""Exercise source-identical LibreOffice helpers on Windows without starting LibreOffice."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE_HASH = "f4ebbe4b638904d099eac915ada405b1031d1d7c5a80ecd5d733580d4eee1359"
MIRRORS = (
    "documents-spreadsheets-presentations/official-reference/docx-anthropics",
    "documents-spreadsheets-presentations/official-reference/pptx-anthropics",
    "documents-spreadsheets-presentations/official-reference/xlsx-anthropics",
    "science-research-data-analysis/latest-release-community/docx-scientific-agent-skills",
    "science-research-data-analysis/latest-release-community/pptx-scientific-agent-skills",
    "science-research-data-analysis/latest-release-community/xlsx-scientific-agent-skills",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    if sys.platform != "win32" or hasattr(socket, "AF_UNIX"):
        raise ValueError("This control requires Windows Python without socket.AF_UNIX")
    root = args.root.resolve()
    relative_paths = [f"included/skills/by-category/{mirror}/scripts/office/soffice.py" for mirror in MIRRORS]
    results = []
    with tempfile.TemporaryDirectory(prefix="office-helpers-control-") as temporary:
        private = Path(temporary)
        (private / "profile").mkdir()
        (private / "temp").mkdir()
        env = os.environ.copy()
        env.update(USERPROFILE=str(private / "profile"), TEMP=str(private / "temp"), TMP=str(private / "temp"))
        for relative_path in relative_paths:
            source = root / relative_path
            if hashlib.sha256(source.read_bytes()).hexdigest() != SOURCE_HASH:
                raise ValueError(f"Unexpected helper bytes: {relative_path}")
            result = subprocess.run(
                [sys.executable, "-I", "-B", str(source), "--version"],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            expected = "module 'socket' has no attribute 'AF_UNIX'"
            if result.returncode != 1 or expected not in result.stderr or result.stdout:
                raise ValueError(f"Expected startup failure changed: {relative_path}")
            results.append(
                {
                    "path": relative_path,
                    "sha256": SOURCE_HASH,
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr.replace(str(root), "<repository>"),
                }
            )
        if list((private / "profile").iterdir()):
            raise ValueError("The isolated profile was unexpectedly modified")
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "python": platform.python_version(),
                "has_af_unix": False,
                "available_soffice": shutil.which("soffice") is not None,
                "libreoffice_started": False,
                "isolated_profile_empty": True,
                "agent_scored": False,
                "stderr_path_normalization": "repository root replaced by <repository>",
                "helpers": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

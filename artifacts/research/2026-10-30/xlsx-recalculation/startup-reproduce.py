"""Reproduce the pinned and current XLSX helper startup failure on Windows."""

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

import openpyxl

HASHES = {
    "pinned_recalc": "e8251c94ae0c6678b6793d56d2620dd2daf7c73e1da00db6c4aaf4d5e34acd8e",
    "pinned_office": "f4ebbe4b638904d099eac915ada405b1031d1d7c5a80ecd5d733580d4eee1359",
    "current_recalc": "66f6e726d5a53cfabea0b6471d6669deb95e54e96cb7913b687e4388da1bb3d9",
    "current_office": "df2c8d7249c132a4512d744482e4b5ed0ecbe885f0bcfb1295e7e6a7ced0432c",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in HASHES:
        parser.add_argument(f"--{name.replace('_', '-')}", required=True, type=Path)
    args = parser.parse_args()
    if sys.platform != "win32" or hasattr(socket, "AF_UNIX"):
        raise ValueError("This control requires Windows Python without socket.AF_UNIX")
    sources = {}
    for name, expected in HASHES.items():
        content = getattr(args, name).read_bytes()
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError(f"Unexpected source bytes: {name}")
        sources[name] = content
    results = {}
    with tempfile.TemporaryDirectory(prefix="xlsx-startup-control-") as temporary:
        root = Path(temporary)
        for name in ("pinned", "current"):
            workspace = root / name
            (workspace / "office").mkdir(parents=True)
            (workspace / "profile").mkdir()
            (workspace / "temp").mkdir()
            (workspace / "recalc.py").write_bytes(sources[f"{name}_recalc"])
            (workspace / "office/soffice.py").write_bytes(sources[f"{name}_office"])
            workbook_path = workspace / "input.xlsx"
            workbook = openpyxl.Workbook()
            workbook.active["A1"] = "=1+1"
            workbook.save(workbook_path)
            workbook.close()
            env = os.environ.copy()
            env.update(
                USERPROFILE=str(workspace / "profile"), TEMP=str(workspace / "temp"), TMP=str(workspace / "temp")
            )
            wrapper = (
                "import runpy,sys; sys.path.insert(0,sys.argv[1]); "
                "sys.argv=[sys.argv[1]+'/recalc.py',sys.argv[2]]; runpy.run_path(sys.argv[0],run_name='__main__')"
            )
            process = subprocess.run(
                [sys.executable, "-I", "-B", "-c", wrapper, str(workspace), str(workbook_path)],
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            workbook = openpyxl.load_workbook(workbook_path, data_only=True)
            cached_value = workbook.active["A1"].value
            workbook.close()
            expected_text = "module 'socket' has no attribute 'AF_UNIX'"
            if (
                process.returncode != 1
                or expected_text not in process.stdout + process.stderr
                or cached_value is not None
            ):
                raise ValueError(f"Expected startup failure changed for {name}")
            if list((workspace / "profile").iterdir()):
                raise ValueError("Control unexpectedly touched the isolated user profile")
            results[name] = {
                "exit_code": process.returncode,
                "stdout": process.stdout,
                "stderr": process.stderr.replace(str(workspace), "<workspace>"),
                "cached_formula_value": cached_value,
                "isolated_profile_empty": True,
            }
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "python": platform.python_version(),
                "openpyxl": openpyxl.__version__,
                "source_sha256": HASHES,
                "available_soffice": shutil.which("soffice") is not None,
                "has_af_unix": False,
                "libreoffice_started": False,
                "agent_scored": False,
                "results": results,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

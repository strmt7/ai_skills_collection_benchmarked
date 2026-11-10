"""Discover declared native shell tools without assuming a Git installation layout."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import NamedTuple


class Shells(NamedTuple):
    bash: Path
    utilities: Path
    dash: Path | None


def discover() -> Shells | None:
    configured = os.environ.get("AI_SKILLS_BASH")
    candidates: list[Path] = []
    if configured:
        candidates.append(Path(configured))
    elif os.name == "nt":
        git = shutil.which("git")
        if git:
            executable = Path(git).resolve()
            for parent in list(executable.parents)[:3]:
                candidates += [parent / "usr/bin/bash.exe", parent / "bin/bash.exe"]
    elif bash := shutil.which("bash"):
        candidates.append(Path(bash))
    for candidate in dict.fromkeys(candidates):
        if not candidate.is_file():
            continue
        process = subprocess.run([str(candidate), "--version"], check=False, capture_output=True, timeout=10)
        if process.returncode or not process.stdout.startswith(b"GNU bash, version "):
            continue
        utilities = os.environ.get("AI_SKILLS_UNIX_BIN")
        choices = (
            [Path(utilities)]
            if utilities
            else [candidate.parent, candidate.parent.parent / "usr/bin", Path(os.defpath.split(os.pathsep)[0])]
        )
        suffix = ".exe" if os.name == "nt" else ""
        directory = next(
            (folder for folder in choices if all((folder / (name + suffix)).is_file() for name in ("head", "wc"))), None
        )
        if directory is None:
            if configured:
                raise RuntimeError("Configured GNU Bash has no declared head/wc runtime")
            continue
        dash_value = os.environ.get("AI_SKILLS_DASH")
        dash = Path(dash_value) if dash_value else directory / ("dash" + suffix)
        if dash_value and not dash.is_file():
            raise RuntimeError("The declared dash executable is unavailable")
        return Shells(candidate.absolute(), directory.absolute(), dash.absolute() if dash.is_file() else None)
    if configured:
        raise RuntimeError("The declared GNU Bash executable is unavailable or failed admission")
    return None

"""Shared checkout-owned process, cache and transport boundaries for agent tools."""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import platform
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from _catalog_publication import checked_path
from _windows_owned_python import run_python

EXECUTE = "import subprocess,sys; raise SystemExit(subprocess.call(sys.argv[1:],stdin=subprocess.DEVNULL))"
SCRIPT = """import runpy,sys
from pathlib import Path
script=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(script.parent))
sys.argv=sys.argv[1:]
runpy.run_path(str(script),run_name='__main__')
"""


def script_command(root: Path, interpreter: Path, name: str, *arguments: str | Path) -> list[str | Path]:
    return [interpreter, "-I", "-B", "-c", SCRIPT, root / "tools" / name, *arguments]


def input_identity(root: Path, names: list[str]) -> str:
    records = {name: hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in names}
    return hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()


def home_path(root: Path, target: Path) -> Path:
    target = target.absolute()
    if target == root / ".venv" or not target.is_relative_to(root / ".venv"):
        raise ValueError("Provider home must be a dedicated directory under this checkout's .venv")
    return checked_path(root, target.relative_to(root).as_posix())


def require_interpreter() -> None:
    if (
        sys.platform != "win32"
        or platform.machine().upper() not in {"AMD64", "X86_64"}
        or sys.implementation.name != "cpython"
        or sys.version_info[:3] != (3, 13, 17)
    ):
        raise ValueError("Run this Windows x64 provider launcher with CPython 3.13.17 (for example, py -3.13)")


def profile_environment(home: Path, extra_paths: dict[str, str]) -> dict[str, str]:
    allowed = {"SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT"}
    child = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    paths = {
        "HOME": "profile",
        "USERPROFILE": "profile",
        "APPDATA": "profile/AppData/Roaming",
        "LOCALAPPDATA": "profile/AppData/Local",
        "TEMP": "temporary",
        "TMP": "temporary",
        "PIP_CACHE_DIR": "pip-cache",
        **extra_paths,
    }
    for key, relative in paths.items():
        path = checked_path(home, relative)
        path.mkdir(parents=True, exist_ok=True)
        child[key] = str(path)
    child.update(
        PYTHONUTF8="1",
        PYTHONNOUSERSITE="1",
        PYTHONSAFEPATH="1",
        PYTHON_DOTENV_DISABLED="1",
        PYTHONHASHSEED="0",
        PIP_CONFIG_FILE="nul",
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        PIP_NO_INPUT="1",
        DO_NOT_TRACK="1",
        LITELLM_TELEMETRY="False",
        HF_HUB_DISABLE_TELEMETRY="1",
        TOKENIZERS_PARALLELISM="false",
    )
    return child


def phase(
    root: Path, home: Path, name: str, arguments: list[str | Path], *, environment: dict[str, str], timeout: int = 600
) -> dict[str, Any]:
    directory = checked_path(home, "logs/" + name + "-" + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    with (directory / "stdout.log").open("xb") as stdout, (directory / "stderr.log").open("xb") as stderr:
        status, receipt = run_python(
            sys.executable,
            EXECUTE,
            [str(value) for value in arguments],
            cwd=root,
            environment=environment,
            stdout=stdout,
            stderr=stderr,
            timeout=timeout,
            output_limit=16 * 1024 * 1024,
        )
    receipt.update(exit_code=status, phase=name)
    (directory / "process.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    if status != 0 or receipt["active_processes_after_cleanup"] != 0:
        raise ValueError(f"{name} failed (exit {status}); native diagnostics: {directory}")
    return {"phase": name, "logs": str(directory), **receipt}


def download_archive(home: Path, pin: dict[str, Any]) -> Path:
    parts = urlsplit(pin["archive_url"])
    if (
        parts.scheme != "https"
        or parts.netloc != "files.pythonhosted.org"
        or not parts.path.startswith("/packages/")
        or parts.query
        or parts.fragment
    ):
        raise ValueError("Provider source must use its pinned PyPI HTTPS artifact URL")
    connection = http.client.HTTPSConnection("files.pythonhosted.org", timeout=60)
    try:
        connection.request("GET", parts.path, headers={"User-Agent": "AI-Skills-Provider-Setup/1"})
        response = connection.getresponse()
        raw = response.read(pin["archive_bytes"] + 1)
        status = response.status
    finally:
        connection.close()
    metadata = {
        "url": pin["archive_url"],
        "status_code": status,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    (home / "upstream-response.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n")
    archive = home / "upstream.tar.gz"
    archive.write_bytes(raw)
    if status != 200:
        raise ValueError("Pinned source download failed; redirects and alternate sources are not accepted")
    if len(raw) != pin["archive_bytes"] or metadata["sha256"] != pin["archive_sha256"]:
        raise ValueError("Downloaded source differs from the pinned archive")
    return archive

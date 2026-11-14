"""Frozen offline Python environments for native benchmark verifiers."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import platform
import re
import stat
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any

PREFIX = PurePosixPath("/tmp/grader-dependencies")
PYTHON = str(PREFIX / "bin/python")
INPUT = Path("/tmp/benchmark-inputs")
MAX_BYTES = 256 * 1024**2
MAX_ENTRIES = 20000


def validate_environment(spec: Any, asset: Callable[[Any], bytes]) -> dict[str, Any]:
    """Require a complete target graph, not a cross-platform candidate pool."""
    if (
        not isinstance(spec, dict)
        or set(spec) != {"schema_version", "python_version", "machine", "wheels", "resources", "setup_timeout_seconds"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] != 1
        or not isinstance(spec["python_version"], str)
        or re.fullmatch(r"3\.\d+\.\d+", spec["python_version"]) is None
        or spec["machine"] != "x86_64"
        or type(spec["setup_timeout_seconds"]) is not int
        or not 30 <= spec["setup_timeout_seconds"] <= 240
        or not isinstance(spec["resources"], dict)
        or set(spec["resources"]) != {"memory_bytes", "tmpfs_bytes"}
        or not isinstance(spec["wheels"], list)
        or not 2 <= len(spec["wheels"]) <= 64
    ):
        raise ValueError("Expected a frozen Linux x64 grader Python environment")
    projects, filenames, total = set(), set(), 0
    for row in spec["wheels"]:
        if (
            not isinstance(row, dict)
            or set(row) != {"project", "version", "path", "sha256"}
            or not isinstance(row["project"], str)
            or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", row["project"]) is None
            or row["project"] in projects
            or not isinstance(row["version"], str)
            or re.fullmatch(r"\d+(?:\.\d+)*(?:\.post\d+)?", row["version"]) is None
            or not isinstance(row["path"], str)
            or re.fullmatch(r"[A-Za-z0-9._+-]+\.whl", Path(row["path"]).name) is None
            or Path(row["path"]).name.casefold() in filenames
        ):
            raise ValueError("Invalid or repeated grader dependency wheel")
        total += len(asset(row))
        projects.add(row["project"])
        filenames.add(Path(row["path"]).name.casefold())
    if not {"pip", "pytest"} <= projects or total > 48 * 1024**2:
        raise ValueError("The frozen graph must include pip and pytest within the staging budget")
    return spec


def environment_packet(spec: dict[str, Any], asset: Callable[[Any], bytes]) -> dict[str, bytes]:
    """Stage only admitted bytes; the native installer cannot contact a package index."""
    lock = "".join(f"{row['project']}=={row['version']} --hash=sha256:{row['sha256']}\n" for row in spec["wheels"])
    return {
        "grader-requirements.lock": lock.encode(),
        **{"grader-wheels/" + Path(row["path"]).name: asset(row) for row in spec["wheels"]},
        "tools/_native_grader_dependencies.py": Path(__file__).read_bytes(),
    }


def inventory(root: Path | None = None) -> dict[str, Any]:
    """Bind the entire read-only installed namespace, including modes and links."""
    root = Path(PREFIX) if root is None else root
    pending, rows, total = [root], [], 0
    while pending:
        path = pending.pop()
        info = path.lstat()
        row: dict[str, Any] = {"path": path.relative_to(root).as_posix(), "mode": stat.S_IMODE(info.st_mode)}
        if info.st_uid != 0 or (not path.is_symlink() and info.st_mode & 0o222):
            raise ValueError("Grader dependencies must remain root-owned and read-only")
        if path.is_symlink():
            if not path.resolve(strict=True).is_relative_to(root):
                raise ValueError("Grader dependency link leaves its environment")
            row.update(kind="link", target=os.readlink(path))
        elif stat.S_ISDIR(info.st_mode):
            row["kind"] = "directory"
            pending.extend(path.iterdir())
        elif stat.S_ISREG(info.st_mode):
            total += info.st_size
            if total > MAX_BYTES:
                raise ValueError("Grader dependencies exceed the expanded byte budget")
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            row.update(kind="file", bytes=info.st_size, sha256=digest)
        else:
            raise ValueError("Unsupported grader dependency object")
        rows.append(row)
        if len(rows) + len(pending) > MAX_ENTRIES:
            raise ValueError("Grader dependencies exceed the namespace budget")
    rows.sort(key=lambda row: row["path"])
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"objects": len(rows), "bytes": total, "sha256": digest, "inventory": rows}


def versions() -> dict[str, str]:
    return {
        re.sub(r"[-_.]+", "-", dist.metadata["Name"]).lower(): dist.version
        for dist in importlib.metadata.distributions()
    }


def prepare() -> dict[str, Any]:
    """Execute only as root in an owned, network-disabled, resource-bounded lease."""
    spec = json.loads((INPUT / "task.json").read_bytes())["python_environment"]
    prefix = Path(PREFIX)
    uid = getattr(os, "getuid", lambda: -1)
    if uid() != 0 or prefix.exists():
        raise ValueError("Grader environment setup needs root and a fresh private destination")
    if platform.python_version() != spec["python_version"] or platform.machine() != spec["machine"]:
        raise ValueError("Native Python or architecture differs from the frozen environment")
    base_versions = versions()
    env = {
        "PATH": os.defpath,
        "HOME": "/tmp/grader-setup-home",
        "LANG": "C.UTF-8",
        "PIP_CONFIG_FILE": os.devnull,
        "PIP_NO_INDEX": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
    }
    Path(env["HOME"]).mkdir()
    commands = []

    def run(args: list[str]) -> bytes:
        result = subprocess.run(
            args, env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=60, check=False, cwd=INPUT
        )
        record = {
            "argv": args,
            "exit_code": result.returncode,
            "stdout": result.stdout.decode(),
            "stderr": result.stderr.decode(),
        }
        commands.append(record)
        print(json.dumps(record), file=sys.stderr, flush=True)
        if result.returncode:
            raise ValueError("Offline grader dependency installation failed")
        return result.stdout

    run([sys.executable, "-I", "-B", "-m", "venv", "--without-pip", "--copies", str(PREFIX)])
    common = [
        "install",
        "--no-index",
        "--no-cache-dir",
        "--require-hashes",
        "--only-binary=:all:",
        "--no-compile",
        "--no-input",
        "--progress-bar",
        "off",
        "--find-links=" + str(INPUT / "grader-wheels"),
    ]
    pip_row = next(row for row in spec["wheels"] if row["project"] == "pip")
    bootstrap = INPUT / "grader-pip.lock"
    bootstrap.write_text(f"pip=={pip_row['version']} --hash=sha256:{pip_row['sha256']}\n")
    run([sys.executable, "-I", "-B", "-m", "pip", "--isolated", "--python", PYTHON, *common, "-r", str(bootstrap)])
    run([PYTHON, "-I", "-B", "-m", "pip", "--isolated", *common, "-r", str(INPUT / "grader-requirements.lock")])
    run([PYTHON, "-I", "-B", "-m", "pip", "check"])
    code = "import json,sys;sys.path.insert(0,'/tmp/benchmark-inputs/tools');from _native_grader_dependencies import versions;print(json.dumps({'prefix':sys.prefix,'versions':versions()}))"
    observed = json.loads(run([PYTHON, "-I", "-B", "-c", code]))
    expected = {row["project"]: row["version"] for row in spec["wheels"]}
    if observed != {"prefix": str(PREFIX), "versions": expected} or versions() != base_versions:
        raise ValueError("Installed graph differs from its lock or changed the base interpreter")
    pending = [prefix]
    while pending:
        path = pending.pop()
        if path.is_symlink():
            continue
        if path.is_dir():
            pending.extend(path.iterdir())
        path.chmod(stat.S_IMODE(path.stat().st_mode) & ~0o222)
    return {
        "python_version": platform.python_version(),
        "versions": expected,
        "inventory": inventory(),
        "base_interpreter_unchanged": True,
        "commands": commands,
    }

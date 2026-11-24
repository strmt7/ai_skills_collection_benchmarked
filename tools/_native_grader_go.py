"""Frozen offline Go module inputs for native SWE-Skills-Bench verifiers."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Any

from _trial_protocol import relative_path

INPUT = PurePosixPath("/tmp/benchmark-inputs")
HOME = PurePosixPath("/tmp/grader-go")
MODULES = "grader-go-proxy"
DECLARATIONS = {"go.mod", "go.sum", "go.work", "go.work.sum"}
PROXY_RECORD = re.compile(r"(?:[A-Za-z0-9._~!-]+/)+@v/v[0-9][A-Za-z0-9.+!-]*[.](info|mod|zip)")
MAX_PROXY_BYTES = 48 * 1024**2


def validate_go_environment(spec: Any, asset: Callable[[Any], bytes]) -> dict[str, Any]:
    """Validate portable paths, a closed staging inventory and explicit guest limits."""
    if (
        not isinstance(spec, dict)
        or set(spec) != {"schema_version", "go_version", "go_sha256", "modules", "resources", "setup_timeout_seconds"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] != 1
        or not isinstance(spec["go_version"], str)
        or re.fullmatch(r"go1[.][0-9]+[.][0-9]+", spec["go_version"]) is None
        or not isinstance(spec["go_sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", spec["go_sha256"]) is None
        or type(spec["setup_timeout_seconds"]) is not int
        or not 30 <= spec["setup_timeout_seconds"] <= 600
        or not isinstance(spec["resources"], dict)
        or set(spec["resources"]) != {"memory_bytes", "tmpfs_bytes", "cpu_count", "repository_bytes"}
        or not isinstance(spec["modules"], list)
        or len(spec["modules"]) > 3000
    ):
        raise ValueError("Expected a frozen Linux x64 Go grader environment")

    paths: set[str] = set()
    versions: dict[str, set[str]] = {}
    total = 0
    for item in spec["modules"]:
        if not isinstance(item, dict) or set(item) != {"path", "sha256", "target"}:
            raise ValueError("Invalid Go module asset declaration")
        target = relative_path(item["target"])
        if PROXY_RECORD.fullmatch(target) is None or target.casefold() in paths:
            raise ValueError("Invalid or repeated Go module proxy record")
        data = asset(item)
        if not data:
            raise ValueError("Go module proxy records cannot be empty")
        total += len(data)
        if total > MAX_PROXY_BYTES:
            raise ValueError("Go proxy files exceed the bounded input packet")

        version, suffix = target.rsplit(".", 1)
        versions.setdefault(version, set()).add(suffix)
        paths.add(target.casefold())
    if any(not {"info", "mod"} <= records for records in versions.values()):
        raise ValueError("Each Go proxy version requires its info and module records")
    return spec


def go_environment_packet(spec: dict[str, Any], asset: Callable[[Any], bytes]) -> dict[str, bytes]:
    return {
        "tools/_native_grader_go.py": Path(__file__).read_bytes(),
        **{MODULES + "/" + row["target"]: asset(row) for row in spec["modules"]},
    }


def go_environment(inherited: dict[str, str], spec: dict[str, Any]) -> dict[str, str]:
    """Use the publisher image's compiler and only the staged module bytes."""
    env = {**inherited}
    env.pop("GOWORK", None)
    env.update(
        HOME=str(HOME),
        GOENV="off",
        GOFLAGS="",
        GO111MODULE="on",
        GOTOOLCHAIN="local",
        GOPATH=str(HOME / "gopath"),
        GOMODCACHE=str(HOME / "modules"),
        GOCACHE=str(HOME / "cache"),
        GOTMPDIR=str(HOME / "tmp"),
        GOMAXPROCS=str(spec["resources"]["cpu_count"]),
        GOPROXY=f"file://{INPUT / MODULES}" if spec["modules"] else "off",
        GOPRIVATE="",
        GONOPROXY="none",
        GOSUMDB="off",
        GOVCS="*:off",
    )
    return env


def _digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def proxy_inventory(spec: dict[str, Any]) -> dict[str, Any]:
    """Verify native image staging against the host's frozen module declarations."""
    root = Path(INPUT / MODULES)
    expected = {row["target"]: row["sha256"] for row in spec["modules"]}
    observed: dict[str, str] = {}
    for path in [root, *root.rglob("*")] if root.exists() else []:
        info = path.lstat()
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError("The staged Go proxy must be root-owned and read-only to the verifier")
        if stat.S_ISREG(info.st_mode):
            observed[path.relative_to(root).as_posix()] = _digest(path)
        elif not stat.S_ISDIR(info.st_mode):
            raise ValueError("Unsupported object in the staged Go proxy")
    if observed != expected:
        raise ValueError("Native Go proxy bytes differ from the frozen graph")
    return {"files": len(observed), "sha256": hashlib.sha256(json.dumps(observed, sort_keys=True).encode()).hexdigest()}


def _module_files(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _digest(path)
        for path in root.rglob("go.*")
        if path.name in DECLARATIONS and path.is_file()
    }


def prepare_go() -> dict[str, Any]:
    """Run publisher dependency setup on the frozen starting tree under the grader UID."""
    uid = getattr(os, "getuid", lambda: 0)()
    home = Path(HOME)
    if uid == 0 or home.exists():
        raise ValueError("Go setup requires a fresh environment and an unprivileged grader")
    spec = json.loads(Path(INPUT / "task.json").read_bytes())["go_environment"]
    proxy = proxy_inventory(spec)
    env = go_environment(dict(os.environ), spec)
    go = shutil.which("go", path=env.get("PATH"))
    if go is None or _digest(Path(go)) != spec["go_sha256"]:
        raise ValueError("Native Go executable differs from the frozen image identity")
    version = subprocess.run([go, "version"], env=env, capture_output=True, text=True, timeout=10, check=True)
    if version.stderr or version.stdout.strip() != f"go version {spec['go_version']} linux/amd64":
        raise ValueError("Native Go release or target differs from the frozen environment")

    home.mkdir(mode=0o700)
    Path(env["GOTMPDIR"]).mkdir()
    starting_tree = home / "baseline"
    shutil.copytree(Path(INPUT / "baseline"), starting_tree, copy_function=shutil.copyfile)
    original = _module_files(starting_tree)
    if "go.mod" not in original:
        raise ValueError("The frozen Go starting tree requires a root go.mod")
    command = [go, "mod", "download"]
    result = subprocess.run(
        command,
        cwd=starting_tree,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=spec["setup_timeout_seconds"],
        check=False,
    )
    record = {
        "argv": command,
        "exit_code": result.returncode,
        "stdout": result.stdout.decode("utf-8", errors="replace"),
        "stderr": result.stderr.decode("utf-8", errors="replace"),
    }
    if result.returncode:
        raise ValueError(f"Publisher Go dependency setup failed: {record}")
    if _module_files(starting_tree) != original:
        raise ValueError("Freeze the publisher's post-setup module declarations before grading")
    return {"uid": uid, "version": version.stdout.strip(), "proxy": proxy, "download": record}

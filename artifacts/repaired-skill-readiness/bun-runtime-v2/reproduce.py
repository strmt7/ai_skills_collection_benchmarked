"""Reproduce Bun 1.4.5 package, runtime, test and bundle controls on x64."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BUN_VERSION = "1.4.5"
NODE_VERSION = "v24.22.3"
LOCK_DIGEST = "59912fe72e8001cd3ef4506c781f65ca47d05378d3818d2bdb52c5bb2632301a"
RUNTIMES = {
    "linux": (
        51336091,
        "dcb23a18a1c2fff12d57bcef696dbbb42eb67fde29f43816ecb595459a24c463",
        "a7ec1b37e6ff9d187e4198c5b6df9a4eb1c74dd31804fb3bac55cc4ceca1ac01",
    ),
    "win32": (
        54438042,
        "3c081c73865e7a3453a9d514cc2ba3d699880621bcf67bb17241ff5194cb1d4b",
        "86fc4785327db5f5c7558dc6156c543b433c313e813a222e088086222ab4afa6",
    ),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def prepare_bun(root: Path, os_name: str, size: int, checksum: str) -> Path:
    """Admit the pinned release archive before extracting and running one binary."""
    name = f"bun-{os_name}-x64-baseline.zip"
    archive = root / name
    url = f"https://github.com/oven-sh/bun/releases/download/bun-v{BUN_VERSION}/{name}"
    with urllib.request.urlopen(url, timeout=35) as response, archive.open("xb") as target:
        remaining = size
        while remaining > 0:
            block = response.read(min(1024**2, remaining))
            if not block:
                break
            target.write(block)
            remaining -= len(block)
        require(remaining == 0 and not response.read(1), "Bun archive size mismatch")
    with archive.open("rb") as source:
        require(hashlib.file_digest(source, "sha256").hexdigest() == checksum, "Bun archive hash mismatch")
    executable = "bun.exe" if os_name == "windows" else "bun"
    bun = root / executable
    with zipfile.ZipFile(archive) as package:
        [member] = [info for info in package.infolist() if Path(info.filename).name == executable and not info.is_dir()]
        with package.open(member) as source, bun.open("xb") as target:
            shutil.copyfileobj(source, target)
    if os_name == "linux":
        bun.chmod(0o700)
    return bun


def run_controls(bun: Path, node: Path, root: Path, output: Path) -> tuple[str, dict[str, dict[str, int | str]]]:
    profile = root / "profile"
    profile.mkdir()
    environment = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR", "COMSPEC") if key in os.environ}
    environment.update(
        PATH=os.pathsep.join(map(str, (bun.parent, node.parent))),
        HOME=str(profile),
        USERPROFILE=str(profile),
        LOCALAPPDATA=str(profile / "local"),
        APPDATA=str(profile / "appdata"),
        TEMP=str(profile),
        TMP=str(profile),
        TMPDIR=str(profile),
        XDG_CACHE_HOME=str(profile / "cache"),
        XDG_CONFIG_HOME=str(profile / "config"),
        BUN_INSTALL_CACHE_DIR=str(profile / "bun-cache"),
        BUN_DISABLE_TRANSPILER_CACHE="1",
        BUN_NO_TELEMETRY="1",
    )
    checks: dict[str, dict[str, int | str]] = {}

    def run(label: str, command: list[str | Path], directory: Path, *, exit_code: int = 0) -> tuple[str, str]:
        result = subprocess.run(
            command,
            env=environment,
            cwd=directory,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=20,
        )
        (output / f"{label}.stdout.native").write_bytes(result.stdout)
        (output / f"{label}.stderr.native").write_bytes(result.stderr)
        require(result.returncode == exit_code, f"{label} returned {result.returncode}; expected {exit_code}")
        checks[label] = {
            "exit": result.returncode,
            "stdout_sha256": digest(result.stdout),
            "stderr_sha256": digest(result.stderr),
        }
        return result.stdout.decode("utf-8").strip(), result.stderr.decode("utf-8")

    require(run("bun-version", [bun, "--version"], root)[0] == BUN_VERSION, "Bun version mismatch")
    require(run("node-version", [node, "--version"], root)[0] == NODE_VERSION, "Node version mismatch")
    project = root / "fixture"
    project.mkdir()
    for name, value in (("dep", "qualified value"), ("alt", "alternate value")):
        dependency = project / name
        dependency.mkdir()
        write_json(
            dependency / "package.json",
            {"name": "fixture-dep", "version": "1.0.0", "type": "module", "main": "./index.mjs"},
        )
        (dependency / "index.mjs").write_bytes(f"export const value = {json.dumps(value)};\n".encode())

    manifest = {
        "name": "bun-compatibility",
        "private": True,
        "type": "module",
        "dependencies": {"fixture-dep": "file:./dep"},
    }
    write_json(project / "package.json", manifest)
    frozen_install = [bun, "install", "--frozen-lockfile", "--ignore-scripts"]
    missing_lock = root / "missing-lock"
    missing_lock.mkdir()
    shutil.copytree(project / "dep", missing_lock / "dep")
    write_json(missing_lock / "package.json", manifest)
    run("frozen-without-lock", frozen_install, missing_lock)
    require(
        not any((missing_lock / name).exists() for name in ("bun.lock", "bun.lockb")),
        "Missing-lock control wrote a lock",
    )
    installed = missing_lock / "node_modules" / "fixture-dep" / "index.mjs"
    require(
        "qualified value" in installed.read_text(encoding="utf-8"),
        "Missing-lock control did not install the dependency",
    )

    run("lock-only", [bun, "install", "--lockfile-only", "--ignore-scripts"], project)
    lock = project / "bun.lock"
    require(digest(lock.read_bytes()) == LOCK_DIGEST, "Generated project lock changed")
    run("frozen-install", frozen_install, project)
    require(digest(lock.read_bytes()) == LOCK_DIGEST, "Frozen install rewrote the lock")
    (project / "app.ts").write_bytes(b'import { value } from "fixture-dep";\nconsole.log(value);\n')
    (project / "runtime-types.ts").write_bytes(b'const value: number = "text";\nconsole.log(typeof value);\n')
    require(run("typescript-runtime", [bun, "run", "app.ts"], project)[0] == "qualified value", "Bun output mismatch")
    require(
        run("typescript-transpile-only", [bun, "run", "runtime-types.ts"], project)[0] == "string",
        "Type control changed",
    )
    run("node-target-build", [bun, "build", "./app.ts", "--target=node", "--outdir", "./dist"], project)
    require(
        run("node-target-runtime", [node, "dist/app.js"], project)[0] == "qualified value",
        "Node bundle output mismatch",
    )

    test = project / "acceptance.test.ts"
    test.write_bytes(b'import { expect, test } from "bun:test";\ntest("value", () => expect(7).toBe(7));\n')
    run("passing-test", [bun, "test", "./acceptance.test.ts"], project)
    test.write_bytes(test.read_bytes().replace(b".toBe(7)", b".toBe(8)", 1))
    output_text = run("failed-assertion", [bun, "test", "./acceptance.test.ts"], project, exit_code=1)
    require("fail" in "".join(output_text).lower(), "Assertion failure evidence is absent")
    manifest["dependencies"] = {"fixture-dep": "file:./alt"}
    write_json(project / "package.json", manifest)
    output_text = run("rejected-drift", frozen_install, project, exit_code=1)
    require(
        "frozen" in "".join(output_text).lower() and digest(lock.read_bytes()) == LOCK_DIGEST, "Drift control failed"
    )
    return LOCK_DIGEST, checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("node", type=Path, help="Node v24.22.3 x64 executable")
    parser.add_argument("output", type=Path, help="New directory for native observations")
    args = parser.parse_args()
    if sys.platform not in RUNTIMES or platform.machine().lower() not in {"x86_64", "amd64"}:
        parser.error("this control supports Windows and Linux x64")
    os_name = "windows" if sys.platform == "win32" else "linux"
    size, checksum, node_checksum = RUNTIMES[sys.platform]
    node = args.node.resolve(strict=True)
    with node.open("rb") as source:
        require(hashlib.file_digest(source, "sha256").hexdigest() == node_checksum, "Node executable hash mismatch")
    output = args.output.resolve()
    output.mkdir()
    with tempfile.TemporaryDirectory(prefix="ai-skills-bun-") as temporary:
        root = Path(temporary)
        bun = prepare_bun(root, os_name, size, checksum)
        lock_digest, checks = run_controls(bun, node, root, output)
    require(not root.exists(), "The scratch fixture remains")
    write_json(
        output / "result.json",
        {
            "platform": os_name,
            "bun": BUN_VERSION,
            "node": NODE_VERSION,
            "archive_sha256": checksum,
            "node_sha256": node_checksum,
            "lock_sha256": lock_digest,
            "frozen_without_lock_installed": True,
            "frozen_without_lock_created_lock": False,
            "checks": checks,
            "scratch_removed": True,
            "model_attempts": 0,
        },
    )
    print(json.dumps({"platform": os_name, "checks": len(checks), "passed": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

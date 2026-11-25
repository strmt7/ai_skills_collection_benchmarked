"""Reproduce the locked slides controls with isolated native dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import zipfile
from contextlib import nullcontext
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MIRROR = Path(
    "skills/by-category/documents-spreadsheets-presentations/latest-release-creative/"
    "ckm-slides/references/html-template.md"
)
SUPPORTED_NODES = {"v24.22.3", "v26.13.1"}


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def decode(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path.name}")
    return value


def make_manager(cache: Path, destination: Path, supplied: Path | None, offline: bool) -> tuple[Path, str]:
    pins = decode(HERE / "manager.json")
    host = {"win32": "windows", "linux": "linux"}.get(sys.platform)
    if host is None or platform.machine().lower() not in {"amd64", "x86_64"}:
        raise ValueError("The slides controls support Windows and Linux x64")
    release = pins["assets"][host]
    archive = supplied or cache / release["name"]
    if not archive.exists():
        if supplied is not None or offline:
            raise ValueError("The specified or cached pnpm archive is missing")
        with urllib.request.urlopen(release["url"], timeout=30) as response:
            content = response.read(release["bytes"] + 1)
        if len(content) != release["bytes"] or hashlib.sha256(content).hexdigest() != release["sha256"]:
            raise ValueError("The downloaded pnpm archive differs from the publisher pin")
        with tempfile.TemporaryDirectory(dir=cache, prefix="pnpm-") as download:
            staged = Path(download) / archive.name
            staged.write_bytes(content)
            staged.replace(archive)
    if archive.stat().st_size != release["bytes"] or sha256(archive) != release["sha256"]:
        raise ValueError("The pnpm archive differs from the publisher pin")
    name = "pnpm.exe" if host == "windows" else "pnpm"
    executable = destination / name
    with executable.open("xb") as output:
        if host == "windows":
            with zipfile.ZipFile(archive) as bundle:
                [entry] = [item for item in bundle.infolist() if Path(item.filename).name == name and not item.is_dir()]
                with bundle.open(entry) as source:
                    shutil.copyfileobj(source, output)
        else:
            with tarfile.open(archive, "r:gz") as bundle:
                [entry] = [item for item in bundle if item.isfile() and Path(item.name).name == name]
                source = bundle.extractfile(entry)
                if source is None:
                    raise ValueError("The pnpm archive has no usable executable")
                with source:
                    shutil.copyfileobj(source, output)
    if host == "linux":
        executable.chmod(0o700)
    return executable, release["sha256"]


def control_commands(original: Path, repaired: Path, playwright: Path, chart: Path, version: str, engine: str):
    yield f"labels-{engine}", "labels", [playwright, original, repaired, engine]
    yield f"motion-{engine}", "motion", [playwright, original, repaired, engine]
    for layout in ("desktop", "narrow"):
        yield (
            f"navigation-{engine}-{layout}",
            "navigation",
            [playwright, original, repaired, "playwright-default", engine, layout],
        )
    for layout in ("desktop", "narrow", "landscape"):
        yield (
            f"chart-{engine}-{layout}",
            "chart",
            [playwright, repaired, version, chart, "playwright-default", engine, "-", layout],
        )
    for layout in ("narrow", "landscape"):
        yield f"overflow-{engine}-{layout}", "overflow", [playwright, original, repaired, engine, layout]


def reproduce(args: argparse.Namespace, cache: Path, work: Path) -> dict[str, Any]:
    node = args.node.resolve(strict=True)
    pnpm, archive_sha = make_manager(cache, work, args.manager_archive, args.offline)
    small_environment = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "LANG", "LC_ALL", "SystemDrive")
    env = {key: os.environ[key] for key in small_environment if key in os.environ}
    profile = cache / "profile"
    data = {name: profile / name for name in ("cache", "config", "local", "roaming", "runtime", "tmp")}
    for directory in data.values():
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = cache / "registry.npmrc"
    config.write_text("registry=https://registry.npmjs.org/\n", encoding="ascii")
    global_config = cache / "empty.npmrc"
    global_config.write_bytes(b"")
    env.update(
        PATH=str(node.parent) + os.pathsep + env.get("PATH", ""),
        HOME=str(profile),
        USERPROFILE=str(profile),
        LOCALAPPDATA=str(data["local"]),
        APPDATA=str(data["roaming"]),
        XDG_CACHE_HOME=str(data["cache"]),
        XDG_CONFIG_HOME=str(data["config"]),
        XDG_RUNTIME_DIR=str(data["runtime"]),
        TEMP=str(data["tmp"]),
        TMP=str(data["tmp"]),
        TMPDIR=str(data["tmp"]),
        PNPM_HOME=str(profile / "pnpm"),
        PLAYWRIGHT_BROWSERS_PATH=str(cache / "browsers"),
        PLAYWRIGHT_SKIP_BROWSER_GC="1",
        npm_config_userconfig=str(config),
        npm_config_globalconfig=str(global_config),
        CI="true",
    )

    def run(label: str, command: list[Path | str], timeout: int = 45) -> Path:
        stdout = args.output / (label + ".stdout.native")
        stderr = args.output / (label + ".stderr.native")
        with stdout.open("xb") as capture, stderr.open("xb") as errors:
            proc = subprocess.run(
                list(map(str, command)),
                cwd=work,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=capture,
                stderr=errors,
                timeout=timeout,
                check=False,
            )
        if proc.returncode:
            raise ValueError(f"{label} exited {proc.returncode}. See {stderr.name}.")
        return stdout

    for name in ("package.json", "pnpm-lock.yaml"):
        shutil.copyfile(HERE / "dependencies" / name, work / name)
    dependency = decode(work / "package.json")
    node_version = run("node", [node, "--version"]).read_text(encoding="utf-8").strip()
    if node_version not in SUPPORTED_NODES:
        raise ValueError(f"Unsupported Node runtime {node_version}")
    manager_version = run("pnpm", [pnpm, "--version"]).read_text(encoding="utf-8").strip()
    if dependency["engines"]["pnpm"] != manager_version:
        raise ValueError("The native pnpm version differs from the package manifest")
    lock_sha = sha256(work / "pnpm-lock.yaml")
    command: list[Path | str] = [
        pnpm,
        "install",
        "--frozen-lockfile",
        "--ignore-scripts",
        "--store-dir",
        cache / "store",
    ]
    if args.offline:
        command.append("--offline")
    run("dependencies", command, 120)
    if sha256(work / "pnpm-lock.yaml") != lock_sha:
        raise ValueError("Frozen install changed the lock")
    playwright = work / "node_modules/playwright"
    chart = work / "node_modules/chart.js/dist/chart.umd.min.js"
    cli = playwright / "cli.js"
    engines = ["chromium", "webkit" if sys.platform == "win32" else "firefox"]
    if not args.offline:
        run("install-chromium", [node, cli, "install", "--only-shell", "chromium"], 150)
        run("install-secondary-browser", [node, cli, "install", engines[1]], 150)
    result = {
        "platform": sys.platform,
        "node": node_version,
        "node_sha256": sha256(node),
        "pnpm": manager_version,
        "pnpm_archive_sha256": archive_sha,
        "pnpm_lock_sha256": lock_sha,
        "chart_bundle_sha256": sha256(chart),
        "offline_install": args.offline,
        "engines": engines,
        "agent_performance_tested": False,
    }
    if args.prepare_only:
        return {**result, "native_receipts": {}}
    original = ROOT / "included" / MIRROR
    repaired = ROOT / "included/repaired" / MIRROR
    native_receipts = {}
    for engine in engines:
        commands = control_commands(
            original, repaired, playwright, chart, dependency["devDependencies"]["chart.js"], engine
        )
        for label, script, parameters in commands:
            report = run(label, [node, HERE / (script + ".cjs"), *parameters])
            value = decode(report)
            if value["platform"] != sys.platform or value["browser_engine"] != engine:
                raise ValueError(f"Unexpected platform or engine in {label}")
            native_receipts[label] = sha256(report)
    return {**result, "native_receipts": native_receipts}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path, required=True, help="Path to the selected Node runtime")
    parser.add_argument("--output", type=Path, required=True, help="New directory for native receipts")
    parser.add_argument("--manager-archive", type=Path, help="A previously downloaded exact pnpm release asset")
    parser.add_argument("--cache-root", type=Path, help="An owned cache for dependency and browser reuse")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--offline", action="store_true", help="Exercise a complete cached installation")
    action.add_argument(
        "--prepare-only", action="store_true", help="Populate the owned cache without running browser cases"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if (args.offline or args.prepare_only) and args.cache_root is None:
        raise ValueError("--offline and --prepare-only require an explicit --cache-root")
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    cache_manager = (
        nullcontext(args.cache_root)
        if args.cache_root is not None
        else tempfile.TemporaryDirectory(prefix="slides-cache-")
    )
    with cache_manager as directory, tempfile.TemporaryDirectory(prefix="slides-controls-") as temporary:
        cache = Path(directory).resolve()
        cache.mkdir(parents=True, exist_ok=True)
        result = reproduce(args, cache, Path(temporary))
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

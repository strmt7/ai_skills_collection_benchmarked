"""Exercise Yarn 4 cache restoration on independent, offline fixtures."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / (
    "included/skills/by-category/devops-cloud-operations/latest-release-devops/"
    "github-actions-generator/examples/actions/setup-node-cached/action.yml"
)
OVERLAY = ROOT / "included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/yarn-cache-install"
SOURCE_SHA256 = "6df9f7fb7b7034bbd8e66ecd2ae7342028a47a5d25136f8592b6c7e611b69add"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_package(path: Path) -> None:
    files = {
        "package/package.json": b'{"name":"fixture-package","version":"1.0.0","main":"index.js"}',
        "package/index.js": b'module.exports = "fixture-ok";\n',
    }
    with (
        path.open("wb") as stream,
        gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as compressed,
        tarfile.open(fileobj=compressed, mode="w") as archive,
    ):
        for name, data in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            member.mtime = 0
            archive.addfile(member, io.BytesIO(data))


def exercise(node: Path, yarn: Path, output: Path) -> dict[str, Any]:
    source = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    if sha(source) != SOURCE_SHA256 or b"yarn cache dir" not in source:
        raise ValueError("The source action changed; review the baseline")
    if b"if: steps.cache.outputs.cache-hit != 'true'" not in source:
        raise ValueError("The source cache-hit condition changed")
    output.mkdir(parents=True, exist_ok=False)
    logs: dict[str, dict[str, object]] = {}
    with tempfile.TemporaryDirectory(prefix="yarn-cache-control-") as temp:
        root = Path(temp)
        env = os.environ.copy()
        env.update(
            {
                "YARN_IGNORE_PATH": "1",
                "YARN_ENABLE_TELEMETRY": "0",
                "YARN_ENABLE_NETWORK": "0",
                "YARN_GLOBAL_FOLDER": str(root / "global"),
                "CI": "false",
            }
        )

        def run(name: str, args: list[str], cwd: Path, cache: Path) -> subprocess.CompletedProcess[bytes]:
            current_env = {**env, "YARN_CACHE_FOLDER": str(cache)}
            result = subprocess.run(args, cwd=cwd, env=current_env, capture_output=True, timeout=60, check=False)
            for suffix, data in (("stdout", result.stdout), ("stderr", result.stderr)):
                (output / f"{name}.{suffix}").write_bytes(data)
            logs[name] = {
                "exit_code": result.returncode,
                "stdout_sha256": sha(result.stdout),
                "stderr_sha256": sha(result.stderr),
            }
            return result

        package = root / "fixture.tgz"
        make_package(package)
        version = run("yarn-version", [str(node), str(yarn), "--version"], root, root / "version-cache")
        if version.returncode or version.stdout.strip() != b"4.18.1":
            raise ValueError("This control requires Yarn 4.18.1")
        node_version = run("node-version", [str(node), "--version"], root, root / "version-cache")
        if node_version.returncode:
            raise ValueError("Could not determine the Node version")
        for linker in ("node-modules", "pnp"):
            group = root / linker
            seed = group / "seed"
            seed.mkdir(parents=True)
            manifest = {
                "name": "yarn-control",
                "version": "1.0.0",
                "private": True,
                "dependencies": {"fixture-package": "file:./fixture.tgz"},
            }
            (seed / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
            (seed / ".yarnrc.yml").write_text(f"nodeLinker: {linker}\nenableGlobalCache: false\n", encoding="utf-8")
            shutil.copyfile(package, seed / "fixture.tgz")
            seed_cache = group / "seed-cache"
            source_command = run(
                f"{linker}-source-cache-command", [str(node), str(yarn), "cache", "dir"], seed, seed_cache
            )
            if source_command.returncode == 0 or b"Command not found" not in source_command.stdout:
                raise ValueError("The source command did not exhibit the expected Yarn 4 error")
            config = run(
                f"{linker}-config-cache", [str(node), str(yarn), "config", "get", "cacheFolder"], seed, seed_cache
            )
            if config.returncode or Path(os.fsdecode(config.stdout.strip())).resolve() != seed_cache.resolve():
                raise ValueError("Yarn did not report the configured cache")
            initial = run(f"{linker}-seed", [str(node), str(yarn), "install", "--no-immutable"], seed, seed_cache)
            if initial.returncode or not list(seed_cache.glob("*.zip")):
                raise ValueError("Could not seed the offline package cache")
            fresh = group / "fresh"
            fresh.mkdir()
            for name in ("package.json", ".yarnrc.yml", "yarn.lock", "fixture.tgz"):
                shutil.copyfile(seed / name, fresh / name)
            cache = group / "restored-cache"
            shutil.copytree(seed_cache, cache)
            probe = [str(node)] + (["--require", str(fresh / ".pnp.cjs")] if linker == "pnp" else [])
            probe += ["-e", 'if(require("fixture-package")!=="fixture-ok") process.exit(2)']
            before = run(f"{linker}-before-install", probe, fresh, cache)
            if before.returncode == 0 or b"MODULE_NOT_FOUND" not in before.stderr:
                raise ValueError("A fresh project unexpectedly loaded its dependency")
            installed = run(f"{linker}-install", [str(node), str(yarn), "install", "--immutable"], fresh, cache)
            after = run(f"{linker}-after-install", probe, fresh, cache)
            if installed.returncode or after.returncode:
                raise ValueError("The immutable offline installation failed")
            mismatch = group / "mismatch"
            mismatch.mkdir()
            for name in ("package.json", ".yarnrc.yml", "yarn.lock", "fixture.tgz"):
                shutil.copyfile(seed / name, mismatch / name)
            manifest["dependencies"] = {}
            (mismatch / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
            rejected = run(
                f"{linker}-mismatched-lock", [str(node), str(yarn), "install", "--immutable"], mismatch, cache
            )
            if rejected.returncode == 0 or b"YN0028" not in rejected.stdout:
                raise ValueError("A mismatched lockfile was not rejected")
        result: dict[str, Any] = {
            "platform": platform.system(),
            "node_version": node_version.stdout.decode().strip(),
            "yarn_version": version.stdout.decode().strip(),
            "yarn_js_sha256": sha(yarn.read_bytes()),
            "source_action_sha256": sha(source),
            "runner_sha256": sha(Path(__file__).read_bytes()),
            "overlay_sha256": sha((OVERLAY / "SKILL.md").read_bytes()),
            "fixture_tarball_sha256": sha(package.read_bytes()),
            "network_enabled": False,
            "github_cache_service_tested": False,
            "agent_performance_tested": False,
            "logs": logs,
        }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--yarn-js", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    result = exercise(args.node.resolve(strict=True), args.yarn_js.resolve(strict=True), args.output_dir.resolve())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

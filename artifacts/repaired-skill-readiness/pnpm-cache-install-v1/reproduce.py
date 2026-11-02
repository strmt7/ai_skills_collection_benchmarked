"""Exercise pnpm 12 store restoration in an independent offline fixture."""

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
OVERLAY = ROOT / "included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/pnpm-cache-install"
SOURCE_SHA256 = "6df9f7fb7b7034bbd8e66ecd2ae7342028a47a5d25136f8592b6c7e611b69add"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_package(path: Path, nonce: str = "control") -> None:
    files = {
        "package/package.json": json.dumps({"name": "fixture-package", "version": "1.0.0", "nonce": nonce}).encode(),
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


def exercise(node: Path, pnpm: Path, output: Path) -> dict[str, Any]:
    source = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    if sha(source) != SOURCE_SHA256 or b"pnpm store path" not in source:
        raise ValueError("The source action changed; review the baseline")
    if b"if: steps.cache.outputs.cache-hit != 'true'" not in source:
        raise ValueError("The source cache-hit condition changed")
    output.mkdir(parents=True, exist_ok=False)
    logs: dict[str, dict[str, object]] = {}
    with tempfile.TemporaryDirectory(prefix="pnpm-cache-control-") as temp:
        root = Path(temp)
        env = os.environ.copy()
        env.update(
            {
                "XDG_CONFIG_HOME": str(root / "config"),
                "XDG_CACHE_HOME": str(root / "cache"),
                "XDG_DATA_HOME": str(root / "data"),
                "PNPM_HOME": str(root / "pnpm-home"),
                "PNPM_CONFIG_CACHE_DIR": str(root / "metadata-cache"),
                "CI": "true",
            }
        )

        def run(name: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
            result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, timeout=90, check=False)
            for suffix, data in (("stdout", result.stdout), ("stderr", result.stderr)):
                (output / f"{name}.{suffix}").write_bytes(data)
            logs[name] = {
                "exit_code": result.returncode,
                "stdout_sha256": sha(result.stdout),
                "stderr_sha256": sha(result.stderr),
            }
            return result

        version = run("pnpm-version", [str(pnpm), "--version"], root)
        if version.returncode or version.stdout.strip() != b"12.16.1":
            raise ValueError("This control requires pnpm 12.16.1")
        node_version = run("node-version", [str(node), "--version"], root)
        if node_version.returncode:
            raise ValueError("Could not determine Node version")
        seed = root / "seed"
        seed.mkdir()
        manifest = {
            "name": "pnpm-control",
            "version": "1.0.0",
            "private": True,
            "dependencies": {"fixture-package": "file:./fixture.tgz"},
        }
        (seed / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
        make_package(seed / "fixture.tgz")
        seed_store = root / "seed-store"
        location = run("store-path", [str(pnpm), "store", "path", "--store-dir", str(seed_store)], seed)
        if location.returncode or not Path(os.fsdecode(location.stdout.strip())).resolve().is_relative_to(
            seed_store.resolve()
        ):
            raise ValueError("pnpm did not report a path inside the isolated store")
        install = [str(pnpm), "install", "--offline"]
        first = run("seed-install", install + ["--no-frozen-lockfile", "--store-dir", str(seed_store)], seed)
        if first.returncode or not (seed / "pnpm-lock.yaml").is_file():
            raise ValueError("Failed to seed the isolated store and lockfile")
        fresh = root / "fresh"
        fresh.mkdir()
        for name in ("package.json", "pnpm-lock.yaml", "fixture.tgz"):
            shutil.copyfile(seed / name, fresh / name)
        restored = root / "restored-store"
        shutil.copytree(seed_store, restored, symlinks=True)
        probe = [str(node), "-e", 'if(require("fixture-package")!=="fixture-ok") process.exit(2)']
        before = run("before-install", probe, fresh)
        if before.returncode == 0 or b"MODULE_NOT_FOUND" not in before.stderr:
            raise ValueError("The uninstalled project unexpectedly loaded its dependency")
        installed = run("frozen-install", install + ["--frozen-lockfile", "--store-dir", str(restored)], fresh)
        after = run("after-install", probe, fresh)
        if installed.returncode or after.returncode:
            raise ValueError("The immutable offline installation failed")
        no_archive = root / "no-archive"
        no_archive.mkdir()
        for name in ("package.json", "pnpm-lock.yaml"):
            shutil.copyfile(seed / name, no_archive / name)
        missing = run("missing-archive", install + ["--frozen-lockfile", "--store-dir", str(restored)], no_archive)
        if missing.returncode == 0 or b"ERR_PNPM_TARBALL_READ_LOCAL_TARBALL" not in missing.stderr:
            raise ValueError("A missing local tarball was unexpectedly accepted")
        no_lock = root / "no-lock"
        no_lock.mkdir()
        for name in ("package.json", "fixture.tgz"):
            shutil.copyfile(seed / name, no_lock / name)
        missing_lock = run("missing-lock", install + ["--frozen-lockfile", "--store-dir", str(restored)], no_lock)
        if missing_lock.returncode == 0 or b"ERR_PNPM_NO_LOCKFILE" not in missing_lock.stderr:
            raise ValueError("A missing lockfile was unexpectedly accepted")
        mismatch = root / "mismatch"
        mismatch.mkdir()
        for name in ("package.json", "pnpm-lock.yaml", "fixture.tgz"):
            shutil.copyfile(seed / name, mismatch / name)
        manifest["dependencies"] = {}
        (mismatch / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
        rejected = run("mismatched-lock", install + ["--frozen-lockfile", "--store-dir", str(restored)], mismatch)
        if rejected.returncode == 0 or b"ERR_PNPM_OUTDATED_LOCKFILE" not in rejected.stderr:
            raise ValueError("A mismatched lockfile was not rejected")
        result: dict[str, Any] = {
            "platform": platform.system(),
            "node_version": node_version.stdout.decode().strip(),
            "pnpm_version": version.stdout.decode().strip(),
            "pnpm_sha256": sha(pnpm.read_bytes()),
            "source_action_sha256": sha(source),
            "runner_sha256": sha(Path(__file__).read_bytes()),
            "overlay_sha256": sha((OVERLAY / "SKILL.md").read_bytes()),
            "example_sha256": sha((OVERLAY / "examples/pnpm-ci.yml").read_bytes()),
            "fixture_tarball_sha256": sha((seed / "fixture.tgz").read_bytes()),
            "pnpm_offline_mode": True,
            "github_cache_service_tested": False,
            "agent_performance_tested": False,
            "logs": logs,
        }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--pnpm", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    result = exercise(args.node.resolve(strict=True), args.pnpm.resolve(strict=True), args.output_dir.resolve())
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

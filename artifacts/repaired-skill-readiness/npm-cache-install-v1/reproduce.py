"""Reproduce an npm cache hit with an independent local package fixture."""

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
SOURCE = (
    ROOT
    / "included/skills/by-category/devops-cloud-operations/latest-release-devops/github-actions-generator"
    / "examples/actions/setup-node-cached/action.yml"
)
OVERLAY = ROOT / "included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/npm-cache-install"
SOURCE_SHA256 = "6df9f7fb7b7034bbd8e66ecd2ae7342028a47a5d25136f8592b6c7e611b69add"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package(path: Path, name: str = "fixture-pkg") -> None:
    contents = {
        "package/package.json": json.dumps({"name": name, "version": "1.0.0", "main": "index.js"}).encode(),
        "package/index.js": b'module.exports = "cache-fixture-ok";\n',
    }
    with (
        path.open("wb") as stream,
        gzip.GzipFile(filename="", mode="wb", fileobj=stream, mtime=0) as compressed,
        tarfile.open(fileobj=compressed, mode="w") as archive,
    ):
        for name, data in contents.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            member.mtime = 0
            archive.addfile(member, io.BytesIO(data))


def exercise(node: Path, npm: list[str], output: Path) -> dict[str, Any]:
    source = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    if sha(source) != SOURCE_SHA256 or b"if: steps.cache.outputs.cache-hit != 'true'" not in source:
        raise ValueError("The source cache-hit condition changed; review the baseline")
    if b"npm config get cache" not in source or b"npm ci" not in source:
        raise ValueError("The source npm cache or install command changed")
    example = (OVERLAY / "examples/npm-ci.yml").read_bytes()
    if b"      - run: npm ci\n" not in example:
        raise ValueError("The maintained workflow's npm install step changed")
    raw = output / "raw"
    raw.mkdir()
    logs: dict[str, dict[str, object]] = {}

    with tempfile.TemporaryDirectory(prefix="npm-cache-install-") as temporary:
        root = Path(temporary)
        env = os.environ.copy()
        env.update(
            {
                "PATH": str(node.parent) + os.pathsep + env.get("PATH", ""),
                "npm_config_userconfig": str(root / "user.npmrc"),
                "npm_config_globalconfig": str(root / "global.npmrc"),
                "npm_config_cache": str(root / "seed-cache"),
                "npm_config_audit": "false",
                "npm_config_fund": "false",
                "npm_config_update_notifier": "false",
                "npm_config_offline": "true",
            }
        )
        (root / "user.npmrc").write_text("", encoding="utf-8")
        (root / "global.npmrc").write_text("", encoding="utf-8")

        def run(name: str, command: list[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
            result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=90, check=False)
            for suffix, data in (("stdout", result.stdout), ("stderr", result.stderr)):
                (raw / f"{name}.{suffix}").write_bytes(data)
            logs[name] = {
                "exit_code": result.returncode,
                "stdout_sha256": sha(result.stdout),
                "stderr_sha256": sha(result.stderr),
            }
            return result

        node_version = run("node-version", [str(node), "--version"], root)
        npm_version = run("npm-version", [*npm, "--version"], root)
        if node_version.returncode or npm_version.returncode:
            raise ValueError("Node or npm could not be executed")
        seed = root / "seed"
        seed.mkdir()
        tarball = seed / "fixture.tgz"
        package(tarball)
        manifest = {
            "name": "cache-control",
            "version": "1.0.0",
            "private": True,
            "dependencies": {"fixture-pkg": "file:fixture.tgz"},
        }
        (seed / "package.json").write_text(json.dumps(manifest), encoding="utf-8")
        if run("lock", [*npm, "install", "--package-lock-only"], seed).returncode:
            raise ValueError("Could not generate the fixture lockfile")
        if run("seed-install", [*npm, "ci"], seed).returncode:
            raise ValueError("The original cache-miss install failed")
        listing = run("seed-cache-list", [*npm, "cache", "ls"], seed)
        if listing.returncode or b"pacote:tarball:file:fixture.tgz" not in listing.stdout:
            raise ValueError("The npm package cache did not contain the fixture tarball")
        clean = root / "clean"
        clean.mkdir()
        for name in ("package.json", "package-lock.json"):
            shutil.copyfile(seed / name, clean / name)
        shutil.copytree(root / "seed-cache", root / "restored-cache")
        env["npm_config_cache"] = str(root / "restored-cache")
        listing = run("restored-cache-list", [*npm, "cache", "ls"], clean)
        if (
            listing.returncode
            or b"pacote:tarball:file:fixture.tgz" not in listing.stdout
            or (clean / "node_modules").exists()
            or (clean / "fixture.tgz").exists()
        ):
            raise ValueError("The restored package cache or fresh workspace is invalid")
        check = [str(node), "-e", 'process.stdout.write(require("fixture-pkg"))']
        before = run("original-hit-load", check, clean)
        if before.returncode == 0 or b"MODULE_NOT_FOUND" not in before.stderr:
            raise ValueError("The simulated original cache-hit path did not reproduce the missing dependency")
        if run("maintained-install", [*npm, "ci"], clean).returncode:
            raise ValueError("The maintained npm ci command failed with a restored offline cache")
        after = run("maintained-load", check, clean)
        if after.returncode or after.stdout != b"cache-fixture-ok":
            raise ValueError("The dependency did not load after the maintained install")
        for name, mismatch in (("missing-lock", False), ("mismatched-lock", True)):
            case = root / name
            case.mkdir()
            data = json.loads((seed / "package.json").read_text(encoding="utf-8"))
            if mismatch:
                package(case / "other.tgz", "new-fixture")
                data["devDependencies"] = {"new-fixture": "file:other.tgz"}
                shutil.copyfile(seed / "package-lock.json", case / "package-lock.json")
            (case / "package.json").write_text(json.dumps(data), encoding="utf-8")
            failure = run(name, [*npm, "ci"], case)
            if failure.returncode == 0 or b"EUSAGE" not in failure.stderr:
                raise ValueError(f"{name}: expected npm ci to reject the lockfile")
        return {
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "node_version": node_version.stdout.decode().strip(),
            "npm_version": npm_version.stdout.decode().strip(),
            "source_action_sha256": sha(source),
            "overlay_sha256": sha((OVERLAY / "SKILL.md").read_bytes()),
            "example_sha256": sha(example),
            "fixture_tarball_sha256": sha(tarball.read_bytes()),
            "runner_sha256": sha(Path(__file__).read_bytes()),
            "restored_cache_contains_package": True,
            "fresh_workspace_had_node_modules": False,
            "original_cache_hit_missing_dependency": True,
            "maintained_offline_install_succeeded": True,
            "missing_and_mismatched_locks_rejected": True,
            "logs": logs,
            "scope": "Synthetic npm fixture and simulated cache-hit condition; no GitHub cache service or agent trial.",
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path, required=True)
    executables = parser.add_mutually_exclusive_group(required=True)
    executables.add_argument("--npm", type=Path)
    executables.add_argument("--npm-cli", type=Path, help="Run npm-cli.js with the selected Node executable")
    parser.add_argument("--output-dir", type=Path, required=True, help="New evidence directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    node = args.node.resolve(strict=True)
    npm = [str(node), str(args.npm_cli.resolve(strict=True))] if args.npm_cli else [str(args.npm.resolve(strict=True))]
    args.output_dir.mkdir(parents=True, exist_ok=False)
    result = exercise(node, npm, args.output_dir)
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

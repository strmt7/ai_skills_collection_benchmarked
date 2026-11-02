"""Prepare and probe a disposable npm project in GitHub Actions."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from reproduce import package


def prepare(workspace: Path, run_id: str, attempt: str) -> None:
    if not run_id.isdigit() or not attempt.isdigit():
        raise ValueError("Run ID and attempt must be numeric")
    files = [workspace / name for name in ("package.json", "package-lock.json", "fixture.tgz")]
    if any(path.exists() for path in files):
        raise ValueError("The disposable workspace already contains a fixture path")
    package(files[2])
    project = {
        "name": f"npm-cache-control-{run_id}-{attempt}",
        "version": "1.0.0",
        "private": True,
        "dependencies": {"fixture-pkg": "file:fixture.tgz"},
    }
    files[0].write_text(json.dumps(project), encoding="utf-8")
    subprocess.run(["npm", "install", "--package-lock-only"], cwd=workspace, check=True, timeout=90)


def probe(workspace: Path, output: Path, cache_hit: str, mode: str) -> None:
    if cache_hit != "true":
        raise ValueError(f"{mode}: expected an exact GitHub Actions cache hit")
    if (workspace / "node_modules").exists():
        raise ValueError(f"{mode}: the clean workspace unexpectedly contains node_modules")
    output.mkdir(parents=True, exist_ok=False)
    observations = {}

    def run(name: str, command: list[str]) -> subprocess.CompletedProcess[bytes]:
        result = subprocess.run(command, cwd=workspace, capture_output=True, timeout=90, check=False)
        for suffix, data in (("stdout", result.stdout), ("stderr", result.stderr)):
            (output / f"{name}.{suffix}").write_bytes(data)
        observations[name] = {
            "exit_code": result.returncode,
            "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
        }
        return result

    cached = run("cache-list", ["npm", "cache", "ls"])
    if cached.returncode or b"pacote:tarball:file:fixture.tgz" not in cached.stdout:
        raise ValueError(f"{mode}: restored npm cache does not contain the fixture")
    check = ["node", "-e", 'process.stdout.write(require("fixture-pkg"))']
    before = run("before-install", check)
    if before.returncode == 0 or b"MODULE_NOT_FOUND" not in before.stderr:
        raise ValueError(f"{mode}: the clean workspace did not exhibit the missing dependency")
    (workspace / "fixture.tgz").unlink()
    install = run("npm-ci", ["npm", "ci"])
    if install.returncode:
        raise ValueError(f"{mode}: offline npm ci failed after cache restoration")
    after = run("after-install", check)
    if after.returncode or after.stdout != b"cache-fixture-ok":
        raise ValueError(f"{mode}: the dependency did not load after npm ci")
    result = {"mode": mode, "cache_hit": cache_hit, "observations": observations}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    seed = commands.add_parser("prepare")
    seed.add_argument("--workspace", type=Path, required=True)
    seed.add_argument("--run-id", required=True)
    seed.add_argument("--attempt", required=True)
    check = commands.add_parser("probe")
    check.add_argument("--workspace", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    check.add_argument("--cache-hit", required=True)
    check.add_argument("--mode", choices=("source", "maintained"), required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "prepare":
        prepare(args.workspace, args.run_id, args.attempt)
    else:
        probe(args.workspace, args.output, args.cache_hit, args.mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

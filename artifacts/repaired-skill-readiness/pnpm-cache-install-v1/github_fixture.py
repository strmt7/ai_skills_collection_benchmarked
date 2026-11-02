"""Prepare and inspect an isolated GitHub Actions pnpm cache fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from reproduce import make_package


def prepare(workspace: Path, run_id: str, attempt: str) -> None:
    if not re.fullmatch(r"[0-9]+", run_id) or not re.fullmatch(r"[0-9]+", attempt):
        raise ValueError("Run ID and attempt must be decimal numbers")
    names = ("package.json", "pnpm-lock.yaml", "fixture.tgz", "node_modules")
    if any((workspace / name).exists() for name in names):
        raise ValueError("The workspace already contains a fixture path")
    make_package(workspace / "fixture.tgz", f"{run_id}-{attempt}")
    manifest = {
        "name": "pnpm-control",
        "version": "1.0.0",
        "private": True,
        "dependencies": {"fixture-package": "file:./fixture.tgz"},
    }
    (workspace / "package.json").write_text(json.dumps(manifest) + "\n", encoding="utf-8", newline="\n")


def probe(workspace: Path, output: Path, cache_hit: str, mode: str) -> None:
    if cache_hit != "true":
        raise ValueError("Expected an exact GitHub Actions cache hit")
    node = shutil.which("node")
    pnpm = shutil.which("pnpm")
    if not node or not pnpm:
        raise ValueError("pnpm and Node must be available on PATH")
    output.mkdir(parents=True, exist_ok=False)
    logs: dict[str, dict[str, object]] = {}

    def run(name: str, command: list[str]) -> subprocess.CompletedProcess[bytes]:
        result = subprocess.run(command, cwd=workspace, capture_output=True, timeout=120, check=False)
        for suffix, data in (("stdout", result.stdout), ("stderr", result.stderr)):
            (output / f"{name}.{suffix}").write_bytes(data)
        logs[name] = {
            "exit_code": result.returncode,
            "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr).hexdigest(),
        }
        return result

    command = [node, "-e", 'if(require("fixture-package")!=="fixture-ok") process.exit(2)']
    first = run("initial-load", command)
    if mode == "source":
        if first.returncode == 0 or b"MODULE_NOT_FOUND" not in first.stderr:
            raise ValueError("Simulated source cache-hit path unexpectedly installed the dependency")
        installed = run("install", [pnpm, "install", "--offline", "--frozen-lockfile"])
        if installed.returncode or run("after-install", command).returncode:
            raise ValueError("The locked installation did not load the fixture")
    elif first.returncode:
        raise ValueError("The maintained setup action did not install the fixture")
    (output / "result.json").write_text(
        json.dumps({"mode": mode, "cache_hit": cache_hit, "logs": logs}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    create = sub.add_parser("prepare")
    create.add_argument("--workspace", type=Path, required=True)
    create.add_argument("--run-id", required=True)
    create.add_argument("--attempt", required=True)
    check = sub.add_parser("probe")
    check.add_argument("--workspace", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    check.add_argument("--cache-hit", required=True)
    check.add_argument("--mode", choices=("source", "maintained"), required=True)
    args = parser.parse_args(argv)
    if args.operation == "prepare":
        prepare(args.workspace.resolve(strict=True), args.run_id, args.attempt)
    else:
        probe(args.workspace.resolve(strict=True), args.output.resolve(), args.cache_hit, args.mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

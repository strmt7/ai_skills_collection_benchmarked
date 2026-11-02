"""Measure selected Bun CLI and shell examples without project dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import TypedDict


class Observation(TypedDict):
    exit_code: int
    stdout: str
    stderr: str


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bun", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bun = args.bun.resolve(strict=True)
    workspace = args.workspace.resolve()
    output = args.output.resolve()
    if workspace.exists() or output.exists():
        raise ValueError("Workspace and output must be new paths")
    if not output.parent.is_dir() or output.is_relative_to(workspace):
        raise ValueError("Output parent must exist outside the workspace")
    workspace.mkdir(parents=True)
    (workspace / "package.json").write_text(
        json.dumps({"private": True, "scripts": {"dev": "bun run probe.ts"}}) + "\n", encoding="utf-8"
    )
    (workspace / ".env").write_text("REVIEW_SAMPLE=default-file\n", encoding="utf-8")
    (workspace / ".explicit").write_text("REVIEW_SAMPLE=explicit-file\n", encoding="utf-8")
    (workspace / "probe.ts").write_text(
        "console.log(JSON.stringify({sample: process.env.REVIEW_SAMPLE ?? null, runtime: process.versions.bun ?? null}))\n",
        encoding="utf-8",
    )
    (workspace / "probe.test.ts").write_text(
        'import { test, expect } from "bun:test"; test("arithmetic", () => expect(1 + 2).toBe(3));\n', encoding="utf-8"
    )
    env = os.environ.copy()
    env.pop("REVIEW_SAMPLE", None)
    env["PATH"] = str(bun.parent) + os.pathsep + env.get("PATH", "")
    cases = {
        "version": [str(bun), "--version"],
        "explicit_after_run": [str(bun), "run", "--env-file=.explicit", "dev"],
        "default_env": [str(bun), "run", "dev"],
        "bun_test": [str(bun), "test"],
    }
    if os.name == "nt":
        shell = shutil.which("powershell.exe")
        if shell is None:
            raise RuntimeError("Windows PowerShell not found")
        cases["shell_inline"] = [
            shell,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "REVIEW_SAMPLE=inline bun run probe.ts",
        ]
        cases["shell_native"] = [
            shell,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$env:REVIEW_SAMPLE='inline'; bun run probe.ts",
        ]
    else:
        cases["shell_inline"] = ["/bin/sh", "-c", "REVIEW_SAMPLE=inline bun run probe.ts"]
    observations: dict[str, Observation] = {}
    for name, cmd in cases.items():
        p = subprocess.run(
            cmd,
            cwd=workspace,
            env=env,
            text=True,
            encoding="utf-8-sig",
            errors="replace",
            capture_output=True,
            timeout=30,
        )
        observations[name] = {"exit_code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}

    def sample(name: str) -> str | None:
        try:
            return json.loads(observations[name]["stdout"])["sample"]
        except (KeyError, json.JSONDecodeError, TypeError):
            return None

    checks = {
        "version": observations["version"]["exit_code"] == 0 and observations["version"]["stdout"].strip() == "1.4.4",
        "explicit_file": observations["explicit_after_run"]["exit_code"] == 0
        and sample("explicit_after_run") == "explicit-file",
        "default_file": observations["default_env"]["exit_code"] == 0 and sample("default_env") == "default-file",
        "bun_test": observations["bun_test"]["exit_code"] == 0 and "1 pass" in observations["bun_test"]["stderr"],
        "shell_behavior_matches_platform": (
            observations["shell_inline"]["exit_code"] != 0
            if os.name == "nt"
            else observations["shell_inline"]["exit_code"] == 0 and sample("shell_inline") == "inline"
        ),
    }
    if os.name == "nt":
        checks["powershell_native"] = (
            observations["shell_native"]["exit_code"] == 0 and sample("shell_native") == "inline"
        )
    with bun.open("rb") as binary:
        binary_sha256 = hashlib.file_digest(binary, "sha256").hexdigest()
    result = {
        "schema_version": 1,
        "platform": platform.system(),
        "architecture": platform.machine(),
        "binary_sha256": binary_sha256,
        "cases": observations,
        "checks": checks,
        "agent_efficacy_scored": False,
        "limitations": [
            "Selected CLI examples and shell syntax only; no deployment, package compatibility, performance, security or agent efficacy claim."
        ],
    }
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(json.dumps({"output": str(output), "checks": checks}, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

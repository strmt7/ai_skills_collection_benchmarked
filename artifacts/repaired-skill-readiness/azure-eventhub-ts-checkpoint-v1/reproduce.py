"""Compile and exercise the checkpoint callbacks without contacting Azure."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ORIGINAL = ROOT / (
    "included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-ts/SKILL.md"
)
EXAMPLE = ROOT / (
    "included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/"
    "azure-eventhub-ts-checkpoint/examples/checkpoint-consumer.ts"
)
ORIGINAL_SHA256 = "bd9b7a5bb69f8b558611f749624c9751c2d0549f97eb513714d548e9e48963e2"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", type=Path, required=True)
    parser.add_argument("--npm-cli", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    node = args.node.resolve(strict=True)
    npm = args.npm_cli.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    if digest(ORIGINAL.read_bytes()) != ORIGINAL_SHA256:
        raise ValueError("Pinned original skill bytes differ")

    results = []
    with tempfile.TemporaryDirectory(prefix="eventhub-ts-checkpoint-") as temporary:
        work = Path(temporary)
        for name in ("package.json", "package-lock.json", "tsconfig.json", "control.test.ts"):
            shutil.copyfile(HERE / name, work / name)
        shutil.copyfile(EXAMPLE, work / "checkpoint-consumer.ts")
        env = dict(os.environ, ORIGINAL_SKILL=str(ORIGINAL))
        commands = [
            ("node-version", [str(node), "--version"]),
            ("npm-version", [str(node), str(npm), "--version"]),
            ("install", [str(node), str(npm), "ci", "--ignore-scripts", "--no-audit", "--no-fund"]),
            ("typecheck", [str(node), str(work / "node_modules/typescript/bin/tsc"), "--project", "tsconfig.json"]),
            ("callbacks", [str(node), "--test", "--test-reporter", "tap", str(work / "dist/control.test.js")]),
        ]
        for name, command in commands:
            result = subprocess.run(command, cwd=work, env=env, capture_output=True, timeout=300, check=False)
            (output / f"{name}.stdout").write_bytes(result.stdout)
            (output / f"{name}.stderr").write_bytes(result.stderr)
            results.append(
                {
                    "name": name,
                    "returncode": result.returncode,
                    "stdout_sha256": digest(result.stdout),
                    "stderr_sha256": digest(result.stderr),
                }
            )
            if result.returncode:
                break
        callbacks = output / "callbacks.stdout"
        passed = (
            len(results) == len(commands)
            and all(result["returncode"] == 0 for result in results)
            and b"# tests 5" in callbacks.read_bytes()
            and b"# pass 5" in callbacks.read_bytes()
            and b"# fail 0" in callbacks.read_bytes()
        )
    report = {
        "schema_version": 1,
        "status": "passed" if passed else "failed",
        "platform": platform.system(),
        "node_version": (output / "node-version.stdout").read_text(encoding="utf-8").strip(),
        "npm_version": (output / "npm-version.stdout").read_text(encoding="utf-8").strip()
        if (output / "npm-version.stdout").exists()
        else None,
        "original_sha256": ORIGINAL_SHA256,
        "example_sha256": digest(EXAMPLE.read_bytes()),
        "control_sha256": {
            name: digest((HERE / name).read_bytes())
            for name in ("package.json", "package-lock.json", "tsconfig.json", "control.test.ts", "reproduce.py")
        },
        "commands": results,
        "azure_service_called": False,
        "agent_performance_tested": False,
    }
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

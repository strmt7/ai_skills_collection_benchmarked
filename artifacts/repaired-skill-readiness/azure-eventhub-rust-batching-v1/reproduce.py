"""Compile the locked Rust Event Hubs example without running or contacting Azure."""

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
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
EXAMPLE = ROOT / (
    "included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/"
    "azure-eventhub-rust-batching/examples"
)
TOOLCHAIN = "1.99.1"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(rustup: Path, output: Path) -> dict[str, Any]:
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="eventhub-rust-") as temporary:
        workspace = Path(temporary)
        case = workspace / "example"
        (case / "src").mkdir(parents=True)
        for name in ("Cargo.toml", "Cargo.lock", "src/main.rs"):
            shutil.copyfile(EXAMPLE / name, case / name)
        env = dict(os.environ)
        env.update(
            CARGO_HOME=str(workspace / "cargo-home"),
            CARGO_TARGET_DIR=str(workspace / "target"),
            CARGO_TERM_COLOR="never",
        )
        versions = {}
        for tool in ("cargo", "rustc"):
            result = subprocess.run(
                [str(rustup), "run", TOOLCHAIN, tool, "--version"], cwd=case, env=env, capture_output=True, timeout=30
            )
            value = result.stdout.decode("utf-8").strip()
            if result.returncode or not value.startswith(f"{tool} {TOOLCHAIN} "):
                raise ValueError(f"Expected {tool} {TOOLCHAIN}; inspect the installed toolchain")
            versions[tool] = value
        result = subprocess.run(
            [str(rustup), "run", TOOLCHAIN, "cargo", "check", "--locked", "--all-targets"],
            cwd=case,
            env=env,
            capture_output=True,
            timeout=900,
        )
        (output / "check.stdout").write_bytes(result.stdout)
        (output / "check.stderr").write_bytes(result.stderr)
        if result.returncode:
            raise ValueError("Locked cargo check failed; inspect retained streams")
        report = {
            "schema_version": 1,
            "platform": platform.system(),
            "toolchain": versions,
            "check_exit_code": result.returncode,
            "source_sha256": sha((case / "src/main.rs").read_bytes()),
            "manifest_sha256": sha((case / "Cargo.toml").read_bytes()),
            "lock_sha256": sha((case / "Cargo.lock").read_bytes()),
            "stdout_sha256": sha(result.stdout),
            "stderr_sha256": sha(result.stderr),
            "azure_service_called": False,
            "agent_performance_tested": False,
        }
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rustup", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.rustup.is_absolute() or not args.rustup.is_file():
        raise ValueError("--rustup must be an absolute path to an existing executable")
    report = run(args.rustup.resolve(), args.output)
    print(json.dumps({"ok": True, "check_exit_code": report["check_exit_code"], "azure_service_called": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Run isolated JavaScript inventory controls with pinned frameworks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCRIPT = ROOT / (
    "included/repaired/skills/by-category/documents-spreadsheets-presentations/"
    "reddit-verified-gtm-registry/docs-from-code-js-inventory/scripts/inventory.mjs"
)
NAMES = (
    "identifies Next route exports, JS and TypeScript; excludes unrelated cache",
    "Next conventions preserve patterns and disclose unresolved cases",
    "tracks Express direct and mounted routers without treating arbitrary get as a route",
    "CommonJS and reassignment are handled conservatively",
    "malformed input fails atomically without executing target source",
    "controlled Next.js 16 route handlers agree with filesystem candidates",
    "Next fixture exits with failure after a controlled framework error",
    "controlled Express 5 requests agree with direct and mounted route candidates",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    inputs = [
        SCRIPT,
        SCRIPT.parent / "package.json",
        SCRIPT.parent / "package-lock.json",
        HERE / "inventory.test.mjs",
        HERE / "next-live.mjs",
        HERE / "package.json",
        HERE / "package-lock.json",
        HERE / "reproduce.py",
    ]
    before = {p.relative_to(ROOT).as_posix(): digest(p) for p in inputs}
    node = shutil.which("node")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not node or not npm:
        raise RuntimeError("Node.js and npm are required")
    node_version = subprocess.check_output([node, "--version"], text=True).strip()
    npm_version = subprocess.check_output([npm, "--version"], text=True).strip()
    with tempfile.TemporaryDirectory(prefix="docs-js-inventory-") as tmp:
        temporary = Path(tmp)
        shutil.copyfile(SCRIPT, temporary / "inventory.mjs")
        for name in ("inventory.test.mjs", "next-live.mjs", "package.json", "package-lock.json"):
            shutil.copyfile(HERE / name, temporary / name)
        environment = dict(os.environ, NEXT_TELEMETRY_DISABLED="1")
        install = subprocess.run(
            [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
            cwd=temporary,
            env=environment,
            capture_output=True,
            timeout=240,
            check=False,
        )
        (output / "install.stdout").write_bytes(install.stdout)
        (output / "install.stderr").write_bytes(install.stderr)
        if install.returncode:
            raise RuntimeError(f"npm ci failed with status {install.returncode}; see retained logs")
        process = subprocess.run(
            [node, "--test", "--test-reporter=tap", "inventory.test.mjs"],
            cwd=temporary,
            env=environment,
            capture_output=True,
            timeout=180,
            check=False,
        )
        (output / "test.tap").write_bytes(process.stdout)
        (output / "test.stderr").write_bytes(process.stderr)
        runtime = temporary / "runtime"
        runtime.mkdir()
        for name in ("inventory.mjs", "package.json", "package-lock.json"):
            shutil.copyfile(SCRIPT.parent / name, runtime / name)
        runtime_install = subprocess.run(
            [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"],
            cwd=runtime,
            env=environment,
            capture_output=True,
            timeout=240,
            check=False,
        )
        (output / "runtime-install.stdout").write_bytes(runtime_install.stdout)
        (output / "runtime-install.stderr").write_bytes(runtime_install.stderr)
        if runtime_install.returncode:
            raise RuntimeError("Runtime dependency installation failed; see retained logs")
        fixture = temporary / "project"
        fixture.mkdir()
        (fixture / "index.js").write_text(
            "import express from 'express'; const app = express(); "
            "app.get('/health', handler); throw new Error('must not execute');\n",
            encoding="utf-8",
        )
        runtime_result = temporary / "runtime-result.json"
        runtime_run = subprocess.run(
            [node, str(runtime / "inventory.mjs"), str(fixture), str(runtime_result)],
            cwd=temporary,
            env=environment,
            capture_output=True,
            timeout=30,
            check=False,
        )
        (output / "runtime.stdout").write_bytes(runtime_run.stdout)
        (output / "runtime.stderr").write_bytes(runtime_run.stderr)
        runtime_data = json.loads(runtime_result.read_text(encoding="utf-8")) if runtime_result.is_file() else {}
        runtime_ok = runtime_run.returncode == 0 and [r["path"] for r in runtime_data.get("routes", [])] == ["/health"]
    tap = process.stdout.decode("utf-8", errors="strict")
    passed = re.findall(r"^ok \d+ - (.+)$", tap, flags=re.MULTILINE)
    unchanged = before == {p.relative_to(ROOT).as_posix(): digest(p) for p in inputs}
    success = process.returncode == 0 and passed == list(NAMES) and "# fail 0" in tap and unchanged and runtime_ok
    result = {
        "schema_version": 1,
        "status": "passed" if success else "failed",
        "platform": platform.system(),
        "node": node_version,
        "npm": npm_version,
        "case_names": passed,
        "cases": len(passed),
        "test_exit_code": process.returncode,
        "minimal_runtime_install_and_cli_passed": runtime_ok,
        "inputs_sha256": before,
        "target_project_imported_by_inventory": False,
        "owned_express_and_next_fixtures_executed": True,
        "agent_performance_tested": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())

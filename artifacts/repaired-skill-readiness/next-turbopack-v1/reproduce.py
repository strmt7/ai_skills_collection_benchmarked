"""Reproduce the locked Next.js bundler and analyzer controls."""

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
FIXTURE = HERE / "fixture"
SNAPSHOT = "qualification"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def qualify(output: Path) -> dict[str, object]:
    node = shutil.which("node")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if node is None or npm is None:
        raise ValueError("The qualified Node.js and npm tools must be on PATH")
    output.mkdir(parents=True, exist_ok=False)
    sources = [Path(__file__), *(path for path in sorted(FIXTURE.rglob("*")) if path.is_file())]
    source_hashes = {path.relative_to(HERE).as_posix(): digest(path) for path in sources}
    with tempfile.TemporaryDirectory(prefix="next-controls-") as temporary:
        work = Path(temporary)
        for name in ("package.json", "package-lock.json"):
            shutil.copyfile(FIXTURE / name, work / name)
        (work / "user.npmrc").touch()
        (work / "global.npmrc").touch()
        environment = {
            key: value
            for key, value in os.environ.items()
            if not key.lower().startswith("npm_config_") and key.upper() not in {"NODE_OPTIONS", "NODE_PATH"}
        }
        environment.update(
            CI="true",
            NEXT_TELEMETRY_DISABLED="1",
            npm_config_userconfig=str(work / "user.npmrc"),
            npm_config_globalconfig=str(work / "global.npmrc"),
            npm_config_cache=str(work / "npm-cache"),
            npm_config_registry="https://registry.npmjs.org/",
        )

        def run(label: str, command: list[str], cwd: Path = work, *, expected_exit: int = 0, timeout: int = 180) -> str:
            stdout = output / f"{label}.stdout"
            stderr = output / f"{label}.stderr"
            with stdout.open("xb") as out, stderr.open("xb") as err:
                child = subprocess.run(
                    command, cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
                    stdout=out, stderr=err, timeout=timeout, check=False,
                )
            if child.returncode != expected_exit:
                raise ValueError(f"{label} exited {child.returncode}, expected {expected_exit}. See {stderr.name}.")
            if stdout.stat().st_size > 8 * 1024 * 1024:
                raise ValueError(f"{label} exceeded the expected output size")
            return stdout.read_text(encoding="utf-8")

        node_version = run("node-version", [node, "--version"]).strip()
        npm_version = run("npm-version", [npm, "--version"]).strip()
        run("install", [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"])
        cli = [node, str(work / "node_modules/next/dist/bin/next")]
        next_version = run("next-version", [*cli, "--version"]).strip()
        locked_version = json.loads((work / "package-lock.json").read_bytes())["packages"]["node_modules/next"]["version"]
        if next_version != f"Next.js v{locked_version}":
            raise ValueError("The installed Next.js CLI does not match the fixture lock")
        invalid = run("unsupported", [*cli, "dev", "--no-turbopack"], expected_exit=1, timeout=10)
        message = invalid + (output / "unsupported.stderr").read_text(encoding="utf-8")
        if "unknown option" not in message or "--no-turbopack" not in message:
            raise ValueError("The unsupported flag did not produce the expected CLI error")

        for label, bundler, flags in (("turbo", "Turbopack", []), ("webpack", "webpack", ["--webpack"])):
            app = work / label
            shutil.copytree(FIXTURE / "project", app)
            build = run(label, [*cli, "build", *flags], cwd=app)
            html = (app / ".next/server/app/index.html").read_text(encoding="utf-8")
            if bundler not in build or "<main>control ready</main>" not in html:
                raise ValueError(f"{label} did not identify its bundler and build the expected page")

        app = work / "analyzer"
        shutil.copytree(FIXTURE / "project", app)
        run("analyze", [*cli, "analyze", "--output", "--snapshot", SNAPSHOT], cwd=app)
        exported = run("export", [*cli, "analyze", "export", "--snapshot", SNAPSHOT], cwd=app)
        records = [json.loads(line) for line in exported.splitlines() if line.strip()]
        if not records or any(not isinstance(record, dict) for record in records):
            raise ValueError("The analyzer did not export a JSON Lines object stream")
        metadata, *rows = records
        routes = {record.get("route") for record in rows if record.get("type") == "route"}
        if (
            metadata.get("type") != "meta"
            or metadata.get("snapshot_name") != SNAPSHOT
            or metadata.get("selected_routes") != len(routes)
            or "/" not in routes
        ):
            raise ValueError("The analyzer export did not identify the fresh snapshot and expected route")
        result: dict[str, object] = {
            "schema_version": 1,
            "platform": platform.system(),
            "node": node_version,
            "npm": npm_version,
            "next": next_version,
            "unsupported_exit": 1,
            "turbo_exit": 0,
            "webpack_exit": 0,
            "analyze_exit": 0,
            "expected_html": True,
            "root_in_analyzer": True,
            "export_records": len(records),
            "export_sha256": digest(output / "export.stdout"),
            "package_lock_sha256": source_hashes["fixture/package-lock.json"],
            "inputs_sha256": source_hashes,
            "agent_efficacy_scored": False,
        }
    if any(digest(path) != source_hashes[path.relative_to(HERE).as_posix()] for path in sources):
        raise ValueError("Fixture or driver changed during qualification")
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory for native logs and the result")
    arguments = parser.parse_args(argv)
    result = qualify(arguments.output.resolve())
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

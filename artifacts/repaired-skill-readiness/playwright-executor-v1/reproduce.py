from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def normalized(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(node: Path, original: Path, candidate: Path, browsers: Path, scratch: Path, output: Path) -> dict[str, Any]:
    old = normalized(original / "run.js")
    new = normalized(candidate / "run.js")
    old_line = b"env: { ...process.env, NODE_PATH: nodeModules, PW_SKILL_DIR: skillDir },"
    new_line = (
        b"env: {\n      ...process.env,\n"
        b"      NODE_PATH: [nodeModules, process.env.NODE_PATH].filter(Boolean).join(path.delimiter),\n"
        b"      PW_SKILL_DIR: skillDir,\n    },"
    )
    if old.count(old_line) != 1 or old.replace(old_line, new_line) != new:
        raise ValueError("The executors differ beyond the selected NODE_PATH repair")
    if digest(old) != "f2afe1a17379548abee60e91c9cee9a3907ff5ae9a2423d9190e45ace761399d":
        raise ValueError("Original executor is not the pinned source")
    for name in ("package.json", "package-lock.json"):
        if normalized(original / name) != normalized(candidate / name):
            raise ValueError(f"Both installations must have the same {name}")
    versions = []
    for install in (original, candidate):
        versions.append(
            json.loads((install / "node_modules/playwright/package.json").read_text(encoding="utf-8"))["version"]
        )
    if versions != ["1.64.1", "1.64.1"]:
        raise ValueError("Both executors must use the same Playwright 1.64.1")
    scratch.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=False)
    fixture = Path(tempfile.mkdtemp(prefix="node-path-", dir=scratch))
    module = fixture / "external-modules/fixture-helper"
    module.mkdir(parents=True)
    (module / "index.js").write_text("module.exports = 'fixture-ok';\n", encoding="utf-8")
    script = fixture / "probe.cjs"
    script.write_text("console.log(require('fixture-helper'));\n", encoding="utf-8")
    env = os.environ.copy()
    empty_search = fixture / "empty-search"
    empty_search.mkdir()
    env["NODE_PATH"] = os.pathsep.join((str(empty_search), str(module.parent)))
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers)
    env.pop("PW_SCRIPT_DIR", None)

    def execute(label: str, args: list[str], variables: dict[str, str]) -> dict[str, Any]:
        completed = subprocess.run(
            [str(node), *args],
            cwd=fixture,
            env=variables,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        (output / f"{label}.stdout.txt").write_text(completed.stdout, encoding="utf-8", newline="\n")
        (output / f"{label}.stderr.txt").write_text(completed.stderr, encoding="utf-8", newline="\n")
        return {
            "exit": completed.returncode,
            "fixture_ok": completed.stdout.strip() == "fixture-ok",
            "missing_fixture": "Cannot find module 'fixture-helper'" in completed.stderr,
        }

    direct = execute("direct", [str(script)], env)
    prior = execute("original", [str(original / "run.js"), str(script)], env)
    repaired = execute("repaired", [str(candidate / "run.js"), str(script)], env)
    inline = execute("inline", [str(candidate / "run.js"), "-e", "console.log(require('fixture-helper'))"], env)
    clean_env = env.copy()
    clean_env.pop("NODE_PATH", None)
    playwright_script = fixture / "playwright-check.cjs"
    playwright_script.write_text("console.log(require('playwright/package.json').version);\n", encoding="utf-8")
    no_path = subprocess.run(
        [str(node), str(candidate / "run.js"), str(playwright_script)],
        cwd=fixture,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    browser_code = "const b = await chromium.launch({headless:true}); try { const p = await b.newPage(); await p.setContent('<title>control</title><main>ready</main>'); console.log(await p.title(), await p.locator('main').innerText()); } finally { await b.close(); }"
    browser = subprocess.run(
        [str(node), str(candidate / "run.js"), "-e", browser_code],
        cwd=fixture,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    (output / "browser.stdout.txt").write_text(browser.stdout, encoding="utf-8", newline="\n")
    (output / "browser.stderr.txt").write_text(browser.stderr, encoding="utf-8", newline="\n")
    version = subprocess.run(
        [str(node), "--version"], capture_output=True, text=True, timeout=20, check=True
    ).stdout.strip()
    result = {
        "node": version,
        "platform": os.name,
        "playwright": versions[0],
        "original_sha256": digest(old),
        "repaired_sha256": digest(new),
        "package_lock_sha256": digest(normalized(candidate / "package-lock.json")),
        "cases": {"direct": direct, "original": prior, "repaired": repaired, "inline": inline},
        "playwright_without_node_path": {"exit": no_path.returncode, "version": no_path.stdout.strip()},
        "browser_smoke": {"exit": browser.returncode, "result": browser.stdout.strip()},
        "agent_efficacy_scored": False,
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    if not (
        direct["exit"] == 0
        and direct["fixture_ok"]
        and prior["exit"] != 0
        and prior["missing_fixture"]
        and repaired["exit"] == 0
        and repaired["fixture_ok"]
        and inline["exit"] == 0
        and inline["fixture_ok"]
        and no_path.returncode == 0
        and no_path.stdout.strip() == "1.64.1"
        and browser.returncode == 0
        and browser.stdout.strip() == "control ready"
    ):
        raise ValueError("Observed executor behavior differs from the recorded control")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test a pinned Playwright executor with and without the NODE_PATH repair."
    )
    for name in ("node", "original", "candidate", "browsers", "scratch", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                run(
                    *(
                        getattr(args, name).resolve()
                        for name in ("node", "original", "candidate", "browsers", "scratch", "output")
                    )
                ),
                indent=2,
            )
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Set up and run the isolated, source-admitted Windows research crawler.

This product includes software developed by UncleCode (https://x.com/unclecode)
as part of the Crawl4AI project (https://github.com/unclecode/crawl4ai).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import urllib.request
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import prepare_crawl4ai_source as source
import verify_crawl4ai_wheel as wheel
from _catalog_publication import checked_path
from _windows_owned_python import run_python

ROOT = Path(__file__).resolve().parents[1]
INPUTS = "toolchains/crawl4ai"
EXECUTE = "import subprocess,sys; raise SystemExit(subprocess.call(sys.argv[1:],stdin=subprocess.DEVNULL))"
SCRIPT = """import runpy,sys
from pathlib import Path
script=Path(sys.argv[1]).resolve()
sys.path.insert(0,str(script.parent))
sys.argv=sys.argv[1:]
runpy.run_path(str(script),run_name='__main__')
"""
BROWSER_PROBE = """import hashlib,importlib.metadata,json,sys
from pathlib import Path
from patchright.sync_api import sync_playwright
home=Path(sys.argv[1]).resolve()
with sync_playwright() as provider:
    executable=Path(provider.chromium.executable_path).resolve()
    if not executable.is_file() or not executable.is_relative_to(home/'browsers'):
        raise ValueError('Installed browser is missing or outside the owned provider home')
    raw=executable.read_bytes()
    print(json.dumps({'relative_executable':executable.relative_to(home).as_posix(),
                      'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),
                      'patchright_version':importlib.metadata.version('patchright')}))
"""


def script_command(interpreter: Path, name: str, *arguments: str | Path) -> list[str | Path]:
    return [interpreter, "-I", "-B", "-c", SCRIPT, ROOT / "tools" / name, *arguments]


def identity(root: Path) -> str:
    names = [
        INPUTS + "/source.json",
        INPUTS + "/requirements.txt",
        INPUTS + "/requirements-build.txt",
        INPUTS + "/requirements-bootstrap.txt",
    ]
    records = {name: hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in names}
    return hashlib.sha256(json.dumps(records, sort_keys=True).encode()).hexdigest()


def home_path(root: Path, selected: Path | None) -> Path:
    target = selected or root / ".venv/agent-tools" / ("crawl4ai-" + identity(root)[:16])
    target = target.absolute()
    if target == root / ".venv" or not target.is_relative_to(root / ".venv"):
        raise ValueError("Provider home must be a dedicated directory under this checkout's .venv")
    return checked_path(root, target.relative_to(root).as_posix())


def require_interpreter() -> None:
    if (
        sys.platform != "win32"
        or platform.machine().upper() not in {"AMD64", "X86_64"}
        or sys.implementation.name != "cpython"
        or sys.version_info[:3] != (3, 13, 17)
    ):
        raise ValueError("Run this Windows x64 provider launcher with CPython 3.13.17 (for example, py -3.13)")


def environment(home: Path) -> dict[str, str]:
    allowed = {"SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT"}
    child = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    for key, relative in {
        "HOME": "profile",
        "USERPROFILE": "profile",
        "APPDATA": "profile/AppData/Roaming",
        "LOCALAPPDATA": "profile/AppData/Local",
        "TEMP": "temporary",
        "TMP": "temporary",
        "NLTK_DATA": "nltk",
        "CRAWL4AI_BASE_DIRECTORY": "runtime-data",
        "CRAWL4_AI_BASE_DIRECTORY": "setup-data",
        "PLAYWRIGHT_BROWSERS_PATH": "browsers",
        "PIP_CACHE_DIR": "pip-cache",
    }.items():
        path = checked_path(home, relative)
        path.mkdir(parents=True, exist_ok=True)
        child[key] = str(path)
    child.update(
        PYTHONUTF8="1",
        PYTHONNOUSERSITE="1",
        PYTHONHASHSEED="0",
        PIP_CONFIG_FILE="nul",
        PIP_DISABLE_PIP_VERSION_CHECK="1",
        PIP_NO_INPUT="1",
        DO_NOT_TRACK="1",
        LITELLM_TELEMETRY="False",
        HF_HUB_DISABLE_TELEMETRY="1",
        TOKENIZERS_PARALLELISM="false",
        CRAWL4AI_CHROMIUM_SANDBOX="true",
    )
    return child


def phase(home: Path, name: str, arguments: list[str | Path], *, timeout: int = 600) -> dict[str, Any]:
    directory = checked_path(home, "logs/" + name + "-" + uuid.uuid4().hex)
    directory.mkdir(parents=True)
    env = environment(home)
    env["SOURCE_DATE_EPOCH"] = str(json.loads((ROOT / INPUTS / "source.json").read_bytes())["source_date_epoch"])
    with (directory / "stdout.log").open("xb") as stdout, (directory / "stderr.log").open("xb") as stderr:
        status, receipt = run_python(
            sys.executable,
            EXECUTE,
            [str(value) for value in arguments],
            cwd=ROOT,
            environment=env,
            stdout=stdout,
            stderr=stderr,
            timeout=timeout,
            output_limit=16 * 1024 * 1024,
        )
    receipt.update(exit_code=status, phase=name)
    (directory / "process.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    if status != 0 or receipt["active_processes_after_cleanup"] != 0:
        raise ValueError(f"{name} failed (exit {status}); native diagnostics: {directory}")
    return {"phase": name, "logs": str(directory), **receipt}


def verify(home: Path) -> dict[str, Any]:
    receipt_path = checked_path(home, "installation.json")
    if not receipt_path.is_file():
        raise ValueError("Provider setup is incomplete; run setup with a new --home to preserve failed diagnostics")
    receipt = json.loads(receipt_path.read_bytes())
    if (
        not isinstance(receipt, dict)
        or type(receipt.get("schema_version")) is not int
        or receipt["schema_version"] != 1
    ):
        raise ValueError("Provider installation receipt has an invalid schema")
    name = receipt.get("wheel_name") if isinstance(receipt, dict) else None
    if (
        not isinstance(name, str)
        or Path(name).name != name
        or "/" in name
        or "\\" in name
        or ":" in name
        or not name.endswith(".whl")
    ):
        raise ValueError("Provider receipt must select a wheel filename within its dedicated home")
    if receipt.get("input_identity") != identity(ROOT):
        raise ValueError("Provider inputs changed; run setup with a new dedicated home")
    pin = json.loads((ROOT / INPUTS / "source.json").read_bytes())
    if (
        receipt.get("provider_version") != pin["version"]
        or receipt.get("wheel_sha256") != pin["qualified_wheel_sha256"]
        or receipt.get("python_version") != "3.13.17"
    ):
        raise ValueError("Provider installation receipt differs from admitted runtime inputs")
    runtime = checked_path(home, "runtime/Scripts/python.exe")
    candidate = checked_path(home, "wheel/" + name)
    wheel.prepare(ROOT, candidate, home / "admission", check=True)
    checks = [
        phase(home, "pip-check", [runtime, "-I", "-m", "pip", "check"]),
        phase(
            home,
            "installed-source",
            script_command(
                runtime,
                "verify_crawl4ai_wheel.py",
                "--wheel",
                candidate,
                "--stage",
                home / "admission",
                "--check",
                "--installed",
                "--json",
            ),
        ),
    ]
    browser = phase(home, "browser-probe", [runtime, "-I", "-c", BROWSER_PROBE, home], timeout=30)
    observed = json.loads((Path(browser["logs"]) / "stdout.log").read_bytes())
    if observed != receipt.get("browser"):
        raise ValueError("Installed browser executable changed; qualify a new provider home")
    checks.append(browser)
    return {"ok": True, "provider_version": pin["version"], "home": str(home), "checks": checks}


def setup(home: Path) -> dict[str, Any]:
    if home.exists():
        return verify(home)
    home.mkdir(parents=True)
    pin = json.loads((ROOT / INPUTS / "source.json").read_bytes())
    request = urllib.request.Request(pin["archive_url"], headers={"User-Agent": "AI-Skills-Provider-Setup/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read(pin["archive_bytes"] + 1)
        (home / "upstream-response.json").write_text(
            json.dumps(
                {"url": response.url, "status_code": response.status, "bytes": len(raw), "sha256": source.digest(raw)},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    archive = home / "upstream.tar.gz"
    archive.write_bytes(raw)
    if len(raw) != pin["archive_bytes"] or source.digest(raw) != pin["archive_sha256"]:
        raise ValueError("Downloaded source differs from the pinned archive")
    source.prepare(ROOT, archive, home / "source")
    steps = []
    steps.append(phase(home, "create-build", [sys.executable, "-I", "-m", "venv", home / "build"]))
    build = home / "build/Scripts/python.exe"
    steps.append(
        phase(
            home,
            "build-dependencies",
            [build, "-I", "-m", "pip", "install", "--require-hashes", "-r", ROOT / INPUTS / "requirements-build.txt"],
        )
    )
    steps.append(phase(home, "build-pip-check", [build, "-I", "-m", "pip", "check"]))
    steps.append(
        phase(
            home,
            "build-wheel",
            [
                build,
                "-I",
                "-B",
                "-m",
                "build",
                "--wheel",
                "--no-isolation",
                "--outdir",
                home / "wheel",
                home / "source",
            ],
        )
    )
    candidates = list((home / "wheel").glob("*.whl"))
    if len(candidates) != 1:
        raise ValueError("Build must produce exactly one wheel")
    candidate = candidates[0]
    wheel.prepare(ROOT, candidate, home / "admission")
    runtime = home / "runtime/Scripts/python.exe"
    steps.append(phase(home, "create-runtime", [sys.executable, "-I", "-m", "venv", home / "runtime"]))
    steps.append(
        phase(
            home,
            "bootstrap",
            [
                runtime,
                "-I",
                "-m",
                "pip",
                "install",
                "--require-hashes",
                "-r",
                ROOT / INPUTS / "requirements-bootstrap.txt",
            ],
        )
    )
    steps.append(
        phase(
            home,
            "runtime-dependencies",
            [
                runtime,
                "-I",
                "-m",
                "pip",
                "install",
                "--require-hashes",
                "--find-links",
                home / "wheel",
                "-r",
                home / "admission/requirements.txt",
            ],
        )
    )
    steps.append(phase(home, "runtime-pip-check", [runtime, "-I", "-m", "pip", "check"]))
    steps.append(
        phase(
            home,
            "installed-source",
            script_command(
                runtime,
                "verify_crawl4ai_wheel.py",
                "--wheel",
                candidate,
                "--stage",
                home / "admission",
                "--check",
                "--installed",
                "--json",
            ),
        )
    )
    steps.append(
        phase(
            home,
            "native-controls",
            [
                runtime,
                "-I",
                "-B",
                ROOT / "tools/check_crawl4ai_contracts.py",
                "--fixture-root",
                home / "controls-fixture",
                "--output",
                home / "controls.json",
            ],
        )
    )
    controls = json.loads((home / "controls.json").read_bytes())
    if controls.get("passed") is not True or len(controls.get("checks", [])) != 20:
        raise ValueError("All twenty native provider controls must pass")
    steps.append(phase(home, "browser-install", [runtime, "-I", "-m", "patchright", "install", "chromium"]))
    browser = phase(home, "browser-probe", [runtime, "-I", "-c", BROWSER_PROBE, home], timeout=30)
    steps.append(browser)
    browser_identity = json.loads((Path(browser["logs"]) / "stdout.log").read_bytes())
    receipt = {
        "schema_version": 1,
        "input_identity": identity(ROOT),
        "provider_version": pin["version"],
        "python_version": platform.python_version(),
        "wheel_name": candidate.name,
        "wheel_sha256": source.digest(candidate.read_bytes()),
        "source_files_admitted": len(pin["runtime_files"]),
        "native_controls": len(controls["checks"]),
        "browser": browser_identity,
        "setup_implementation_sha256": source.digest(Path(__file__).read_bytes()),
        "steps": steps,
        "external_page_qualified": False,
        "agent_efficacy_claim": False,
    }
    with (home / "installation.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    return {
        "ok": True,
        "home": str(home),
        "provider_version": pin["version"],
        "native_controls": 20,
        "source_files_admitted": len(pin["runtime_files"]),
        "external_page_qualified": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, help="Dedicated provider directory under this checkout's .venv")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("setup", help="Build, admit and normally install the complete pinned provider graph")
    commands.add_parser("check", help="Verify existing source admission and installed dependency consistency")
    crawl = commands.add_parser("crawl", help="Capture one public HTTPS page with the mandatory strict research policy")
    crawl.add_argument("--url", required=True)
    crawl.add_argument("--output", type=Path, required=True, help="New native result under workspace .venv")
    crawl.add_argument("--metadata", type=Path, required=True, help="New metadata receipt under workspace .venv")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        require_interpreter()
        home = home_path(ROOT, args.home)
        if args.command == "setup":
            result = setup(home)
        else:
            result = verify(home)
            if args.command == "crawl":
                outputs = [home_path(ROOT, path) for path in [args.output, args.metadata]]
                if outputs[0] == outputs[1] or any(path.exists() for path in outputs):
                    raise ValueError("Native result and metadata must be distinct new paths")
                for path in outputs:
                    path.parent.mkdir(parents=True, exist_ok=True)
                result = phase(
                    home,
                    "capture",
                    [
                        home / "runtime/Scripts/python.exe",
                        "-I",
                        "-B",
                        ROOT / "tools/crawl4ai_capture.py",
                        "--url",
                        args.url,
                        "--output",
                        outputs[0],
                        "--metadata",
                        outputs[1],
                        "--home",
                        home,
                    ],
                    timeout=120,
                )
                result.update(ok=True, output=str(outputs[0]), metadata=str(outputs[1]))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        result = {"ok": False, "errors": [str(error)]}
    print(json.dumps(result, indent=2))
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

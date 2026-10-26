"""Set up and use the isolated local CPU CocoIndex Code provider."""

from __future__ import annotations

import argparse
import http.client
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _agent_tool_runtime as owned
import prepare_cocoindex_source as source
import verify_cocoindex_wheel as wheel
from _catalog_publication import checked_path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = "toolchains/cocoindex-code"


def identity(root: Path) -> str:
    names = [
        INPUTS + "/" + name
        for name in [
            "source.json",
            "model.json",
            "requirements.txt",
            "requirements-build.txt",
            "requirements-bootstrap.txt",
        ]
    ]
    return owned.input_identity(root, names)


def home_path(root: Path, selected: Path | None) -> Path:
    target = selected or root / ".venv/agent-tools" / ("cocoindex-" + identity(root)[:16])
    return owned.home_path(root, target)


def environment(home: Path) -> dict[str, str]:
    env = owned.profile_environment(home, {"HF_HOME": "huggingface", "TORCH_HOME": "torch"})
    env.update(
        COCOINDEX_DISABLE_USAGE_TRACKING="1",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
        HF_HUB_DOWNLOAD_TIMEOUT="60",
        OMP_NUM_THREADS="4",
        MKL_NUM_THREADS="4",
        SOURCE_DATE_EPOCH=str(json.loads((ROOT / INPUTS / "source.json").read_bytes())["source_date_epoch"]),
    )
    return env


def phase(home: Path, name: str, arguments: list[str | Path], *, online_model: bool = False) -> dict[str, Any]:
    env = environment(home)
    if online_model:
        env["HF_HUB_OFFLINE"] = "0"
    return owned.phase(ROOT, home, name, arguments, environment=env)


def worker(home: Path, name: str, *arguments: str | Path, online_model: bool = False) -> dict[str, Any]:
    return phase(
        home,
        name,
        owned.script_command(
            ROOT, home / "runtime/Scripts/python.exe", "cocoindex_runtime.py", "--home", home, name, *arguments
        ),
        online_model=online_model,
    )


def verify(home: Path) -> dict[str, Any]:
    path = checked_path(home, "installation.json")
    if not path.is_file():
        raise ValueError("Provider setup is incomplete; preserve diagnostics and run setup with a new --home")
    receipt = json.loads(path.read_bytes())
    pin = json.loads((ROOT / INPUTS / "source.json").read_bytes())
    expected = {
        "schema_version": 1,
        "input_identity": identity(ROOT),
        "provider_version": pin["version"],
        "python_version": "3.13.17",
        "wheel_name": pin["qualified_wheel_name"],
        "wheel_sha256": pin["qualified_wheel_sha256"],
    }
    if not isinstance(receipt, dict) or any(receipt.get(name) != value for name, value in expected.items()):
        raise ValueError("Provider installation receipt differs from its admitted inputs")
    if type(receipt["schema_version"]) is not int:
        raise ValueError("Provider installation receipt has an invalid schema")
    candidate = checked_path(home, "wheel/" + pin["qualified_wheel_name"])
    wheel.prepare(ROOT, candidate, home / "admission", check=True)
    checks = [
        phase(home, "pip-check", [home / "runtime/Scripts/python.exe", "-I", "-m", "pip", "check"]),
        worker(home, "check-runtime"),
        worker(home, "check-model"),
    ]
    return {"ok": True, "home": str(home), "provider_version": pin["version"], "checks": checks}


def setup(home: Path) -> dict[str, Any]:
    if home.exists():
        return verify(home)
    home.mkdir(parents=True)
    pin = json.loads((ROOT / INPUTS / "source.json").read_bytes())
    archive = owned.download_archive(home, pin)
    source.prepare(ROOT, archive, home / "source")
    build = home / "build/Scripts/python.exe"
    runtime = home / "runtime/Scripts/python.exe"
    steps = [
        phase(home, "create-build", [sys.executable, "-I", "-m", "venv", home / "build"]),
        phase(
            home,
            "build-dependencies",
            [build, "-I", "-m", "pip", "install", "--require-hashes", "-r", ROOT / INPUTS / "requirements-build.txt"],
        ),
        phase(home, "build-pip-check", [build, "-I", "-m", "pip", "check"]),
        phase(
            home,
            "build-wheel",
            [build, "-I", "-m", "build", "--wheel", "--no-isolation", "--outdir", home / "wheel", home / "source"],
        ),
    ]
    candidates = list((home / "wheel").glob("*.whl"))
    if len(candidates) != 1 or candidates[0].name != pin["qualified_wheel_name"]:
        raise ValueError("Build must produce the single admitted local-only CocoIndex wheel")
    candidate = candidates[0]
    source.prepare(ROOT, archive, home / "source", check=True)
    wheel.prepare(ROOT, candidate, home / "admission")
    steps.extend(
        [
            phase(home, "create-runtime", [sys.executable, "-I", "-m", "venv", home / "runtime"]),
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
            ),
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
            ),
            phase(home, "runtime-pip-check", [runtime, "-I", "-m", "pip", "check"]),
            worker(home, "check-runtime"),
            worker(home, "install-model", online_model=True),
            worker(home, "check-model"),
        ]
    )
    model = json.loads((ROOT / INPUTS / "model.json").read_bytes())
    receipt = {
        "schema_version": 1,
        "input_identity": identity(ROOT),
        "provider_version": pin["version"],
        "python_version": platform.python_version(),
        "wheel_name": candidate.name,
        "wheel_sha256": source.digest(candidate.read_bytes()),
        "source_files_admitted": len(pin["runtime_files"]) + len(pin["core"]["runtime_files"]),
        "runtime_distributions": len(pin["runtime_versions"]),
        "model_files_admitted": len(model["files"]),
        "model_revision": model["revision"],
        "setup_implementation_sha256": source.digest(Path(__file__).read_bytes()),
        "steps": steps,
        "model_query_qualified": False,
        "cloud_embeddings_supported": False,
        "agent_efficacy_claim": False,
    }
    with (home / "installation.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    return {
        "ok": True,
        "home": str(home),
        "provider_version": pin["version"],
        "source_files_admitted": receipt["source_files_admitted"],
        "model_files_admitted": len(model["files"]),
        "model_query_qualified": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, help="Dedicated provider directory under this checkout's .venv")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("setup", help="Build and normally install the complete local-only provider and pinned model")
    commands.add_parser("check", help="Verify dependency versions, provider sources and local model bytes")
    index = commands.add_parser("index", help="Index only explicit current-repository prefixes")
    index.add_argument("--corpus", type=Path, required=True)
    index.add_argument("--prefix", action="append", required=True)
    index.add_argument("--check", action="store_true")
    query = commands.add_parser("search", help="Write a native source-bound search receipt")
    query.add_argument("--corpus", type=Path, required=True)
    query.add_argument("--query", required=True)
    query.add_argument("--path", action="append", default=[])
    query.add_argument("--limit", type=int, choices=range(1, 21), default=5)
    query.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        owned.require_interpreter()
        home = home_path(ROOT, args.home)
        result = setup(home) if args.command == "setup" else verify(home)
        if args.command == "index":
            arguments: list[str | Path] = ["--corpus", args.corpus]
            for prefix in args.prefix:
                arguments.extend(["--prefix", prefix])
            if args.check:
                arguments.append("--check")
            process = worker(home, "index", *arguments)
            result.update(corpus=str(args.corpus), operation=process)
        elif args.command == "search":
            arguments = [
                "--corpus",
                args.corpus,
                "--query",
                args.query,
                "--limit",
                str(args.limit),
                "--output",
                args.output,
            ]
            for pattern in args.path:
                arguments.extend(["--path", pattern])
            process = worker(home, "query", *arguments)
            result.update(output=str(args.output), operation=process)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, http.client.HTTPException) as error:
        result = {"ok": False, "errors": [str(error)]}
    print(json.dumps(result, indent=2))
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

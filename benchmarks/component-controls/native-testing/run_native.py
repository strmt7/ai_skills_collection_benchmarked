"""Reproduce native ASan and dictionary contracts, without scoring an AI agent."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import shutil
import sys
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHILD = "import subprocess,sys; p=subprocess.run(sys.argv[1:],timeout=35); raise SystemExit(p.returncode)"
FIXTURES = (
    "allocation-boundary.cpp",
    "dictionary-loader.cpp",
    "unsupported-c-escapes.dict",
    "portable-byte-escapes.dict",
    "quoted-and-backslash.dict",
    "all-byte-values.dict",
    "unterminated-quote.dict",
)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inputs() -> dict[str, str]:
    result = {
        name: hashlib.sha256((HERE / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        for name in ("run_native.py", "source.json", *FIXTURES)
    }
    result["tools/_windows_owned_python.py"] = hashlib.sha256(
        (ROOT / "tools/_windows_owned_python.py").read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()
    return result


def provision(archive: Path, destination: Path, source: dict[str, Any]) -> Path:
    if sys.version_info < (3, 14):
        raise ValueError("Archive extraction requires CPython 3.14 or later")
    if archive.stat().st_size != source["archive_bytes"] or digest(archive) != source["archive_sha256"]:
        raise ValueError("LLVM archive differs from the pinned official release asset")
    destination.mkdir(parents=True, exist_ok=False)
    if shutil.disk_usage(destination).free < 7 * 1024**3:
        raise ValueError("LLVM extraction requires at least 7 GiB of free disk space")
    zstd = importlib.import_module("compression.zstd")
    with tarfile.open(archive, "r:zst", options={zstd.DecompressionParameter.window_log_max: 30}) as tar:
        members = tar.getmembers()
        expanded = 0
        for member in members:
            relative = PurePosixPath(member.name)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or ":" in member.name
                or "\\" in member.name
                or not (member.isfile() or member.isdir())
                or not (destination / member.name).resolve().is_relative_to(destination.resolve())
            ):
                raise ValueError("Archive contains an unsupported or escaping member")
            expanded += member.size
            if expanded > 6 * 1024**3:
                raise ValueError("Archive exceeds the qualified expanded-size bound")
        tar.extractall(destination, members=members, filter="data")
    (compiler,) = destination.glob("*/bin/clang++.exe")
    if digest(compiler) != source["compiler_sha256"]:
        raise ValueError("Extracted compiler differs from the qualified official asset")
    return compiler


def execute(compiler: Path, workspace: Path, output: Path, source: dict[str, Any]) -> dict[str, Any]:
    snapshot = inputs()
    sys.path.insert(0, str(ROOT / "tools"))
    from _windows_owned_python import run_python

    if digest(compiler) != source["compiler_sha256"]:
        raise ValueError("Explicit compiler differs from the qualified official asset")
    runtime = compiler.parent.parent / source["runtime_relative_path"]
    if digest(runtime) != source["runtime_sha256"]:
        raise ValueError("Matching ASan runtime DLL differs from the qualified official asset")
    workspace.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=False)
    for name in FIXTURES:
        (workspace / name).write_bytes((HERE / name).read_bytes().replace(b"\r\n", b"\n"))
    allowed = {
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "TEMP",
        "TMP",
        "PATH",
        "PATHEXT",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMW6432",
        "PROGRAMDATA",
    }
    environment = {key.upper(): value for key, value in os.environ.items() if key.upper() in allowed}
    environment["PATH"] = (
        str(runtime.parent) + os.pathsep + str(compiler.parent) + os.pathsep + environment.get("PATH", "")
    )
    environment["ASAN_OPTIONS"] = "symbolize=1:halt_on_error=1"
    environment["ASAN_SYMBOLIZER_PATH"] = str(compiler.with_name("llvm-symbolizer.exe"))
    controls: list[dict[str, Any]] = []

    def run(label: str, args: list[str], zero: bool = True, required: tuple[str, ...] = ()) -> None:
        stdout_path, stderr_path = output / (label + ".stdout.native"), output / (label + ".stderr.native")
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            code, process = run_python(
                sys.executable,
                CHILD,
                args,
                cwd=workspace,
                environment=environment,
                stdout=stdout,
                stderr=stderr,
                timeout=40,
                output_limit=2 * 1024 * 1024,
            )
        combined = stdout_path.read_bytes() + stderr_path.read_bytes()
        passed = (code == 0) == zero and all(token.encode() in combined for token in required)
        passed &= process["termination_reason"] is None and process["active_processes_after_cleanup"] == 0
        controls.append(
            {
                "label": label,
                "arguments": ["<compiler>" if a == str(compiler) else a for a in args],
                "exit_code": code,
                "expected_zero_exit": zero,
                "required_diagnostics": list(required),
                "stdout_sha256": digest(stdout_path),
                "stderr_sha256": digest(stderr_path),
                "process": process,
                "passed": passed,
            }
        )
        (output / "commands.json").write_text(json.dumps(controls, indent=2) + "\n", encoding="utf-8")
        if not passed:
            raise ValueError(f"Native contract failed: {label}; complete logs retained")

    run("compiler-version", [str(compiler), "--version"], required=("clang version " + source["version"],))
    run(
        "asan-build",
        [
            str(compiler),
            "-O1",
            "-g",
            "-fno-omit-frame-pointer",
            "-fsanitize=address",
            "-fuse-ld=lld",
            "-v",
            "allocation-boundary.cpp",
            "-o",
            "allocation-boundary.exe",
        ],
    )
    run("asan-clean", [str(workspace / "allocation-boundary.exe")])
    run(
        "asan-out-of-bounds",
        [str(workspace / "allocation-boundary.exe"), "outside"],
        False,
        ("ERROR: AddressSanitizer: heap-buffer-overflow",),
    )
    run(
        "fuzzer-build",
        [
            str(compiler),
            "-O1",
            "-g",
            "-fsanitize=fuzzer,address",
            "-fuse-ld=lld",
            "dictionary-loader.cpp",
            "-o",
            "dictionary-loader.exe",
        ],
    )
    fuzzer = str(workspace / "dictionary-loader.exe")
    run("fuzzer-help", [fuzzer, "-help=1"], required=("rss_limit_mb", "malloc_limit_mb"))
    for label, zero, diagnostic in [
        ("unsupported-c-escapes", False, "ParseDictionaryFile: error in line 1"),
        ("portable-byte-escapes", True, "Dictionary: 1 entries"),
        ("quoted-and-backslash", True, "Dictionary: 1 entries"),
        ("all-byte-values", True, "Dictionary: 1 entries"),
        ("unterminated-quote", False, "ParseDictionaryFile: error in line 1"),
    ]:
        run(
            label,
            [
                fuzzer,
                "-runs=1",
                "-seed=1",
                "-timeout=2",
                "-max_len=512",
                "-rss_limit_mb=256",
                "-malloc_limit_mb=32",
                "-dict=" + label + ".dict",
            ],
            zero,
            (diagnostic,),
        )
    if inputs() != snapshot:
        raise ValueError("Native collector or fixture inputs changed during qualification")
    return {
        "measurement_kind": "native_component_contract_controls",
        "compiler_version": source["version"],
        "input_sha256": snapshot,
        "controls": controls,
        "all_passed": True,
        "agent_performance_claim": False,
        "independent_model_trials": 0,
        "scope": "Windows x64 LLVM ASan detection and libFuzzer dictionary admission; no campaign, MSVC compiler, other fuzzer or leak qualification",
    }


def check() -> int:
    recorded = json.loads((HERE / "result.json").read_bytes())
    if (
        recorded["input_sha256"] != inputs()
        or recorded["agent_performance_claim"]
        or recorded["independent_model_trials"] != 0
    ):
        raise ValueError("Published native component evidence is stale or misclassified")
    if (
        len(recorded["controls"]) != 11
        or not recorded["all_passed"]
        or not all(row["passed"] for row in recorded["controls"])
    ):
        raise ValueError("Published native component evidence is incomplete")
    print(json.dumps({"errors": [], "controls": 11, "agent_performance_claim": False}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--toolchain", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.check:
        return check()
    if sys.platform != "win32":
        raise ValueError("Native qualification supports Windows x64 only")
    source = json.loads((HERE / "source.json").read_bytes())
    if not args.workspace or not args.output or bool(args.compiler) == bool(args.archive):
        raise ValueError("Use explicit --workspace, --output and exactly one of --compiler or --archive")
    if args.archive:
        if not args.toolchain:
            raise ValueError("Archive extraction needs a new --toolchain directory")
        compiler = provision(args.archive.resolve(), args.toolchain.resolve(), source)
    else:
        compiler = args.compiler.resolve()
    result = execute(compiler, args.workspace.resolve(), args.output.resolve(), source)
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_passed": True, "controls": len(result["controls"]), "agent_performance_claim": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

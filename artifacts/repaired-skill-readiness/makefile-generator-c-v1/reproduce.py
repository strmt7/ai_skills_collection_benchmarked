from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

SOURCE_HASH = "f85287a85ab0b152b2d7f8681642d616031896e4e75d45b78970de514a324747"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalized(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def run(source: Path, repair: Path, make: Path, scratch: Path, output: Path) -> dict[str, Any]:
    original = normalized(source)
    if digest(original) != SOURCE_HASH:
        raise ValueError("Original generator differs from the pinned source")
    make_version = subprocess.run(
        [str(make), "--version"], capture_output=True, text=True, check=True, timeout=20
    ).stdout.splitlines()[0]
    gcc_version = subprocess.run(
        ["gcc", "--version"], capture_output=True, text=True, check=True, timeout=20
    ).stdout.splitlines()[0]
    if not make_version.startswith("GNU Make "):
        raise ValueError("The control requires GNU Make")
    scratch.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=False)
    original_copy = scratch / "source-generator.sh"
    original_copy.write_bytes(original)
    env = os.environ.copy()
    for key in (
        "CC",
        "CFLAGS",
        "CPPFLAGS",
        "LDFLAGS",
        "LDLIBS",
        "PICFLAGS",
        "MAKEFLAGS",
        "MFLAGS",
        "GNUMAKEFLAGS",
        "MAKEFILES",
    ):
        env.pop(key, None)
    temp = Path(tempfile.mkdtemp(prefix="make-c-control-", dir=scratch))

    def fixture(kind: str, variant: str, case: str) -> Path:
        folder = temp / f"{kind}-{variant}-{case}"
        folder.mkdir()
        (folder / "src").mkdir()
        (folder / "src/main.c").write_text(
            "int shared_global = 42; int *get_global(void) { return &shared_global; } int main(void) { return 0; }\n",
            encoding="utf-8",
        )
        if variant == "original":
            args = ["bash", str(original_copy), kind, "demo", "Makefile"]
        else:
            args = [sys.executable, str(repair / "generate.py"), "--kind", kind, "--name", "demo"]
        subprocess.run(args, cwd=folder, env=env, capture_output=True, text=True, check=True, timeout=30)
        return folder

    def cc_origin(folder: Path) -> str:
        args = [str(make), "--no-print-directory", "--eval=probe:;@printf '%s|%s\\n' '$(CC)' '$(origin CC)'", "probe"]
        return subprocess.run(
            args, cwd=folder, env=env, capture_output=True, text=True, check=True, timeout=30
        ).stdout.strip()

    def link_case(variant: str, case: str) -> dict[str, Any]:
        folder = fixture("c-lib", variant, case)
        variables = env.copy()
        args = [str(make), "--no-print-directory", "-j4", "all"]
        if case == "environment_cflags":
            variables["CFLAGS"] = "-O2"
        elif case == "command_cflags":
            args.append("CFLAGS=-O2")
        elif case == "invalid_ldflags":
            args.append("LDFLAGS=-Wl,--this-option-does-not-exist")
        elif case == "missing_ldlibs":
            args.append("LDLIBS=-lthis_library_does_not_exist")
        result = subprocess.run(
            args, cwd=folder, env=variables, capture_output=True, text=True, check=False, timeout=60
        )
        (output / f"{variant}-{case}.stdout.txt").write_text(result.stdout, encoding="utf-8", newline="\n")
        (output / f"{variant}-{case}.stderr.txt").write_text(result.stderr, encoding="utf-8", newline="\n")
        return {
            "exit": result.returncode,
            "shared_exists": (folder / "build/libdemo.so.1.0.0").is_file(),
            "pic_error": "fPIC" in result.stderr,
            "expected_invalid_flag": "this-option-does-not-exist" in result.stderr,
            "expected_missing_library": "this_library_does_not_exist" in result.stderr,
        }

    results: dict[str, dict[str, Any]] = {
        variant: {
            "cc_default": cc_origin(fixture("c", variant, "cc")),
            "link_cases": {
                case: link_case(variant, case)
                for case in ("environment_cflags", "command_cflags", "invalid_ldflags", "missing_ldlibs")
            },
        }
        for variant in ("original", "repaired")
    }
    report = {
        "source_sha256": digest(original),
        "repair_sha256": {
            name: digest(normalized(repair / name)) for name in ("generate.py", "templates/c.mk", "templates/c-lib.mk")
        },
        "make_version": make_version,
        "compiler": gcc_version,
        "platform": platform.platform(),
        "results": results,
        "agent_efficacy_scored": False,
    }
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    old, new = results["original"], results["repaired"]
    valid = old["cc_default"] == "cc|default" and new["cc_default"] == "gcc|file"
    for case in ("environment_cflags", "command_cflags"):
        valid = (
            valid
            and old["link_cases"][case]["exit"] != 0
            and old["link_cases"][case]["pic_error"]
            and new["link_cases"][case]["exit"] == 0
            and new["link_cases"][case]["shared_exists"]
        )
    for case, marker in (("invalid_ldflags", "expected_invalid_flag"), ("missing_ldlibs", "expected_missing_library")):
        valid = (
            valid
            and old["link_cases"][case]["exit"] == 0
            and old["link_cases"][case]["shared_exists"]
            and new["link_cases"][case]["exit"] != 0
            and new["link_cases"][case][marker]
        )
    if not valid:
        raise ValueError("Observed behavior differs from the recorded component control")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare pinned and repaired C Makefile generators in isolated fixtures."
    )
    for name in ("source", "repair", "make", "scratch", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                run(*(getattr(args, name).resolve() for name in ("source", "repair", "make", "scratch", "output"))),
                indent=2,
            )
        )
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

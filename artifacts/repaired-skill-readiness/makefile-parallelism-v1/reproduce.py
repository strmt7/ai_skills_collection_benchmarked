"""Exercise GNU Make ordering examples with synthetic recipes on Linux."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/coding-refactoring-repository-automation/latest-release-devops/makefile-parallelism"
)
MARKER = """\
import json, pathlib, sys, time
start = time.monotonic_ns()
time.sleep(0.5)
end = time.monotonic_ns()
pathlib.Path(sys.argv[1] + '.json').write_text(json.dumps([start, end]), encoding='utf-8')
"""
ORIGINAL = """\
.PHONY: all prepare publish verify
.NOTPARALLEL: prepare publish verify
STEP ?= printf '%s\\n'
all: publish verify
publish verify: prepare
prepare publish verify:
\t@$(STEP) $@
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(make: str, makefile: Path, directory: Path, goals: list[str]) -> dict[str, Any]:
    directory.mkdir()
    marker = directory / "marker.py"
    marker.write_text(MARKER, encoding="utf-8")
    step = f"{shlex.quote(sys.executable)} {shlex.quote(str(marker))}"
    env = os.environ.copy()
    for variable in ("MAKEFLAGS", "GNUMAKEFLAGS", "MAKEFILES"):
        env.pop(variable, None)
    command = [make, "--no-print-directory", "-j2", "-f", str(makefile), f"STEP={step}", *goals]
    process = subprocess.run(command, cwd=directory, env=env, capture_output=True, text=True, timeout=30, check=True)
    intervals = {
        name: json.loads((directory / f"{name}.json").read_bytes()) for name in ("prepare", "publish", "verify")
    }
    return {"intervals_ns": intervals, "stdout": process.stdout, "stderr": process.stderr}


def run(make: str) -> dict[str, Any]:
    if platform.system() != "Linux":
        raise ValueError("These executable controls require Linux")
    version = subprocess.run(
        [make, "--version"], capture_output=True, text=True, timeout=10, check=True
    ).stdout.splitlines()[0]
    if not version.startswith("GNU Make "):
        raise ValueError("The controls require GNU Make")
    original_skill = OVERLAY / "provenance/original.SKILL.md"
    if ".NOTPARALLEL: docker-build docker-push docker-run" not in original_skill.read_text(encoding="utf-8"):
        raise ValueError("The original parallelism example changed")
    with tempfile.TemporaryDirectory(prefix="make-parallel-controls-") as temporary:
        root = Path(temporary)
        original = root / "original.mk"
        original.write_text(ORIGINAL, encoding="utf-8")
        observations = {
            "original": observe(make, original, root / "original", ["all"]),
            "ordered_all": observe(make, OVERLAY / "examples/ordered.mk", root / "ordered-all", ["all"]),
            "ordered_direct": observe(make, OVERLAY / "examples/ordered.mk", root / "ordered-direct", ["verify"]),
            "serial_all": observe(make, OVERLAY / "examples/serial.mk", root / "serial-all", ["all"]),
            "serial_multiple_goals": observe(
                make, OVERLAY / "examples/serial.mk", root / "serial-multiple", ["publish", "verify"]
            ),
        }
    for name, item in observations.items():
        intervals = item["intervals_ns"]
        prepare, publish, verify = (intervals[key] for key in ("prepare", "publish", "verify"))
        item["prepare_completed_first"] = prepare[1] <= min(publish[0], verify[0])
        item["siblings_overlap"] = max(publish[0], verify[0]) < min(publish[1], verify[1])
        item["publish_completed_before_verify"] = publish[1] <= verify[0]
        if not item["prepare_completed_first"]:
            raise AssertionError(f"{name}: preparation did not finish before dependent recipes")
        if name.startswith("ordered") and not item["publish_completed_before_verify"]:
            raise AssertionError(f"{name}: dependency order was not respected")
        if name.startswith("serial") and item["siblings_overlap"]:
            raise AssertionError(f"{name}: sibling recipes overlapped")
    # GNU Make 4.4 introduced the target-specific .NOTPARALLEL behavior.
    if version.startswith("GNU Make 4.4") and not observations["original"]["siblings_overlap"]:
        raise AssertionError("The 4.4 original-example control did not demonstrate sibling overlap")
    return {
        "schema_version": 1,
        "platform": platform.system(),
        "python": platform.python_version(),
        "make": version,
        "source_sha256": digest(original_skill),
        "examples_sha256": {name: digest(OVERLAY / "examples" / name) for name in ("ordered.mk", "serial.mk")},
        "observations": observations,
        "external_services_called": False,
        "agent_performance_tested": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--make", default="make")
    args = parser.parse_args(argv)
    print(json.dumps(run(args.make), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

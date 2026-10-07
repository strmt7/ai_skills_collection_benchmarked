#!/usr/bin/env python3
"""Install a verified stable wheel into an offline dependency image, then pin its ID.

The build context contains only the wheel and this fixed recipe. Container build
steps are trusted dependency installation, not agent grading. Candidate execution
uses the separately inspected bounded backend with its original constraints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
WHEEL_NAME = "atheris-3.1.0-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.whl"
WHEEL_SHA256 = "315a0b5c819852b1ffe1ca72efc389c7724881f2c33e4aacb8c6bcec49bd5011"


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New receipt")
    return parser


def main(argv=None):
    from isolated_python import IMAGE

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    if not args.wheel.is_file() or args.wheel.is_symlink() or args.wheel.stat().st_size > 40 * 1024 * 1024:
        raise ValueError("wheel must be a bounded regular file")
    raw = args.wheel.read_bytes()
    if hashlib.sha256(raw).hexdigest() != WHEEL_SHA256:
        raise ValueError("wheel does not match the primary release digest")
    recipe = (
        f"FROM {IMAGE}\n"
        f"LABEL ai-skills.dependency=atheris ai-skills.wheel-sha256={WHEEL_SHA256}\n"
        f"COPY {WHEEL_NAME} /tmp/{WHEEL_NAME}\n"
        f"RUN python -m pip install --disable-pip-version-check --no-cache-dir --no-index --no-deps /tmp/{WHEEL_NAME}\n"
    )
    with tempfile.TemporaryDirectory(prefix="atheris-image-") as temporary:
        context = Path(temporary)
        (context / WHEEL_NAME).write_bytes(raw)
        (context / "Dockerfile").write_text(recipe, encoding="utf-8", newline="\n")
        built = subprocess.run(
            [
                "docker",
                "build",
                "--network",
                "none",
                "--pull=false",
                "--iidfile",
                str(context / "image-id"),
                str(context),
            ],
            capture_output=True,
            timeout=180,
            check=False,
        )
        image = (context / "image-id").read_text("ascii").strip() if (context / "image-id").is_file() else None
    inspection = {}
    if built.returncode == 0 and isinstance(image, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        inspected = subprocess.run(["docker", "image", "inspect", image], capture_output=True, timeout=15, check=True)
        inspection = json.loads(inspected.stdout)[0]
    passed = (
        built.returncode == 0
        and inspection.get("Id") == image
        and inspection.get("Config", {}).get("Labels", {}).get("ai-skills.wheel-sha256") == WHEEL_SHA256
        and inspection.get("Config", {}).get("Labels", {}).get("ai-skills.dependency") == "atheris"
    )
    if hashlib.sha256(args.wheel.read_bytes()).hexdigest() != WHEEL_SHA256:
        raise ValueError("input wheel changed during build")
    receipt = {
        "schema_version": 1,
        "evidence_class": "offline-trusted-dependency-image-preparation-not-runtime-readiness",
        "passed": passed,
        "base_image": IMAGE,
        "image": image,
        "wheel_filename": WHEEL_NAME,
        "wheel_sha256": WHEEL_SHA256,
        "dockerfile": recipe,
        "dockerfile_sha256": hashlib.sha256(recipe.encode()).hexdigest(),
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "build_returncode": built.returncode,
        "build_output": (built.stdout + built.stderr).decode("utf-8", errors="replace")[:65536],
        "runtime_constraints_weakened": False,
        "wheel_contents_modified": False,
        "agent_efficacy_scored": False,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"passed": passed, "image": image, "build_returncode": built.returncode}))
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Prepare a verified LLVM subset and immutable native fixtures offline; no agent grading."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
NAME = "LLVM-23.1.3-Linux-X64.tar.zst"
DIGEST = "14d2f701eb68fb799001bdea6231048f3990690fa2f406d563555ff8f744daba"
SIZE = 1188398549
SOURCES = {
    "libfuzzer.md": ROOT / "included/skills/by-category/testing-qa-benchmarking/security-reference/libfuzzer/SKILL.md",
    "coverage.md": ROOT
    / "included/skills/by-category/testing-qa-benchmarking/security-reference/coverage-analysis/SKILL.md",
    "fixture.py": Path(__file__).with_name("llvm_image_fixture.py"),
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv=None):
    from isolated_python import IMAGE

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    if (
        args.archive.is_symlink()
        or not args.archive.is_file()
        or args.archive.stat().st_size != SIZE
        or digest(args.archive) != DIGEST
    ):
        raise ValueError("archive does not match stable official release")
    inputs = {p.relative_to(ROOT).as_posix(): digest(p) for p in SOURCES.values()}
    recipe = (
        f"FROM {IMAGE}\n"
        f"LABEL ai-skills.dependency=llvm-native-controls ai-skills.release-sha256={DIGEST}\n"
        "COPY llvm.tar.zst libfuzzer.md coverage.md fixture.py /tmp/\n"
        "RUN python /tmp/fixture.py\n"
    )
    with tempfile.TemporaryDirectory(prefix="llvm-image-", dir=ROOT / ".venv/research-state") as temporary:
        context = Path(temporary)
        shutil.copyfile(args.archive, context / "llvm.tar.zst")
        for name, source in SOURCES.items():
            shutil.copyfile(source, context / name)
        (context / "Dockerfile").write_text(recipe, encoding="utf-8", newline="\n")
        result = subprocess.run(
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
            timeout=600,
            check=False,
        )
        image = (context / "image-id").read_text("ascii").strip() if (context / "image-id").is_file() else None
    inspection = {}
    if result.returncode == 0 and isinstance(image, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        inspected = subprocess.run(["docker", "image", "inspect", image], capture_output=True, timeout=15, check=True)
        inspection = json.loads(inspected.stdout)[0]
    passed = (
        result.returncode == 0
        and inspection.get("Id") == image
        and inspection.get("Config", {}).get("Labels", {}).get("ai-skills.release-sha256") == DIGEST
        and inspection.get("Config", {}).get("Labels", {}).get("ai-skills.dependency") == "llvm-native-controls"
    )
    if digest(args.archive) != DIGEST or any(digest(ROOT / p) != d for p, d in inputs.items()):
        raise ValueError("image input changed during build")
    receipt = {
        "schema_version": 1,
        "evidence_class": "offline-trusted-native-source-fixture-image-preparation",
        "passed": passed,
        "base_image": IMAGE,
        "image": image,
        "release_url": "https://github.com/llvm/llvm-project/releases/download/llvmorg-23.1.3/" + NAME,
        "archive_size": SIZE,
        "archive_sha256": DIGEST,
        "project_file_sha256": inputs,
        "dockerfile": recipe,
        "dockerfile_sha256": hashlib.sha256(recipe.encode()).hexdigest(),
        "reproducer_sha256": digest(Path(__file__)),
        "build_returncode": result.returncode,
        "build_output": (result.stdout + result.stderr).decode("utf-8", errors="replace")[:65536],
        "release_subset_unmodified": True,
        "runtime_constraints_weakened": False,
        "agent_efficacy_scored": False,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"passed": passed, "image": image, "build_returncode": result.returncode}))
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())

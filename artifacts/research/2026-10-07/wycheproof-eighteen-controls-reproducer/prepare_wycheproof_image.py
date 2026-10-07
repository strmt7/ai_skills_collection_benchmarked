"""Prepare a hash-qualified offline provider/schema image, without scoring an agent."""

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
MANIFEST = Path(__file__).with_name("wycheproof-inputs.json")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv=None):
    from isolated_python import IMAGE

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    manifest_bytes = MANIFEST.read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest["base_image"] != IMAGE or len(manifest["wheels"]) != 8:
        raise ValueError("unsupported input manifest")
    wheel_paths = []
    for entry in manifest["wheels"].values():
        name = entry["filename"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+\.whl", name):
            raise ValueError("noncanonical wheel filename")
        path = args.wheel_dir / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != entry["bytes"]:
            raise ValueError("wheel is not the qualified regular file")
        if entry["bytes"] > 8 * 1024 * 1024 or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("wheel hash or size mismatch")
        wheel_paths.append(path)
    recipe = (
        f"FROM {IMAGE}\n"
        f"LABEL ai-skills.dependency=wycheproof-provider ai-skills.inputs-sha256={hashlib.sha256(manifest_bytes).hexdigest()}\n"
        "COPY *.whl /tmp/wheels/\n"
        "RUN python -m pip install --disable-pip-version-check --no-cache-dir --no-index /tmp/wheels/*.whl && python -m pip check\n"
    )
    with tempfile.TemporaryDirectory(prefix="wycheproof-image-") as temporary:
        stage = Path(temporary)
        for path in wheel_paths:
            shutil.copyfile(path, stage / path.name)
        (stage / "Dockerfile").write_text(recipe, encoding="utf-8", newline="\n")
        built = subprocess.run(
            ["docker", "build", "--network", "none", "--pull=false", "--iidfile", str(stage / "image-id"), str(stage)],
            capture_output=True,
            timeout=180,
            check=False,
        )
        image = (stage / "image-id").read_text().strip() if (stage / "image-id").is_file() else None
    inspection = {}
    if built.returncode == 0 and isinstance(image, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", image):
        inspected = subprocess.run(["docker", "image", "inspect", image], capture_output=True, timeout=15, check=True)
        inspection = json.loads(inspected.stdout)[0]
    passed = (
        built.returncode == 0
        and inspection.get("Id") == image
        and inspection.get("Config", {}).get("Labels", {}).get("ai-skills.inputs-sha256")
        == hashlib.sha256(manifest_bytes).hexdigest()
        and inspection.get("Config", {}).get("Labels", {}).get("ai-skills.dependency") == "wycheproof-provider"
    )
    if MANIFEST.read_bytes() != manifest_bytes:
        raise ValueError("input manifest changed during preparation")
    for path, entry in zip(wheel_paths, manifest["wheels"].values(), strict=True):
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("wheel changed during preparation")
    receipt = {
        "schema_version": 1,
        "evidence_class": "offline-trusted-provider-and-schema-image-preparation-not-runtime-readiness",
        "passed": passed,
        "base_image": IMAGE,
        "image": image,
        "inputs_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "wheels": manifest["wheels"],
        "dockerfile": recipe,
        "dockerfile_sha256": hashlib.sha256(recipe.encode()).hexdigest(),
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "build_returncode": built.returncode,
        "build_output": (built.stdout + built.stderr).decode("utf-8", errors="replace")[:65536],
        "agent_efficacy_scored": False,
        "runtime_constraints_weakened": False,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"passed": passed, "image": image, "build_returncode": built.returncode}))
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())

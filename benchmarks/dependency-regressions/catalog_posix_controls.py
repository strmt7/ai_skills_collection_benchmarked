#!/usr/bin/env python3
"""Replay publication/mode contracts in the qualified Linux Docker image."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

EXPECTED_CHECKS = {
    "publication_preserves_posix_executable_mode_and_previous_files",
    "repeated_posix_stage_has_no_drift",
    "later_posix_rename_failure_restores_earlier_outputs",
    "posix_symlink_publication_target_rejected",
    "portable_tree_hash_copy_and_posix_mode_tamper_detection",
}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New JSON receipt; never overwritten")
    return parser


def main(argv=None):
    import _catalog_publication as publication
    from isolated_python import run_isolated

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    parent = publication.checked_path(ROOT, ".venv/posix-publication-controls")
    parent.mkdir(parents=True, exist_ok=True)
    names = ["tools/build_catalog.py", "tools/_catalog_publication.py", "tools/update_readme_badges.py"]
    names += [file.relative_to(ROOT).as_posix() for file in (ROOT / "tools/_lib_b").glob("*.py")]
    input_hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}
    fixture = ROOT / "benchmarks/dependency-regressions/catalog_posix_fixture.py"
    input_hashes[fixture.relative_to(ROOT).as_posix()] = hashlib.sha256(fixture.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="fixture-", dir=parent) as temporary:
        source = Path(temporary)
        for name in names:
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
        shutil.copy2(fixture, source / "candidate.py")
        vendor = Path(yaml.__file__).parent
        for file in vendor.glob("*.py"):
            name = "vendor/yaml/" + file.name
            (source / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, source / name)
            names.append(name)
        names.append("candidate.py")
        invocation = run_isolated(source, names, {}, timeout=30)
    result = invocation.get("candidate_response", {}).get("result", {})
    passed = (
        invocation["status"] == "completed"
        and invocation["cleanup_verified"]
        and result.get("platform") == "linux"
        and result.get("uid") == 65534
        and set(result.get("checks", [])) == EXPECTED_CHECKS
        and result.get("fixture_temporary_directory_removed") is True
    )
    for name, digest in input_hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"input changed during controls: {name}")
    receipt = {
        "schema_version": 1,
        "evidence_class": "actual-linux-publication-and-mode-controls",
        "passed": passed,
        "project_file_sha256": input_hashes,
        "pyyaml_version": version("PyYAML"),
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "invocation": invocation,
        "agent_efficacy_scored": False,
        "scope": "Qualified Linux image, actual filesystem/mode contracts; not the full Linux suite",
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": passed,
                "status": invocation["status"],
                "result": result,
                "cleanup_verified": invocation["cleanup_verified"],
            }
        )
    )
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())

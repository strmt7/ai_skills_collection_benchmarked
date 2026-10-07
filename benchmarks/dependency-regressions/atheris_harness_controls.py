#!/usr/bin/env python3
"""Exercise unchanged Atheris source examples using a pinned offline dependency image."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import urllib3

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
PACKAGE = "included/skills/by-category/testing-qa-benchmarking/security-reference/atheris"
EXPECTED = {
    "original_version_verification_raises_attribute_error",
    "original_dynamic_preload_path_misses_installed_sanitizer_library",
    "json_ignore_decode_collapses_distinct_input_bytes",
    "http_example_reads_wire_as_body_without_parsing_status_or_headers",
    "http_harness_swallows_injected_unexpected_runtime_error",
    "real_provider_empty_input_uses_degenerate_defaults",
    "real_instrumented_engine_completes_64_bounded_calls",
    "original_quickstart_replays_known_seed_python_exception",
}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New control receipt")
    return parser


def main(argv=None):
    from isolated_python import IMAGE, run_isolated

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    image_bytes = args.image_receipt.read_bytes()
    image_receipt = json.loads(image_bytes)
    if not image_receipt.get("passed") or image_receipt.get("base_image") != IMAGE:
        raise ValueError("dependency image preparation is not qualified")
    original = ROOT / PACKAGE / "SKILL.md"
    fixture = Path(__file__).with_name("atheris_harness_fixture.py")
    inputs = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in [original, fixture]}
    vendor_hashes = {}
    with tempfile.TemporaryDirectory(prefix="atheris-controls-") as temporary:
        stage = Path(temporary)
        shutil.copyfile(original, stage / "original-SKILL.md")
        shutil.copyfile(fixture, stage / "candidate.py")
        names = ["original-SKILL.md", "candidate.py"]
        vendor = Path(urllib3.__file__).parent
        for source in sorted(vendor.rglob("*.py")):
            name = "vendor/urllib3/" + source.relative_to(vendor).as_posix()
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            vendor_hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
            names.append(name)
        invocation = run_isolated(stage, names, {}, image=image_receipt["image"], timeout=40)
    result = invocation.get("candidate_response", {}).get("result", {})
    passed = (
        invocation["status"] == "completed"
        and invocation["cleanup_verified"]
        and set(result.get("checks", [])) == EXPECTED
        and len(result.get("checks", [])) == len(EXPECTED)
        and result.get("temporary_directory_removed") is True
        and result.get("uid") == 65534
        and result.get("platform") == "linux"
        and result.get("python_version") == "3.14.8"
        and result.get("agent_processes") == 0
    )
    for name, digest in inputs.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError("source changed during controls")
    if args.image_receipt.read_bytes() != image_bytes:
        raise ValueError("image preparation receipt changed during controls")
    receipt = {
        "schema_version": 1,
        "evidence_class": "actual-atheris-source-harness-and-bounded-engine-controls",
        "passed": passed,
        "project_file_sha256": inputs,
        "dependency_image_receipt_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "urllib3_version": version("urllib3"),
        "urllib3_member_sha256": vendor_hashes,
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "invocation": invocation,
        "agent_efficacy_scored": False,
        "scope": "Original source examples, actual pure-Python engine, injected exception and known-seed replay; no native target/sanitizer/coding-agent score",
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

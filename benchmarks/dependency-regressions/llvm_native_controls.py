#!/usr/bin/env python3
"""Validate native compiler/coverage source controls; never score skill or agent efficacy."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
EXPECTED = {
    "matching_stable_compiler_and_profile_tools",
    "original_division_zero_crashes_without_optimization",
    "original_unused_division_eliminated_at_O2",
    "defined_byte_decode_and_consumed_result_detect_zero_with_ubsan",
    "same_checked_target_accepts_valid_denominator",
    "original_replay_reports_success_for_unreadable_input",
    "original_replay_truncates_valid_long_path_and_still_succeeds",
    "glibc_empty_input_replay_works_here_not_portability_proof",
    "O3_source_based_profiles_export_parseable_json",
    "lcov_export_is_not_json",
    "repeating_profile_argument_does_not_create_differential_coverage",
    "matching_profile_merge_preserves_both_distinct_target_paths",
    "bounded_driver_replays_valid_completely",
    "bounded_driver_replays_empty_completely",
    "bounded_driver_replays_long_path_completely",
    "bounded_driver_replays_exact_limit_completely",
    "bounded_driver_rejects_unreadable_before_target",
    "bounded_driver_rejects_oversized_before_target",
    "bounded_driver_rejects_missing_before_target",
    "bounded_driver_rejects_symlink_before_target",
    "bounded_driver_rejects_directory_before_target",
}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv=None):
    from isolated_python import IMAGE, run_isolated

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    image_bytes = args.image_receipt.read_bytes()
    image = json.loads(image_bytes)
    if not image.get("passed") or image.get("base_image") != IMAGE:
        raise ValueError("native image not qualified")
    for name, digest in image["project_file_sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError("native fixture input changed since build")
    fixture = Path(__file__).with_name("llvm_native_fixture.py")
    fixture_bytes = fixture.read_bytes()
    with tempfile.TemporaryDirectory(prefix="native-controls-") as temporary:
        source = Path(temporary)
        shutil.copyfile(fixture, source / "candidate.py")
        invocation = run_isolated(
            source, ["candidate.py"], {}, image=image["image"], timeout=100, output_limit=2 * 1024 * 1024
        )
    result = invocation.get("candidate_response", {}).get("result", {})
    passed = (
        invocation["status"] == "completed"
        and invocation["cleanup_verified"]
        and set(result.get("checks", [])) == EXPECTED
        and len(result.get("checks", [])) == len(EXPECTED)
        and result.get("uid") == 65534
        and result.get("agent_processes") == 0
        and result.get("temporary_directory_removed") is True
        and result.get("runtime_compilation") is False
    )
    if fixture.read_bytes() != fixture_bytes or args.image_receipt.read_bytes() != image_bytes:
        raise ValueError("native control input changed during run")
    receipt = {
        "schema_version": 1,
        "evidence_class": "actual-native-source-contract-controls-not-independent-benchmark",
        "passed": passed,
        "image_preparation_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "fixture_sha256": hashlib.sha256(fixture_bytes).hexdigest(),
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "expected_controls": sorted(EXPECTED),
        "invocation": invocation,
        "agent_efficacy_scored": False,
        "runtime_constraints_weakened": False,
        "scope": "Fixed known-input native source examples, sanitizer smoke and source-based profiles; no bug-finding campaign, leak detection or agent comparison",
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as output:
        output.write(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": passed,
                "status": invocation["status"],
                "checks": result.get("checks"),
                "cleanup_verified": invocation["cleanup_verified"],
                "error": invocation.get("candidate_response", {}).get("error"),
            }
        )
    )
    return int(not passed)


if __name__ == "__main__":
    raise SystemExit(main())

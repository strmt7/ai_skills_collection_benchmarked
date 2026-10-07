#!/usr/bin/env python3
"""Replay unchanged skill-creator contracts in the qualified Linux backend."""

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
PACKAGE = "included/skills/by-category/testing-qa-benchmarking/official-reference/skill-creator-anthropics"
EXPECTED_CHECKS = {
    "ungraded_planned_run_omitted_from_denominator",
    "entrypoint_direct_grading_layout_not_aggregated",
    "output_characters_reported_as_tokens",
    "nonzero_embedded_duration_discards_sibling_token_usage",
    "contradictory_out_of_range_score_and_fixed_repetition_metadata_accepted",
    "empty_required_frontmatter_values_accepted",
    "literal_yaml_block_description_newlines_changed",
    "packager_follows_link_outside_selected_package",
    "reported_test_set_used_for_candidate_selection",
    "duplicate_query_text_moves_declared_test_rows_into_training_results",
    "small_stratified_split_leaves_no_training_rows",
    "missing_model_cli_counted_as_correct_negative_trigger",
}


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New receipt; never overwritten")
    return parser


def main(argv=None):
    from isolated_python import run_isolated

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    originals = sorted((ROOT / PACKAGE / "scripts").glob("*.py"))
    fixture = Path(__file__).with_name("skill_creator_fixture.py")
    input_hashes = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in [*originals, fixture]
    }
    parent = ROOT / ".venv/skill-creator-controls"
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fixture-", dir=parent) as temporary:
        source = Path(temporary)
        names = []
        for original in originals:
            name = "original/scripts/" + original.name
            (source / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, source / name)
            names.append(name)
        for original in Path(yaml.__file__).parent.glob("*.py"):
            name = "vendor/yaml/" + original.name
            (source / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, source / name)
            names.append(name)
        shutil.copy2(fixture, source / "candidate.py")
        names.append("candidate.py")
        invocation = run_isolated(source, names, {}, timeout=30)
    result = invocation.get("candidate_response", {}).get("result", {})
    passed = (
        invocation["status"] == "completed"
        and invocation["cleanup_verified"]
        and result.get("platform") == "linux"
        and result.get("uid") == 65534
        and len(result.get("checks", [])) == len(EXPECTED_CHECKS)
        and set(result.get("checks", [])) == EXPECTED_CHECKS
        and result.get("ai_processes_launched") == 0
        and result.get("provider_calls") == 0
        and result.get("fixture_temporary_directory_removed") is True
    )
    for name, digest in input_hashes.items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"input changed during controls: {name}")
    receipt = {
        "schema_version": 1,
        "evidence_class": "actual-skill-creator-package-contract-controls",
        "passed": passed,
        "project_file_sha256": input_hashes,
        "pyyaml_version": version("PyYAML"),
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "invocation": invocation,
        "agent_efficacy_scored": False,
        "scope": "Actual original Python, owned filesystem fixtures and injected evaluator values; no AI/provider runs",
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

"""Qualify selected mutation/graph tool contracts without scoring a coding agent."""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def literals(path, names):
    return {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in ast.parse(path.read_text()).body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in names
    }


def validate_invocation(execution, image, profile):
    from isolated_python import OWNER_LABEL, validate_inspection

    observed = execution.get("isolation_checks", {})
    inspection = {
        "Config": {
            "Image": observed.get("observed_image"),
            "User": observed.get("observed_user"),
            "Labels": {OWNER_LABEL: observed.get("observed_ownership_token")},
        },
        "Image": observed.get("resolved_image_id"),
        "HostConfig": observed.get("observed_host_constraints", {}),
        "Mounts": observed.get("observed_mounts", []),
    }
    return (
        execution.get("status") == "completed"
        and execution.get("cleanup_verified") is True
        and not execution.get("cleanup_error")
        and execution.get("candidate_response", {}).get("worker_status") == "returned"
        and observed.get("observed_ownership_token")
        and not validate_inspection(inspection, observed["observed_ownership_token"], profile, image=image)
    )


def campaign_checks(result, expected):
    checks = {}
    campaigns = result["campaigns"]
    checks["selected_tool_versions_and_python_3148"] = result["python"].startswith("3.14.8 ") and result[
        "versions"
    ] == {"mutmut": "3.8.0", "trailmark": "0.5.0", "tree-sitter-language-pack": "1.21.0", "tree-sitter": "0.25.2"}
    checks["frozen_source_and_configuration"] = all(
        result[key] == hashlib.sha256(expected[name].encode()).hexdigest()
        for key, name in (("source_sha256", "SOURCE"), ("config_sha256", "CONFIG"))
    )
    raw = {}
    for name in ("weak", "strong"):
        campaign = campaigns[name]
        checks[f"{name}_unmodified_baseline_and_campaign_complete"] = (
            campaign["baseline"]["exit_code"] == campaign["run"]["exit_code"] == campaign["export"]["exit_code"] == 0
            and campaign["tests_sha256"] == hashlib.sha256(expected[name.upper()].encode()).hexdigest()
        )
        raw[name] = campaign["metadata"]["mutants/src/gate.py.meta"]["exit_code_by_key"]
        counts = Counter({0: "survived", 1: "killed", 33: "no_tests"}[status] for status in raw[name].values())
        stats = campaign["stats"]
        checks[f"{name}_complete_status_denominator"] = (
            stats["total"] == len(raw[name]) == 6
            and sum(value for key, value in stats.items() if key != "total") == 6
            and all(stats[key] == counts.get(key, 0) for key in ("killed", "survived", "no_tests"))
            and all(
                stats[key] == 0
                for key in ("skipped", "suspicious", "timeout", "check_was_interrupted_by_user", "segfault")
            )
        )
        cli_results = dict(re.findall(r"^\s*(\S+): (.+)$", campaign["results"]["stdout"], re.M))
        checks[f"{name}_raw_outcomes_agree_with_results_command"] = campaign["results"][
            "exit_code"
        ] == 0 and cli_results == {
            key: {0: "survived", 1: "killed", 33: "no tests"}[status] for key, status in raw[name].items()
        }
    checks["identical_generated_mutant_ids_and_function_hashes"] = (
        set(raw["weak"]) == set(raw["strong"])
        and campaigns["weak"]["metadata"]["mutants/src/gate.py.meta"]["hash_by_function_name"]
        == campaigns["strong"]["metadata"]["mutants/src/gate.py.meta"]["hash_by_function_name"]
    )
    boundary = "gate.x_eligible__mutmut_1"
    checks["boundary_assertion_kills_previous_survivor"] = raw["weak"][boundary] == 0 and raw["strong"][boundary] == 1
    checks["five_untested_mutants_retained_in_both_campaigns"] = all(
        {key for key, value in raw[name].items() if value == 33}
        == {f"gate.x_public_entrypoint__mutmut_{number}" for number in range(1, 6)}
        for name in ("weak", "strong")
    )
    for index, token in enumerate(("--paths-to-mutate", "--runner", "junitxml")):
        interface = campaigns["weak"]["interfaces"][index]
        checks[f"legacy_{token}_is_rejected_by_released_cli"] = (
            interface["exit_code"] == 2 and token in interface["stderr"]
        )
    trailmark = campaigns["weak"]["trailmark"]
    checks["offline_python_grammar_parses_campaign_source"] = (
        trailmark["exit_code"] == 0 and json.loads(trailmark["stdout"])["summary"]["functions"] == 2
    )
    return checks


def graph_checks(result, expected):
    checks = {
        "graph_fixture_source_frozen": result["source_sha256"]
        == hashlib.sha256(expected["SOURCE"].encode()).hexdigest(),
        "graph_preanalysis_and_local_call_resolve": result["preanalysis_completed"] is True
        and len(result["callers"]["helper"]) == 1
        and result["library_internal_call_result"] == 42,
        "zero_static_callers_does_not_prevent_external_invocation": result["callers"]["externally_called"] == []
        and result["external_invocation_result"] == 42,
        "original_triage_dismisses_externally_invoked_and_unmapped_cases": {
            row["mutant_id"] for row in result["original_batch_triage"]["false_positives"]
        }
        == {"external-return-change", "unmapped"},
        "original_ambiguous_mapping_changes_with_insertion_order": [
            row["id"] for row in result["original_ambiguous_choices"]
        ]
        == ["a", "b"],
        "original_test_substring_filter_excludes_production_contest_path": result[
            "original_production_substring_exclusion"
        ]
        is None,
        "original_merge_shares_removal_with_only_first_mutant": [
            row["mutation"]["mutant_id"] for row in result["original_many_mutations_one_removal_merge"]["corroborated"]
        ]
        == ["one"]
        and [row["mutant_id"] for row in result["original_many_mutations_one_removal_merge"]["missing_tests"]]
        == ["two"],
    }
    cases = result["generic_montgomery_bijection_cases"]
    checks["nontrivial_montgomery_inverse_mapping_and_shared_limb_cases"] = len(cases) == 2 and all(
        case["modulus"] in (19, 65521)
        and case["radix"] % case["modulus"] != 1
        and case["canonical_inputs"][0] != case["canonical_inputs"][1]
        and all(0 <= value < case["modulus"] for value in case["canonical_inputs"])
        and [value * case["radix"] % case["modulus"] for value in case["canonical_inputs"]]
        == case["internal_residues"]
        == [1, 2]
        and not all(a == b for a, b in zip(*case["limbs"], strict=True))
        and any(a == b for a, b in zip(*case["limbs"], strict=True))
        for case in cases
    )
    checks["generic_math_does_not_claim_case_study_library_execution"] = (
        result["case_study_rust_library_executed"] is False
    )
    return checks


def main(argv=None):
    from isolated_python import run_isolated

    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists")
    preparation = json.loads(args.image_receipt.read_bytes())
    if preparation.get("passed") is not True or preparation.get("languages_provisioned") != ["python"]:
        raise ValueError("exact offline Python parser image is not qualified")
    paths = [
        Path(__file__),
        Path(__file__).with_name("mutation_campaign_fixture.py"),
        Path(__file__).with_name("mutation_graph_fixture.py"),
        ROOT / "tools/isolated_python.py",
        ROOT
        / "included/skills/by-category/testing-qa-benchmarking/security-reference/genotoxic/references/graph-analysis.md",
    ]
    hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    executions = {}
    checks = {}
    for name, profile in (("campaign", "python-mutation"), ("graph", "python-small")):
        fixture = Path(__file__).with_name(f"mutation_{name}_fixture.py")
        with tempfile.TemporaryDirectory(prefix="mutation-tool-controls-") as directory:
            stage = Path(directory)
            shutil.copyfile(fixture, stage / "candidate.py")
            names = ["candidate.py"]
            if name == "graph":
                shutil.copyfile(paths[-1], stage / "original-graph-analysis.md")
                names.append("original-graph-analysis.md")
            execution = run_isolated(
                stage, names, {}, image=preparation["image"], profile=profile, timeout=180, output_limit=1024 * 1024
            )
        executions[name] = execution
        checks[f"{name}_bounded_inspection_execution_and_cleanup"] = bool(
            validate_invocation(execution, preparation["image"], profile)
        )
        if checks[f"{name}_bounded_inspection_execution_and_cleanup"]:
            result = execution["candidate_response"]["result"]
            try:
                checks.update(
                    campaign_checks(result, literals(fixture, {"SOURCE", "CONFIG", "WEAK", "STRONG"}))
                    if name == "campaign"
                    else graph_checks(result, literals(fixture, {"SOURCE"}))
                )
            except (KeyError, TypeError, ValueError) as error:
                checks[f"{name}_result_contract"] = False
                execution["validation_error"] = str(error)[:2048]
    if checks.get("campaign_bounded_inspection_execution_and_cleanup"):
        forged = copy.deepcopy(executions["campaign"]["candidate_response"]["result"])
        forged["campaigns"]["strong"]["stats"]["total"] = 1
        expected = literals(paths[1], {"SOURCE", "CONFIG", "WEAK", "STRONG"})
        checks["incomplete_denominator_is_rejected"] = not all(campaign_checks(forged, expected).values())
        forged_execution = copy.deepcopy(executions["campaign"])
        forged_execution["cleanup_verified"] = False
        checks["unverified_cleanup_is_rejected"] = not validate_invocation(
            forged_execution, preparation["image"], "python-mutation"
        )
    if any(
        hashlib.sha256(path.read_bytes()).hexdigest() != hashes[path.relative_to(ROOT).as_posix()] for path in paths
    ):
        raise ValueError("source changed during qualification")
    receipt = {
        "schema_version": 1,
        "evidence_class": "selected-tool-runtime-and-source-example-controls-not-skill-benchmark",
        "passed": all(checks.values()),
        "checks": checks,
        "source_sha256": hashes,
        "provider_preparation_sha256": hashlib.sha256(args.image_receipt.read_bytes()).hexdigest(),
        "executions": executions,
        "agent_efficacy_scored": False,
        "skill_runtime_benchmark_passes": 0,
        "untested_mutants_are_not_passes": True,
        "other_languages_qualified": False,
    }
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            {
                "passed": receipt["passed"],
                "checks": len(checks),
                "failed_checks": [name for name, passed in checks.items() if not passed],
            }
        )
    )
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Bind wrapper repair claims to source provenance and actual native outcomes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_catalog import sha256_file

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / (
    "included/repaired/skills/by-category/coding-refactoring-repository-automation/"
    "latest-release-devops/makefile-generator-project-wrappers"
)
EVIDENCE = ROOT / "artifacts/research/2026-11-13/makefile-project-wrappers"


def test_project_wrapper_repair_retains_complete_source_and_evidence() -> None:
    repair = json.loads((PACKAGE / "repair.json").read_bytes())
    source = ROOT / repair["source_mirror"]
    assert sha256_file(source / "SKILL.md") == repair["original_skill_sha256"]
    assert sha256_file(PACKAGE / repair["provenance_skill"]) == repair["original_skill_sha256"]
    for path in (source / "scripts/generate_makefile_template.sh", PACKAGE / "provenance/original.generate.sh"):
        assert sha256_file(path) == repair["original_generator_sha256"]
    actual_package = {
        path.relative_to(PACKAGE).as_posix(): sha256_file(path)
        for path in PACKAGE.rglob("*")
        if path.is_file() and path.name != "repair.json"
    }
    assert actual_package == repair["overlay_sha256"]
    actual_evidence = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in EVIDENCE.iterdir()
        if path.is_file() and path.name != "review.json"
    }
    review = json.loads((EVIDENCE / "review.json").read_bytes())
    assert actual_evidence == repair["evidence_sha256"] == review["artifacts"]
    assert (
        hashlib.sha256((PACKAGE / "repair.json").read_bytes()).hexdigest()
        == review["maintained_repair"]["repair_manifest_sha256"]
    )
    assert repair["readiness_status"] == "component_controls_only"
    assert repair["model_performance_claim"] is False
    assert review["agent_efficacy_established"] is False and review["model_invocations"] == 0
    assert review["whole_skill_complete"] is False and review["whole_package_readiness"] is False
    counts = {}
    for name in review["native_cases"]:
        result = json.loads((EVIDENCE / name).read_bytes())
        observation = result["observation"]
        assert observation["passed"] and result["lease_closed"] and result["remaining_owned_containers"] == 0
        cases = observation["cases"]
        assert len(cases) == len({row["case"] for row in cases})
        counts[name] = len(cases)
        control = EVIDENCE / (name.removesuffix("-result.json") + "-control.py.txt")
        assert hashlib.sha256(control.read_bytes()).hexdigest() == result["program_sha256"]
    assert counts == review["native_cases"] and sum(counts.values()) == review["total_component_cases"]


def test_python_repair_keeps_real_build_tests_and_resolved_environment() -> None:
    observation = json.loads((EVIDENCE / "python-result.json").read_bytes())["observation"]
    cases = {row["case"]: row for row in observation["cases"]}
    assert cases["hash-locked-fresh-reinstall"]["packages_equal"] is True
    assert cases["system-interpreter-unchanged"]["packages_equal"] is True
    assert cases["original-build-produces-wheel-and-sdist"]["wheel_present"] is True
    assert cases["original-build-produces-wheel-and-sdist"]["source_present"] is True
    assert cases["original-development-install-isolated"]["project_installed"] is True
    assert cases["original-real-test-passes"]["exit_code"] == 0
    assert cases["original-real-test-failure-propagates"]["exit_code"] != 0
    assert cases["original-default-formatter-compatibility-observed"]["wrapper_exit"] == 0
    assert cases["original-default-formatter-compatibility-observed"]["black_check_exit"] == 1
    for name in ("black_check_exit", "isort_check_exit"):
        assert cases["explicit-project-formatter-policy-agrees"][name] == 0
    setup = json.loads((EVIDENCE / "setup.json").read_bytes())
    assert setup["python_resolved_versions"] == observation["installed_versions"]
    assert setup["python_hash_lock"] == observation["locked_requirements"]
    assert setup["global_installation"] is False and setup["sdk_host_extraction"] is False


def test_java_repair_keeps_stale_class_abi_and_actual_discovery_controls() -> None:
    result = json.loads((EVIDENCE / "java-result.json").read_bytes())
    cases = {row["case"]: row for row in result["observation"]["cases"]}
    assert cases["wrong-sdk-digest-rejected-before-execution"]["rejected"] is True
    assert cases["sdk-transfer-digest-admitted"]["sha256"] == result["sdk_sha256"]
    assert cases["original-removed-source-retains-class"]["obsolete_class_retained"] is True
    assert cases["fresh-native-output-excludes-removed-source"]["obsolete_class_retained"] is False
    assert cases["original-changed-abi-build-reports-success"]["exit_code"] == 0
    assert cases["original-changed-abi-runtime-fails"]["exit_code"] != 0
    assert cases["fresh-native-compiler-rejects-changed-abi"]["exit_code"] != 0
    assert cases["original-failing-test-not-discovered"]["actual_tests_run"] == 0
    assert cases["original-failing-test-not-discovered"]["exit_code"] == 0
    for name in ("explicit-junit4-class-failure", "current-console-propagates-actual-failure"):
        assert cases[name]["exit_code"] != 0
    assert cases["current-console-executes-passing-test"]["exit_code"] == 0
    assert cases["current-console-rejects-zero-tests"]["exit_code"] == 2


def test_project_wrapper_cleanup_and_configuration_do_not_claim_placeholder_success() -> None:
    original = json.loads((EVIDENCE / "original-scope-result.json").read_bytes())["observation"]
    cases = {row["case"]: row for row in original["cases"]}
    assert cases["python-clean-crosses-environment-boundary"]["nested_dependency_cache_removed"] is True
    for name in ("generic-build-placeholder", "generic-test-placeholder"):
        assert cases[name]["exit_code"] == 0 and cases[name]["actual_build_or_test_established"] is False
    observation = json.loads((EVIDENCE / "wrapper-result.json").read_bytes())["observation"]
    cases = {row["case"]: row for row in observation["cases"]}
    assert cases["declared-cleanup-preserves-dependencies-and-sibling"]["owned_outputs_removed"] is True
    assert cases["declared-cleanup-preserves-dependencies-and-sibling"]["retained_bytes_equal"] is True
    for name in ("unconfigured-build-fails", "unconfigured-test-fails", "configured-test-propagates-real-failure"):
        assert cases[name]["exit_code"] != 0
    for name in ("configured-build-produces-real-output", "configured-test-executes-real-passing-assertion"):
        assert cases[name]["exit_code"] == 0

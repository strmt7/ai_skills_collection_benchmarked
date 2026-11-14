"""Keep the Go instruction repair bound to its source and native observations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_catalog import sha256_file

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    ROOT
    / "included/repaired/skills/by-category/coding-refactoring-repository-automation/latest-release-devops/makefile-generator-go"
)
EVIDENCE = ROOT / "artifacts/research/2026-11-13/makefile-go"


def test_go_repair_preserves_source_and_complete_evidence_bindings() -> None:
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
    assert actual_evidence == repair["evidence_sha256"]
    review = json.loads((EVIDENCE / "review.json").read_bytes())
    assert review["artifacts"] == actual_evidence
    assert (
        review["maintained_repair"]["repair_manifest_sha256"]
        == hashlib.sha256((PACKAGE / "repair.json").read_bytes()).hexdigest()
    )
    assert repair["model_performance_claim"] is False
    assert review["agent_efficacy_established"] is False and review["model_invocations"] == 0
    assert repair["readiness_status"] == "component_controls_only" and review["whole_skill_complete"] is False


def test_go_repair_keeps_staleness_failure_and_sound_test_controls() -> None:
    result = json.loads((EVIDENCE / "result.json").read_bytes())
    observation = result["observation"]
    cases = {item["case"]: item for item in observation["cases"]}
    assert len(cases) == len(observation["cases"])
    review = json.loads((EVIDENCE / "review.json").read_bytes())
    assert review["go_native_cases"] == len(cases)
    sdk = json.loads((EVIDENCE / "sdk-capture.json").read_bytes())["capture"]
    assert result["sdk_sha256"] == sdk["sha256"]
    assert observation["go_version"] == f"go version {sdk['version']} linux/amd64"
    assert cases["wrong-sdk-digest-rejected-before-execution"]["rejected"] is True
    assert cases["original-embedded-resource-change"]["old_binary_retained"] is True
    assert cases["original-embedded-resource-change"]["output"] == "initial|dev"
    assert cases["maintained-embedded-resource-change"]["old_binary_retained"] is False
    assert cases["maintained-embedded-resource-change"]["output"] == "updated|dev"
    assert cases["native-go-recognizes-resource-change"]["exit_code"] == 0
    assert cases["original-missing-required-resource"]["exit_code"] == 0
    assert cases["maintained-missing-required-resource"]["exit_code"] != 0
    for kind in ("original", "maintained"):
        assert cases[f"{kind}-actual-test-passes"]["exit_code"] == 0
        assert cases[f"{kind}-actual-test-failure-propagates"]["exit_code"] != 0
        assert cases[f"{kind}-initial-no-external-dependencies"]["go_sum_present"] is False
    records = observation["records"]
    assert any(row["exit_code"] != 0 and "no matching files found" in row["stderr"] for row in records)
    assert any(row["exit_code"] != 0 and "controlled test failure" in row["stdout"] for row in records)
    assert result["lease_closed"] is True and result["remaining_owned_containers"] == 0

"""Verify the Python inventory overlay and its recorded qualification."""

import hashlib
import json

from helpers import ROOT

OVERLAY = ROOT / (
    "included/repaired/skills/by-category/documents-spreadsheets-presentations/"
    "reddit-verified-gtm-registry/docs-from-code-python-inventory"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/docs-from-code-python-inventory-v1"
MIRROR = ROOT / (
    "included/skills/by-category/documents-spreadsheets-presentations/reddit-verified-gtm-registry/docs-from-code"
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(path):
    return path.read_bytes().replace(b"\r\n", b"\n")


def test_overlay_preserves_upstream_and_binds_evidence():
    repair = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert (OVERLAY / "provenance/original.SKILL.md").read_bytes() == canonical(MIRROR / "SKILL.md")
    assert (OVERLAY / "provenance/upstream.README.md").read_bytes() == canonical(MIRROR / "README.md")
    assert repair["original_skill_sha256"] == digest(OVERLAY / "provenance/original.SKILL.md")
    assert repair["model_performance_claim"] is False
    for path, expected in repair["overlay_sha256"].items():
        assert digest(OVERLAY / path) == expected, path
    for path, expected in repair["evidence_sha256"].items():
        assert digest(EVIDENCE / path) == expected, path


def test_recorded_runs_bind_inputs_and_keep_scope_explicit():
    qualification = json.loads((EVIDENCE / "qualification.json").read_text(encoding="utf-8"))
    cases = json.loads((EVIDENCE / "cases.json").read_text(encoding="utf-8"))["cases"]
    assert len(cases) == len(set(cases)) == qualification["cases"] == 25
    assert "test_prior_independent_five_case_controls" in cases
    assert "test_selected_candidates_agree_with_real_framework_route_tables" in cases
    assert len(qualification["runs"]) == 5
    for entry in qualification["runs"]:
        path = EVIDENCE / f"{entry['name']}-result.json"
        assert digest(path) == entry["result_sha256"]
        result = json.loads(path.read_text(encoding="utf-8"))
        assert result["status"] == "passed"
        assert result["platform"] == entry["platform"]
        assert result["python"] == entry["python"]
        assert result["test_cases"] == 25
        assert result["passed_cases"] == entry["passed"]
        assert result["skipped_cases"] == entry["skipped"]
        assert not result["failed_cases"] and not result["error_cases"]
        for name, expected in result["inputs_sha256"].items():
            assert digest(ROOT / name) == expected, name
        assert result["target_project_imported_by_inventory"] is False
        assert result["owned_runtime_fixture_executed"] is True
        assert result["graphify_executed"] is False
        assert result["typescript_fallback_tested"] is False
        assert result["agent_performance_tested"] is False

"""Verify the JavaScript inventory overlay and recorded control evidence."""

import hashlib
import json
import re

from helpers import ROOT

OVERLAY = ROOT / (
    "included/repaired/skills/by-category/documents-spreadsheets-presentations/"
    "reddit-verified-gtm-registry/docs-from-code-js-inventory"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/docs-from-code-js-inventory-v1"
MIRROR = ROOT / (
    "included/skills/by-category/documents-spreadsheets-presentations/reddit-verified-gtm-registry/docs-from-code"
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_overlay_preserves_upstream_and_binds_evidence():
    repair = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert (OVERLAY / "provenance/original.SKILL.md").read_bytes() == (MIRROR / "SKILL.md").read_bytes().replace(
        b"\r\n", b"\n"
    )
    assert (OVERLAY / "provenance/upstream.README.md").read_bytes() == (MIRROR / "README.md").read_bytes().replace(
        b"\r\n", b"\n"
    )
    assert repair["original_skill_sha256"] == digest(OVERLAY / "provenance/original.SKILL.md")
    assert repair["model_performance_claim"] is False
    assert set(repair["overlay_sha256"]) == {
        "SKILL.md",
        "scripts/inventory.mjs",
        "scripts/package.json",
        "scripts/package-lock.json",
        "provenance/original.SKILL.md",
        "provenance/upstream.README.md",
    }
    assert set(repair["evidence_sha256"]) == {
        "inventory.test.mjs",
        "next-live.mjs",
        "package.json",
        "package-lock.json",
        "reproduce.py",
        "qualification.json",
        "sources.json",
        "windows-node24-result.json",
        "linux-node24-result.json",
        "raw/windows-node24.tap",
        "raw/linux-node24.tap",
    }
    for path, expected in repair["overlay_sha256"].items():
        assert digest(OVERLAY / path) == expected, path
    for path, expected in repair["evidence_sha256"].items():
        assert digest(EVIDENCE / path) == expected, path


def test_recorded_runs_bind_inputs_and_keep_scope_explicit():
    qualification = json.loads((EVIDENCE / "qualification.json").read_text(encoding="utf-8"))
    assert qualification["cases"] == 7
    assert qualification["agent_performance_tested"] is False
    assert {run["platform"] for run in qualification["runs"]} == {"Windows", "Linux"}
    for run in qualification["runs"]:
        result_path = EVIDENCE / f"{run['name']}-result.json"
        tap_path = EVIDENCE / "raw" / f"{run['name']}.tap"
        assert digest(result_path) == run["result_sha256"]
        assert digest(tap_path) == run["tap_sha256"]
        result = json.loads(result_path.read_text(encoding="utf-8"))
        assert result["status"] == "passed"
        assert result["platform"] == run["platform"] and result["node"] == run["node"]
        assert result["minimal_runtime_install_and_cli_passed"] is True
        assert result["owned_express_and_next_fixtures_executed"] is True
        assert result["target_project_imported_by_inventory"] is False
        assert result["agent_performance_tested"] is False
        tap = tap_path.read_text(encoding="utf-8")
        assert re.findall(r"^ok \d+ - (.+)$", tap, flags=re.MULTILINE) == result["case_names"]
        assert len(result["case_names"]) == len(set(result["case_names"])) == result["cases"] == 7
        assert "# fail 0" in tap and "# skipped 0" in tap
        for path, expected in result["inputs_sha256"].items():
            assert digest(ROOT / path) == expected, path

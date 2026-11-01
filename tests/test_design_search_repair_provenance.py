"""Verify the repaired search's source binding without executing an agent."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design"
REPAIR = (
    ROOT
    / "included/repaired/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/design-local-search-v1/qualification.json"
SOURCE_MANIFEST = ROOT / "artifacts/research/2026-11-01/design-search/source-manifest.json"


def canonical(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(canonical(path)).hexdigest()


def test_source_data_and_original_skill_are_preserved() -> None:
    repair = json.loads((REPAIR / "repair.json").read_text(encoding="utf-8"))
    source = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    assert repair["source_commit"] == source["source_commit"]
    assert repair["source_skill_id"] == source["skill_id"]
    assert canonical(REPAIR / repair["provenance_skill"]) == canonical(SOURCE / "SKILL.md")
    assert sha256(SOURCE / "SKILL.md") == repair["original_skill_sha256"] == source["files"]["SKILL.md"]
    assert set(repair["data_sha256"]) == {path for path in source["files"] if path.startswith("data/")}
    for path, expected in repair["data_sha256"].items():
        assert canonical(REPAIR / path) == canonical(SOURCE / path)
        assert sha256(SOURCE / path) == expected == source["files"][path]


def test_qualification_binds_current_repair() -> None:
    repair = json.loads((REPAIR / "repair.json").read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert sha256(REPAIR / "SKILL.md") == repair["repaired_skill_sha256"]
    assert sha256(REPAIR / "scripts/search.py") == repair["repaired_script_sha256"] == evidence["repair_script_sha256"]
    assert sha256(REPAIR / "test_search_contract.py") == evidence["synthetic_control_script_sha256"]
    assert sha256(REPAIR / "test_search_data.py") == evidence["bundled_data_control_script_sha256"]
    assert sha256(REPAIR / repair["license_file"]) == repair["license_sha256"]
    assert evidence["source_commit"] == repair["source_commit"]
    assert evidence["agent_efficacy_scored"] is False
    assert repair["model_performance_claim"] is False
    assert (ROOT / repair["readiness_evidence"]).resolve() == EVIDENCE.resolve()

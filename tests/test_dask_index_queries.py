"""Check Dask index repair evidence and locked-source provenance."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/dask-index-queries"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/dask-index-queries-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_qualified_dask_examples_bind_to_original_and_both_platforms():
    repair = json.loads((OVERLAY / "repair.json").read_bytes())
    source = ROOT / repair["source_mirror"]
    for original, reference in (
        ("original.SKILL.md", "SKILL.md"),
        ("original.dataframes.md", "references/dataframes.md"),
    ):
        assert (OVERLAY / "provenance" / original).read_bytes() == (source / reference).read_bytes().replace(
            b"\r\n", b"\n"
        )
    for base, key in ((OVERLAY, "overlay_sha256"), (EVIDENCE, "evidence_sha256")):
        actual = {
            p.relative_to(base).as_posix(): sha(p)
            for p in base.rglob("*")
            if p.is_file() and p.name != "repair.json" and "__pycache__" not in p.parts
        }
        assert repair[key] == actual
    qualification = json.loads((EVIDENCE / "qualification.json").read_bytes())
    assert qualification["skill_sha256"] == sha(OVERLAY / "SKILL.md")
    assert qualification["runner_sha256"] == sha(EVIDENCE / "reproduce.py")
    assert set(qualification["results"]) == {"windows-result.json", "linux-result.json"}
    expected_checks = {
        "overlapping_unsorted",
        "already_sorted",
        "duplicate_labels",
        "empty_range",
        "invalid_presorted_input_rejected_by_lookup",
    }
    for filename, digest in qualification["results"].items():
        result_path = EVIDENCE / filename
        result = json.loads(result_path.read_bytes())
        assert sha(result_path) == digest
        assert result["platform"].lower() == filename.removesuffix("-result.json")
        assert result["dask"] == "2026.8.0"
        assert result["pandas"] == "3.1.0"
        assert result["skill_sha256"] == qualification["skill_sha256"]
        assert set(result["checks"]) == expected_checks
        assert result["agent_performance_tested"] is False
        assert result["full_skill_reviewed"] is False


def test_dask_revision_ledger_points_to_unchanged_repair_manifest():
    ledger = json.loads((ROOT / "data/improvement_ledger.json").read_bytes())
    skill = ledger["skills"]["k-dense-ai-scientific-agent-skills-scientific-skills-dask-skill-md"]
    repair = OVERLAY / "repair.json"
    assert any(
        item["path"] == repair.relative_to(ROOT).as_posix() and item["sha256"] == sha(repair)
        for item in skill["revision"]["evidence"]
    )

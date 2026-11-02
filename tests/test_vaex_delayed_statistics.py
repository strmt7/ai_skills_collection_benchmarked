"""Check selected Vaex statistics evidence and locked-source provenance."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/vaex-delayed-statistics"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/vaex-delayed-statistics-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_qualified_vaex_examples_bind_to_original_and_both_platforms():
    repair = json.loads((OVERLAY / "repair.json").read_bytes())
    source = ROOT / repair["source_mirror"]
    for original, reference in (
        ("original.SKILL.md", "SKILL.md"),
        ("original.performance.md", "references/performance.md"),
        ("original.io_operations.md", "references/io_operations.md"),
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
    assert qualification["source_distribution"]["declared_license"] == "UNKNOWN"
    assert qualification["source_distribution"]["locally_built_wheel_distributed"] is False
    expected = {
        "original_mean_executes_at_call",
        "assignment_does_not_trigger_execution",
        "csv_uses_lazy_dataset",
        "delayed_statistics_resolve_correctly",
        "delayed_statistics_share_observed_pass",
    }
    for filename, digest in qualification["results"].items():
        result_path = EVIDENCE / filename
        result = json.loads(result_path.read_bytes())
        assert sha(result_path) == digest
        assert result["platform"].lower() == filename.removesuffix("-result.json")
        assert result["vaex_core"] == "4.19.0"
        assert result["dask"] == "2024.8.2"
        assert result["skill_sha256"] == qualification["skill_sha256"]
        assert set(result["checks"]) == expected
        assert result["agent_performance_tested"] is False
        assert result["full_skill_reviewed"] is False


def test_vaex_ledger_binds_review_and_repair_evidence():
    ledger = json.loads((ROOT / "data/improvement_ledger.json").read_bytes())
    skill = ledger["skills"]["k-dense-ai-scientific-agent-skills-scientific-skills-vaex-skill-md"]
    for phase, path in (("research", EVIDENCE / "qualification.json"), ("revision", OVERLAY / "repair.json")):
        assert any(
            item["path"] == path.relative_to(ROOT).as_posix() and item["sha256"] == sha(path)
            for item in skill[phase]["evidence"]
        )

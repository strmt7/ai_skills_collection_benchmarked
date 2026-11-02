"""Check FlowIO repair evidence and source-bound resource review."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/flowio-fcs-basics"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/flowio-fcs-basics-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_qualified_flowio_examples_bind_sources_and_both_platforms():
    repair = json.loads((OVERLAY / "repair.json").read_bytes())
    source = ROOT / repair["source_mirror"]
    for original, reference in (
        ("original.SKILL.md", "SKILL.md"),
        ("original.api_reference.md", "references/api_reference.md"),
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
    assert qualification["fixture_fetcher_sha256"] == sha(EVIDENCE / "fetch_fixture.py")
    assert set(qualification["results"]) == {"windows-result.json", "linux-result.json"}
    assert qualification["tutorial_fixture"]["distributed_in_repository"] is False
    assert qualification["tutorial_fixture"]["data_use_terms_verified"] is False
    for filename, digest in qualification["results"].items():
        result_path = EVIDENCE / filename
        result = json.loads(result_path.read_bytes())
        assert sha(result_path) == digest
        assert result["platform"].lower() == filename.removesuffix("-result.json")
        assert result["flowio"] == "1.4.0" and result["numpy"] == "2.5.4"
        assert result["skill_sha256"] == qualification["skill_sha256"]
        assert result["fixture_sha256"] == qualification["tutorial_fixture"]["sha256"]
        assert len(set(result["checks"])) == 10
        assert result["agent_performance_tested"] is False
        assert result["full_skill_reviewed"] is False


def test_flowio_ledger_records_review_scope_and_repair_evidence():
    ledger = json.loads((ROOT / "data/improvement_ledger.json").read_bytes())
    skill = ledger["skills"]["k-dense-ai-scientific-agent-skills-scientific-skills-flowio-skill-md"]
    for phase, path in (("research", EVIDENCE / "qualification.json"), ("revision", OVERLAY / "repair.json")):
        assert any(
            item["path"] == path.relative_to(ROOT).as_posix() and item["sha256"] == sha(path)
            for item in skill[phase]["evidence"]
        )
    for resource_path in ("SKILL.md", "references/api_reference.md"):
        resource = skill["research"]["resources"][resource_path]
        assert resource["status"] == "reviewed"
        assert "remain untested" in resource["review_scope"]

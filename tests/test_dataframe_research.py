"""Check the scope and source binding of selected dataframe controls."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/polars-lazy-queries"
)
QUALIFICATION = ROOT / "artifacts/repaired-skill-readiness/polars-lazy-queries-v1"
RESEARCH = ROOT / "artifacts/research/2026-11-02/dataframe-research-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_polars_overlay_preserves_locked_sources_and_qualified_results():
    repair = json.loads((OVERLAY / "repair.json").read_bytes())
    source = ROOT / repair["source_mirror"]
    for original, reference in (
        ("original.SKILL.md", "SKILL.md"),
        ("original.best_practices.md", "references/best_practices.md"),
        ("original.io_guide.md", "references/io_guide.md"),
    ):
        assert (OVERLAY / "provenance" / original).read_bytes() == (source / reference).read_bytes().replace(
            b"\r\n", b"\n"
        )
    for root, key in ((OVERLAY, "overlay_sha256"), (QUALIFICATION, "evidence_sha256")):
        actual = {
            p.relative_to(root).as_posix(): sha(p)
            for p in root.rglob("*")
            if p.is_file() and p.name != "repair.json" and "__pycache__" not in p.parts
        }
        assert repair[key] == actual
    qualified = json.loads((QUALIFICATION / "qualification.json").read_bytes())
    assert qualified["skill_sha256"] == sha(OVERLAY / "SKILL.md")
    assert qualified["runner_sha256"] == sha(QUALIFICATION / "reproduce.py")
    for filename, digest in qualified["results"].items():
        result_path = QUALIFICATION / filename
        result = json.loads(result_path.read_bytes())
        assert sha(result_path) == digest
        assert result["platform"].lower() == filename.removesuffix("-result.json")
        assert result["polars"] == "2.1.0"
        assert result["skill_sha256"] == qualified["skill_sha256"]
        assert result["removed_argument_errors"] == {
            "dtypes": "ArgumentRemovedError",
            "streaming": "ArgumentRemovedError",
        }
        assert len(set(result["checks"])) == 5
        assert result["agent_performance_tested"] is False
        assert result["full_skill_reviewed"] is False


def test_cross_skill_review_binds_ledger_and_dask_observation():
    report_path = RESEARCH / "report.json"
    report = json.loads(report_path.read_bytes())
    ledger = json.loads((ROOT / "data/improvement_ledger.json").read_bytes())
    for name in ("polars", "dask", "vaex"):
        skill_id = f"k-dense-ai-scientific-agent-skills-scientific-skills-{name}-skill-md"
        skill = ledger["skills"][skill_id]
        assert skill["source_signature"] == report["source_signatures"][name]
        assert any(
            item["path"] == report_path.relative_to(ROOT).as_posix() and item["sha256"] == sha(report_path)
            for item in skill["research"]["evidence"]
        )
    dask = report["dask"]
    for name, key in (
        ("dask-probe.py", "probe_sha256"),
        ("requirements-windows.txt", "requirements_sha256"),
        ("dask-windows-result.json", "result_sha256"),
    ):
        assert sha(RESEARCH / name) == dask[key]
    result = json.loads((RESEARCH / "dask-windows-result.json").read_bytes())
    assert result["dask"] == "2026.8.0"
    assert result["incorrect_presorted_lookup_error"] == "ValueError"
    assert result["default_index_lookup"] == {"timestamp": 3, "value": 30}
    assert report["vaex"]["runtime_tested"] is False

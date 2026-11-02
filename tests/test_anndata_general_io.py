"""Check AnnData general-I/O evidence and source provenance."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/anndata-general-io"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/anndata-general-io-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_qualified_examples_bind_to_sources_and_environments():
    manifest = json.loads((OVERLAY / "repair.json").read_bytes())
    source = ROOT / manifest["source_mirror"]
    for original, mirror in (
        ("original.SKILL.md", "SKILL.md"),
        ("original.io_operations.md", "references/io_operations.md"),
    ):
        assert (OVERLAY / "provenance" / original).read_bytes() == (source / mirror).read_bytes().replace(
            b"\r\n", b"\n"
        )
    for base, key in ((OVERLAY, "overlay_sha256"), (EVIDENCE, "evidence_sha256")):
        actual = {
            p.relative_to(base).as_posix(): sha(p)
            for p in base.rglob("*")
            if p.is_file() and p.name != "repair.json" and "__pycache__" not in p.parts
        }
        assert manifest[key] == actual
    qualification = json.loads((EVIDENCE / "qualification.json").read_bytes())
    assert qualification["skill_sha256"] == sha(OVERLAY / "SKILL.md")
    assert qualification["runner_sha256"] == sha(EVIDENCE / "reproduce.py")
    assert all(sha(EVIDENCE / path) == expected for path, expected in qualification["requirements_sha256"].items())
    for system in ("windows", "linux"):
        filename = f"{system}-result.json"
        assert qualification["results"][filename] == sha(EVIDENCE / filename)
        result = json.loads((EVIDENCE / filename).read_bytes())
        assert result["platform"].lower() == system
        assert result["skill_sha256"] == qualification["skill_sha256"]
        assert result["python"] == qualification["python_version"]
        assert result["anndata"] == qualification["anndata_version"]
        assert len(set(result["checks"])) == 9
        assert set(result["full_collection_materialization_failures"]) == {"same_order", "reordered"}
        assert not result["agent_performance_tested"]

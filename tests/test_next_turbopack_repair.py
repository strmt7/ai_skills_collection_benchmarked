from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/repaired-skill-readiness/next-turbopack-v1"
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/coding-refactoring-repository-automation"
    / "selected-structure-reference/nextjs-turbopack"
)
MIRROR = (
    ROOT
    / "included/skills/by-category/coding-refactoring-repository-automation"
    / "selected-structure-reference/nextjs-turbopack/SKILL.md"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_overlay_preserves_original_and_binds_evidence() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert digest(OVERLAY / manifest["provenance_skill"]) == digest(MIRROR) == manifest["original_skill_sha256"]
    assert digest(OVERLAY / "SKILL.md") == manifest["repaired_skill_sha256"]
    assert digest(OVERLAY / manifest["license_file"]) == manifest["license_sha256"]
    assert manifest["model_performance_claim"] is False
    for name, expected in manifest["evidence_sha256"].items():
        assert digest(ARTIFACT / name) == expected, name


def test_component_observations_and_locked_versions() -> None:
    lock = json.loads((ARTIFACT / "fixture/package-lock.json").read_text(encoding="utf-8"))
    assert lock["packages"]["node_modules/next"]["version"] == "16.4.3"
    assert lock["packages"]["node_modules/react"]["version"] == "19.3.1"
    assert lock["packages"]["node_modules/react-dom"]["version"] == "19.3.1"
    for platform in ("windows", "linux"):
        data = json.loads((ARTIFACT / f"{platform}-result.json").read_text(encoding="utf-8"))
        assert (data["node"], data["npm"], data["next"]) == ("v26.13.0", "12.2.1", "Next.js v16.4.3")
        assert data["unsupported_exit"] == 1
        assert data["turbo_exit"] == data["webpack_exit"] == data["analyze_exit"] == 0
        assert data["expected_html"] and data["root_in_analyzer"]
        assert data["agent_efficacy_scored"] is False
        assert data["package_lock_sha256"] == digest(ARTIFACT / "fixture/package-lock.json")

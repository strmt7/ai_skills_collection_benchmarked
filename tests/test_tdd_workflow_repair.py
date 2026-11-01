"""Verify provenance and the observed Jest threshold control for the TDD overlay."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "included/skills/by-category/testing-qa-benchmarking/selected-structure-reference/tdd-workflow-everything-claude-code"
)
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/tdd-workflow-everything-claude-code"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/tdd-jest-v1"


def canonical(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def digest(path: Path) -> str:
    return hashlib.sha256(canonical(path)).hexdigest()


def threshold_example(path: Path, option: str) -> dict[str, Any]:
    blocks = re.findall(r"```json\s*\n(.*?)\n```", canonical(path).decode("utf-8"), re.S)
    matches = []
    for block in blocks:
        try:
            value = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get("jest"), dict) and option in value["jest"]:
            matches.append(value["jest"][option])
    assert len(matches) == 1
    return matches[0]


def test_provenance_and_corrected_configuration_match() -> None:
    repair = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert canonical(SOURCE / "SKILL.md") == canonical(OVERLAY / repair["provenance_skill"])
    assert digest(SOURCE / "SKILL.md") == repair["original_skill_sha256"]
    assert digest(OVERLAY / "SKILL.md") == repair["repaired_skill_sha256"]
    assert digest(OVERLAY / repair["license_file"]) == repair["license_sha256"]
    assert threshold_example(SOURCE / "SKILL.md", "coverageThresholds") == threshold_example(
        OVERLAY / "SKILL.md", "coverageThreshold"
    )
    for name, expected in repair["evidence_sha256"].items():
        assert digest(EVIDENCE / name) == expected
    assert repair["model_performance_claim"] is False


def test_real_jest_controls_bind_both_source_versions_and_platforms() -> None:
    repair = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    upstream = json.loads((EVIDENCE / "upstream-observation.json").read_text(encoding="utf-8"))
    for prefix, commit, source_hash in (
        ("", repair["source_commit"], repair["original_skill_sha256"]),
        ("upstream-", upstream["observed_main_commit"], upstream["source_sha256"]),
    ):
        for runtime in ("", "node26-"):
            observations = []
            for platform in ("windows", "linux"):
                result = json.loads((EVIDENCE / f"{prefix}{runtime}{platform}-result.json").read_text(encoding="utf-8"))
                assert result["source_commit"] == commit
                assert result["source_skill_sha256"] == source_hash
                assert result["overlay_skill_sha256"] == repair["repaired_skill_sha256"]
                assert result["jest_version"] == "30.5.2"
                if runtime:
                    assert result["node_version"] == "v26.13.0"
                assert result["agent_efficacy_scored"] is False
                observed = result["results"]
                assert observed["source_low"]["exit_code"] == 0
                assert observed["source_low"]["unknown_plural_warning"] is True
                assert observed["overlay_low"]["exit_code"] == 1
                assert observed["overlay_low"]["threshold_failure"] is True
                assert observed["overlay_full"]["exit_code"] == 0
                assert observed["overlay_full"]["coverage_percent"]["branches"] == 100
                assert observed["source_low"]["coverage_percent"]["branches"] == 50
                observations.append(observed)
            assert observations[0] == observations[1]

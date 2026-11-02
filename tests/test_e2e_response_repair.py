from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/repaired-skill-readiness/e2e-response-v1"
OVERLAY = ROOT / "included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/e2e-testing"
MIRROR = ROOT / "included/skills/by-category/testing-qa-benchmarking/selected-structure-reference/e2e-testing/SKILL.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_original_overlay_and_evidence_are_source_bound() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    original = OVERLAY / manifest["provenance_skill"]
    assert digest(original) == digest(MIRROR) == manifest["original_skill_sha256"]
    assert digest(OVERLAY / "SKILL.md") == manifest["repaired_skill_sha256"]
    assert digest(OVERLAY / manifest["license_file"]) == manifest["license_sha256"]
    assert manifest["model_performance_claim"] is False
    for name, expected in manifest["evidence_sha256"].items():
        assert digest(ARTIFACT / name) == expected, name


def test_recorded_controls_preserve_results_and_limit_claims() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    results = sorted(ARTIFACT.glob("*-windows.json")) + sorted(ARTIFACT.glob("*-linux.json"))
    assert len(results) == 7
    upstream = json.loads((ARTIFACT / "upstream-observation.json").read_text(encoding="utf-8"))
    for result in results:
        data = json.loads(result.read_text(encoding="utf-8"))
        assert data["overlay_sha256"] == manifest["repaired_skill_sha256"]
        source_hash = (
            upstream["normalized_sha256"] if result.name.startswith("upstream-") else manifest["original_skill_sha256"]
        )
        assert data["source_sha256"] == source_hash
        lock_platform = "windows" if data["platform"] == "win32" else "linux"
        assert data["lock_sha256"] == digest(ARTIFACT / "locks" / lock_platform / "package-lock.json")
        assert data["served"] == 31
        assert data["agent_efficacy_scored"] is False
        assert data["rejected_bad_status"] is True
        assert set(data["counts"]) == {"original", "ordering_only", "overlay"}
        assert all(item["passed"] + item["timed_out"] == 10 for item in data["counts"].values())
        assert data["counts"]["overlay"] == {"passed": 10, "timed_out": 0}


def test_control_rejects_unreviewed_overlay_before_loading_dependencies(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is not installed")
    with subprocess.Popen(
        [node, str(ARTIFACT / "control.cjs"), str(MIRROR), str(MIRROR), str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        try:
            _, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired as error:
            returncode_at_timeout = process.poll()
            error.add_note(f"Child return code at timeout: {returncode_at_timeout!r}")
            process.kill()
            process.communicate()
            raise
    assert process.returncode != 0
    assert "Source or overlay does not match the reviewed content" in stderr

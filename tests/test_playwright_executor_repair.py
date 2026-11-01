from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/repaired-skill-readiness/playwright-executor-v1"
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/testing-qa-benchmarking/latest-release-browser-automation/playwright-skill"
)
MIRROR = ROOT / "included/skills/by-category/testing-qa-benchmarking/latest-release-browser-automation/playwright-skill"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_overlay_and_provenance_match_the_declared_source() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert digest(OVERLAY / manifest["provenance_skill"]) == digest(MIRROR / "SKILL.md")
    assert digest(OVERLAY / "provenance/original.run.js") == digest(MIRROR / "run.js")
    assert digest(OVERLAY / "run.js") == manifest["repaired_executor_sha256"]
    assert manifest["model_performance_claim"] is False
    for name, expected in manifest["overlay_sha256"].items():
        assert digest(OVERLAY / name) == expected, name
    for name, expected in manifest["evidence_sha256"].items():
        assert digest(ARTIFACT / name) == expected, name


def test_component_evidence_records_both_runtimes_and_platforms() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    results = sorted(ARTIFACT.glob("node*.json"))
    assert len(results) == 4
    for path in results:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["original_sha256"] == manifest["original_executor_sha256"]
        assert data["repaired_sha256"] == manifest["repaired_executor_sha256"]
        assert data["package_lock_sha256"] == digest(OVERLAY / "package-lock.json")
        assert data["playwright"] == "1.64.1" and data["agent_efficacy_scored"] is False
        assert data["cases"]["direct"]["exit"] == 0 and data["cases"]["direct"]["fixture_ok"]
        assert data["cases"]["original"]["exit"] != 0 and data["cases"]["original"]["missing_fixture"]
        assert all(
            data["cases"][name]["exit"] == 0 and data["cases"][name]["fixture_ok"] for name in ("repaired", "inline")
        )
        assert data["playwright_without_node_path"] == {"exit": 0, "version": "1.64.1"}
        assert data["browser_smoke"] == {"exit": 0, "result": "control ready"}


def test_control_rejects_an_unrepaired_executor_before_installation(tmp_path: Path) -> None:
    scratch, output = tmp_path / "scratch", tmp_path / "output"
    result = subprocess.run(
        [
            sys.executable,
            str(ARTIFACT / "reproduce.py"),
            "--node",
            sys.executable,
            "--original",
            str(MIRROR),
            "--candidate",
            str(MIRROR),
            "--browsers",
            str(tmp_path),
            "--scratch",
            str(scratch),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    assert result.returncode != 0
    assert json.loads(result.stdout)["ok"] is False
    assert not scratch.exists() and not output.exists()

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from _native_shells import discover

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "included/skills/by-category/devops-cloud-operations/latest-release-devops/bash-script-generator"
OVERLAY = (
    ROOT / "included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/bash-script-generator"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/bash-generator-v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_repair_preserves_source_and_binds_the_observation() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert digest(SOURCE / "SKILL.md") == digest(OVERLAY / manifest["provenance_skill"])
    assert digest(SOURCE / "SKILL.md") == manifest["original_skill_sha256"]
    assert digest(OVERLAY / "SKILL.md") == manifest["repaired_skill_sha256"]
    assert digest(OVERLAY / manifest["license_file"]) == manifest["license_sha256"]
    assert manifest["model_performance_claim"] is False
    for name, expected in manifest["evidence_sha256"].items():
        assert digest(EVIDENCE / name) == expected

    recorded = json.loads((EVIDENCE / "windows.json").read_text(encoding="utf-8"))
    assert recorded["source_skill_sha256"] == manifest["original_skill_sha256"]
    assert recorded["source_ci_sha256"] == digest(SOURCE / "scripts/run_ci_checks.sh")
    assert recorded["source_template_sha256"] == digest(SOURCE / "assets/templates/standard-template.sh")
    assert recorded["overlay_skill_sha256"] == digest(OVERLAY / manifest["prior_repair_skill"])
    assert recorded["overlay_skill_sha256"] == manifest["prior_repair_sha256"]
    assert recorded["agent_efficacy_scored"] is False
    assert all(recorded["observations_match"].values())

    errexit = json.loads((EVIDENCE / "errexit-windows.json").read_text(encoding="utf-8"))
    assert errexit["source_guide_sha256"] == digest(SOURCE / "docs/bash-scripting-guide.md")
    assert errexit["overlay_skill_sha256"] == manifest["repaired_skill_sha256"]
    assert errexit["cases"]["pipeline"]["stderr"] == "right\nleft\n"
    assert all(errexit["observations_match"].values())
    assert errexit["agent_efficacy_scored"] is False


def installed_bash() -> Path:
    runtime = discover()
    if runtime is None:
        pytest.skip("Qualified native Bash is unavailable")
    return runtime.bash


def test_component_control_against_installed_shells() -> None:
    bash = installed_bash()
    runtime = discover()
    dash_path = runtime.dash if runtime is not None else None
    if not dash_path or not Path(dash_path).is_file():
        pytest.skip("dash is unavailable")
    dash = Path(dash_path)
    process = subprocess.run(
        [sys.executable, str(EVIDENCE / "control.py"), "--bash", str(bash), "--dash", str(dash)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=180,
    )
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["exit_codes"]["upstream_self_checks"] == 0
    assert result["exit_codes"]["invalid_output_bash_syntax"] != 0
    assert result["exit_codes"]["template_bash_syntax"] == 0
    assert result["exit_codes"]["template_dash_syntax"] != 0
    assert result["exit_codes"]["valid_output_dash_execution"] == 0


def test_errexit_and_pipeline_controls_against_installed_bash() -> None:
    bash = installed_bash()
    process = subprocess.run(
        [sys.executable, str(EVIDENCE / "errexit-control.py"), "--bash", str(bash)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["cases"]["standalone"]["exit_code"] != 0
    assert result["cases"]["conditional"]["stdout"] == "continued\nbranch\n"
    assert result["cases"]["explicit"]["stdout"] == "caught\n"
    assert result["cases"]["pipeline"]["stdout"] == "status=4\n"
    assert set(result["cases"]["pipeline"]["stderr"].splitlines()) == {"left", "right"}

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

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
    assert recorded["overlay_skill_sha256"] == manifest["repaired_skill_sha256"]
    assert recorded["agent_efficacy_scored"] is False
    assert all(recorded["observations_match"].values())


def test_component_control_against_installed_shells() -> None:
    if os.name == "nt":
        git = shutil.which("git")
        if not git:
            pytest.skip("Git for Windows is unavailable")
        git_home = Path(git).resolve().parent.parent
        bash, dash = git_home / "bin/bash.exe", git_home / "usr/bin/dash.exe"
    else:
        bash_path, dash_path = shutil.which("bash"), shutil.which("dash")
        if not bash_path or not dash_path:
            pytest.skip("Bash or dash is unavailable")
        bash, dash = Path(bash_path), Path(dash_path)
    if not bash.is_file() or not dash.is_file():
        pytest.skip("Bash or dash is unavailable")
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

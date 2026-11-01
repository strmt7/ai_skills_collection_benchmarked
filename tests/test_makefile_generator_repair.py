from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/repaired-skill-readiness/makefile-generator-c-v1"
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/coding-refactoring-repository-automation/latest-release-devops/makefile-generator-c"
)
MIRROR = (
    ROOT
    / "included/skills/by-category/coding-refactoring-repository-automation/latest-release-devops/makefile-generator"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_overlay_and_provenance_match_the_declared_source() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert digest(OVERLAY / manifest["provenance_skill"]) == digest(MIRROR / "SKILL.md")
    assert digest(OVERLAY / "provenance/original.generate.sh") == digest(
        MIRROR / "scripts/generate_makefile_template.sh"
    )
    assert manifest["model_performance_claim"] is False
    for name, expected in manifest["overlay_sha256"].items():
        assert digest(OVERLAY / name) == expected, name
    for name, expected in manifest["evidence_sha256"].items():
        assert digest(ARTIFACT / name) == expected, name


def test_recorded_controls_show_the_expected_compiler_and_link_behavior() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    data = json.loads((ARTIFACT / "result.json").read_text(encoding="utf-8"))
    assert data["source_sha256"] == manifest["original_generator_sha256"]
    assert data["agent_efficacy_scored"] is False
    assert data["make_version"] == "GNU Make 4.4.1"
    for name, value in data["repair_sha256"].items():
        assert digest(OVERLAY / name) == value
    old, new = data["results"]["original"], data["results"]["repaired"]
    assert old["cc_default"] == "cc|default" and new["cc_default"] == "gcc|file"
    for case in ("environment_cflags", "command_cflags"):
        assert old["link_cases"][case]["exit"] != 0 and old["link_cases"][case]["pic_error"]
        assert new["link_cases"][case]["exit"] == 0 and new["link_cases"][case]["shared_exists"]
    for case, marker in (("invalid_ldflags", "expected_invalid_flag"), ("missing_ldlibs", "expected_missing_library")):
        assert old["link_cases"][case]["exit"] == 0 and old["link_cases"][case]["shared_exists"]
        assert new["link_cases"][case]["exit"] != 0 and new["link_cases"][case][marker]


def test_control_rejects_wrong_source_before_creating_fixture(tmp_path: Path) -> None:
    scratch, output = tmp_path / "scratch", tmp_path / "output"
    result = subprocess.run(
        [
            sys.executable,
            str(ARTIFACT / "reproduce.py"),
            "--source",
            str(MIRROR / "SKILL.md"),
            "--repair",
            str(OVERLAY),
            "--make",
            sys.executable,
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

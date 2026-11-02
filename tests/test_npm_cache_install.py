"""Verify the npm repair's provenance and retained component observations."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/npm-cache-install"
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/npm-cache-install-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_repair_and_platform_observations_bind_exact_inputs() -> None:
    repair = json.loads((OVERLAY / "repair.json").read_bytes())
    mirror = ROOT / repair["source_mirror"]
    for source, original, key in (
        (mirror / "SKILL.md", OVERLAY / "provenance/original.SKILL.md", "original_skill_sha256"),
        (
            mirror / "examples/actions/setup-node-cached/action.yml",
            OVERLAY / "provenance/original-action.yml",
            "source_action_sha256",
        ),
    ):
        canonical = source.read_bytes().replace(b"\r\n", b"\n")
        assert original.read_bytes() == canonical
        assert hashlib.sha256(canonical).hexdigest() == repair[key]
    for directory, key in ((OVERLAY, "overlay_sha256"), (EVIDENCE, "evidence_sha256")):
        actual = {
            p.relative_to(directory).as_posix(): sha(p)
            for p in directory.rglob("*")
            if p.is_file() and p.name != "repair.json" and "__pycache__" not in p.parts
        }
        assert repair[key] == actual
    qualification = json.loads((EVIDENCE / "qualification.json").read_bytes())
    assert not qualification["agent_performance_tested"]
    assert not qualification["github_cache_service_tested_in_local_results"]
    assert qualification["runner_sha256"] == sha(EVIDENCE / "reproduce.py")
    assert qualification["github_fixture_sha256"] == sha(EVIDENCE / "github_fixture.py")
    fixtures = set()
    for filename, platform, node, npm in (
        ("windows-node26-npm12.json", "Windows", "v26.13.0", "12.2.1"),
        ("windows-node26-npm11.json", "Windows", "v26.13.0", "11.20.0"),
        ("linux-node24-npm11.json", "Linux", "v24.15.0", "11.12.1"),
    ):
        result_path = EVIDENCE / filename
        assert qualification["results"][filename] == sha(result_path)
        result = json.loads(result_path.read_bytes())
        assert (result["platform"], result["node_version"], result["npm_version"]) == (platform, node, npm)
        assert result["source_action_sha256"] == repair["source_action_sha256"]
        assert result["runner_sha256"] == qualification["runner_sha256"]
        assert result["overlay_sha256"] == sha(OVERLAY / "SKILL.md")
        assert result["example_sha256"] == sha(OVERLAY / "examples/npm-ci.yml")
        assert result["restored_cache_contains_package"]
        assert not result["fresh_workspace_had_node_modules"]
        assert result["original_cache_hit_missing_dependency"]
        assert result["maintained_offline_install_succeeded"]
        assert result["missing_and_mismatched_locks_rejected"]
        for key in ("original-hit-load", "missing-lock", "mismatched-lock"):
            assert result["logs"][key]["exit_code"] != 0
        for key in ("seed-install", "maintained-install", "maintained-load"):
            assert result["logs"][key]["exit_code"] == 0
        fixtures.add(result["fixture_tarball_sha256"])
    assert len(fixtures) == 1


def test_fixture_preparation_does_not_overwrite_existing_files(tmp_path: Path) -> None:
    sentinel = tmp_path / "package.json"
    sentinel.write_text("existing", encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(EVIDENCE / "github_fixture.py"),
            "prepare",
            "--workspace",
            str(tmp_path),
            "--run-id",
            "123",
            "--attempt",
            "1",
        ],
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0
    assert b"already contains a fixture path" in result.stderr
    assert sentinel.read_text(encoding="utf-8") == "existing"


def test_probe_rejects_non_hit_before_modifying_fixture(tmp_path: Path) -> None:
    sentinel = tmp_path / "fixture.tgz"
    sentinel.write_bytes(b"existing")
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(EVIDENCE / "github_fixture.py"),
            "probe",
            "--workspace",
            str(tmp_path),
            "--output",
            str(tmp_path / "out"),
            "--cache-hit",
            "false",
            "--mode",
            "source",
        ],
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0
    assert b"expected an exact GitHub Actions cache hit" in result.stderr
    assert sentinel.read_bytes() == b"existing"
    assert not (tmp_path / "out").exists()

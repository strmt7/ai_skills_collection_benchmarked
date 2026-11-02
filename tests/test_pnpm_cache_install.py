"""Verify the pnpm repair's provenance and component observations."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/pnpm-cache-install"
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/pnpm-cache-install-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_repair_and_observations_bind_exact_inputs() -> None:
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
    fixtures = set()
    for filename, system, node, binary in (
        (
            "windows-node26-pnpm12.json",
            "Windows",
            "v26.13.0",
            "da363262507ee4111efdc7f52f55e0404c2a833b258129b589571d6b3a804555",
        ),
        (
            "linux-node24-pnpm12.json",
            "Linux",
            "v24.15.0",
            "41fe8049fc73f4239b99487c35def4eacdb3cb18659a6003573500e3cc313628",
        ),
    ):
        result = json.loads((EVIDENCE / filename).read_bytes())
        assert (result["platform"], result["node_version"], result["pnpm_version"], result["pnpm_sha256"]) == (
            system,
            node,
            "12.16.1",
            binary,
        )
        assert result["source_action_sha256"] == repair["source_action_sha256"]
        assert result["runner_sha256"] == sha(EVIDENCE / "reproduce.py")
        assert result["overlay_sha256"] == sha(OVERLAY / "SKILL.md")
        assert result["example_sha256"] == sha(OVERLAY / "examples/pnpm-ci.yml")
        assert not result["agent_performance_tested"]
        assert not result["github_cache_service_tested"]
        assert result["pnpm_offline_mode"]
        for name in ("before-install", "missing-archive", "missing-lock", "mismatched-lock"):
            assert result["logs"][name]["exit_code"] != 0
        for name in ("pnpm-version", "node-version", "store-path", "seed-install", "frozen-install", "after-install"):
            assert result["logs"][name]["exit_code"] == 0
        fixtures.add(result["fixture_tarball_sha256"])
    assert len(fixtures) == 1


def test_fixture_refuses_existing_files_and_distinct_runs_change_package(tmp_path: Path) -> None:
    first, second = tmp_path / "first", tmp_path / "second"
    first.mkdir()
    second.mkdir()
    script = str(EVIDENCE / "github_fixture.py")
    for folder, run_id in ((first, "123"), (second, "124")):
        result = subprocess.run(
            [sys.executable, script, "prepare", "--workspace", str(folder), "--run-id", run_id, "--attempt", "1"],
            capture_output=True,
            timeout=30,
            check=False,
        )
        assert result.returncode == 0
    assert sha(first / "fixture.tgz") != sha(second / "fixture.tgz")
    manifest = (first / "package.json").read_bytes()
    repeated = subprocess.run(
        [sys.executable, script, "prepare", "--workspace", str(first), "--run-id", "123", "--attempt", "1"],
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert repeated.returncode != 0
    assert (first / "package.json").read_bytes() == manifest


def test_probe_refuses_miss_without_writing(tmp_path: Path) -> None:
    output = tmp_path / "out"
    result = subprocess.run(
        [
            sys.executable,
            str(EVIDENCE / "github_fixture.py"),
            "probe",
            "--workspace",
            str(tmp_path),
            "--output",
            str(output),
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
    assert not output.exists()

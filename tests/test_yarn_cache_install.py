"""Verify the Yarn repair's source binding and component observations."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / "included/repaired/skills/by-category/devops-cloud-operations/latest-release-devops/yarn-cache-install"
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/yarn-cache-install-v1"


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
    fixture_hashes = set()
    for filename, system, node in (
        ("windows-node26-yarn4.json", "Windows", "v26.13.0"),
        ("linux-node24-yarn4.json", "Linux", "v24.15.0"),
    ):
        result = json.loads((EVIDENCE / filename).read_bytes())
        assert (result["platform"], result["node_version"], result["yarn_version"]) == (system, node, "4.18.1")
        assert result["source_action_sha256"] == repair["source_action_sha256"]
        assert result["runner_sha256"] == sha(EVIDENCE / "reproduce.py")
        assert result["overlay_sha256"] == sha(OVERLAY / "SKILL.md")
        assert result["yarn_js_sha256"] == "a28ad591febb769f939c11f82f89bacad0b0fac0c884d3b78fa2aaaee970907e"
        assert not result["agent_performance_tested"]
        assert not result["github_cache_service_tested"]
        assert not result["network_enabled"]
        for linker in ("node-modules", "pnp"):
            for name in ("source-cache-command", "before-install", "mismatched-lock"):
                assert result["logs"][f"{linker}-{name}"]["exit_code"] != 0
            for name in ("config-cache", "seed", "install", "after-install"):
                assert result["logs"][f"{linker}-{name}"]["exit_code"] == 0
        fixture_hashes.add(result["fixture_tarball_sha256"])
    assert len(fixture_hashes) == 1


def test_runner_wont_overwrite_existing_output(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            str(EVIDENCE / "reproduce.py"),
            "--node",
            sys.executable,
            "--yarn-js",
            sys.executable,
            "--output-dir",
            str(output),
        ],
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0
    assert list(output.iterdir()) == []

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/repaired-skill-readiness/bun-runtime-v1"
OVERLAY = ROOT / "included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/bun-runtime"
MIRROR = ROOT / "included/skills/by-category/testing-qa-benchmarking/selected-structure-reference/bun-runtime/SKILL.md"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_original_overlay_and_component_evidence_are_source_bound() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert digest(OVERLAY / manifest["provenance_skill"]) == digest(MIRROR) == manifest["original_skill_sha256"]
    assert digest(OVERLAY / "SKILL.md") == manifest["repaired_skill_sha256"]
    assert digest(OVERLAY / manifest["license_file"]) == manifest["license_sha256"]
    assert manifest["model_performance_claim"] is False
    for name, expected in manifest["evidence_sha256"].items():
        assert digest(ARTIFACT / name) == expected, name


def test_recorded_runtime_controls_are_complete() -> None:
    for platform in ("windows", "linux"):
        folder = ARTIFACT / platform
        data = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        assert data["bun_version"] == "1.4.4"
        assert data["agent_efficacy_scored"] is False
        assert cases["no_lock_frozen"] == {"exit": 0, "lock_exists": False, "lock_sha256": None}
        assert cases["create_lock"]["exit"] == cases["matching_frozen"]["exit"] == 0
        assert cases["mismatch_frozen"]["exit"] != 0
        assert all(cases[name]["lock_exists"] for name in ("create_lock", "matching_frozen", "mismatch_frozen"))
        assert cases["create_lock"]["lock_sha256"] == cases["matching_frozen"]["lock_sha256"]
        assert cases["matching_frozen"]["lock_sha256"] == cases["mismatch_frozen"]["lock_sha256"]
        assert "lockfile is frozen" in (folder / "mismatched-lock.stderr.txt").read_text(encoding="utf-8")
        node = json.loads((folder / "node26-http.json").read_text(encoding="utf-8"))
        bun = json.loads((folder / "bun14-http.json").read_text(encoding="utf-8"))
        assert node["node_compat_version"] == "26.13.0" and node["http_server_is_net_server"] is True
        assert bun["bun_version"] == "1.4.4" and bun["http_server_is_net_server"] is False


def test_recorded_shell_controls_distinguish_shell_syntax() -> None:
    for platform in ("windows", "linux"):
        folder = ARTIFACT / platform
        data = json.loads((folder / "shell-control.json").read_text(encoding="utf-8"))
        previous = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        assert data["binary_sha256"] == previous["binary_sha256"]
        assert data["agent_efficacy_scored"] is False and all(data["checks"].values())
        assert json.loads(cases["explicit_after_run"]["stdout"])["sample"] == "explicit-file"
        assert json.loads(cases["default_env"]["stdout"])["sample"] == "default-file"
        if platform == "windows":
            assert cases["shell_inline"]["exit_code"] != 0
            assert cases["shell_native"]["exit_code"] == 0
            assert json.loads(cases["shell_native"]["stdout"])["sample"] == "inline"
        else:
            assert cases["shell_inline"]["exit_code"] == 0
            assert json.loads(cases["shell_inline"]["stdout"])["sample"] == "inline"


def test_control_rejects_wrong_runtime_without_creating_fixture(tmp_path: Path) -> None:
    scratch, output = tmp_path / "scratch", tmp_path / "output"
    result = subprocess.run(
        [
            sys.executable,
            str(ARTIFACT / "frozen-control.py"),
            "--bun",
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

"""Source binding and safe preparation checks for the SVG editor overlay."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MIRROR = ROOT / "included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master"
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ppt-master"
)
ARTIFACT = ROOT / "artifacts/repaired-skill-readiness/ppt-svg-text-move-v1/qualification.json"
INSTALLER = OVERLAY / "scripts/prepare_ppt_master.py"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_installer():
    spec = importlib.util.spec_from_file_location("svg_repair_installer", INSTALLER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_provenance_and_recorded_observations() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_bytes())
    result = json.loads(ARTIFACT.read_bytes())
    original_skill = (MIRROR / "SKILL.md").read_bytes().replace(b"\r\n", b"\n")
    provenance = (OVERLAY / "provenance/original.SKILL.md").read_bytes()
    assert original_skill == provenance
    assert digest(provenance) == manifest["original_skill_sha256"]
    assert digest((OVERLAY / "LICENSE").read_bytes()) == manifest["license_sha256"]
    assert digest((OVERLAY / "SKILL.md").read_bytes()) == manifest["repaired_skill_sha256"]
    assert digest((OVERLAY / "scripts/app.js").read_bytes()) == manifest["repaired_script_sha256"]
    assert digest(INSTALLER.read_bytes()) == manifest["preparer_sha256"]
    assert (
        load_installer().source_script_sha256(MIRROR / "scripts/svg_editor/static/app.js")
        == manifest["original_script_sha256"]
    )
    assert result["repaired_script_sha256"] == manifest["repaired_script_sha256"]
    assert result["source_script_sha256"] == manifest["original_script_sha256"]
    assert len(result["real_backend"]["cases"]) == 7
    assert len(result["isolated_races"]["cases"]) == 6
    for name, expected in result["control_scripts"].items():
        assert digest((ROOT / "benchmarks/component-controls/ppt-svg-editor" / name).read_bytes()) == expected
    assert result["model_performance_claim"] is False
    assert result["original_scanning_alerts_closed"] is False


def test_preparation_refuses_existing_output_and_tampered_repair(tmp_path: Path) -> None:
    existing = tmp_path / "existing"
    existing.mkdir()
    sentinel = existing / "keep.txt"
    sentinel.write_bytes(b"keep")
    result = subprocess.run(
        [sys.executable, "-I", str(INSTALLER), "--repo", str(ROOT), "--destination", str(existing)],
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 2
    assert b"destination already exists" in result.stderr
    assert sentinel.read_bytes() == b"keep"

    copied_installer = tmp_path / "prepare_ppt_master.py"
    shutil.copyfile(INSTALLER, copied_installer)
    (tmp_path / "app.js").write_text("tampered", encoding="utf-8")
    destination = tmp_path / "new-skill"
    result = subprocess.run(
        [sys.executable, "-I", str(copied_installer), "--repo", str(ROOT), "--destination", str(destination)],
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 2
    assert b"repair bytes do not match" in result.stderr
    assert not destination.exists()


def test_preparation_rejects_linked_source(tmp_path: Path) -> None:
    installer = load_installer()
    repo = tmp_path / "repo"
    source = repo / installer.SOURCE
    source.parent.mkdir(parents=True)
    try:
        source.symlink_to(MIRROR, target_is_directory=True)
    except OSError:
        pytest.skip("Directory symlinks are unavailable on this host")
    destination = tmp_path / "new-skill"
    with pytest.raises(ValueError, match="link or reparse point"):
        installer.prepare(repo, OVERLAY / "scripts/app.js", destination)
    assert not destination.exists()


def test_git_checkout_preserves_hash_bound_evidence(tmp_path: Path) -> None:
    git = shutil.which("git")
    if git is None:
        pytest.skip("Git is required for checkout conversion controls")
    paths = [
        MIRROR / "scripts/svg_editor/static/app.js",
        OVERLAY / "scripts/app.js",
        OVERLAY / "provenance/original.SKILL.md",
        OVERLAY / "repair.json",
        ARTIFACT,
    ]
    expected = {path.relative_to(ROOT).as_posix(): path.read_bytes() for path in paths}
    original = paths[0].relative_to(ROOT).as_posix()
    expected[original] = expected[original].replace(b"\r\n", b"\n")

    def run(*args: str) -> None:
        subprocess.run(
            [git, "-c", "core.longpaths=true", *args], cwd=tmp_path, capture_output=True, timeout=20, check=True
        )

    run("init", "--initial-branch=main")
    (tmp_path / ".gitattributes").write_bytes((ROOT / ".gitattributes").read_bytes().replace(b"\r\n", b"\n"))
    for name, data in expected.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    run("-c", "core.autocrlf=false", "add", "--", ".gitattributes", *expected)
    installer = load_installer()
    for setting in ("true", "false"):
        for name, data in expected.items():
            target = tmp_path / name
            target.unlink()
            run("-c", f"core.autocrlf={setting}", "checkout-index", "--", name)
            if name == original:
                assert installer.source_script_sha256(target) == installer.ORIGINAL_SCRIPT_LF
            else:
                assert target.read_bytes() == data

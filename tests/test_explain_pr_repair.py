from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from build_catalog import sanitized_file_bytes

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/repaired-skill-readiness/explain-pr-diff-v1"
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/coding-refactoring-repository-automation/reddit-verified-gtm-registry/explain-this-pr"
)
MIRROR = (
    ROOT
    / "included/skills/by-category/coding-refactoring-repository-automation/reddit-verified-gtm-registry/explain-this-pr"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_provenance_and_component_evidence_are_source_bound() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert (OVERLAY / "provenance/original.SKILL.md").read_bytes() == sanitized_file_bytes(MIRROR / "SKILL.md")
    assert (OVERLAY / "provenance/upstream.README.md").read_bytes() == sanitized_file_bytes(MIRROR / "README.md")
    assert digest(OVERLAY / "provenance/original.SKILL.md") == manifest["original_skill_sha256"]
    assert manifest["model_performance_claim"] is False
    for name, expected in manifest["overlay_sha256"].items():
        assert digest(OVERLAY / name) == expected
    for name, expected in manifest["evidence_sha256"].items():
        assert digest(ARTIFACT / name) == expected


@pytest.mark.parametrize("line_ending", [b"\n", b"\r\n"])
def test_mirror_checkout_line_endings_preserve_canonical_provenance(tmp_path: Path, line_ending: bytes) -> None:
    for original, preserved in (("SKILL.md", "original.SKILL.md"), ("README.md", "upstream.README.md")):
        canonical = (OVERLAY / "provenance" / preserved).read_bytes()
        checkout = tmp_path / original
        checkout.write_bytes(canonical.replace(b"\n", line_ending))
        assert sanitized_file_bytes(checkout) == canonical


def test_full_diff_exposes_change_omitted_from_excerpt() -> None:
    raw = (ARTIFACT / "raw/full.diff").read_bytes()
    full = raw.decode("utf-8")
    excerpt = "\n".join(full.splitlines()[:200])
    assert len(full.splitlines()) == 513
    assert "z_totals.py" not in excerpt and "+    return sum(items) + 5" not in excerpt
    assert "z_totals.py" in full and "+    return sum(items) + 5" in full
    for platform in ("windows", "linux"):
        result = json.loads((ARTIFACT / f"{platform}-result.json").read_text(encoding="utf-8"))
        assert result["diff_sha256"] == hashlib.sha256(raw).hexdigest()
        assert result["agent_efficacy_scored"] is False and all(result["checks"].values())


def test_control_reproduces_diff_and_refuses_existing_outputs(tmp_path: Path) -> None:
    if shutil.which("git") is None:
        pytest.skip("Git is not installed")
    workspace, output = tmp_path / "workspace", tmp_path / "observation.json"
    command = [sys.executable, str(ARTIFACT / "control.py"), "--workspace", str(workspace), "--output", str(output)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stderr
    recorded = output.read_bytes()
    assert json.loads(recorded)["diff_sha256"] == digest(ARTIFACT / "raw/full.diff")
    repeated = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
    assert repeated.returncode != 0 and output.read_bytes() == recorded

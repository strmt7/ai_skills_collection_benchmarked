import json

import create_repaired_skill_overlays as repairs
import pytest


def prepare(monkeypatch, tmp_path, paths):
    overlays = tmp_path / "included/repaired/skills"
    artifacts = tmp_path / "artifacts/repaired-skill-readiness" / repairs.RUN_NAME
    overlays.mkdir(parents=True)
    artifacts.mkdir(parents=True)
    monkeypatch.setattr(repairs, "ROOT", tmp_path)
    monkeypatch.setattr(repairs, "REPAIRED_ROOT", overlays)
    monkeypatch.setattr(repairs, "ARTIFACT_ROOT", artifacts)
    manifest = {
        "runner": repairs.RUNNER_ID,
        "run_name": repairs.RUN_NAME,
        "repairs": [{"repaired_path": path} for path in paths],
    }
    (overlays / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return overlays, artifacts


def test_regeneration_preserves_other_maintained_repairs(monkeypatch, tmp_path):
    overlays, artifacts = prepare(monkeypatch, tmp_path, ["included/repaired/skills/legacy"])
    legacy = overlays / "legacy"
    maintained = overlays / "maintained"
    legacy.mkdir()
    maintained.mkdir()
    (legacy / "SKILL.md").write_text("old generated output", encoding="utf-8")
    (maintained / "SKILL.md").write_bytes(b"separate maintained repair\n")
    (artifacts / "old-result.json").write_text("{}", encoding="utf-8")
    repairs.clean_generated_outputs()
    assert not legacy.exists()
    assert (maintained / "SKILL.md").read_bytes() == b"separate maintained repair\n"
    assert not (artifacts / "old-result.json").exists()
    assert artifacts.is_dir()


@pytest.mark.parametrize("escape", ["../outside", "included/repaired/skills", "included/repaired/skills/../../outside"])
def test_invalid_target_stops_before_any_deletion(monkeypatch, tmp_path, escape):
    overlays, artifacts = prepare(monkeypatch, tmp_path, ["included/repaired/skills/legacy", escape])
    legacy = overlays / "legacy"
    legacy.mkdir()
    sentinel = legacy / "SKILL.md"
    sentinel.write_bytes(b"preserve original\n")
    with pytest.raises(ValueError, match="escapes"):
        repairs.clean_generated_outputs()
    assert sentinel.read_bytes() == b"preserve original\n"
    assert artifacts.is_dir()


def test_unknown_generator_cannot_clean_outputs(monkeypatch, tmp_path):
    overlays, artifacts = prepare(monkeypatch, tmp_path, [])
    (overlays / "manifest.json").write_text('{"runner":"different-generator"}', encoding="utf-8")
    with pytest.raises(ValueError, match="ownership manifest"):
        repairs.clean_generated_outputs()
    assert artifacts.is_dir()


def test_artifact_parent_is_not_a_cleanup_target(monkeypatch, tmp_path):
    _, artifacts = prepare(monkeypatch, tmp_path, [])
    monkeypatch.setattr(repairs, "ARTIFACT_ROOT", artifacts.parent)
    with pytest.raises(ValueError, match="artifact cleanup target escapes"):
        repairs.clean_generated_outputs()
    assert artifacts.is_dir()

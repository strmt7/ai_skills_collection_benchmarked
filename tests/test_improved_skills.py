from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest
import validate_improved_skills as overlays
from _lib_b.io_utils import read_json


def test_experimental_overlays_preserve_original_sources():
    manifest = read_json(overlays.ROOT / "data/improved_skills_manifest.json")
    catalog = read_json(overlays.ROOT / "data/skills_catalog.json")
    assert not overlays.validate(manifest, catalog, overlays.ROOT)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source_commit", "0" * 40, "source commit"),
        ("source_file_sha256", "0" * 64, "original provenance"),
        ("overlay_sha256", "0" * 64, "overlay hash"),
        ("performance_status", "superior", "performance claims"),
        ("overlay_path", "../outside", "escapes"),
        ("license", "unknown", "license notice"),
        ("license_file_sha256", "0" * 64, "license notice hash"),
        ("package_file_sha256", {}, "complete package file hashes"),
        ("package_file_sha256", {"SKILL.md": "0" * 64}, "package file coverage or hash mismatch"),
        ("package_file_sha256", {"../escaped.py": "0" * 64}, "invalid package hash record"),
    ],
)
def test_fabricated_or_stale_overlay_evidence_is_rejected(field, value, message):
    manifest = copy.deepcopy(read_json(overlays.ROOT / "data/improved_skills_manifest.json"))
    manifest["skills"][0][field] = value
    catalog = read_json(overlays.ROOT / "data/skills_catalog.json")
    assert any(message in error for error in overlays.validate(manifest, catalog, overlays.ROOT))


def test_absolute_manifest_paths_rejected(tmp_path):
    with pytest.raises(ValueError, match="relative strings"):
        overlays.inside(tmp_path, str(tmp_path / "file"))
    assert overlays.inside(tmp_path, "relative/file") == tmp_path / Path("relative/file")


@pytest.mark.parametrize(
    "manifest",
    [None, [], {}, {"manifest_version": 1, "skills": [None]}, {"manifest_version": 1, "skills": [{"skill_id": []}]}],
)
def test_malformed_manifest_rejected_without_crashing(manifest, tmp_path):
    assert overlays.validate(manifest, [], tmp_path)


def test_changed_bundled_script_is_rejected(tmp_path):
    manifest = read_json(overlays.ROOT / "data/improved_skills_manifest.json")
    item = next(
        record for record in manifest["skills"] if record["skill_id"] == "anthropics-skills-skills-mcp-builder-skill-md"
    )
    catalog = read_json(overlays.ROOT / "data/skills_catalog.json")
    source = next(record for record in catalog if record["id"] == item["skill_id"])
    shutil.copytree(overlays.ROOT / item["overlay_path"], tmp_path / item["overlay_path"])
    mirror = tmp_path / source["mirrored_path"]
    mirror.mkdir(parents=True)
    shutil.copyfile(overlays.ROOT / source["mirrored_path"] / "SKILL.md", mirror / "SKILL.md")
    selected = {"manifest_version": 1, "skills": [item]}
    assert overlays.validate(selected, catalog, tmp_path) == []
    script = tmp_path / item["overlay_path"] / "scripts/qualify_sdk.py"
    script.write_text(script.read_text(encoding="utf-8") + "\n# changed helper\n", encoding="utf-8")
    assert any(
        "package file coverage or hash mismatch" in error for error in overlays.validate(selected, catalog, tmp_path)
    )

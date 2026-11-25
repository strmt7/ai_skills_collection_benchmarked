from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest
import validate_improved_skills as overlays
from _lib_b.io_utils import read_json
from build_catalog import sha256_file


def test_experimental_overlays_preserve_original_sources():
    manifest = read_json(overlays.ROOT / "data/improved_skills_manifest.json")
    catalog = read_json(overlays.ROOT / "data/skills_catalog.json")
    assert not overlays.validate(manifest, catalog, overlays.ROOT)


@pytest.mark.parametrize("version", ["v1", "v2"])
def test_frozen_trials_keep_their_original_instruction_bytes(version):
    protocol = read_json(overlays.ROOT / f"benchmarks/agent-effectiveness/development/protocol-{version}.json")
    skills = protocol["conditions"]["improved"]["skills"]
    assert skills
    for skill in skills:
        assert sha256_file(overlays.ROOT / skill["path"]) == skill["sha256"]


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


def test_overlay_accepts_validated_historical_source_and_checks_current_mirror(tmp_path):
    manifest = read_json(overlays.ROOT / "data/improved_skills_manifest.json")
    item = manifest["skills"][0]
    source = next(row for row in read_json(overlays.ROOT / "data/skills_catalog.json") if row["id"] == item["skill_id"])
    if source["commit_sha"] != item["source_commit"]:
        from _source_history import resolve_entry

        source, _ = resolve_entry(overlays.ROOT, source, item["skill_id"], item["source_commit"])
    shutil.copytree(overlays.ROOT / item["overlay_path"], tmp_path / item["overlay_path"])
    relative = "artifacts/source-history/example/SKILL.md"
    snapshot = tmp_path / relative
    snapshot.parent.mkdir(parents=True)
    raw = (tmp_path / item["original_path"]).read_bytes()
    snapshot.write_bytes(raw)
    versions = [
        {
            "entry": source,
            "observed_catalog_revision": "a" * 40,
            "observed_catalog_sha256": "b" * 64,
            "skill_snapshot": relative,
            "skill_snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        }
    ]
    mirror = tmp_path / source["mirrored_path"] / "SKILL.md"
    mirror.parent.mkdir(parents=True)
    mirror.write_text("# Updated source\n", encoding="utf-8")
    current = {**source, "commit_sha": "d" * 40, "skill_file_sha256": sha256_file(mirror)}
    selected = {"manifest_version": 1, "skills": [item]}
    assert any("source commit is absent" in error for error in overlays.validate(selected, [current], tmp_path))

    history = tmp_path / "data/catalog_source_history.json"
    history.parent.mkdir()
    history.write_text(json.dumps({"schema_version": 1, "versions": versions}), encoding="utf-8")
    assert overlays.validate(selected, [current], tmp_path) == []
    mirror.write_text("# Unexpected mirror edit\n", encoding="utf-8")
    assert any(
        "immutable source mirror was changed" in error for error in overlays.validate(selected, [current], tmp_path)
    )
    snapshot.write_bytes(raw + b"tampered")
    assert any("snapshot bytes changed" in error for error in overlays.validate(selected, [current], tmp_path))

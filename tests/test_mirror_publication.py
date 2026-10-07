from __future__ import annotations

import os
import subprocess
from pathlib import Path

import build_catalog as catalog
import pytest


@pytest.fixture
def publication(tmp_path, monkeypatch):
    root, sources = tmp_path / "workspace", tmp_path / "sources"
    source = sources / "fixture" / "skills" / "example"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text("# new skill\n", encoding="utf-8", newline="\n")
    script = source / "scripts" / "no-extension"
    script.parent.mkdir()
    script.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8", newline="\n")
    subprocess.run(["git", "init", str(sources / "fixture")], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(sources / "fixture"), "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(sources / "fixture"), "update-index", "--chmod=+x", "skills/example/scripts/no-extension"],
        check=True,
    )
    script.chmod(0o755)
    modes = catalog.skill_file_modes(source)
    previous = root / "included" / "skills"
    previous.mkdir(parents=True)
    (previous / "previous.txt").write_text("preserve me", encoding="utf-8")
    monkeypatch.setattr(catalog, "ROOT", root)
    monkeypatch.setattr(catalog, "SOURCE_ROOT", sources)
    monkeypatch.setattr(catalog, "SOURCES", [{"repo": "fixture/example", "dir": "fixture"}])
    entry = {
        "id": "fixture-example",
        "name": "example",
        "category": "fixture",
        "subcategory": "reference",
        "install_name": "example",
        "mirrored_path": "included/skills/by-category/fixture/reference/example",
        "agent_ready_path": "included/agent-ready/example/SKILL.md",
        "source_repo": "fixture/example",
        "source_path": "skills/example/SKILL.md",
        "immutable_source_url": "https://example.invalid/source",
        "selected_ref": "fixture",
        "commit_sha": "a" * 40,
        "benchmark_scenarios": [],
        "has_required_frontmatter": False,
        "skill_file_sha256": catalog.sha256_file(source / "SKILL.md"),
        "skill_dir_sha256": catalog.sha256_tree(source, file_modes=modes),
        "file_modes": modes,
        "source_group": "fixture",
        "source_tier": "reference",
    }
    return root, source, entry


def test_untracked_windows_copy_retains_source_modes_and_hash(publication):
    root, _, entry = publication
    catalog.mirror_all_skills([entry])
    copied = root / entry["mirrored_path"]
    assert entry["file_modes"]["scripts/no-extension"] == "100755"
    assert catalog.sha256_tree(copied, file_modes=entry["file_modes"]) == entry["skill_dir_sha256"]
    if os.name != "nt":
        assert (copied / "scripts/no-extension").stat().st_mode & 0o111
    backups = list((root / ".venv/generation-staging").glob("*-previous"))
    assert len(backups) == 1
    assert (backups[0] / "previous.txt").read_text() == "preserve me"


def test_declared_new_credential_policy_publishes_neutralized_copy_only(publication):
    import json

    root, source, entry = publication
    text = "# new skill\ncredential: " + "sk_" + "live_" + "exampleValue123\n"
    (source / "SKILL.md").write_text(text, encoding="utf-8", newline="\n")
    entry.update(
        credential_policy_version=2,
        skill_file_sha256=catalog.sha256_file(source / "SKILL.md", credential_policy=2),
        skill_dir_sha256=catalog.sha256_tree(source, file_modes=entry["file_modes"], credential_policy=2),
    )
    catalog.mirror_all_skills([entry])
    mirrored = root / entry["mirrored_path"]
    assert (mirrored / "SKILL.md").read_text("utf-8") == "# new skill\ncredential: <STRIPE_SERVER_KEY>\n"
    assert (source / "SKILL.md").read_text("utf-8") == text
    assert catalog.sha256_tree(mirrored, file_modes=entry["file_modes"]) == entry["skill_dir_sha256"]
    assert json.loads((root / "included/skills/manifest.json").read_text("utf-8"))[0]["credential_policy_version"] == 2


def test_failed_copy_preserves_previous_tree(publication, monkeypatch):
    root, _, entry = publication

    def fail(*args, **kwargs):
        raise OSError("simulated disk failure")

    monkeypatch.setattr(catalog, "copy_sanitized_tree", fail)
    with pytest.raises(OSError, match="simulated disk failure"):
        catalog.mirror_all_skills([entry])
    assert (root / "included/skills/previous.txt").read_text() == "preserve me"


def test_source_changed_after_collection_cannot_publish(publication):
    root, source, entry = publication
    (source / "SKILL.md").write_text("changed after collection", encoding="utf-8")
    with pytest.raises(ValueError, match="staged mirror hash differs"):
        catalog.mirror_all_skills([entry])
    assert (root / "included/skills/previous.txt").read_text() == "preserve me"


@pytest.mark.parametrize(
    "path",
    [
        "../outside",
        "included/skills/by-category/../../outside",
        "/outside",
        "included/skills/by-category/a/../b",
        "included/skills/by-category\\outside",
    ],
)
def test_mirror_path_escape_is_rejected_before_writes(publication, path):
    root, _, entry = publication
    entry["mirrored_path"] = path
    with pytest.raises(ValueError):
        catalog.mirror_all_skills([entry])
    assert (root / "included/skills/previous.txt").read_text() == "preserve me"
    assert not (root / ".venv").exists()


def test_overlapping_mirror_paths_are_rejected(publication):
    root, _, entry = publication
    with pytest.raises(ValueError, match="overlapping"):
        catalog.mirror_all_skills([entry, entry.copy()])
    assert (root / "included/skills/previous.txt").read_text() == "preserve me"


@pytest.mark.parametrize(
    "modes",
    [
        {},
        {"SKILL.md": "100644"},
        {"SKILL.md": "100777", "scripts/no-extension": "100755"},
        {"SKILL.md": "100644", "scripts/no-extension": "100755", "../outside": "100644"},
    ],
)
def test_incomplete_or_invalid_modes_cannot_hash(publication, modes):
    _, source, _ = publication
    with pytest.raises(ValueError):
        catalog.sha256_tree(source, file_modes=modes)


def test_failed_publication_rename_rolls_back(publication, monkeypatch):
    root, _, entry = publication
    original = Path.rename

    def failing_rename(path, destination):
        if path.name.startswith("skill-mirrors-") and not path.name.endswith("-previous"):
            raise OSError("simulated publication failure")
        return original(path, destination)

    monkeypatch.setattr(Path, "rename", failing_rename)
    with pytest.raises(OSError, match="simulated publication failure"):
        catalog.mirror_all_skills([entry])
    assert (root / "included/skills/previous.txt").read_text() == "preserve me"


def test_empty_collection_cannot_replace_previous_tree(publication):
    root, _, _ = publication
    with pytest.raises(ValueError, match="empty mirror collection"):
        catalog.mirror_all_skills([])
    assert (root / "included/skills/previous.txt").read_text() == "preserve me"


def test_mode_tampering_is_detected_on_posix(publication):
    _, source, entry = publication
    if os.name == "nt":
        pytest.skip("NTFS mode preservation is checked through explicit source Git metadata")
    (source / "scripts/no-extension").chmod(0o644)
    with pytest.raises(ValueError, match="filesystem executable mode differs"):
        catalog.sha256_tree(source, file_modes=entry["file_modes"])


def test_directory_enumeration_error_is_not_silently_ignored(publication, monkeypatch):
    _, source, _ = publication

    def inaccessible(path, *, followlinks, onerror):
        onerror(PermissionError("unreadable source directory"))
        yield str(path), [], []

    monkeypatch.setattr(catalog.os, "walk", inaccessible)
    with pytest.raises(PermissionError, match="unreadable source directory"):
        catalog.skill_tree_files(source)

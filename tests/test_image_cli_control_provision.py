from __future__ import annotations

import json

import prepare_image_cli_controls as controls
import pytest
from build_catalog import sha256_tree


@pytest.fixture
def fixture(tmp_path):
    root = tmp_path / "workspace"
    mirror = root / "included/skills/example"
    mirror.mkdir(parents=True)
    (mirror / "SKILL.md").write_bytes(b"# Preserve exact source bytes\r\n")
    (mirror / "src").mkdir()
    (mirror / "src/helper.js").write_bytes(b"export const value = 1;\r\n")
    (mirror / "package.json").write_text("{}", encoding="utf-8")
    (mirror / "package-lock.json").write_text("{}", encoding="utf-8")
    (mirror / "LICENSE").write_text("fixture license", encoding="utf-8")
    (root / "data").mkdir()
    (root / "data/skills_catalog.json").write_text(
        json.dumps(
            [
                {
                    "id": controls.SKILL_ID,
                    "mirrored_path": "included/skills/example",
                    "commit_sha": "a" * 40,
                    "immutable_source_url": "https://example.invalid/pinned",
                    "skill_dir_sha256": sha256_tree(mirror),
                }
            ]
        ),
        encoding="utf-8",
    )
    graph = root / controls.FIXTURE
    graph.mkdir(parents=True)
    (graph / "package.json").write_text(json.dumps({"dependencies": {"fixture-dependency": "1.2.3"}}), encoding="utf-8")
    (graph / "package-lock.json").write_text(
        json.dumps(
            {
                "packages": {
                    "": {"dependencies": {"fixture-dependency": "1.2.3"}},
                    "node_modules/fixture-dependency": {"version": "1.2.3"},
                }
            }
        ),
        encoding="utf-8",
    )
    (graph / "LICENSE").write_text("fixture license", encoding="utf-8")
    return root, mirror, root / ".venv/controls"


def test_byte_preserving_complete_stage_and_check(fixture):
    root, mirror, target = fixture
    result = controls.prepare(root, target)
    assert result["ok"] is True
    assert (target / "SKILL.md").read_bytes() == (mirror / "SKILL.md").read_bytes()
    assert (target / "src/helper.js").read_bytes() == (mirror / "src/helper.js").read_bytes()
    assert controls.prepare(root, target, check=True)["ok"] is True
    assert controls.files(target) == result["staged_file_sha256"]
    assert controls.files(mirror) == result["original_source_file_sha256"]
    assert (target / "package.json").read_bytes() != (mirror / "package.json").read_bytes()
    # Installed dependency contents do not masquerade as source provenance.
    (target / "node_modules/dependency").mkdir(parents=True)
    (target / "node_modules/dependency/index.js").write_text("installed dependency")
    assert controls.prepare(root, target, check=True)["ok"] is True


def test_existing_stage_never_overwritten(fixture):
    root, _, target = fixture
    controls.prepare(root, target)
    (target / "SKILL.md").write_text("user change")
    with pytest.raises(ValueError, match="already exists"):
        controls.prepare(root, target)
    assert (target / "SKILL.md").read_text() == "user change"


@pytest.mark.parametrize("change", ["modified", "missing", "extra"])
def test_changed_stage_rejected_in_check(fixture, change):
    root, _, target = fixture
    controls.prepare(root, target)
    if change == "modified":
        (target / "src/helper.js").write_text("changed")
    elif change == "missing":
        (target / "src/helper.js").unlink()
    else:
        (target / "extra.js").write_text("extra")
    with pytest.raises(ValueError, match="input files differ"):
        controls.prepare(root, target, check=True)


@pytest.mark.parametrize("destination", ["outside", "mirror", "fixture", "root"])
def test_unsafe_destination_rejected(fixture, destination):
    root, mirror, _ = fixture
    target = {"outside": root.parent / "outside", "mirror": mirror, "fixture": root / controls.FIXTURE, "root": root}[
        destination
    ]
    with pytest.raises(ValueError):
        controls.prepare(root, target)
    assert not (root.parent / "outside").exists()
    assert not (root / ".venv").exists()


def test_modified_mirror_rejected_before_copy(fixture):
    root, mirror, target = fixture
    (mirror / "src/helper.js").write_text("unlocked source change")
    with pytest.raises(ValueError, match="differs from catalog"):
        controls.prepare(root, target)
    assert not target.exists()


@pytest.mark.parametrize("field", ["declaration", "resolution"])
def test_inconsistent_graph_cannot_be_qualified(fixture, field):
    root, _, target = fixture
    path = root / controls.FIXTURE / "package-lock.json"
    lock = json.loads(path.read_text())
    if field == "declaration":
        lock["packages"][""]["dependencies"]["fixture-dependency"] = "1.2.2"
    else:
        lock["packages"]["node_modules/fixture-dependency"]["version"] = "1.2.2"
    path.write_text(json.dumps(lock))
    with pytest.raises(ValueError, match="disagree|resolutions differ"):
        controls.prepare(root, target)
    assert not target.exists()


def test_unreadable_source_tree_fails_instead_of_hashing_empty(fixture, monkeypatch):
    _, mirror, _ = fixture

    def fail(path, *, followlinks, onerror):
        onerror(PermissionError("unreadable source"))
        yield str(path), [], []

    monkeypatch.setattr(controls.os, "walk", fail)
    with pytest.raises(PermissionError, match="unreadable"):
        controls.files(mirror)

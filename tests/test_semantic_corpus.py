"""Corpus coverage and freshness controls independent of embedding retrieval."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import prepare_semantic_corpus as corpus
import pytest


@pytest.fixture
def repository(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    (root / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    skill = root / "skills/example"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("entrypoint\n", encoding="utf-8")
    (skill / "reference.md").write_text("essential support resource\n", encoding="utf-8")
    (skill / "run.sh").write_bytes(b"#!/bin/sh\r\nprintf hello\r\n")
    (root / "private.txt").write_text("outside selected scope\n", encoding="utf-8")
    return root, root / ".venv/semantic-corpus/example"


def test_selected_resources_preserve_bytes_and_exclude_unselected_files(repository):
    root, output = repository
    result = corpus.prepare(root, output, ["skills"], check=False)
    assert result == {"ok": True, "errors": [], "selected_files": 3, "text_files": 3, "excluded_files": {}}
    assert not (output / "tree/private.txt").exists()
    assert (output / "tree/skills/example/run.sh").read_bytes() == b"#!/bin/sh\r\nprintf hello\r\n"
    assert corpus.prepare(root, output, ["skills"], check=True)["ok"]


def test_git_inventory_diagnostic_cannot_become_a_partial_corpus(repository, monkeypatch):
    root, output = repository
    calls = []

    def diagnostic(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 0, b"skills/example/SKILL.md\0", b"warning: resource unreadable\n")

    monkeypatch.setattr(corpus.subprocess, "run", diagnostic)
    with pytest.raises(ValueError, match="incomplete Git file inventory"):
        corpus.inventory(root, ["skills"])
    assert calls[0][:4] == ["git", "-c", "core.longpaths=true", "-C"]
    assert not output.exists()


def test_tracked_deletion_is_excluded_but_remaining_sources_are_preserved(repository):
    root, output = repository
    subprocess.run(["git", "-C", str(root), "add", "skills"], check=True)
    (root / "skills/example/reference.md").unlink()
    result = corpus.prepare(root, output, ["skills"], check=False)
    assert result["ok"] and result["selected_files"] == result["text_files"] == 2
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["files"]) == {"skills/example/SKILL.md", "skills/example/run.sh"}
    assert corpus.prepare(root, output, ["skills"], check=True)["ok"]


def test_every_nontext_resource_has_explicit_hashed_exclusion(repository):
    root, output = repository
    (root / "skills/nul.bin").write_bytes(b"a\0b")
    (root / "skills/nonutf8.bin").write_bytes(b"\xff")
    (root / "skills/large.txt").write_bytes(b"a" * (corpus.MAX_FILE_BYTES + 1))
    result = corpus.prepare(root, output, ["skills"], check=False)
    assert result["excluded_files"] == {
        "skills/nul.bin": "contains_nul",
        "skills/nonutf8.bin": "not_utf8",
        "skills/large.txt": "larger_than_4_mib",
    }
    assert result["selected_files"] == 6 and result["text_files"] == 3
    manifest = json.loads((output / "manifest.json").read_text())
    assert len(manifest["files"]["skills/nul.bin"]["sha256"]) == 64
    assert corpus.prepare(root, output, ["skills"], check=True)["ok"]
    (root / "skills/nul.bin").write_bytes(b"changed\0bytes")
    assert not corpus.prepare(root, output, ["skills"], check=True)["ok"]


@pytest.mark.parametrize("change", ["edit", "add", "delete"])
def test_changed_source_inventory_is_stale_without_writes(repository, change):
    root, output = repository
    corpus.prepare(root, output, ["skills"], check=False)
    manifest = (output / "manifest.json").read_bytes()
    target = root / "skills/example/reference.md"
    if change == "edit":
        target.write_text("changed source")
    elif change == "add":
        (target.parent / "new.md").write_text("new resource")
    else:
        target.unlink()
    result = corpus.prepare(root, output, ["skills"], check=True)
    assert not result["ok"] and "source inventory or binding changed; prepare a new corpus" in result["errors"]
    assert (output / "manifest.json").read_bytes() == manifest


@pytest.mark.parametrize("change", ["edit", "add", "delete", "binding"])
def test_tampered_corpus_or_binding_is_rejected(repository, change):
    root, output = repository
    corpus.prepare(root, output, ["skills"], check=False)
    target = output / "tree/skills/example/reference.md"
    if change == "edit":
        target.write_text("changed corpus")
    elif change == "add":
        (target.parent / "unexpected.md").write_text("extra")
    elif change == "delete":
        target.unlink()
    else:
        data = json.loads((output / "manifest.json").read_text())
        data["source_root"] = "different repository"
        (output / "manifest.json").write_text(json.dumps(data))
    assert not corpus.prepare(root, output, ["skills"], check=True)["ok"]


def test_rejects_existing_output_without_overwrite(repository):
    root, output = repository
    corpus.prepare(root, output, ["skills"], check=False)
    manifest = (output / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        corpus.prepare(root, output, ["skills"], check=False)
    assert (output / "manifest.json").read_bytes() == manifest


def test_cocoindex_state_does_not_change_resource_inventory(repository):
    root, output = repository
    corpus.prepare(root, output, ["skills"], check=False)
    state = output / "tree/.cocoindex_code"
    state.mkdir()
    (state / "settings.yml").write_text("generated local settings")
    assert corpus.prepare(root, output, ["skills"], check=True)["ok"]


@pytest.mark.parametrize("name", ["../outside", "/absolute", "a/../b", "a//b", "a\\b", "C:outside", ".", ""])
def test_rejects_noncanonical_prefixes(repository, name):
    root, output = repository
    with pytest.raises(ValueError):
        corpus.prepare(root, output, [name], check=False)
    assert not output.exists()


def test_rejects_output_outside_ignored_workspace(repository):
    root, _ = repository
    with pytest.raises(ValueError, match="child"):
        corpus.prepare(root, root / "skills/output", ["skills"], check=False)


def test_empty_scope_cannot_be_presented_as_complete(repository):
    root, output = repository
    with pytest.raises(ValueError, match="no indexable"):
        corpus.prepare(root, output, ["missing"], check=False)


def test_rejects_source_changed_during_preparation(repository, monkeypatch):
    root, output = repository
    original = corpus.inventory
    calls = 0

    def changing_inventory(root, prefixes):
        nonlocal calls
        calls += 1
        if calls == 2:
            (root / "skills/new.md").write_text("new input")
        return original(root, prefixes)

    monkeypatch.setattr(corpus, "inventory", changing_inventory)
    with pytest.raises(ValueError, match="changed during"):
        corpus.prepare(root, output, ["skills"], check=False)
    assert not (output / "manifest.json").exists()


def test_cli_failures_are_json_envelopes(repository, capsys):
    root, output = repository
    assert corpus.main(["--root", str(root), "--output", str(output), "--prefix", "missing", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


def test_local_state_is_rejected_before_git_inventory(repository, monkeypatch):
    root, output = repository
    monkeypatch.setattr(corpus, "git_files", lambda _: pytest.fail("local state must not be enumerated"))
    with pytest.raises(ValueError, match="local .venv"):
        corpus.prepare(root, output, [".venv"], check=False)


def test_symlink_resources_are_not_followed(repository):
    root, output = repository
    target = root / "skills/linked.txt"
    try:
        target.symlink_to(root / "private.txt")
    except OSError:
        pytest.skip("host does not permit creating filesystem symlinks")
    with pytest.raises(ValueError, match="symlink"):
        corpus.prepare(root, output, ["skills"], check=False)


def test_multiple_symlink_directories_in_corpus_are_rejected(repository):
    root, output = repository
    corpus.prepare(root, output, ["skills"], check=False)
    for name in ("first", "second"):
        try:
            (output / "tree" / name).symlink_to(root / "skills", target_is_directory=True)
        except OSError:
            pytest.skip("host does not permit creating filesystem symlinks")
    errors = corpus.prepare(root, output, ["skills"], check=True)["errors"]
    assert any("first" in error for error in errors)
    assert any("second" in error for error in errors)

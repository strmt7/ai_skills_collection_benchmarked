import copy
import json

import build_catalog as builder
import pytest


def entry(identifier, name, repo="owner/skills"):
    return {
        "id": identifier,
        "name": name,
        "source_repo": repo,
        "source_path": f"skills/{name}/SKILL.md",
        "category": "Documents",
        "subcategory": "reference",
    }


def test_removing_a_duplicate_does_not_rename_a_retained_installation():
    old = entry("retained", "docx", "anthropics/skills")
    builder.assign_install_names([old], preserved_names={"retained": "docx-anthropics"})
    before = copy.deepcopy(old)
    builder.assign_install_names([old], preserved_names={"retained": "docx-anthropics"})
    assert old == before
    assert old["install_name"] == "docx-anthropics"


def test_new_duplicate_cannot_steal_a_retained_name_and_rebuild_is_stable():
    retained = entry("zzz-retained", "exa-search")
    builder.assign_install_names([retained])
    before = copy.deepcopy(retained)
    added = entry("aaa-new", "exa-search", "K-Dense-AI/scientific-agent-skills")
    entries = [added, retained]
    builder.assign_install_names(entries, preserved_names={retained["id"]: retained["install_name"]})
    assert retained == before
    assert added["install_name"] != retained["install_name"]
    scoped_result = copy.deepcopy(entries)
    builder.assign_install_names(entries, preserved_names={item["id"]: item["install_name"] for item in entries})
    assert entries == scoped_result


@pytest.mark.parametrize("names", [{"one": "../escape"}, {"one": "UPPERCASE"}, {"one": "same", "two": "same"}])
def test_invalid_or_duplicate_locked_names_are_rejected(names):
    with pytest.raises(ValueError):
        builder.assign_install_names([entry("one", "first"), entry("two", "second")], preserved_names=names)


def test_source_lock_is_the_persistent_name_input(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    path = data / "source_lock.json"
    path.write_text(json.dumps({"sources": [{"skills": [{"id": "one", "install_name": "kept"}]}]}), encoding="utf-8")
    assert builder.locked_install_names(tmp_path) == {"one": "kept"}
    path.write_text(
        json.dumps(
            {"sources": [{"skills": [{"id": "one", "install_name": "first"}, {"id": "one", "install_name": "second"}]}]}
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate"):
        builder.locked_install_names(tmp_path)


def test_check_errors_remain_machine_readable_and_distinct_from_drift(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(builder, "ROOT", tmp_path)
    monkeypatch.setattr(builder, "git_latest_commit_epoch_for", lambda *args: 0)

    def refused(*args):
        raise ValueError("source archive required")

    monkeypatch.setattr(builder, "scoped_refresh_inputs", refused)
    assert builder.main(["--refresh-source", "owner/repo", "--check", "--json"]) == 2
    assert json.loads(capsys.readouterr().out) == {"ok": False, "mode": "check", "errors": ["source archive required"]}


def test_first_build_timestamp_seed_is_not_a_malformed_versioned_lock(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    path = data / "source_lock.json"
    path.write_text('{"generated_on":"2026-04-17"}', encoding="utf-8")
    assert builder.locked_install_names(tmp_path) == {}
    path.write_text('{"lock_version":1}', encoding="utf-8")
    with pytest.raises(ValueError, match="source records"):
        builder.locked_install_names(tmp_path)

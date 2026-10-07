"""Whole-output publication preserves originals across late failures."""

from __future__ import annotations

import json
from pathlib import Path

import _catalog_publication as publication
import build_catalog as catalog
import pytest


@pytest.fixture
def transaction(tmp_path):
    root = tmp_path / "workspace"
    root.mkdir()
    original = {"data/catalog.json": "old metadata", "included/skills/SKILL.md": "old skill"}
    for relative, text in original.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs/unrelated.md").write_text("keep unrelated", encoding="utf-8")
    legacy = root / "included/priority"
    legacy.mkdir()
    (legacy / "legacy.txt").write_text("retain retired content", encoding="utf-8")

    def build(staged):
        for relative, text in {
            "data/catalog.json": "new metadata",
            "included/skills/SKILL.md": "new skill",
            "docs/generated.md": "new document",
        }.items():
            path = staged / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    outputs = ("data/catalog.json", "included/skills", "docs/generated.md", "included/priority")
    staged, journal = publication.prepare(root, outputs, build)
    return root, staged, journal, original


def assert_originals(root, original):
    for relative, text in original.items():
        assert (root / relative).read_text(encoding="utf-8") == text
    assert not (root / "docs/generated.md").exists()
    assert (root / "docs/unrelated.md").read_text(encoding="utf-8") == "keep unrelated"
    assert (root / "included/priority/legacy.txt").read_text(encoding="utf-8") == "retain retired content"


def test_complete_publication_retains_previous_outputs_and_unrelated_files(transaction):
    root, staged, journal, original = transaction
    publication.publish(root, staged, journal)
    assert (root / "data/catalog.json").read_text() == "new metadata"
    assert (root / "included/skills/SKILL.md").read_text() == "new skill"
    assert (root / "docs/generated.md").read_text() == "new document"
    assert not (root / "included/priority").exists()
    for relative, text in original.items():
        assert (staged / "previous" / relative).read_text() == text
    assert (staged / "previous/included/priority/legacy.txt").read_text() == "retain retired content"
    assert (root / "docs/unrelated.md").read_text() == "keep unrelated"
    assert json.loads((staged / "journal.json").read_text())["status"] == "published"
    assert not (root / ".venv/generation-staging/publication.lock").exists()


@pytest.mark.parametrize("failure", ["data/catalog.json", "included/skills", "docs/generated.md"])
def test_rename_failure_restores_metadata_mirrors_and_new_outputs(transaction, monkeypatch, failure):
    root, staged, journal, original = transaction
    rename = Path.rename

    def fail(path, target):
        if path == staged / "generated" / failure:
            raise OSError("injected replacement failure")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", fail)
    with pytest.raises(OSError, match="injected replacement"):
        publication.publish(root, staged, journal)
    assert_originals(root, original)
    assert journal["status"] == "rolled_back"
    assert not (root / ".venv/generation-staging/publication.lock").exists()


def test_journal_write_failure_after_rename_still_restores_originals(transaction, monkeypatch):
    root, staged, journal, original = transaction
    write = publication.write_journal
    failed = False

    def fail(transaction, state):
        nonlocal failed
        if not failed and any(operation["installed"] for operation in state["operations"]):
            failed = True
            raise OSError("injected journal failure")
        write(transaction, state)

    monkeypatch.setattr(publication, "write_journal", fail)
    with pytest.raises(OSError, match="injected journal failure"):
        publication.publish(root, staged, journal)
    assert_originals(root, original)
    assert journal["status"] == "rolled_back"


def test_rollback_failure_preserves_lock_and_both_recovery_versions(transaction, monkeypatch):
    root, staged, journal, _ = transaction
    rename = Path.rename

    def fail(path, target):
        if path == staged / "generated/included/skills" or path == root / "data/catalog.json":
            # The first metadata backup must work; fail moving the installed
            # metadata back only after the later mirror replacement has failed.
            if path == root / "data/catalog.json" and not (staged / "previous/data/catalog.json").exists():
                return rename(path, target)
            raise OSError("injected rollback failure")
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", fail)
    with pytest.raises(RuntimeError, match="rollback failed"):
        publication.publish(root, staged, journal)
    assert journal["status"] == "rollback_failed"
    assert (root / ".venv/generation-staging/publication.lock").is_file()
    assert (staged / "previous/data/catalog.json").read_text() == "old metadata"
    assert (root / "data/catalog.json").read_text() == "new metadata"
    assert (root / "included/skills/SKILL.md").read_text() == "old skill"


@pytest.mark.parametrize("location", ["target", "stage"])
def test_modifications_before_publication_are_rejected(transaction, location):
    root, staged, journal, original = transaction
    path = (root if location == "target" else staged / "generated") / "data/catalog.json"
    path.write_text("concurrent edit", encoding="utf-8")
    with pytest.raises(ValueError, match="changed"):
        publication.publish(root, staged, journal)
    assert (root / "included/skills/SKILL.md").read_text() == original["included/skills/SKILL.md"]
    assert not (root / "docs/generated.md").exists()


def test_existing_publisher_lock_is_respected(transaction):
    root, staged, journal, original = transaction
    lock = root / ".venv/generation-staging/publication.lock"
    lock.write_text("other publisher", encoding="utf-8")
    with pytest.raises(FileExistsError):
        publication.publish(root, staged, journal)
    assert_originals(root, original)
    assert lock.read_text() == "other publisher"


def test_check_detects_all_different_outputs_without_replacing_them(transaction):
    root, staged, journal, original = transaction
    assert publication.differences(root, staged, journal) == [item["path"] for item in journal["outputs"]]
    assert_originals(root, original)


@pytest.mark.parametrize(
    "outputs",
    [
        (),
        ("same", "same"),
        ("directory", "directory/child"),
        ("../outside",),
        ("/outside",),
        ("a/../b",),
        ("a\\b",),
        ("a:stream",),
    ],
)
def test_invalid_output_paths_rejected_before_build(tmp_path, outputs):
    called = []
    with pytest.raises(ValueError):
        publication.prepare(tmp_path, outputs, lambda path: called.append(path))
    assert called == []
    assert not (tmp_path / ".venv").exists()


def test_failed_generation_leaves_all_original_outputs_untouched(transaction):
    root, _, _, original = transaction

    def fail(staged):
        (staged / "partial.txt").write_text("partial")
        raise OSError("late generation failure")

    with pytest.raises(OSError, match="late generation"):
        publication.prepare(root, ("data/catalog.json", "included/skills"), fail)
    assert_originals(root, original)


def test_undeclared_generated_file_rejected(transaction):
    root, _, _, original = transaction

    def build(staged):
        (staged / "extra").write_text("extra")

    with pytest.raises(ValueError, match="undeclared"):
        publication.prepare(root, ("data/catalog.json",), build)
    assert_originals(root, original)


def test_unreadable_directory_is_not_treated_as_an_empty_tree(tmp_path, monkeypatch):
    def fail(path, *, onerror, followlinks):
        onerror(PermissionError("unreadable directory"))
        yield str(path), [], []

    monkeypatch.setattr(publication.os, "walk", fail)
    with pytest.raises(PermissionError, match="unreadable"):
        publication.signature(tmp_path)


@pytest.fixture
def complete_generator(tmp_path, monkeypatch):
    root, sources = tmp_path / "workspace", tmp_path / "sources"
    root.mkdir()
    source = sources / "fixture/skills/example"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text(
        "---\nname: example\ndescription: A fixture workflow.\n---\n# Workflow\n", encoding="utf-8"
    )
    (root / "data").mkdir()
    (root / "data/source_lock.json").write_text('{"generated_on": "2026-04-17"}', encoding="utf-8")
    (root / "README.md").write_text("previous README", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs/installation.md").write_text("maintained installation gates", encoding="utf-8")
    (root / ".github").mkdir()
    (root / ".github/readme_badges.json").write_text(
        json.dumps(
            {
                "host": "github.com",
                "owner": "fixture",
                "repo": "example",
                "branch_name": "main",
                "badges": [
                    {
                        "alt": "Gate",
                        "image": "https://example.invalid/{repo_path}/{branch}",
                        "target": "https://example.invalid/{repo_path}",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(catalog, "ROOT", root)
    monkeypatch.setattr(catalog, "SOURCE_ROOT", sources)
    monkeypatch.setattr(
        catalog,
        "SOURCES",
        [
            {
                "repo": "fixture/example",
                "dir": "fixture",
                "tier": "reference",
                "group": "fixture sources",
                "policy": "fixture snapshot",
            }
        ],
    )
    monkeypatch.setattr(
        catalog,
        "run_git",
        lambda path, *args: (
            ""
            if args[0] == "status"
            else "https://example.invalid/fixture.git"
            if args[0] == "config"
            else ("b" * 40 if args[-1] == "HEAD^{tree}" else "a" * 40)
        ),
    )
    monkeypatch.setattr(catalog, "git_latest_commit_epoch_for", lambda root, paths: 1790960401)
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    return root, sources


def test_generator_complete_roundtrip_and_freshness(complete_generator, capsys):
    root, sources = complete_generator
    assert catalog.main(["--source-root", str(sources), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["skills"] == 1
    assert (root / "docs/installation.md").read_text() == "maintained installation gates"
    assert "BEGIN GENERATED BADGES" in (root / "README.md").read_text()
    assert json.loads((root / "data/source_lock.json").read_text())["generated_on"] == "2026-04-17"
    assert root == catalog.ROOT and sources == catalog.SOURCE_ROOT
    before = {relative: publication.signature(root / relative) for relative in catalog.GENERATED_OUTPUTS}
    assert catalog.main(["--source-root", str(sources), "--check", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["different_outputs"] == []
    assert before == {relative: publication.signature(root / relative) for relative in catalog.GENERATED_OUTPUTS}
    (root / "docs/methodology.md").write_text("drift", encoding="utf-8")
    assert catalog.main(["--source-root", str(sources), "--check", "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["different_outputs"] == ["docs/methodology.md"]
    assert (root / "docs/methodology.md").read_text() == "drift"


@pytest.fixture
def scoped_generator(complete_generator, capsys):
    root, sources = complete_generator
    source = sources / "other/skills/unrelated"
    source.mkdir(parents=True)
    (source / "SKILL.md").write_text(
        "---\nname: unrelated\ndescription: An independent fixture.\n---\n# Workflow\n", encoding="utf-8"
    )
    catalog.SOURCES.append({**catalog.SOURCES[0], "repo": "fixture/other", "dir": "other"})
    assert catalog.main(["--source-root", str(sources), "--json"]) == 0
    capsys.readouterr()
    return root, sources


def test_scoped_refresh_uses_only_selected_checkout_and_preserves_other_locks(scoped_generator, monkeypatch, capsys):
    root, sources = scoped_generator
    before = json.loads((root / "data/skills_catalog.json").read_text())
    old_lock = json.loads((root / "data/source_lock.json").read_text())
    retained = next(entry for entry in before if entry["source_repo"] == "fixture/other")
    mirror_signature = publication.signature(root / retained["mirrored_path"])
    # Its source checkout is deliberately unavailable: the locked mirror is the
    # verified input, so a scoped refresh must not access or re-resolve its Git HEAD.
    (sources / "other").rename(sources / "unavailable-other")
    (sources / "fixture/skills/example/new.txt").write_text("new public resource\n", encoding="utf-8")
    original_git = catalog.run_git

    def git(path, *args):
        assert path == sources / "fixture"
        if args == ("rev-parse", "HEAD"):
            return "c" * 40
        return original_git(path, *args)

    monkeypatch.setattr(catalog, "run_git", git)
    arguments = ["--source-root", str(sources), "--refresh-source", "fixture/example", "--json"]
    assert catalog.main(arguments) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["refreshed_sources"] == ["fixture/example"] and result["retained_skills"] == 1
    after = json.loads((root / "data/skills_catalog.json").read_text())
    assert next(entry for entry in after if entry["source_repo"] == "fixture/other") == retained
    assert publication.signature(root / retained["mirrored_path"]) == mirror_signature
    lock = json.loads((root / "data/source_lock.json").read_text())
    assert lock["sources"][1] == old_lock["sources"][1]
    assert lock["sources"][0]["commit_sha"] == "c" * 40
    updated = next(entry for entry in after if entry["source_repo"] == "fixture/example")
    assert (root / updated["mirrored_path"] / "new.txt").read_text() == "new public resource\n"
    assert catalog.main([*arguments, "--check"]) == 0
    assert json.loads(capsys.readouterr().out)["different_outputs"] == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("skill_file_sha256", "b" * 64),
        ("source_path", "other/SKILL.md"),
        ("install_name", "other-name"),
        ("credential_policy_version", 2),
        ("file_modes", {}),
        ("dependency_graph", "unrecorded-graph"),
    ],
)
def test_scoped_refresh_rejects_lock_catalog_disagreement(scoped_generator, field, value):
    root, sources = scoped_generator
    path = root / "data/source_lock.json"
    lock = json.loads(path.read_text())
    lock["sources"][1]["skills"][0][field] = value
    path.write_text(json.dumps(lock), encoding="utf-8")
    before = {relative: publication.signature(root / relative) for relative in catalog.GENERATED_OUTPUTS}
    with pytest.raises(ValueError, match="source lock differs"):
        catalog.main(["--source-root", str(sources), "--refresh-source", "fixture/example"])
    assert before == {relative: publication.signature(root / relative) for relative in catalog.GENERATED_OUTPUTS}
    assert len(catalog.SOURCES) == 2


def test_scoped_refresh_rejects_modified_retained_mirror(scoped_generator):
    root, sources = scoped_generator
    entries = json.loads((root / "data/skills_catalog.json").read_text())
    retained = next(entry for entry in entries if entry["source_repo"] == "fixture/other")
    path = root / retained["mirrored_path"] / "SKILL.md"
    path.write_text("changed mirror", encoding="utf-8")
    with pytest.raises(ValueError, match="mirror changed"):
        catalog.main(["--source-root", str(sources), "--refresh-source", "fixture/example"])
    assert path.read_text() == "changed mirror"


def test_scoped_refresh_does_not_silently_rename_retained_skills(scoped_generator):
    root, sources = scoped_generator
    path = sources / "fixture/skills/example/SKILL.md"
    path.write_text(path.read_text().replace("name: example", "name: unrelated"), encoding="utf-8")
    before = publication.signature(root / "included/skills")
    with pytest.raises(ValueError, match="rename retained"):
        catalog.main(["--source-root", str(sources), "--refresh-source", "fixture/example"])
    assert publication.signature(root / "included/skills") == before
    assert len(catalog.SOURCES) == 2


def test_scoped_refresh_rejects_unknown_source_without_publication(scoped_generator):
    root, sources = scoped_generator
    before = publication.signature(root / "data")
    with pytest.raises(ValueError, match="already locked"):
        catalog.main(["--source-root", str(sources), "--refresh-source", "unknown/repo"])
    assert publication.signature(root / "data") == before


def test_scoped_refresh_requires_selected_source_to_still_contain_skills(scoped_generator):
    root, sources = scoped_generator
    (sources / "fixture/skills/example/SKILL.md").unlink()
    before = publication.signature(root / "included/skills")
    with pytest.raises(ValueError, match="no longer contains"):
        catalog.main(["--source-root", str(sources), "--refresh-source", "fixture/example"])
    assert publication.signature(root / "included/skills") == before
    assert len(catalog.SOURCES) == 2


def test_scoped_refresh_materializes_legacy_git_modes_without_changing_resources(scoped_generator, monkeypatch, capsys):
    root, sources = scoped_generator
    helper = sources / "other/skills/unrelated/helper.sh"
    helper.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8", newline="\n")
    helper.chmod(0o755)
    # Model the legacy index-only executable bit, including NTFS where chmod
    # cannot express it. The staging tree deliberately has no corresponding index.
    monkeypatch.setattr(
        catalog,
        "_git_modes",
        lambda path: {path / "helper.sh": 0o100755} if path.name == "unrelated" and ".venv" not in path.parts else {},
    )
    assert catalog.main(["--source-root", str(sources), "--json"]) == 0
    capsys.readouterr()
    catalog_path = root / "data/skills_catalog.json"
    entries = json.loads(catalog_path.read_text())
    retained = next(entry for entry in entries if entry["source_repo"] == "fixture/other")
    retained.pop("file_modes")
    catalog_path.write_text(json.dumps(entries), encoding="utf-8")
    lock_path = root / "data/source_lock.json"
    lock = json.loads(lock_path.read_text())
    lock["sources"][1]["skills"][0].pop("file_modes")
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    signature = publication.signature(root / retained["mirrored_path"])
    args = ["--source-root", str(sources), "--refresh-source", "fixture/example", "--json"]
    assert catalog.main(args) == 0
    capsys.readouterr()
    new = next(entry for entry in json.loads(catalog_path.read_text()) if entry["id"] == retained["id"])
    assert new["file_modes"]["helper.sh"] == "100755"
    assert {key: value for key, value in new.items() if key != "file_modes"} == retained
    assert publication.signature(root / retained["mirrored_path"]) == signature
    assert json.loads(lock_path.read_text())["sources"][1]["skills"][0]["file_modes"] == new["file_modes"]
    assert catalog.main([*args, "--check"]) == 0
    assert json.loads(capsys.readouterr().out)["different_outputs"] == []


def test_generator_v2_records_policy_and_preserves_original_source(complete_generator, monkeypatch, capsys):
    import validate_source_lock

    root, sources = complete_generator
    original = sources / "fixture/skills/example/SKILL.md"
    text = "---\nname: example\ndescription: " + "sk_" + "live_" + "exampleValue123\n---\n# Workflow\n"
    original.write_text(text, encoding="utf-8", newline="\n")
    old_policy = catalog.CREDENTIAL_POLICY_VERSION
    args = ["--source-root", str(sources), "--credential-policy", "2", "--json"]
    assert catalog.main(args) == 0
    capsys.readouterr()
    assert old_policy == catalog.CREDENTIAL_POLICY_VERSION
    entries = json.loads((root / "data/skills_catalog.json").read_text("utf-8"))
    entry = entries[0]
    lock = json.loads((root / "data/source_lock.json").read_text("utf-8"))
    assert entry["credential_policy_version"] == lock["sources"][0]["skills"][0]["credential_policy_version"] == 2
    assert entry["description"] == "<STRIPE_SERVER_KEY>"
    assert "<STRIPE_SERVER_KEY>" in (root / entry["mirrored_path"] / "SKILL.md").read_text("utf-8")
    assert original.read_text("utf-8") == text
    assert catalog.main([*args, "--check"]) == 0
    assert json.loads(capsys.readouterr().out)["different_outputs"] == []
    monkeypatch.setattr(validate_source_lock, "ROOT", root)
    monkeypatch.setattr(validate_source_lock, "run_git", catalog.run_git)
    report = validate_source_lock.Report()
    validate_source_lock.validate_sources_structure(lock, report)
    validate_source_lock.validate_mirrors(lock, report)
    validate_source_lock.validate_live_checkouts(lock, sources, strict=True, report=report)
    assert report.errors == []


def test_generator_late_failure_does_not_publish_metadata(complete_generator, monkeypatch):
    root, sources = complete_generator
    before = publication.signature(root / "data")

    def fail(*args, **kwargs):
        raise OSError("documentation generation failed after catalog writes")

    monkeypatch.setattr(catalog, "write_docs", fail)
    with pytest.raises(OSError, match="documentation generation failed"):
        catalog.main(["--source-root", str(sources)])
    assert publication.signature(root / "data") == before
    assert (root / "README.md").read_text() == "previous README"
    assert not (root / "included").exists()
    assert root == catalog.ROOT and sources == catalog.SOURCE_ROOT


def test_generator_missing_output_does_not_delete_existing_files(complete_generator, monkeypatch):
    root, sources = complete_generator
    monkeypatch.setattr(catalog, "write_agent_ready_skills", lambda entries: None)
    with pytest.raises(ValueError, match="required generated output is missing"):
        catalog.main(["--source-root", str(sources)])
    assert (root / "README.md").read_text() == "previous README"


def test_catalog_refresh_preserves_independent_schemas_and_artifact_inventories(complete_generator):
    root, sources = complete_generator
    repository = Path(__file__).resolve().parents[1]
    schemas = {path.name: path.read_bytes() for path in (repository / "evaluators").glob("*.schema.json")}
    (root / "evaluators").mkdir()
    for name, content in schemas.items():
        (root / "evaluators" / name).write_bytes(content)
    repair_manifest = root / "included/repaired/skills/manifest.json"
    repair_manifest.parent.mkdir(parents=True)
    repair_manifest.write_text(json.dumps({"repairs": [{"id": "a"}, {"id": "b"}]}), encoding="utf-8")
    adapter_registry = root / "data/external_benchmark_methods.json"
    adapter_registry.write_text(json.dumps({"methods": [{"id": "x"}]}), encoding="utf-8")
    before = {path: path.read_bytes() for path in (repair_manifest, adapter_registry)}
    args = ["--source-root", str(sources)]
    assert catalog.main(args) == 0
    assert catalog.main([*args, "--check"]) == 0
    assert {path.name: path.read_bytes() for path in (root / "evaluators").glob("*.schema.json")} == schemas
    assert all(path.read_bytes() == content for path, content in before.items())
    assert not any(path.startswith("evaluators/") for path in catalog.GENERATED_OUTPUTS)
    readme = (root / "README.md").read_text(encoding="utf-8")
    assert "- `2` repaired skill overlays" in readme
    assert "- `1` selected external benchmark method adapters with smoke artifacts." in readme
    for link in (
        "[Repaired skill readiness](docs/repaired-skill-readiness.md)",
        "[Objective benchmark methods](docs/objective-benchmark-methods.md)",
        "[Contributing guide](CONTRIBUTING.md)",
        "[Changelog](CHANGELOG.md)",
    ):
        assert link in readme
    for gate in (
        "tools/validate_source_lock.py",
        "tools/run_static_benchmarks.py --check",
        "tools/audit_skill_quality.py --check",
        "tools/check_no_secret_patterns.py --history",
        "ruff format --check tools tests",
        "mypy tools tests",
        "pytest -q -n auto",
    ):
        assert gate in readme


def test_unreadable_artifact_inventory_aborts_before_catalog_publication(complete_generator):
    root, sources = complete_generator
    registry = root / "data/external_benchmark_methods.json"
    registry.write_text("invalid JSON", encoding="utf-8")
    before = publication.signature(root / "data")
    with pytest.raises(json.JSONDecodeError):
        catalog.main(["--source-root", str(sources)])
    assert publication.signature(root / "data") == before
    assert (root / "README.md").read_text() == "previous README"


def test_source_head_change_between_collection_and_lock_rejected(complete_generator):
    _, _ = complete_generator
    entries = catalog.collect()
    entries[0]["commit_sha"] = "c" * 40
    with pytest.raises(ValueError, match="HEAD changed after collection"):
        catalog.build_source_lock(entries)


def test_dirty_source_cannot_be_claimed_as_a_pinned_commit(complete_generator, monkeypatch):
    _, sources = complete_generator
    run_git = catalog.run_git
    monkeypatch.setattr(
        catalog,
        "run_git",
        lambda path, *args: " M skills/example/SKILL.md" if args[0] == "status" else run_git(path, *args),
    )
    with pytest.raises(ValueError, match="uncommitted changes"):
        catalog.main(["--source-root", str(sources)])


def test_source_changed_during_collection_rejected(complete_generator, monkeypatch):
    entries = catalog.collect()
    run_git = catalog.run_git
    monkeypatch.setattr(
        catalog,
        "run_git",
        lambda path, *args: " M skills/example/SKILL.md" if args[0] == "status" else run_git(path, *args),
    )
    with pytest.raises(ValueError, match="changed during collection"):
        catalog.build_source_lock(entries)


def test_source_date_epoch_overrides_previous_generation_date(complete_generator, monkeypatch, capsys):
    root, sources = complete_generator
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1790960401")
    assert catalog.main(["--source-root", str(sources), "--json"]) == 0
    capsys.readouterr()
    assert json.loads((root / "data/source_lock.json").read_text())["generated_on"] == "2026-10-02"

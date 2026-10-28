import hashlib
import json
import os
import subprocess

import archive_catalog_source as archive
import pytest
from _source_history import resolve_version


def published_source(tmp_path):
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith(("GIT_AUTHOR_", "GIT_COMMITTER_"))
    }

    def git(*args):
        return (
            subprocess.check_output(
                ["git", "-c", "core.longpaths=true", "-c", "user.name=AI agent", "-c", "user.email=", *args],
                cwd=tmp_path,
                env=environment,
                stderr=subprocess.PIPE,
            )
            .decode()
            .strip()
        )

    git("init")
    content = b"Published original source\n"
    mirror = tmp_path / "included/skills/example/SKILL.md"
    mirror.parent.mkdir(parents=True)
    mirror.write_bytes(content)
    entry = {
        "id": "example",
        "commit_sha": "a" * 40,
        "source_repo": "owner/repo",
        "source_path": "skills/example/SKILL.md",
        "skill_file_sha256": hashlib.sha256(content).hexdigest(),
        "mirrored_path": "included/skills/example",
        "benchmark_scenarios": ["retired-scenario"],
    }
    data = tmp_path / "data"
    data.mkdir()
    (data / "skills_catalog.json").write_text(json.dumps([entry]), encoding="utf-8")
    (data / "benchmark_scenarios.json").write_text(
        json.dumps([{"id": "retired-scenario", "dataset_track_id": "source-skill-repository"}]), encoding="utf-8"
    )
    notice = tmp_path / "artifacts/source-notices/example/LICENSE"
    notice.parent.mkdir(parents=True)
    notice.write_bytes(b"Copyright holder. Permission and disclaimer.\n")
    git("add", ".")
    git("commit", "--no-gpg-sign", "-m", "Record source fixture")
    revision = git("rev-parse", "HEAD")
    arguments = [
        "--root",
        str(tmp_path),
        "--revision",
        revision,
        "--source-repo",
        "owner/repo",
        "--skill-id",
        "example",
        "--notice",
        "artifacts/source-notices/example/LICENSE",
        "--notice-source-path",
        "LICENSE",
        "--json",
    ]
    return arguments, mirror, content


def test_archive_captures_git_input_not_modified_worktree_and_is_idempotent(tmp_path):
    arguments, mirror, content = published_source(tmp_path)
    mirror.write_bytes(b"New worktree source must not become historical evidence\n")
    assert archive.main([*arguments, "--check"]) == 1
    assert not (tmp_path / "data/catalog_source_history.json").exists()
    assert archive.main(arguments) == 0
    version, historical = resolve_version(tmp_path, None, "example", "a" * 40)
    snapshot = tmp_path / version["skill_snapshot"]
    assert historical and snapshot.read_bytes() == content
    assert version["scenarios"] == [{"id": "retired-scenario", "dataset_track_id": "source-skill-repository"}]
    before = (tmp_path / "data/catalog_source_history.json").read_bytes()
    assert archive.main([*arguments, "--check"]) == 0
    assert archive.main(arguments) == 0
    assert (tmp_path / "data/catalog_source_history.json").read_bytes() == before
    assert b"New worktree source" in mirror.read_bytes()


@pytest.mark.parametrize(
    "field,value",
    [("--revision", "main"), ("--source-repo", "other/repo"), ("--skill-id", "unknown"), ("--notice", "../LICENSE")],
)
def test_invalid_archive_selection_publishes_nothing(tmp_path, field, value):
    arguments, _, _ = published_source(tmp_path)
    arguments[arguments.index(field) + 1] = value
    assert archive.main(arguments) == 1
    assert not (tmp_path / "data/catalog_source_history.json").exists()
    assert not (tmp_path / "artifacts/source-history").exists()


def test_drifted_historical_snapshot_is_rejected_without_overwriting_it(tmp_path):
    arguments, _, _ = published_source(tmp_path)
    assert archive.main(arguments) == 0
    record, _ = resolve_version(tmp_path, None, "example", "a" * 40)
    snapshot = tmp_path / record["skill_snapshot"]
    snapshot.write_bytes(b"Drifted historical bytes\n")
    assert archive.main(arguments) == 1
    assert snapshot.read_bytes() == b"Drifted historical bytes\n"


def test_nested_directory_is_not_mistaken_for_the_checkout_root(tmp_path):
    arguments, _, _ = published_source(tmp_path)
    nested = tmp_path / "nested"
    nested.mkdir()
    arguments[arguments.index("--root") + 1] = str(nested)
    assert archive.main(arguments) == 1
    assert not (nested / "data").exists()
    assert not (tmp_path / "data/catalog_source_history.json").exists()


def test_rewritten_revision_preserves_original_provenance(tmp_path):
    arguments, _, _ = published_source(tmp_path)
    current_revision = arguments[arguments.index("--revision") + 1]
    old_revision = "f" * 40
    tree = archive.git_bytes(tmp_path, "rev-parse", current_revision + "^{tree}").decode().strip()
    rewrite_map = tmp_path / "data/history-rewrite-map.json"
    rewrite_map.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "commits": [{"original": old_revision, "replacement": current_revision, "tree": tree}],
            }
        ),
        encoding="utf-8",
    )
    arguments[arguments.index("--revision") + 1] = old_revision
    assert archive.main(arguments) == 0
    history = json.loads((tmp_path / "data/catalog_source_history.json").read_text(encoding="utf-8"))
    assert history["versions"][0]["observed_catalog_revision"] == old_revision
    assert archive.main([*arguments, "--check"]) == 0


@pytest.mark.parametrize("case", ["missing", "duplicate", "wrong_tree", "missing_replacement"])
def test_invalid_rewrite_mapping_is_rejected(tmp_path, case):
    arguments, _, _ = published_source(tmp_path)
    current_revision = arguments[arguments.index("--revision") + 1]
    old_revision = "f" * 40
    tree = archive.git_bytes(tmp_path, "rev-parse", current_revision + "^{tree}").decode().strip()
    item = {"original": old_revision, "replacement": current_revision, "tree": tree}
    if case == "wrong_tree":
        item["tree"] = "e" * 40
    if case == "missing_replacement":
        item["replacement"] = "e" * 40
    if case != "missing":
        rows = [item, item] if case == "duplicate" else [item]
        (tmp_path / "data/history-rewrite-map.json").write_text(
            json.dumps({"schema_version": 1, "commits": rows}), encoding="utf-8"
        )
    arguments[arguments.index("--revision") + 1] = old_revision
    assert archive.main(arguments) == 1
    assert not (tmp_path / "data/catalog_source_history.json").exists()


def test_rewrite_mapping_cannot_reference_unrelated_history(tmp_path):
    arguments, _, _ = published_source(tmp_path)
    current = arguments[arguments.index("--revision") + 1]
    tree = archive.git_bytes(tmp_path, "rev-parse", current + "^{tree}").decode().strip()
    unrelated = (
        subprocess.check_output(
            ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit-tree", tree],
            cwd=tmp_path,
            input=b"Unrelated fixture\n",
        )
        .decode()
        .strip()
    )
    old = "f" * 40
    (tmp_path / "data/history-rewrite-map.json").write_text(
        json.dumps({"schema_version": 1, "commits": [{"original": old, "replacement": unrelated, "tree": tree}]}),
        encoding="utf-8",
    )
    arguments[arguments.index("--revision") + 1] = old
    assert archive.main(arguments) == 1
    assert not (tmp_path / "data/catalog_source_history.json").exists()


def test_invalid_rewrite_json_is_rejected(tmp_path):
    arguments, _, _ = published_source(tmp_path)
    (tmp_path / "data/history-rewrite-map.json").write_text("{", encoding="utf-8")
    arguments[arguments.index("--revision") + 1] = "f" * 40
    assert archive.main(arguments) == 1
    assert not (tmp_path / "data/catalog_source_history.json").exists()

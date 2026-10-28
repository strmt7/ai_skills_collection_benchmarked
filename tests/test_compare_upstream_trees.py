from __future__ import annotations

import copy
import gzip
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import compare_upstream_trees as comparison
import pytest


@pytest.fixture
def git_history(tmp_path: Path):
    repo = tmp_path / "source"
    repo.mkdir()
    environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    git = [
        "git",
        "-c",
        "core.longpaths=true",
        "-c",
        "core.autocrlf=false",
        "-c",
        f"core.hooksPath={tmp_path / 'no-hooks'}",
        "-c",
        f"core.excludesFile={tmp_path / 'no-excludes'}",
        "-c",
        f"core.attributesFile={tmp_path / 'no-attributes'}",
        "-c",
        "commit.gpgsign=false",
        "-C",
        str(repo),
    ]
    subprocess.run([*git, "init", "-q"], check=True, env=environment)

    def put(name: str, text: str) -> None:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def commit(message: str) -> str:
        subprocess.run([*git, "add", "-A"], check=True, env=environment)
        subprocess.run(
            [*git, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", message],
            check=True,
            env=environment,
        )
        return subprocess.check_output([*git, "rev-parse", "HEAD"], env=environment).decode().strip()

    put("SKILL.md", "root skill\n")
    put("skills/alpha/SKILL.md", "old alpha\n")
    put("skills/alpha/reference.txt", "old reference\n")
    put("skills/alpha/a.b", "ordered file\n")
    put("skills/alpha/a-b", "ordered file\n")
    put("skills/alpha/a/nested.txt", "ordered directory\n")
    put("skills/beta/SKILL.md", "old beta\n")
    put("skills/gamma/SKILL.md", "same gamma\n")
    old = commit("old")
    put("skills/alpha/SKILL.md", "new alpha\n")
    put("skills/alpha/new.txt", "new reference\n")
    (repo / "skills/alpha/reference.txt").unlink()
    (repo / "skills/beta/SKILL.md").unlink()
    shutil.copytree(repo / "skills/alpha", repo / "relocated/alpha")
    shutil.copytree(repo / "skills/gamma", repo / "relocated/gamma")
    new = commit("new")

    def objects(revision: str):
        root = subprocess.check_output([*git, "rev-parse", f"{revision}^{{tree}}"], env=environment).decode().strip()
        raw = subprocess.check_output([*git, "ls-tree", "-r", "-t", "-z", "--full-tree", revision], env=environment)
        entries = []
        for record in raw.split(b"\0"):
            if not record:
                continue
            metadata, path = record.split(b"\t", 1)
            mode, kind, sha = metadata.decode().split(" ")
            entries.append({"mode": mode, "type": kind, "sha": sha, "path": path.decode("utf-8")})
        return {"sha": revision, "tree": {"sha": root}}, {"sha": root, "truncated": False, "tree": entries}

    old_commit, old_tree = objects(old)
    new_commit, new_tree = objects(new)
    skills = [{"id": name, "source_path": f"skills/{name}/SKILL.md"} for name in ("alpha", "beta", "gamma")]
    lock = {
        "lock_version": 1,
        "hash_algorithm": "sha256",
        "sources": [{"repo": "example/skills", "commit_sha": old, "skill_count": len(skills), "skills": skills}],
    }
    return lock, old_commit, old_tree, new_commit, new_tree


def test_real_git_trees_produce_complete_resource_deltas(git_history):
    lock, old_commit, old_tree, new_commit, new_tree = git_history
    report = comparison.compare(lock, "example/skills", old_commit, old_tree, new_commit, new_tree, {})
    assert (report["skill_count"], report["changed_skills"], report["missing_new_entrypoints"]) == (3, 2, 1)
    alpha, beta, gamma = report["skills"]
    assert [change["path"] for change in alpha["changes"]] == ["SKILL.md", "new.txt", "reference.txt"]
    assert alpha["changes"][1]["before"] is None and alpha["changes"][2]["after"] is None
    assert beta["new_entrypoint_present"] is False and gamma["changed"] is False
    assert report["measurement_kind"] == "raw_upstream_git_tree_comparison"


def test_repository_root_skill_includes_its_raw_descendant_resources(git_history):
    lock, old_commit, old_tree, new_commit, new_tree = git_history
    source = lock["sources"][0]
    source["skills"] = [{"id": "root", "source_path": "SKILL.md"}]
    source["skill_count"] = 1
    report = comparison.compare(lock, "example/skills", old_commit, old_tree, new_commit, new_tree, {})
    assert report["skills"][0]["changed"] is True
    assert report["skills"][0]["old_resource_count"] > 1


def test_explicit_relocation_compares_corresponding_resource_trees(git_history):
    lock, old_commit, old_tree, new_commit, new_tree = git_history
    report = comparison.compare(
        lock, "example/skills", old_commit, old_tree, new_commit, new_tree, {}, relocation=("skills", "relocated")
    )
    assert report["relocation"] == {"old_prefix": "skills", "new_prefix": "relocated"}
    assert (report["skill_count"], report["changed_skills"], report["missing_new_entrypoints"]) == (3, 2, 1)
    alpha, beta, gamma = report["skills"]
    assert alpha["target_source_path"] == "relocated/alpha/SKILL.md"
    assert [change["path"] for change in alpha["changes"]] == ["SKILL.md", "new.txt", "reference.txt"]
    assert beta["new_entrypoint_present"] is False and gamma["changed"] is False


@pytest.mark.parametrize("relocation", [("missing", "relocated"), ("skills", "missing"), ("skills", "skills")])
def test_relocation_must_bind_distinct_existing_tree_prefixes(git_history, relocation):
    lock, old_commit, old_tree, new_commit, new_tree = git_history
    with pytest.raises(ValueError, match="relocation"):
        comparison.compare(
            lock, "example/skills", old_commit, old_tree, new_commit, new_tree, {}, relocation=relocation
        )


def test_relocation_must_cover_every_locked_entrypoint(git_history):
    lock, old_commit, old_tree, new_commit, new_tree = git_history
    with pytest.raises(ValueError, match="relocation"):
        comparison.compare(
            lock,
            "example/skills",
            old_commit,
            old_tree,
            new_commit,
            new_tree,
            {},
            relocation=("skills/alpha", "relocated/alpha"),
        )


def test_release_tag_must_identify_the_verified_candidate_commit(git_history):
    lock, old_commit, old_tree, new_commit, new_tree = git_history
    release = {"tag_name": "v2.0.0", "draft": False, "prerelease": False, "published_at": "2026-10-01T00:00:00Z"}
    tag = {"ref": "refs/tags/v2.0.0", "object": {"type": "commit", "sha": new_commit["sha"]}}
    report = comparison.compare(
        lock, "example/skills", old_commit, old_tree, new_commit, new_tree, {}, release=release, tag=tag
    )
    assert report["release_evidence"] == {"tag_name": "v2.0.0", "published_at": release["published_at"]}
    for changed_release, changed_tag in (
        ({**release, "draft": True}, tag),
        ({**release, "prerelease": True}, tag),
        ({**release, "published_at": "not-a-date"}, tag),
        ({**release, "published_at": "2026-10-01T00:00:00"}, tag),
        (release, {**tag, "ref": "refs/tags/other"}),
        (release, {**tag, "object": {"type": "commit", "sha": "0" * 40}}),
        (release, {**tag, "object": {"type": "tag", "sha": new_commit["sha"]}}),
        (release, None),
    ):
        with pytest.raises(ValueError, match="release|tag"):
            comparison.compare(
                lock,
                "example/skills",
                old_commit,
                old_tree,
                new_commit,
                new_tree,
                {},
                release=changed_release,
                tag=changed_tag,
            )


@pytest.mark.parametrize("damage", ["truncated", "root", "blob", "duplicate", "missing_parent", "mode"])
def test_tree_integrity_fails_closed(git_history, damage):
    _, _, old_tree, _, _ = git_history
    tree = copy.deepcopy(old_tree)
    if damage == "truncated":
        tree["truncated"] = True
    elif damage == "root":
        tree["sha"] = "0" * 40
    elif damage == "blob":
        next(item for item in tree["tree"] if item["type"] == "blob")["sha"] = "0" * 40
    elif damage == "duplicate":
        tree["tree"].append(copy.deepcopy(tree["tree"][0]))
    elif damage == "missing_parent":
        tree["tree"] = [item for item in tree["tree"] if item["path"] != "skills/alpha"]
    else:
        next(item for item in tree["tree"] if item["type"] == "blob")["mode"] = "000000"
    with pytest.raises(ValueError):
        comparison.verify_tree(tree, old_tree["sha"])


def test_lock_mismatch_and_missing_old_entrypoint_are_rejected(git_history):
    lock, old_commit, old_tree, new_commit, new_tree = git_history
    wrong = copy.deepcopy(lock)
    wrong["sources"][0]["commit_sha"] = "0" * 40
    with pytest.raises(ValueError, match="source lock"):
        comparison.compare(wrong, "example/skills", old_commit, old_tree, new_commit, new_tree, {})
    wrong = copy.deepcopy(lock)
    wrong["hash_algorithm"] = "unknown"
    with pytest.raises(ValueError, match="source lock"):
        comparison.compare(wrong, "example/skills", old_commit, old_tree, new_commit, new_tree, {})
    wrong = copy.deepcopy(lock)
    wrong["sources"][0]["skills"][0]["source_path"] = "skills/missing/SKILL.md"
    with pytest.raises(ValueError, match="absent"):
        comparison.compare(wrong, "example/skills", old_commit, old_tree, new_commit, new_tree, {})


@pytest.mark.parametrize("value", ["", ".", "/absolute", "a/../b", "a//b", "a\\b", "a\0b"])
def test_noncanonical_tree_paths_are_rejected(value):
    with pytest.raises(ValueError):
        comparison.git_path(value)


@pytest.mark.parametrize("text", ['{"a":1,"a":2}', '{"a":NaN}', "[]"])
def test_input_json_is_unambiguous(tmp_path, text):
    path = tmp_path / "input.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError):
        comparison.read_object(path)


def test_compressed_capture_preserves_the_native_response_hash(tmp_path):
    raw = b'{"value": 7}\n'
    path = tmp_path / "capture.json.gz"
    path.write_bytes(gzip.compress(raw, mtime=0))
    value, digest = comparison.read_object(path)
    assert value == {"value": 7}
    assert digest == hashlib.sha256(raw).hexdigest()


def test_compressed_capture_expansion_is_bounded(tmp_path, monkeypatch):
    path = tmp_path / "capture.json.gz"
    path.write_bytes(gzip.compress(b'{"value":"' + b"a" * 1024 + b'"}', mtime=0))
    monkeypatch.setattr(comparison, "MAX_INPUT_BYTES", 64)
    with pytest.raises(ValueError, match="byte limit"):
        comparison.read_object(path)


def test_truncated_compressed_capture_is_rejected(tmp_path):
    path = tmp_path / "capture.json.gz"
    path.write_bytes(gzip.compress(b'{"value": 7}', mtime=0)[:-4])
    with pytest.raises((OSError, EOFError)):
        comparison.read_object(path)


def test_cli_is_deterministic_and_never_overwrites_inputs(git_history, tmp_path, capsys):
    names = ("lock", "old-commit", "old-tree", "new-commit", "new-tree")
    paths = {}
    for name, value in zip(names, git_history, strict=True):
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        paths[name] = path
    output = tmp_path / "report.json"
    argv = ["--repo", "example/skills", "--output", str(output)]
    for name, path in paths.items():
        argv.extend(["--" + name, str(path)])
    assert comparison.main(argv) == 0
    assert json.loads(capsys.readouterr().out)["missing_entrypoints"] == 1
    assert comparison.main([*argv, "--check"]) == 0
    relocated = tmp_path / "relocated.json"
    mapped_argv = [*argv, "--output", str(relocated), "--relocate", "skills", "relocated"]
    assert comparison.main(mapped_argv) == 0
    assert json.loads(relocated.read_text(encoding="utf-8"))["relocation"]["new_prefix"] == "relocated"
    assert comparison.main([*mapped_argv, "--check"]) == 0
    release_path = tmp_path / "release.json"
    tag_path = tmp_path / "tag.json"
    release_path.write_text(
        json.dumps({"tag_name": "v2", "draft": False, "prerelease": False, "published_at": "2026-10-01T00:00:00Z"}),
        encoding="utf-8",
    )
    tag_path.write_text(
        json.dumps({"ref": "refs/tags/v2", "object": {"type": "commit", "sha": git_history[3]["sha"]}}),
        encoding="utf-8",
    )
    released = tmp_path / "released.json"
    release_argv = [*mapped_argv, "--output", str(released), "--release", str(release_path), "--tag", str(tag_path)]
    assert comparison.main(release_argv) == 0
    assert comparison.main([*release_argv, "--check"]) == 0
    tag_path.write_text("{}", encoding="utf-8")
    assert comparison.main([*release_argv, "--check"]) == 1
    assert comparison.main(argv) == 1
    output.write_text("changed", encoding="utf-8")
    assert comparison.main([*argv, "--check"]) == 1
    assert comparison.main([*argv, "--output", str(paths["lock"])]) == 1

from __future__ import annotations

import os
import subprocess

import grade_validator_appcontainer as legacy
import grade_validator_appcontainer_modern as modern
import pytest


def test_support_files_come_from_the_selected_git_commit(tmp_path):
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    subprocess.run(["git", "init", "--quiet", str(fixture)], check=True)
    for name in modern.SUPPORT_FILES:
        path = fixture / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("committed fixture\n", encoding="utf-8")
    environment = {k: v for k, v in os.environ.items() if not k.startswith(("GIT_AUTHOR_", "GIT_COMMITTER_"))}
    git = ["git", "-c", "core.longpaths=true", "-C", str(fixture)]
    subprocess.run([*git, "add", "."], check=True, env=environment)
    subprocess.run(
        [
            *git,
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "--no-gpg-sign",
            "-qm",
            "fixture",
        ],
        check=True,
        env=environment,
    )
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], env=environment).decode().strip()
    (fixture / modern.SUPPORT_FILES[0]).write_text("uncommitted change\n", encoding="utf-8")
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    modern.collect_support(fixture, revision, candidate)
    assert (candidate / modern.SUPPORT_FILES[0]).read_text(encoding="utf-8") == "committed fixture\n"
    with pytest.raises(ValueError, match="exact lowercase"):
        modern.collect_support(fixture, "HEAD", tmp_path / "other")
    assert not (tmp_path / "other").exists()


def test_overlapping_runtime_dependency_and_output_are_refused(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    cache = repo / ".venv"
    cache.mkdir(parents=True)
    monkeypatch.setattr(legacy, "ROOT", repo)
    runtime, deps, output = cache / "runtime", cache / "deps", cache / "output"
    assert modern.checked_homes(runtime, deps, output) == cache.resolve()
    for dependency_home, output_home in [(runtime, output), (deps, deps / "nested"), (cache, output)]:
        with pytest.raises(ValueError):
            modern.checked_homes(runtime, dependency_home, output_home)
        assert not output_home.exists()


def test_runtime_hardlinks_are_rejected_before_granting_access(tmp_path):
    home = tmp_path / "home"
    (home / "runtime").mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.write_bytes(b"private data")
    os.link(outside, home / "runtime" / "linked")
    with pytest.raises(ValueError, match="multiple hard links"):
        legacy.check_unlinked_files(home)
    assert outside.read_bytes() == b"private data"

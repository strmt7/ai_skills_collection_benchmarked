"""GitHub dataset snapshots must bind the URL to the actual Git reference."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import create_independent_runtime_batch as runner
import pytest


@pytest.fixture
def git_repository(tmp_path: Path):
    """Create a private synthetic repository with divergent branches and tags."""
    environment = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}

    def git(*args: str) -> str:
        """Run Git against only the owned temporary fixture."""
        completed = subprocess.run(
            ["git", "-C", str(tmp_path), *args],
            env=environment,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=True,
            timeout=30,
        )
        return completed.stdout.strip()

    git("init", "--initial-branch=main")
    directory = tmp_path / "fixtures"
    directory.mkdir()
    (directory / "file.txt").write_text("first\n", encoding="utf-8")
    git("add", "fixtures/file.txt")
    identity = ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid")
    git(*identity, "commit", "-m", "first")
    first = git("rev-parse", "HEAD")
    git("branch", "feature/nested")
    git("branch", "feature/δ")
    git(*identity, "tag", "-a", "release", "-m", "annotated release")
    (directory / "file.txt").write_text("second\n", encoding="utf-8")
    git("add", "fixtures/file.txt")
    git(*identity, "commit", "-m", "second")
    second = git("rev-parse", "HEAD")
    git("tag", "main", first)
    return tmp_path, environment, git, first, second


def test_dataset_reference_resolution_with_real_git(monkeypatch, git_repository):
    """A slash branch, annotated tag and commit resolve to their actual commit."""
    repo, environment, git, first, second = git_repository
    repo_url = "https://github.com/example/fixture"

    def native_reference_lookup(command, cwd=runner.ROOT):  # noqa: ARG001
        """Replace the network remote with the fixture while retaining Git's ref matching."""
        assert command[:2] == ["git", "ls-remote"]
        command = [str(repo) if item == repo_url else item for item in command]
        completed = subprocess.run(
            command, env=environment, text=True, encoding="utf-8", capture_output=True, check=False, timeout=30
        )
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    def tree_api(url):
        """Build API-shaped evidence from the fixture's real commit and tree."""
        sha = url.split("?")[0].rsplit("/", 1)[-1]
        if "/git/commits/" in url:
            git("cat-file", "-e", sha + "^{commit}")
            return {"sha": sha}
        entries = []
        for line in git("ls-tree", "-r", "-t", sha).splitlines():
            header, path = line.split("\t", 1)
            entries.append({"path": path, "type": header.split()[1]})
        return {"sha": sha, "truncated": False, "tree": entries}

    monkeypatch.setattr(runner, "run_command", native_reference_lookup)
    monkeypatch.setattr(runner, "fetch_json", tree_api)
    for selector, expected_ref in [
        ("feature/nested/fixtures", "refs/heads/feature/nested"),
        ("feature/%CE%B4/fixtures", "refs/heads/feature/δ"),
        ("release/fixtures", "refs/tags/release"),
        (f"{first}/fixtures", first),
    ]:
        snapshot, commands = runner.resolve_dataset_snapshot({"url": f"{repo_url}/tree/{selector}"})
        assert snapshot["resolved"] is True
        assert snapshot["head_sha"] == first != second
        assert snapshot["resolved_ref"] == expected_ref
        assert snapshot["track_subpath"] == "fixtures"
        assert commands

    ambiguous, _ = runner.resolve_dataset_snapshot({"url": f"{repo_url}/tree/main/fixtures"})
    assert ambiguous["resolved"] is False
    assert "ambiguous" in ambiguous["tree_error"]


@pytest.mark.parametrize("kind,path", [("tree", "fixtures/file.txt"), ("blob", "fixtures")])
def test_dataset_url_requires_matching_object_type(monkeypatch, kind, path):
    """A file cannot satisfy a tree URL and a directory cannot satisfy a blob URL."""
    sha = "a" * 40
    monkeypatch.setattr(
        runner,
        "run_command",
        lambda command, **kwargs: {
            "command": command,
            "returncode": 0,
            "stdout": f"{sha}\trefs/heads/main",
            "stderr": "",
        },
    )
    monkeypatch.setattr(
        runner,
        "fetch_json",
        lambda url: {
            "sha": sha,
            "truncated": False,
            "tree": [{"path": "fixtures", "type": "tree"}, {"path": "fixtures/file.txt", "type": "blob"}],
        },
    )
    snapshot, _ = runner.resolve_dataset_snapshot({"url": f"https://github.com/o/r/{kind}/main/{path}"})
    assert snapshot["resolved"] is False
    assert snapshot["track_subpath_present"] is False


def test_unsupported_github_url_does_not_fall_back_to_head_request(monkeypatch):
    """Unsupported GitHub routes cannot pass as generic reachable datasets."""
    monkeypatch.setattr(runner.urllib.request, "urlopen", lambda *args, **kwargs: pytest.fail("unexpected request"))
    snapshot, commands = runner.resolve_dataset_snapshot({"url": "https://github.com/o/r/issues/1"})
    assert snapshot["resolved"] is False
    assert commands == []


@pytest.mark.parametrize("advertisement", ["", "invalid\trefs/heads/missing", f"{'a' * 40} refs/heads/missing"])
def test_missing_or_malformed_ref_cannot_resolve(monkeypatch, advertisement):
    """Missing or invalid advertisements cannot be treated as repository evidence."""
    monkeypatch.setattr(
        runner,
        "run_command",
        lambda command, **kwargs: {"command": command, "returncode": 0, "stdout": advertisement, "stderr": ""},
    )
    monkeypatch.setattr(runner, "fetch_json", lambda url: pytest.fail("unexpected tree request"))
    snapshot, _ = runner.resolve_dataset_snapshot({"url": "https://github.com/o/r/tree/missing/fixtures"})
    assert snapshot["resolved"] is False
    assert snapshot["tree_error"]


def test_annotated_tag_target_must_be_a_verified_commit(monkeypatch):
    """A tag target without a matching commit response cannot become a snapshot."""
    sha = "a" * 40
    monkeypatch.setattr(
        runner,
        "run_command",
        lambda command, **kwargs: {
            "command": command,
            "returncode": 0,
            "stdout": f"{'b' * 40}\trefs/tags/v1\n{sha}\trefs/tags/v1^{{}}",
            "stderr": "",
        },
    )
    monkeypatch.setattr(runner, "fetch_json", lambda url: {"sha": "c" * 40})
    snapshot, _ = runner.resolve_dataset_snapshot({"url": "https://github.com/o/r/tree/v1/fixtures"})
    assert snapshot["resolved"] is False
    assert snapshot["tree_error"] == "reference target is not the requested commit"


def test_reference_lookup_timeout_is_recorded_and_fails_closed(monkeypatch):
    """A stuck Git process produces a failed snapshot and retained command evidence."""

    def timeout(command, **kwargs):
        """Emulate Git exceeding the configured bounded execution time."""
        assert kwargs["timeout"] == 60
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(runner.subprocess, "run", timeout)
    snapshot, commands = runner.resolve_dataset_snapshot({"url": "https://github.com/o/r/tree/main/fixtures"})
    assert snapshot["resolved"] is False
    assert "TimeoutExpired" in commands[0]["stderr"]

from __future__ import annotations

from pathlib import Path

import fetch_research_sources as sources
import pytest


@pytest.mark.parametrize(
    "repo", ["../outside/repo", "owner/../repo", "-switch/repo", "https://host/repo", "owner/repo/extra"]
)
def test_checkout_paths_reject_remote_or_path_injection(tmp_path, repo):
    with pytest.raises(ValueError):
        sources.source_directory(tmp_path, repo)


def test_owner_content_never_enters_public_research_queue():
    assert not sources.eligible({"repo": "strmt7/project", "status": "update_available"})
    assert not sources.eligible({"repo": "ZMB-UZH/project", "status": "current"})
    assert not sources.eligible({"repo": "author/skills", "status": "error"})
    assert sources.eligible({"repo": "author/skills", "status": "current"})


def test_existing_different_checkout_is_never_overwritten(tmp_path, monkeypatch):
    (tmp_path / "author__skills").mkdir()
    calls = []

    def git(directory: Path, *args):
        calls.append(args)
        return "b" * 40

    monkeypatch.setattr(sources, "git", git)
    result = sources.fetch(
        {"repo": "author/skills", "canonical_repo": "author/skills", "current_commit": "a" * 40}, tmp_path
    )
    assert result["status"] == "error"
    assert calls == [("rev-parse", "HEAD")]


def test_check_mode_never_fetches_missing_checkout(tmp_path, monkeypatch):
    def git(*args):
        pytest.fail("check mode must not run Git on missing checkout")

    monkeypatch.setattr(sources, "git", git)
    result = sources.fetch(
        {"repo": "author/skills", "canonical_repo": "author/skills", "current_commit": "a" * 40}, tmp_path, check=True
    )
    assert result["status"] == "error"

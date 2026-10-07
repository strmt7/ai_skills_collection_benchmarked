from __future__ import annotations

import subprocess
from pathlib import Path

import verify_dependency_lock as lockcheck


def test_metadata_does_not_mask_changed_versions_or_hashes():
    assert lockcheck.requirement_lines("# command\nfoo==1\n  --hash=sha256:a\n # via project\n") == [
        "foo==1",
        "--hash=sha256:a",
    ]
    assert lockcheck.requirement_lines("foo==1\n") != lockcheck.requirement_lines("foo==2\n")
    assert lockcheck.requirement_lines("--hash=sha256:a\n") != lockcheck.requirement_lines("--hash=sha256:b\n")


def test_resolver_is_seeded_and_original_is_never_rewritten(tmp_path, monkeypatch):
    project = tmp_path / "pyproject.toml"
    project.write_text("[project]\n", encoding="utf-8")
    lock = tmp_path / "requirements-lock.txt"
    lock.write_text("foo==1\n", encoding="utf-8")

    def run(command, **kwargs):
        target = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("--output-file=")))
        assert target != lock
        assert target.read_text(encoding="utf-8") == "foo==1\n"
        assert "--upgrade" not in command
        target.write_text("foo==2\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(lockcheck.subprocess, "run", run)
    assert not lockcheck.verify(project, lock)["valid"]
    assert lock.read_text(encoding="utf-8") == "foo==1\n"


def test_resolver_failure_fails_closed(tmp_path, monkeypatch):
    lock = tmp_path / "requirements-lock.txt"
    lock.write_text("foo==1\n", encoding="utf-8")
    monkeypatch.setattr(
        lockcheck.subprocess, "run", lambda command, **kwargs: subprocess.CompletedProcess(command, 1, "", "failed")
    )
    result = lockcheck.verify(tmp_path / "pyproject.toml", lock)
    assert not result["valid"]
    assert result["diagnostic"] == "failed"

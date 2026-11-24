from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import verify_dependency_lock as lockcheck
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


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


def test_report_lock_checks_report_extra_without_development_dependencies(tmp_path, monkeypatch):
    project = tmp_path / "pyproject.toml"
    project.write_text("[project]\n", encoding="utf-8")
    lock = tmp_path / "reports.txt"
    lock.write_text("pillow==13.0.0\n", encoding="utf-8")

    def run(command, **kwargs):
        assert [arg for arg in command if arg.startswith("--extra=")] == ["--extra=reports"]
        target = Path(next(arg.split("=", 1)[1] for arg in command if arg.startswith("--output-file=")))
        assert target.read_bytes() == lock.read_bytes()
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(lockcheck.subprocess, "run", run)
    assert lockcheck.verify(project, lock, ("reports",))["valid"]


def test_report_extra_cli_reaches_seeded_verifier(tmp_path, monkeypatch, capsys):
    project, lock = tmp_path / "pyproject.toml", tmp_path / "reports.txt"

    def verify(actual_project, actual_lock, extras):
        assert (actual_project, actual_lock, extras) == (project, lock, ("reports",))
        return {"valid": True, "errors": []}

    monkeypatch.setattr(lockcheck, "verify", verify)
    assert lockcheck.main(["--project", str(project), "--lock", str(lock), "--extra", "reports", "--json"]) == 0
    assert '"valid": true' in capsys.readouterr().out


@pytest.mark.parametrize(
    "lock_files",
    [
        ("requirements-lock.txt", "requirements-reports-lock.txt", "requirements-coverage-lock.txt"),
        ("requirements-dev-lock.txt", "requirements-reports-lock.txt"),
    ],
)
def test_coinstalled_locks_agree_on_active_versions(lock_files: tuple[str, ...]) -> None:
    versions_by_package: dict[str, dict[str, list[str]]] = {}
    for filename in lock_files:
        text = (lockcheck.ROOT / filename).read_text(encoding="utf-8")
        for line in lockcheck.requirement_lines(text):
            if line.startswith("--hash="):
                continue
            requirement = Requirement(line.removesuffix("\\").rstrip())
            if requirement.marker is not None and not requirement.marker.evaluate():
                continue
            versions = versions_by_package.setdefault(canonicalize_name(requirement.name), {})
            versions.setdefault(str(requirement.specifier), []).append(filename)

    conflicts = {package: versions for package, versions in versions_by_package.items() if len(versions) > 1}
    assert not conflicts, f"Coinstalled dependency locks disagree on active versions: {conflicts}"

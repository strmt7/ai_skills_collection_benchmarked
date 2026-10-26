"""Validate the wire, archive and path boundaries without running submitted code."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import zipfile

import appcontainer_runtime as runtime
import appcontainer_validator_worker as worker
import grade_validator_appcontainer as grader
import pytest
from _validator_cases import accepted
from _windows_appcontainer import checked_mounts, checked_path, checked_tree


@pytest.mark.parametrize("payload", [b'{"a":1,"a":2}', b'{"score":NaN}', b"[] trailing", b"\xff", b"[" * 1200])
def test_invalid_wire_is_a_failed_response(tmp_path, payload):
    path = tmp_path / "response"
    path.write_bytes(payload)
    assert grader.parse_response(path) == {"kind": "invalid_response"}


@pytest.mark.parametrize("verdict", [[], {}, None, 1, False])
def test_untrusted_verdict_types_cannot_crash_the_oracle(verdict):
    response = {"kind": "candidate_result", "value": {"verdict": verdict, "errors": ["bad"], "warnings": []}}
    assert not accepted(response, False)
    assert not accepted(response, True)


def test_worker_reports_a_candidate_exception_without_an_expected_result(tmp_path, capsys):
    source = tmp_path / "candidate.py"
    source.write_text("def validate_artifact(path):\n raise ValueError('broken')\n", encoding="utf-8")
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"module": str(source), "artifact": str(tmp_path / "artifact")}), encoding="utf-8")
    assert worker.main([str(request)]) == 0
    assert json.loads(capsys.readouterr().out) == {"kind": "candidate_error", "exception_type": "ValueError"}


@pytest.mark.parametrize("name", ["../escaped", "/absolute", "C:/drive", "dir\\file"])
def test_runtime_refuses_archive_path_escapes(tmp_path, name):
    archive = tmp_path / "input.zip"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr(name.replace("\\", "/"), "not installed")
    if "\\" in name:
        # Windows' ZipInfo normalizes backslashes even while constructing an
        # entry. Preserve an actual hostile wire name in both ZIP headers.
        archive.write_bytes(archive.read_bytes().replace(name.replace("\\", "/").encode(), name.encode()))
    specification = {
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": runtime.digest(archive),
        "files": {},
    }
    with pytest.raises(ValueError, match="escaping path"):
        runtime.setup(tmp_path / "provider", archive, specification)
    assert not (tmp_path / "escaped").exists()


def test_runtime_archive_capture_stops_at_its_byte_budget(tmp_path):
    archive = tmp_path / "oversized.zip"
    archive.write_bytes(b"123456789")
    home = tmp_path / "provider"
    home.mkdir()
    with pytest.raises(ValueError, match="exceeds the pinned byte count"):
        runtime.capture(home, archive, {"archive_bytes": 4})
    assert (home / "python.zip").stat().st_size <= 5


def test_runtime_verifies_the_complete_file_graph(tmp_path):
    installed = tmp_path / "runtime"
    installed.mkdir()
    file = installed / "python.exe"
    file.write_bytes(b"pinned fixture")
    pin = {"files": {"python.exe": hashlib.sha256(file.read_bytes()).hexdigest()}}
    assert runtime.verify(tmp_path, pin) == []
    (installed / "extra.py").write_text("pass", encoding="utf-8")
    assert runtime.verify(tmp_path, pin) == ["unexpected runtime file: extra.py"]
    file.write_bytes(b"changed")
    assert "missing or changed runtime file: python.exe" in runtime.verify(tmp_path, pin)


def test_junction_or_symlink_is_rejected_before_traversal(tmp_path):
    external = tmp_path / "external"
    external.mkdir()
    (external / "sentinel").write_text("preserved", encoding="utf-8")
    mount = tmp_path / "mount"
    mount.mkdir()
    link = mount / "redirect"
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(external)], check=True, capture_output=True)
    else:
        link.symlink_to(external, target_is_directory=True)
    try:
        with pytest.raises(ValueError, match="Reparse"):
            checked_tree(mount)
        with pytest.raises(ValueError, match="Reparse"):
            checked_path(link / "sentinel")
        assert (external / "sentinel").read_text() == "preserved"
    finally:
        if os.name == "nt":
            link.rmdir()
        else:
            link.unlink()


def test_mounts_refuse_output_inside_a_candidate_tree_and_reused_scratch(tmp_path):
    readable, scratch = tmp_path / "read", tmp_path / "scratch"
    readable.mkdir()
    scratch.mkdir()
    executable = readable / "python.exe"
    executable.touch()
    with pytest.raises(ValueError, match="outside every candidate mount"):
        checked_mounts(tmp_path, [readable], scratch, executable, readable / "output")
    (scratch / "old").touch()
    with pytest.raises(ValueError, match="new empty scratch"):
        checked_mounts(tmp_path, [readable], scratch, executable, tmp_path / "observations")


def test_collection_uses_git_blobs_and_refuses_a_nonexact_revision(tmp_path):
    repository = tmp_path / "fixture"
    repository.mkdir()
    subprocess.run(["git", "init", "--quiet", str(repository)], check=True)
    for name in grader.TASK_FILES:
        target = repository / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"committed fixture\n")
    subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(repository), "-c", "user.name=AI agent", "-c", "user.email=", "commit", "-qm", "fixture"],
        check=True,
    )
    revision = subprocess.check_output(["git", "-C", str(repository), "rev-parse", "HEAD"]).decode().strip()
    (repository / grader.TASK_FILES[0]).write_bytes(b"uncommitted change\n")
    submission = tmp_path / "submission"
    (submission / "tools").mkdir(parents=True)
    (submission / "tools/check_benchmark_artifact.py").write_bytes(b"pass\n")
    grader.collect_candidate(submission, repository, revision, tmp_path / "collected")
    assert (tmp_path / "collected" / grader.TASK_FILES[0]).read_bytes() == b"committed fixture\n"
    with pytest.raises(ValueError, match="exact lowercase"):
        grader.collect_candidate(submission, repository, "HEAD", tmp_path / "bad")


def test_invalid_runtime_location_has_no_output_side_effects(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(grader, "ROOT", tmp_path / "repo")
    output = tmp_path / "outside"
    assert (
        grader.main(
            [
                "--submission",
                str(tmp_path),
                "--fixture",
                str(tmp_path),
                "--runtime-home",
                str(tmp_path / "runtime"),
                "--output",
                str(output),
                "--revision",
                "0" * 40,
            ]
        )
        == 2
    )
    assert not output.exists()
    assert json.loads(capsys.readouterr().out)["status"] == "harness_error"

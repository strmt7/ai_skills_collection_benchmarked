"""Validate the wire, archive and path boundaries without running submitted code."""

from __future__ import annotations

import ctypes
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from ctypes import wintypes

import appcontainer_runtime as runtime
import appcontainer_validator_worker as worker
import grade_validator_appcontainer as grader
import pytest
import qualify_appcontainer as qualification
from _validator_cases import accepted
from _windows_appcontainer import Native, checked_mounts, checked_path, checked_tree


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


def test_older_runtime_without_an_acl_receipt_is_not_modified(tmp_path):
    home = tmp_path / "old-runtime"
    home.mkdir()
    marker = home / "existing-file"
    marker.write_bytes(b"preserved")
    errors = runtime.verify_private_home(home, {"archive_sha256": hashlib.sha256(b"archive").hexdigest()})
    assert errors == ["Private runtime ACL receipt is missing; set up a new dedicated runtime home"]
    assert marker.read_bytes() == b"preserved"


@pytest.mark.skipif(sys.platform != "win32", reason="Native Windows ACL and file-lock controls require Windows")
def test_private_runtime_detects_acl_drift_and_rejects_concurrent_lease(tmp_path, monkeypatch):
    home = tmp_path / ".venv/private-runtime"
    directory = home / "runtime"
    directory.mkdir(parents=True)
    file = directory / "python.exe"
    file.write_bytes(b"controlled fixture")
    pin = {"archive_sha256": hashlib.sha256(b"archive").hexdigest()}
    (home / "source.json").write_text(json.dumps(pin), encoding="utf-8")
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    runtime._prepare_private_home(home, pin)
    native = Native()
    original = native.descriptor(file)
    assert runtime.verify_private_home(home, pin) == []
    with pytest.raises(ValueError, match="already has an isolation receipt"):
        runtime._prepare_private_home(home, pin)
    with runtime.lease(home, pin), pytest.raises(RuntimeError, match="in use"), runtime.lease(home, pin):
        pass
    with runtime.lease(home, pin):
        child = (
            "import sys\nsys.path.insert(0,sys.argv[1])\nfrom pathlib import Path\nimport appcontainer_runtime as r\n"
            "try:\n with r.lease(Path(sys.argv[2]),{'archive_sha256':sys.argv[3]}): pass\n"
            "except RuntimeError:\n print('busy')\nelse:\n raise SystemExit(1)\n"
        )
        other = subprocess.run(
            [sys.executable, "-I", "-S", "-c", child, str(grader.ROOT / "tools"), str(home), pin["archive_sha256"]],
            capture_output=True,
            timeout=10,
        )
        assert other.returncode == 0 and other.stdout.strip() == b"busy", other.stderr.decode(errors="replace")
    with pytest.raises(ValueError, match="controlled failure"), runtime.lease(home, pin):
        raise ValueError("controlled failure")
    with runtime.lease(home, pin):
        pass
    try:
        native.grant(file, native.owner_sid(), "S-1-15-2-1")
        assert runtime.verify_private_home(home, pin) == [
            "Private runtime ACL descriptors differ from the setup baseline"
        ]
    finally:
        native.set_descriptor(file, ctypes.create_string_buffer(original))
    assert runtime.verify_private_home(home, pin) == []


@pytest.mark.skipif(sys.platform != "win32", reason="Native Windows ACL controls require Windows")
def test_private_runtime_normalizes_legacy_inheritance_before_recording(tmp_path, monkeypatch):
    home = tmp_path / ".venv/legacy-runtime"
    directory = home / "runtime"
    directory.mkdir(parents=True)
    file = directory / "python.exe"
    file.write_bytes(b"controlled fixture")
    pin = {"archive_sha256": hashlib.sha256(b"archive").hexdigest()}
    (home / "source.json").write_text(json.dumps(pin), encoding="utf-8")
    monkeypatch.setattr(runtime, "ROOT", tmp_path)
    native = Native()
    descriptor = ctypes.create_string_buffer(native.descriptor(file))
    # The obsolete API is used only to reproduce the hosted legacy flag in an owned fixture.
    set_control = native.function(
        "security", "SetSecurityDescriptorControl", [ctypes.c_void_p, wintypes.WORD, wintypes.WORD], wintypes.BOOL
    )
    set_file = native.function(
        "security", "SetFileSecurityW", [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p], wintypes.BOOL
    )
    assert set_control(descriptor, 0x0400, 0)
    assert set_file(str(file), 4, descriptor)
    assert not int.from_bytes(native.descriptor(file)[2:4], "little") & 0x0400
    runtime._prepare_private_home(home, pin)
    assert int.from_bytes(native.descriptor(file)[2:4], "little") & 0x0400
    original = native.descriptor(directory)
    with runtime.lease(home, pin):
        try:
            native.grant(directory, native.owner_sid(), "S-1-15-2-1")
        finally:
            native.set_descriptor(directory, ctypes.create_string_buffer(original))
    assert runtime.verify_private_home(home, pin) == []
    assert file.read_bytes() == b"controlled fixture"


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


def test_collection_uses_git_blobs_and_refuses_a_nonexact_revision(tmp_path, monkeypatch):
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
    if sys.platform != "win32":
        monkeypatch.setattr(
            grader, "read_submission", lambda root: (root / "tools/check_benchmark_artifact.py").read_bytes()
        )
    grader.collect_candidate(submission, repository, revision, tmp_path / "collected")
    assert (tmp_path / "collected" / grader.TASK_FILES[0]).read_bytes() == b"committed fixture\n"
    with pytest.raises(ValueError, match="exact lowercase"):
        grader.collect_candidate(submission, repository, "HEAD", tmp_path / "bad")


@pytest.mark.skipif(sys.platform != "win32", reason="Windows native handle boundary")
def test_legacy_collection_refuses_a_hardlinked_submission(tmp_path):
    submission = tmp_path / "submission"
    (submission / "tools").mkdir(parents=True)
    external = tmp_path / "external"
    external.write_bytes(b"controlled sentinel\n")
    os.link(external, submission / "tools/check_benchmark_artifact.py")
    with pytest.raises(ValueError, match="one link"):
        grader.collect_candidate(submission, tmp_path, "0" * 40, tmp_path / "collected")
    assert not (tmp_path / "collected").exists()
    assert external.read_bytes() == b"controlled sentinel\n"


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


def test_qualification_binds_git_fixture_bytes_across_line_endings(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "--quiet", str(tmp_path)], check=True)
    name = "data/skills_catalog.json"
    path = tmp_path / name
    path.parent.mkdir()
    path.write_bytes(b"[]\n")
    (tmp_path / ".gitattributes").write_bytes(b"data/*.json text eol=lf\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "-c", "user.name=AI agent", "-c", "user.email=", "commit", "-qm", "fixture"],
        check=True,
    )
    path.write_bytes(b"[]\r\n")
    monkeypatch.setattr(qualification, "ROOT", tmp_path)
    monkeypatch.setattr(qualification, "SOURCE_FILES", (name,))
    assert qualification.source_graph() == [
        {"path": name, "sha256": hashlib.sha256(b"[]\n").hexdigest(), "source_kind": "git_fixture_blob"}
    ]


def test_historical_qualification_checks_archived_sources_without_claiming_current_qualification(tmp_path, monkeypatch):
    result = qualification.check()
    assert result["ok"] and result["historical_source_snapshots"]
    assert result["current_source_qualified"] is False
    for path in qualification.HISTORICAL_SOURCES.iterdir():
        (tmp_path / path.name).write_bytes(path.read_bytes())
    (tmp_path / "grade_validator_appcontainer.py.txt").write_bytes(b"changed\n")
    monkeypatch.setattr(qualification, "HISTORICAL_SOURCES", tmp_path)
    assert "Native qualification source graph is stale" in qualification.check()["errors"]


def test_evaluator_fingerprints_detect_changed_source_bytes(tmp_path, monkeypatch):
    source = tmp_path / "tools/public.py"
    source.parent.mkdir()
    source.write_bytes(b"first version\n")
    monkeypatch.setattr(grader, "ROOT", tmp_path)
    monkeypatch.setattr(grader, "EVALUATOR_FILES", ("tools/public.py",))
    original = grader.evaluator_fingerprints()
    assert original == [{"path": "tools/public.py", "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}]
    source.write_bytes(b"changed version\n")
    assert grader.evaluator_fingerprints()[0]["sha256"] != original[0]["sha256"]

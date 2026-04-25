"""Logic tests for tools/validate_source_lock.py.

Exercises the real source_lock.json + mirror tree. These are end-to-end tests:
a failure here means the tool's invariants or the committed data drifted, not
that a mock was misconfigured.
"""

from __future__ import annotations

import importlib
import io
import json
from contextlib import redirect_stderr, redirect_stdout

validate_source_lock = importlib.import_module("validate_source_lock")  # tools/ on sys.path via conftest


def test_default_invocation_runs_clean():
    """No-args invocation must succeed on a fresh clone and report mirror checks."""
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = validate_source_lock.main([])
    assert rc == 0, f"stderr: {err.getvalue()}"
    assert "OK:" in out.getvalue()
    assert "mirror_skills=" in out.getvalue()


def test_json_mode_emits_valid_envelope():
    out = io.StringIO()
    with redirect_stdout(out):
        rc = validate_source_lock.main(["--json"])
    assert rc == 0
    payload = json.loads(out.getvalue())
    for key in (
        "mode",
        "ok",
        "errors",
        "checked_sources",
        "checked_source_skills",
        "checked_mirror_skills",
        "source_root",
    ):
        assert key in payload, f"missing key {key!r} in JSON envelope"
    assert payload["ok"] is True
    assert payload["errors"] == []
    assert payload["mode"] == "offline"
    assert payload["checked_mirror_skills"] > 0


def test_missing_source_root_env_var_does_not_break_offline(monkeypatch):
    monkeypatch.delenv("AI_SKILL_SOURCE_ROOT", raising=False)
    assert validate_source_lock.resolve_source_root(None) is None


def test_env_var_pointing_at_nonexistent_dir_is_ignored(monkeypatch):
    monkeypatch.setenv("AI_SKILL_SOURCE_ROOT", "/definitely/does/not/exist/anywhere")
    assert validate_source_lock.resolve_source_root(None) is None


def test_explicit_source_root_is_used_even_if_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("AI_SKILL_SOURCE_ROOT", raising=False)
    # An explicitly passed path is always resolved (the user asked for live mode).
    missing = tmp_path / "missing-checkouts"
    result = validate_source_lock.resolve_source_root(str(missing))
    assert result == missing.resolve()


def test_unsupported_version_is_reported(tmp_path):
    bad_lock = {"lock_version": 999, "hash_algorithm": "sha256", "sources": []}
    path = tmp_path / "bad_lock.json"
    path.write_text(json.dumps(bad_lock), encoding="utf-8")
    err = io.StringIO()
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = validate_source_lock.main(["--lock", str(path)])
    assert rc == 1
    combined = err.getvalue()
    assert "unsupported lock_version" in combined


def test_duplicate_skill_id_is_reported(tmp_path):
    lock = {
        "lock_version": 1,
        "hash_algorithm": "sha256",
        "sources": [
            {
                "repo": "a/a",
                "origin_url": "",
                "local_dir": "a",
                "commit_sha": "x",
                "tree_sha": "y",
                "skill_count": 1,
                "skills": [{"id": "dup-id", "source_path": "p", "skill_file_sha256": "f", "skill_dir_sha256": "d"}],
            },
            {
                "repo": "b/b",
                "origin_url": "",
                "local_dir": "b",
                "commit_sha": "x",
                "tree_sha": "y",
                "skill_count": 1,
                "skills": [{"id": "dup-id", "source_path": "p", "skill_file_sha256": "f", "skill_dir_sha256": "d"}],
            },
        ],
    }
    path = tmp_path / "dup_lock.json"
    path.write_text(json.dumps(lock), encoding="utf-8")
    err = io.StringIO()
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = validate_source_lock.main(["--lock", str(path)])
    assert rc == 1
    assert "duplicate skill id 'dup-id'" in err.getvalue()


def test_skill_count_mismatch_is_reported(tmp_path):
    lock = {
        "lock_version": 1,
        "hash_algorithm": "sha256",
        "sources": [
            {
                "repo": "a/a",
                "origin_url": "",
                "local_dir": "a",
                "commit_sha": "x",
                "tree_sha": "y",
                "skill_count": 99,  # wrong
                "skills": [{"id": "one", "source_path": "p", "skill_file_sha256": "f", "skill_dir_sha256": "d"}],
            },
        ],
    }
    path = tmp_path / "bad_count.json"
    path.write_text(json.dumps(lock), encoding="utf-8")
    err = io.StringIO()
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = validate_source_lock.main(["--lock", str(path)])
    assert rc == 1
    assert "skill_count != len(skills)" in err.getvalue()


def test_missing_required_skill_field_is_reported(tmp_path):
    lock = {
        "lock_version": 1,
        "hash_algorithm": "sha256",
        "sources": [
            {
                "repo": "a/a",
                "origin_url": "",
                "local_dir": "a",
                "commit_sha": "x",
                "tree_sha": "y",
                "skill_count": 1,
                "skills": [{"id": "one", "source_path": "p"}],  # missing file/dir hashes
            },
        ],
    }
    path = tmp_path / "bad_skill.json"
    path.write_text(json.dumps(lock), encoding="utf-8")
    err = io.StringIO()
    out = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = validate_source_lock.main(["--lock", str(path)])
    assert rc == 1
    assert "missing field" in err.getvalue()


def test_mirror_hash_check_is_stable_across_runs():
    """Running the validator twice must produce the same exit code and same JSON envelope
    (proves the lock + mirror + portable-hash triple is internally deterministic)."""

    def capture():
        out = io.StringIO()
        with redirect_stdout(out):
            rc = validate_source_lock.main(["--json"])
        return rc, out.getvalue()

    rc1, body1 = capture()
    rc2, body2 = capture()
    assert rc1 == rc2 == 0
    assert body1 == body2

"""Controls for the fail-closed Gitleaks history gate."""

import json
import os
from pathlib import Path

import _gitleaks_history_worker as worker
import check_gitleaks_history as gate
import pytest


def outcome(*, code=0, stderr=b"", stdout=b"", reason=None):
    """Describe one completed or interrupted supervised scan."""
    return {"exit_code": code, "stderr": stderr, "stdout": stdout, "termination_reason": reason}


def test_scanner_diagnostics_override_a_successful_exit(tmp_path):
    """A zero exit code cannot turn Git errors into a successful scan."""
    result = gate.evaluate(outcome(stderr=b"Git reported a diagnostic"), tmp_path, None)
    assert result["passed"] is False
    assert result["reason"] == "scanner_diagnostics"
    assert result["diagnostic_bytes"] > 0


def test_redacted_finding_is_reported_as_failure(tmp_path):
    """Retain scanner evidence while failing on a reported finding."""
    result = gate.evaluate(
        outcome(code=1, stderr=b"10:32PM WRN leaks found: 1\n", stdout=b"Finding: redacted\n"), tmp_path, None
    )
    assert result["passed"] is False
    assert result["findings"] == 1
    assert result["redacted_output"] == "Finding: redacted\n"


@pytest.mark.parametrize("reason", ["timeout", "output_limit", "missing_status"])
def test_interrupted_scan_never_passes(tmp_path, reason):
    """A partial worker result is never accepted as a clean scan."""
    result = gate.evaluate(outcome(code=None, stdout=b"partial", reason=reason), tmp_path, None)
    assert result["passed"] is False
    assert result["reason"] == "scan_incomplete"
    assert result["redacted_output"] == "partial"


def test_explicit_diagnostics_are_created_once_outside_the_repository(tmp_path):
    """Preserve diagnostic bytes only at the operator's new chosen path."""
    repo = tmp_path / "repo"
    repo.mkdir()
    report = tmp_path / "diagnostics.txt"
    result = gate.evaluate(outcome(stderr=b"safe fixture diagnostic"), repo, report)
    assert result["diagnostics_retained"] is True
    assert report.read_bytes() == b"safe fixture diagnostic"
    with pytest.raises(gate.GateError):
        gate.evaluate(outcome(stderr=b"another diagnostic"), repo, report)
    with pytest.raises(gate.GateError):
        gate.evaluate(outcome(stderr=b"another diagnostic"), repo, repo / "diagnostics.txt")


def test_configuration_cannot_disable_rules_or_add_exclusions(tmp_path, monkeypatch):
    """Do not scan with a configuration that weakens the default rule set."""
    (tmp_path / ".gitleaks.toml").write_text(
        '[extend]\nuseDefault = true\n[allowlist]\ndescription = "test"\n', encoding="utf-8"
    )
    replies = iter([str(tmp_path), "false", "0" * 40, "refs/heads/main " + "0" * 40])

    def value(*_args):
        """Supply the four expected Git metadata values for this fixture."""
        try:
            return next(replies)
        except StopIteration as error:
            raise AssertionError("Unexpected Git metadata request") from error

    monkeypatch.setattr(worker, "git_value", value)
    with pytest.raises(worker.ScanError, match="without exclusions"):
        worker.verify_repository(Path("git"), tmp_path, {})


def test_unexpected_warning_is_not_a_clean_scan(tmp_path):
    """An unrecognized warning prevents a successful result."""
    result = gate.evaluate(outcome(stderr=b"10:32PM WRN incomplete scan\n"), tmp_path, None)
    assert result["passed"] is False
    assert result["reason"] == "scanner_diagnostics"


def test_findings_with_extra_warning_are_incomplete(tmp_path):
    """Keep redacted partial findings while rejecting additional diagnostics."""
    stderr = b"10:32PM WRN incomplete scan\n10:32PM WRN leaks found: 1\n"
    result = gate.evaluate(outcome(code=1, stderr=stderr, stdout=b"Finding: redacted\n"), tmp_path, None)
    assert result["passed"] is False
    assert result["reason"] == "scanner_diagnostics"
    assert result["redacted_output"] == "Finding: redacted\n"


def test_success_with_unexpected_output_is_rejected(tmp_path):
    """A clean exit cannot conceal unexpected scanner output."""
    result = gate.evaluate(outcome(stdout=b"unexpected output"), tmp_path, None)
    assert result["passed"] is False
    assert result["reason"] == "scanner_failed"


def test_finding_count_must_match_redacted_output(tmp_path):
    """Reject incomplete verbose output while retaining the available evidence."""
    result = gate.evaluate(
        outcome(code=1, stderr=b"10:32PM WRN leaks found: 2\n", stdout=b"Finding: redacted\n"),
        tmp_path,
        None,
    )
    assert result["passed"] is False
    assert result["reason"] == "incomplete_finding_output"
    assert result["findings"] == 2
    assert result["observed_findings"] == 1
    assert result["redacted_output"] == "Finding: redacted\n"


def test_invalid_output_encoding_is_never_silently_replaced(tmp_path):
    """Retain exact non-UTF-8 output when requested and fail the scan."""
    report = tmp_path / "raw-output.bin"
    result = gate.evaluate(outcome(stdout=b"\xff"), tmp_path / "repo", report)
    assert result["passed"] is False
    assert result["reason"] == "invalid_output_encoding"
    assert result["diagnostics_retained"] is True
    assert report.read_bytes() == b"\xff"


def test_external_git_and_gitleaks_overrides_cannot_change_scan_scope(tmp_path, monkeypatch):
    """Discard inherited settings that could redirect or weaken the scan."""
    monkeypatch.setenv("GIT_DIR", "untrusted")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.longpaths")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "false")
    monkeypatch.setenv("GITLEAKS_CONFIG", "untrusted")
    env = worker.scan_environment(Path("git"), tmp_path)
    assert "GIT_DIR" not in env
    assert "GITLEAKS_CONFIG" not in env
    assert env["GIT_CONFIG_COUNT"] == "2"
    assert env["GIT_CONFIG_KEY_1"] == "core.longpaths"
    assert env["GIT_CONFIG_VALUE_1"] == "true"


def test_binary_digest_must_be_a_complete_lowercase_sha256(tmp_path, capsys):
    """Reject malformed approval digests before launching a worker."""
    code = gate.main(
        [
            "--gitleaks",
            str(tmp_path / "scanner"),
            "--git",
            str(tmp_path / "git"),
            "--repository",
            str(tmp_path),
            "--gitleaks-sha256",
            "bad-digest",
            "--json",
        ]
    )
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert result["passed"] is False
    assert "lowercase" in result["error"]


@pytest.mark.parametrize("ending", [b"\n", b"\r\n"])
def test_ignore_file_diagnostic_is_actionable_on_both_platforms(tmp_path, ending):
    """Expose only the known safe diagnostic with either platform newline."""
    result = gate.evaluate(
        outcome(code=2, stderr=b"Repository contains a Gitleaks ignore file" + ending), tmp_path, None
    )
    assert result["passed"] is False
    assert result["reason"] == "scanner_diagnostics"
    assert result["error"] == "Repository contains a Gitleaks ignore file"


def test_failed_diagnostic_stream_creation_closes_the_descriptor(tmp_path, monkeypatch):
    """Close the owned descriptor when stream construction fails."""
    opened = []

    def fail(fd, *_args, **_kwargs):
        """Simulate an operating-system stream construction error."""
        opened.append(fd)
        raise OSError("fixture stream failure")

    with monkeypatch.context() as patch:
        patch.setattr(gate.os, "fdopen", fail)
        with pytest.raises(gate.GateError, match="retain scanner diagnostics"):
            gate.evaluate(outcome(stderr=b"diagnostic"), tmp_path / "repo", tmp_path / "error.bin")
    assert len(opened) == 1
    with pytest.raises(OSError):
        os.fstat(opened[0])

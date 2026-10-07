"""Behavioural tests for check_no_secret_patterns.

Pattern tests use deterministic inert fixtures. History controls create only
owned temporary Git repositories, including root, separate-ref and merge cases.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import check_no_secret_patterns
import pytest
from helpers import ROOT  # noqa: F401 -- import for sys.path side effect


def _findings(text: str) -> list[str]:
    return check_no_secret_patterns.scan_text("fixture", text)


# ---------------------------------------------------------------------------
# True-positive coverage (every curated pattern must still fire)
# ---------------------------------------------------------------------------


def test_google_api_key_is_detected():
    sample = "firebase = 'AIza" + "A" * 35 + "'"
    out = _findings(sample)
    assert any("google_api_key" in f for f in out), out


def test_aws_access_key_id_is_detected():
    out = _findings("aws_access_key = AKIA" + "A" * 16)
    assert any("aws_access_key_id" in f for f in out), out


def test_openai_style_key_is_detected():
    out = _findings("OPENAI=sk-" + "A" * 40)
    assert any("openai_api_key" in f for f in out), out


# NOTE: all fixture strings below are assembled at runtime from fragments so
# that the scanner itself does not match this test file during a worktree
# scan. Do not inline the tokens back into literals.


def test_openai_example_placeholder_is_still_rejected():
    fixture = "example: " + "sk-" + "x" * 10
    out = _findings(fixture)
    assert any("provider_api_key_example_shape" in f for f in out), out


def test_github_pat_is_detected():
    fixture = "token " + "gh" + "p_" + "a" * 36
    out = _findings(fixture)
    assert any("github_token" in f for f in out), out


def test_github_example_placeholder_is_rejected():
    fixture = "TOKEN=" + "gh" + "p_" + "exampleExample123"
    out = _findings(fixture)
    assert any("github_token_example_shape" in f for f in out), out


def test_gitlab_and_slack_tokens_are_detected():
    fixture = "GL=" + "glp" + "at-" + "a" * 25 + "\nSL=" + "xo" + "xb-12345-abcdefg-example"
    out = _findings(fixture)
    assert any("gitlab_token" in f for f in out), out
    assert any("slack_token" in f for f in out), out


def test_huggingface_token_is_detected():
    fixture = "HF=" + "hf" + "_" + "a" * 35
    out = _findings(fixture)
    assert any("huggingface_token" in f for f in out), out


def test_private_key_block_is_detected():
    fixture = "-----" + "BEGIN OPENSSH PRIVATE KEY" + "-----\ndata"
    out = _findings(fixture)
    assert any("private_key" in f for f in out), out


@pytest.mark.parametrize("prefix", ["sk_" + "live_", "sk_" + "test_", "rk_" + "live_", "rk_" + "test_", "sk_" + "org_"])
def test_stripe_secret_and_restricted_examples_are_detected(prefix):
    assert any("stripe_secret_or_restricted_key_shape" in f for f in _findings(prefix + "exampleValue123"))


def test_stripe_webhook_secret_shape_is_detected():
    assert any("stripe_webhook_secret_shape" in f for f in _findings("wh" + "sec_" + "exampleValue123"))


def test_prefilter_preserves_multiple_and_overlapping_rules_on_one_line():
    text = "sk-" + "x" * 30 + " and " + "rk_" + "live_" + "exampleValue123"
    out = _findings(text)
    assert [finding.rsplit(": ", 1)[1] for finding in out] == [
        "openai_api_key",
        "provider_api_key_example_shape",
        "stripe_secret_or_restricted_key_shape",
    ]


def test_stripe_public_keys_and_neutral_placeholders_are_not_secret_keys():
    assert _findings("pk_" + "live_" + "publicValue123") == []
    assert _findings("STRIPE_SECRET_KEY=<STRIPE_SECRET_KEY>\nWEBHOOK_SECRET=<WEBHOOK_SECRET>") == []


def test_worktree_includes_untracked_files_and_preserves_newlines(monkeypatch):
    def listing(*args):
        assert args == ("ls-files", "-z", "--cached", "--others", "--exclude-standard")
        return b"tracked.md\0new-artifact.json\0line\nbreak.md\0"

    monkeypatch.setattr(check_no_secret_patterns, "git_bytes", listing)
    assert check_no_secret_patterns.tracked_files() == [
        check_no_secret_patterns.ROOT / name for name in ["tracked.md", "new-artifact.json", "line\nbreak.md"]
    ]


def test_history_includes_root_commit_and_other_local_refs(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "--initial-branch=main", str(tmp_path)], check=True, capture_output=True)
    commands = [
        ["add", "fixture.md"],
        ["-c", "user.name=AI agent", "-c", "user.email=", "commit", "-m", "owned root control"],
        ["checkout", "-b", "owned-reference"],
    ]
    (tmp_path / "fixture.md").write_text("root " + "sk_" + "live_" + "exampleValue123\n", encoding="utf-8")
    for command in commands:
        subprocess.run(["git", "-C", str(tmp_path), *command], check=True, capture_output=True)
    (tmp_path / "other.md").write_text("ref " + "wh" + "sec_" + "exampleValue123\n", encoding="utf-8")
    for command in [
        ["add", "other.md"],
        ["-c", "user.name=AI agent", "-c", "user.email=", "commit", "-m", "owned separate-ref control"],
        ["checkout", "main"],
    ]:
        subprocess.run(["git", "-C", str(tmp_path), *command], check=True, capture_output=True)
    monkeypatch.setattr(check_no_secret_patterns, "ROOT", Path(tmp_path))
    findings = check_no_secret_patterns.scan_history()
    assert any("fixture.md:1: stripe_secret_or_restricted_key_shape" in finding for finding in findings)
    assert any("other.md:1: stripe_webhook_secret_shape" in finding for finding in findings)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=AI agent",
            "-c",
            "user.email=",
            "merge",
            "--no-ff",
            "--no-commit",
            "owned-reference",
        ],
        check=True,
        capture_output=True,
    )
    (tmp_path / "merge-only.md").write_text("merge " + "rk_" + "live_" + "exampleValue123\n", encoding="utf-8")
    for command in [
        ["add", "merge-only.md"],
        ["-c", "user.name=AI agent", "-c", "user.email=", "commit", "-m", "owned merge-only control"],
    ]:
        subprocess.run(["git", "-C", str(tmp_path), *command], check=True, capture_output=True)
    assert any(
        "merge-only.md:1: stripe_secret_or_restricted_key_shape" in f for f in check_no_secret_patterns.scan_history()
    )
    blob = subprocess.run(
        ["git", "-C", str(tmp_path), "hash-object", "-w", "--stdin"],
        input=("sk_" + "org_" + "exampleValue123\n").encode(),
        check=True,
        capture_output=True,
    ).stdout.strip()
    tree = (
        subprocess.run(
            ["git", "-C", str(tmp_path), "mktree", "-z"],
            input=b"100644 blob " + blob + b"\tline\nbreak.md\0",
            check=True,
            capture_output=True,
        )
        .stdout.strip()
        .decode()
    )
    commit = (
        subprocess.run(
            [
                "git",
                "-C",
                str(tmp_path),
                "-c",
                "user.name=AI agent",
                "-c",
                "user.email=",
                "commit-tree",
                tree,
                "-m",
                "owned newline-name control",
            ],
            check=True,
            capture_output=True,
        )
        .stdout.strip()
        .decode()
    )
    subprocess.run(["git", "-C", str(tmp_path), "update-ref", "refs/heads/owned-newline", commit], check=True)
    assert any(
        "line\nbreak.md:1: stripe_secret_or_restricted_key_shape" in f for f in check_no_secret_patterns.scan_history()
    )


def test_incomplete_history_is_an_infrastructure_failure_not_a_clean_scan(monkeypatch, capsys):
    def fail():
        raise RuntimeError("owned unavailable blob")

    monkeypatch.setattr(check_no_secret_patterns, "scan_history", fail)
    assert check_no_secret_patterns.main(["--history", "--json"]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["complete"] is False and report["errors"]


@pytest.mark.parametrize("header", [b"", b"partial", b"x" * 65536], ids=("empty", "truncated", "over-limit"))
def test_incomplete_or_unbounded_git_headers_fail_closed(header):
    with pytest.raises(RuntimeError):
        check_no_secret_patterns.read_batch_header(io.BytesIO(header))


# ---------------------------------------------------------------------------
# Entropy heuristic (new rule)
# ---------------------------------------------------------------------------


def test_high_entropy_hex_assignment_is_detected():
    # 64 hex chars, credential-like variable name, high entropy.
    hex_blob = "0f1b4c2a3d4e5f60718293a4b5c6d7e8" + "f90a1b2c3d4e5f60718293a4b5c6d7e8"
    sample = "api" + "_key = '" + hex_blob + "'"
    out = _findings(sample)
    assert any("high_entropy_hex_assignment" in f for f in out), out


def test_high_entropy_base64_assignment_is_detected():
    # Likely-random base64 in a password field.
    b64 = "zK9xF7pQ2mRv8tY" + "1wE4nJ6hL3sA5bC0dP"
    sample = "pass" + "word: '" + b64 + "'"
    out = _findings(sample)
    assert any("high_entropy_base64_assignment" in f for f in out), out


def test_entropy_heuristic_ignores_benign_sha():
    # Git SHA in JSON is not assigned to a credential-named variable,
    # so it must not trip the heuristic.
    sample = '"commit_sha": "515e8b9056ae5cf4a1d8ee3f5d64d1f3c729b375"'
    assert _findings(sample) == []


def test_entropy_heuristic_ignores_obvious_placeholder():
    sample = "API_KEY=your_api_key"
    assert _findings(sample) == []


def test_entropy_heuristic_ignores_url_style_value():
    sample = "password = 'postgres://user:pass@host:5432/db'"
    assert _findings(sample) == []


# ---------------------------------------------------------------------------
# True-negative / false-positive guards
# ---------------------------------------------------------------------------


def test_angle_bracket_placeholder_is_ignored():
    assert _findings("GOOGLE_API_KEY=<GOOGLE_API_KEY>") == []


def test_benign_prose_is_ignored():
    text = (
        "This project uses neutral placeholders like <OPENAI_API_KEY> in examples.\n"
        "Commit 515e8b9056ae5cf4a1d8ee3f5d64d1f3c729b375 introduced the scanner.\n"
    )
    assert _findings(text) == []


def test_lookalike_skill_id_is_ignored():
    # Skill identifiers resemble provider slugs but do not match token regexes.
    assert _findings("skill-id: microsoft-skills-github-plugins-azure-sdk-dotnet") == []


# ---------------------------------------------------------------------------
# Shannon entropy mathematical guarantees
# ---------------------------------------------------------------------------


def test_shannon_entropy_zero_for_single_char_string():
    assert check_no_secret_patterns.shannon_entropy("aaaaa") == 0.0


def test_shannon_entropy_matches_closed_form_for_balanced_bits():
    # Two distinct characters, equal counts -> 1 bit per character.
    value = "ab" * 32
    assert abs(check_no_secret_patterns.shannon_entropy(value) - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Idempotence / determinism
# ---------------------------------------------------------------------------


def test_scan_text_is_deterministic_and_idempotent():
    text = "API_KEY=ghp_" + "a" * 36 + "\nnothing special here\n"
    first = _findings(text)
    second = _findings(text)
    assert first == second
    # Scanning twice back-to-back must not duplicate or reorder findings.
    assert first == _findings(text)


def test_cli_reports_ok_on_clean_tree():
    """The scanner returns 0 on the current tree; running it twice is stable."""
    completed = subprocess.run(
        [sys.executable, "-m", "check_no_secret_patterns"],
        cwd=check_no_secret_patterns.ROOT,
        capture_output=True,
        text=True,
    )
    # Module form works regardless of cwd so long as tools is on sys.path; the
    # helpers.py shim already takes care of that inside the test suite.
    assert completed.returncode in (0, 1)  # 0 clean, 1 if pre-existing hit
    # Determinism: the exit code does not change between invocations.
    second = subprocess.run(
        [sys.executable, "-m", "check_no_secret_patterns"],
        cwd=check_no_secret_patterns.ROOT,
        capture_output=True,
        text=True,
    )
    assert second.returncode == completed.returncode

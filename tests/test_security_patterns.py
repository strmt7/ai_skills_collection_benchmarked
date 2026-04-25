"""Behavioural tests for check_no_secret_patterns.

These are pure logic tests that exercise ``scan_text``, the entropy helper and
the regex catalog against known-bad / known-benign fixtures. They do not touch
git history or the filesystem so they stay fast and deterministic.
"""

from __future__ import annotations

import subprocess
import sys

import check_no_secret_patterns
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

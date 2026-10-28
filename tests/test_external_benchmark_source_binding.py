"""Repository-resolution probes must retain the requested immutable source identity."""

from __future__ import annotations

import json
import subprocess
import urllib.error
from io import BytesIO
from types import SimpleNamespace
from typing import Any

import evaluate_external_benchmark_methods as methods
import pytest

PIN = "a" * 40
OTHER = "b" * 40
REPO = "https://github.com/example/benchmark"


def test_tree_fallback_fetches_the_requested_commit_instead_of_default_branch(monkeypatch):
    commands = []

    def unavailable(*_args, **_kwargs):
        raise urllib.error.URLError("controlled API refusal")

    def native(command, **_kwargs):
        commands.append(command)
        if "rev-parse" in command:
            return SimpleNamespace(returncode=0, stdout=PIN + "\n", stderr="")
        if "ls-tree" in command:
            return SimpleNamespace(returncode=0, stdout=b"pinned-only.py\0", stderr=b"")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(methods.urllib.request, "urlopen", unavailable)
    monkeypatch.setattr(methods.subprocess, "run", native)
    receipt: dict[str, Any] = {}
    assert methods.github_tree_paths(REPO, PIN, receipt=receipt) == ["pinned-only.py"]
    assert receipt["transport"] == "pinned-git-tree" and receipt["verified_commit"] == PIN
    assert receipt["api_failure"]["type"] == "URLError"
    assert any("fetch" in command and PIN in command for command in commands)
    assert not any("clone" in command for command in commands)


def test_wrong_fetched_identity_cannot_be_reported_as_requested_tree(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise urllib.error.URLError("controlled API refusal")

    def native(command, **_kwargs):
        if "rev-parse" in command:
            return SimpleNamespace(returncode=0, stdout=OTHER + "\n", stderr="")
        if "ls-tree" in command:
            pytest.fail("tree must not be consumed after source-identity mismatch")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(methods.urllib.request, "urlopen", unavailable)
    monkeypatch.setattr(methods.subprocess, "run", native)
    with pytest.raises(RuntimeError, match="identity"):
        methods.github_tree_paths(REPO, PIN)


def test_fallback_preserves_unicode_directories_and_nul_framed_paths(monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise urllib.error.URLError("controlled API refusal")

    def native(command, **kwargs):
        if "ls-tree" in command:
            assert "-z" in command and "-t" in command
            assert kwargs["text"] is False
            return SimpleNamespace(
                returncode=0,
                stdout='资料\0资料/résumé.txt\0line\r\nbreak.txt\0quote".txt\0'.encode(),
                stderr=b"",
            )
        assert kwargs["encoding"] == "utf-8"
        if "rev-parse" in command:
            return SimpleNamespace(returncode=0, stdout=PIN + "\n", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(methods.urllib.request, "urlopen", unavailable)
    monkeypatch.setattr(methods.subprocess, "run", native)
    assert methods.github_tree_paths(REPO, PIN) == ["line\r\nbreak.txt", 'quote".txt', "资料", "资料/résumé.txt"]


def test_truncated_api_tree_requires_complete_pinned_resolution(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({"sha": PIN, "truncated": True, "tree": [{"path": "partial-only.py"}]}).encode()

    monkeypatch.setattr(methods.urllib.request, "urlopen", lambda *_args, **_kwargs: Response())

    def refuse(*_args, **_kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="controlled pinned fetch failure")

    monkeypatch.setattr(methods.subprocess, "run", refuse)
    with pytest.raises(RuntimeError, match="controlled pinned fetch failure"):
        methods.github_tree_paths(REPO, PIN)


@pytest.mark.parametrize("response_sha", [OTHER, None])
def test_api_tree_with_unverified_commit_requires_pinned_resolution(monkeypatch, response_sha):
    """Reject a complete-looking API tree that does not prove the requested commit."""
    body = json.dumps({"sha": response_sha, "truncated": False, "tree": [{"path": "wrong.py"}]}).encode()
    monkeypatch.setattr(methods.urllib.request, "urlopen", lambda *_args, **_kwargs: BytesIO(body))
    monkeypatch.setattr(
        methods.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=1, stdout="", stderr="controlled pinned fetch failure"),
    )
    receipt: dict[str, Any] = {}
    with pytest.raises(RuntimeError, match="controlled pinned fetch failure"):
        methods.github_tree_paths(REPO, PIN, receipt=receipt)
    assert receipt["api_failure"]["message"] == "repository tree response does not match the requested commit"
    assert receipt["transport"] is None


def test_api_tree_matching_commit_is_accepted(monkeypatch):
    """Accept an explicitly complete API tree for the requested commit."""
    body = json.dumps({"sha": PIN, "truncated": False, "tree": [{"path": "verified.py"}]}).encode()
    monkeypatch.setattr(methods.urllib.request, "urlopen", lambda *_args, **_kwargs: BytesIO(body))
    receipt: dict[str, Any] = {}
    assert methods.github_tree_paths(REPO, PIN, receipt=receipt) == ["verified.py"]
    assert receipt["transport"] == "github-tree-api"


def test_remote_head_timeout_is_preserved_as_failed_resolution(monkeypatch):
    def timeout(command, **_kwargs):
        raise subprocess.TimeoutExpired(command, 60)

    monkeypatch.setattr(methods.subprocess, "run", timeout)
    result = methods.git_head(REPO)
    assert result["resolved"] is False and result["returncode"] != 0
    assert "timeout" in result["stderr"].lower()


def test_malformed_head_is_not_an_immutable_reference(monkeypatch):
    monkeypatch.setattr(
        methods.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="main\tHEAD", stderr=""),
    )
    assert methods.git_head(REPO)["resolved"] is False


def test_existing_probe_evidence_cannot_be_replaced_or_trigger_network(tmp_path, monkeypatch):
    monkeypatch.setattr(methods, "ROOT", tmp_path)
    folder = tmp_path / "artifacts/external-benchmark-integrations" / methods.RUN_NAME
    folder.mkdir(parents=True)
    retained = folder / "manifest.json"
    retained.write_bytes(b"original immutable observation\r\n")
    monkeypatch.setattr(methods, "git_head", lambda *_: pytest.fail("existing evidence must be refused before probing"))
    with pytest.raises(FileExistsError, match="historical evidence"):
        methods.run_smoke()
    assert retained.read_bytes() == b"original immutable observation\r\n"


def test_probe_requires_explicit_observation_and_safe_new_run_name(tmp_path, monkeypatch):
    monkeypatch.setattr(methods, "ROOT", tmp_path)
    for name, timestamp in (("../outside", "2026-10-25T18:00:00Z"), ("fresh", None), ("fresh", "2026-02-30T18:00:00Z")):
        with pytest.raises(ValueError):
            methods.run_smoke(name, timestamp)
    assert not (tmp_path / "artifacts").exists()


def test_selected_probe_preserves_global_registry_and_legacy_report(tmp_path, monkeypatch):
    monkeypatch.setattr(methods, "ROOT", tmp_path)
    doc = tmp_path / "docs/external-benchmark-adapter-smoke.md"
    doc.parent.mkdir()
    doc.write_bytes(b"historical report")
    method = methods.EXTERNAL_METHODS[1]
    original_probe = methods.smoke_probe

    def fixture_probe(value, timestamp, *, run_name):
        return original_probe(
            value,
            timestamp,
            run_name=run_name,
            head_provider=lambda _: {
                "command": [],
                "returncode": 0,
                "stdout": PIN + "\tHEAD",
                "stderr": "",
                "head_sha": PIN,
                "resolved": True,
            },
            tree_provider=lambda *_: ["README.md"],
        )

    monkeypatch.setattr(methods, "smoke_probe", fixture_probe)
    report = methods.run_smoke("fresh-selected", "2026-10-25T18:00:00Z", [method["id"]])
    assert report["summary"]["method_count"] == 1
    assert doc.read_bytes() == b"historical report"
    assert not (tmp_path / "data/external_benchmark_methods.json").exists()
    folder = tmp_path / "artifacts/external-benchmark-integrations/fresh-selected"
    artifact = json.loads((folder / method["id"] / "artifact.json").read_bytes())
    assert artifact["runner"]["run_name"] == "fresh-selected"
    assert artifact["input_snapshot"]["is_real"] is False
    assert artifact["execution"]["model_invoked"] is False
    assert (folder / "report.md").exists()

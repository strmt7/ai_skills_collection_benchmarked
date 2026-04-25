"""Logic tests for tools/evaluate_external_benchmark_methods.py.

Uses injected providers to keep the suite offline and deterministic.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest

eebm = importlib.import_module("evaluate_external_benchmark_methods")


@pytest.fixture
def complete_method() -> dict[str, Any]:
    return {
        "id": "example-adapter",
        "title": "Example Adapter",
        "scope": "repository workflows",
        "repo_url": "https://github.com/example-org/example-bench",
        "source_url": "https://docs.example.org/bench",
        "primary_metrics": ["accuracy", "pass_rate", "recall"],
        "category_fit": ["coding-refactoring-and-repository-automation"],
        "integration_requirements": ["python", "git", "pytest"],
    }


def test_adapter_complete_true_for_well_formed(complete_method):
    assert eebm.adapter_complete(complete_method) is True


def test_adapter_complete_false_when_missing_title(complete_method):
    complete_method.pop("title")
    assert eebm.adapter_complete(complete_method) is False


def test_adapter_complete_false_when_repo_url_not_github(complete_method):
    complete_method["repo_url"] = "https://gitlab.com/x/y"
    assert eebm.adapter_complete(complete_method) is False


def test_adapter_complete_false_when_source_url_not_https(complete_method):
    complete_method["source_url"] = "http://docs.example.org/bench"
    assert eebm.adapter_complete(complete_method) is False


def test_slug_normalises_title():
    assert eebm.slug("HELM Lite v0.3") == "helm-lite-v0-3"


def test_registry_envelope_shape():
    reg = eebm.registry()
    assert reg["registry_version"] == 1
    assert reg["method_count"] >= 1
    assert reg["method_count"] == len(reg["methods"])
    for method in reg["methods"]:
        assert eebm.adapter_complete(method), f"registry contains incomplete method: {method.get('id')}"


def test_smoke_probe_with_injected_providers_is_deterministic(complete_method):
    head_calls: list[str] = []

    def head_provider(url: str) -> dict[str, Any]:
        head_calls.append(url)
        return {
            "command": ["git", "ls-remote", url, "HEAD"],
            "returncode": 0,
            "stdout": "f" * 40 + "\tHEAD",
            "stderr": "",
            "head_sha": "f" * 40,
            "resolved": True,
        }

    def tree_provider(url: str, head_sha: str) -> list[str]:
        return ["README.md", "benchmarks/metrics.py", "benchmarks/run.py", "LICENSE"]

    a = eebm.smoke_probe(
        complete_method,
        "2026-04-25T00:00:00Z",
        head_provider=head_provider,
        tree_provider=tree_provider,
    )
    b = eebm.smoke_probe(
        complete_method,
        "2026-04-25T00:00:00Z",
        head_provider=head_provider,
        tree_provider=tree_provider,
    )
    assert a == b
    assert a["metrics"]["integration_status"] == "adapter_ready"
    assert a["metrics"]["checks_passed"] == a["metrics"]["checks_total"]
    assert head_calls == [complete_method["repo_url"], complete_method["repo_url"]]


def test_smoke_probe_flags_missing_subpath(complete_method):
    complete_method["repo_subpath"] = "benchmarks/missing"

    def head_provider(_: str) -> dict[str, Any]:
        return {
            "command": ["git", "ls-remote", complete_method["repo_url"], "HEAD"],
            "returncode": 0,
            "stdout": "a" * 40 + "\tHEAD",
            "stderr": "",
            "head_sha": "a" * 40,
            "resolved": True,
        }

    def tree_provider(_url: str, _head: str) -> list[str]:
        return ["README.md", "benchmarks/present.py"]

    artifact = eebm.smoke_probe(
        complete_method,
        "2026-04-25T00:00:00Z",
        head_provider=head_provider,
        tree_provider=tree_provider,
    )
    assert artifact["input_snapshot"]["repo_subpath_present"] is False
    assert "required_subpath_resolves" in artifact["metrics"]["blocking_failures"]
    assert artifact["metrics"]["integration_status"] == "adapter_incomplete"


def test_smoke_probe_captures_unresolved_head(complete_method):
    def head_provider(_: str) -> dict[str, Any]:
        return {
            "command": ["git", "ls-remote", complete_method["repo_url"], "HEAD"],
            "returncode": 128,
            "stdout": "",
            "stderr": "offline",
            "head_sha": "",
            "resolved": False,
        }

    def tree_provider(_url: str, _head: str) -> list[str]:
        raise AssertionError("tree_provider must not be called when head unresolved")

    artifact = eebm.smoke_probe(
        complete_method,
        "2026-04-25T00:00:00Z",
        head_provider=head_provider,
        tree_provider=tree_provider,
    )
    assert artifact["input_snapshot"]["head_sha"] == ""
    assert artifact["input_snapshot"]["tree_path_count"] == 0
    assert "repository_head_resolves" in artifact["metrics"]["blocking_failures"]


def test_smoke_probe_captures_tree_exception_text(complete_method):
    def head_provider(_: str) -> dict[str, Any]:
        return {
            "command": [],
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "head_sha": "b" * 40,
            "resolved": True,
        }

    def tree_provider(_url: str, _head: str) -> list[str]:
        raise RuntimeError("hypothetical clone failure")

    artifact = eebm.smoke_probe(
        complete_method,
        "2026-04-25T00:00:00Z",
        head_provider=head_provider,
        tree_provider=tree_provider,
    )
    assert "hypothetical clone failure" in artifact["input_snapshot"]["tree_error"]
    assert artifact["metrics"]["integration_status"] == "adapter_incomplete"

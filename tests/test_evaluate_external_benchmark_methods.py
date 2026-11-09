"""Logic tests for tools/evaluate_external_benchmark_methods.py.

Uses injected providers to keep the suite offline and deterministic.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
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
    assert a["input_snapshot"]["is_real"] is False
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


@pytest.fixture
def retained_probe_bundle(tmp_path, monkeypatch):
    """Read a real retained observation without networking or changing its bytes."""
    root = eebm.ROOT
    name = eebm.CURRENT_RUN_NAME
    manifest_path = Path("artifacts/external-benchmark-integrations") / name / "manifest.json"
    manifest = json.loads((root / manifest_path).read_bytes())
    for relative in [str(manifest_path), *(item["artifact_path"] for item in manifest["artifacts"])]:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((root / relative).read_bytes())
    monkeypatch.setattr(eebm, "ROOT", tmp_path)
    return tmp_path, manifest_path, manifest


def test_frozen_probe_is_independent_of_later_registry_changes(retained_probe_bundle, monkeypatch):
    monkeypatch.setattr(eebm, "EXTERNAL_METHODS", [])
    eebm.check_probe_run(eebm.CURRENT_RUN_NAME)


@pytest.mark.parametrize("mutation", ["duplicate", "count", "head", "score", "method_identity", "definition"])
def test_probe_check_rejects_inconsistent_or_stale_observations(retained_probe_bundle, mutation):
    root, manifest_path, manifest = retained_probe_bundle
    expected = {method["id"]: method for method in eebm.EXTERNAL_METHODS if method["id"] in eebm.CURRENT_PROBE_METHODS}
    item = manifest["artifacts"][0]
    artifact_path = root / item["artifact_path"]
    artifact = json.loads(artifact_path.read_bytes())
    if mutation == "duplicate":
        manifest["artifacts"].append(dict(item))
    elif mutation == "count":
        manifest["summary"]["method_count"] += 1
    elif mutation == "head":
        item["head_sha"] = "0" * 40
    elif mutation == "score":
        item["score_percent"] = 0
    elif mutation == "method_identity":
        artifact["method_id"] = "different-method"
    else:
        artifact["method"]["repo_url"] = "https://github.com/old-owner/old-benchmark"
    (root / manifest_path).write_text(json.dumps(manifest), encoding="utf-8")
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(SystemExit):
        eebm.check_probe_run(eebm.CURRENT_RUN_NAME, expected_methods=expected)


def test_current_probe_cannot_omit_an_expected_method(retained_probe_bundle):
    expected = {method["id"]: method for method in eebm.EXTERNAL_METHODS}
    with pytest.raises(SystemExit, match="cover its declared methods"):
        eebm.check_probe_run(eebm.CURRENT_RUN_NAME, expected_methods=expected)

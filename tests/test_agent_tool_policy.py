"""Mandatory tool routing and evidence acceptance must fail visibly on drift."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import build_catalog
import pytest
import validate_agent_tool_policy as policy

from tests.helpers import ROOT


@pytest.fixture
def contract(tmp_path, monkeypatch):
    for relative in (
        "AGENTS.md",
        "docs/agent-tools.md",
        ".github/workflows/offline-validation.yml",
        *policy.TOOLS.values(),
    ):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    entries = json.loads((ROOT / "data/skills_catalog.json").read_text(encoding="utf-8"))[:2]
    (tmp_path / "data").mkdir()
    (tmp_path / "data/skills_catalog.json").write_text(json.dumps(entries), encoding="utf-8")
    monkeypatch.setattr(build_catalog, "ROOT", tmp_path)
    build_catalog.write_agent_ready_skills(entries)
    return tmp_path


def test_all_catalog_entrypoints_receive_mandatory_policy():
    result = policy.validate(ROOT)
    assert result["ok"], result["errors"]
    assert result["entrypoints_checked"] == len(json.loads((ROOT / "data/skills_catalog.json").read_text()))


def test_generator_preserves_mandatory_policy(contract):
    assert policy.validate(contract)["ok"]


@pytest.mark.parametrize("name", ["caveman", "cocoindex-code-search", "crawl4ai-research"])
def test_missing_mandatory_skill_is_rejected(contract, name):
    (contract / policy.TOOLS[name]).unlink()
    result = policy.validate(contract)
    assert not result["ok"]
    assert any(policy.TOOLS[name] in error for error in result["errors"])


@pytest.mark.parametrize("name", ["caveman", "cocoindex-code-search", "crawl4ai-research"])
def test_optional_activation_cannot_replace_requirement(contract, name):
    path = contract / policy.TOOLS[name]
    path.write_text(path.read_text().replace("mandatory: true", "mandatory: false"), encoding="utf-8")
    assert any("mandatory activation" in error for error in policy.validate(contract)["errors"])


def test_every_missing_entrypoint_is_reported(contract):
    entries = json.loads((contract / "data/skills_catalog.json").read_text())
    for entry in entries:
        (contract / entry["agent_ready_path"]).unlink()
    result = policy.validate(contract)
    assert len([error for error in result["errors"] if "policy link missing" in error]) == 2


def test_ci_cannot_drop_mandatory_gate(contract):
    path = contract / ".github/workflows/offline-validation.yml"
    path.write_text(path.read_text().replace(policy.GATE, "echo gate omitted"), encoding="utf-8")
    assert any("gate missing" in error for error in policy.validate(contract)["errors"])


@pytest.mark.parametrize("bypass", ["        if: false\n", "        continue-on-error: true\n"])
def test_ci_cannot_disable_or_ignore_mandatory_gate(contract, bypass):
    path = contract / ".github/workflows/offline-validation.yml"
    path.write_text(
        path.read_text().replace(f"        run: {policy.GATE}", bypass + f"        run: {policy.GATE}"),
        encoding="utf-8",
    )
    assert any("bypassable" in error for error in policy.validate(contract)["errors"])


def test_ci_comment_cannot_impersonate_executed_gate(contract):
    path = contract / ".github/workflows/offline-validation.yml"
    path.write_text(
        path.read_text().replace(
            f"        run: {policy.GATE}", f"        run: echo gate omitted\n        # {policy.GATE}"
        ),
        encoding="utf-8",
    )
    assert any("gate missing" in error for error in policy.validate(contract)["errors"])


def execution(root: Path, *, navigation=False, web=False):
    receipt = {
        "schema_version": 1,
        "source_root": str(root),
        "task_scope": {"broad_navigation": navigation, "web_research": web},
        "caveman": {
            "applied": True,
            "skill_sha256": hashlib.sha256((root / policy.TOOLS["caveman"]).read_bytes()).hexdigest(),
        },
    }
    path = root / "task.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return path, receipt


def test_exact_scope_does_not_invent_tool_executions(contract):
    path, _ = execution(contract)
    assert policy.validate_execution(contract, path) == []


def test_triggered_evidence_cannot_be_omitted(contract):
    path, _ = execution(contract, navigation=True, web=True)
    errors = policy.validate_execution(contract, path)
    assert len(errors) == 2
    assert errors[0].startswith("cocoindex_code:")
    assert errors[1].startswith("crawl4ai:")


@pytest.mark.parametrize("status,text", [(202, "x"), (200, ""), (403, "denied" * 100)])
def test_unusable_native_crawl_cannot_be_admitted(contract, status, text):
    path, receipt = execution(contract, web=True)
    result_path = contract / "native.json"
    result_path.write_text(
        json.dumps(
            {
                "url": "https://example.org/docs",
                "success": True,
                "status_code": status,
                "markdown": {"raw_markdown": text},
            }
        ),
        encoding="utf-8",
    )
    receipt["crawl4ai"] = {
        "path": str(result_path),
        "sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "url": "https://example.org/docs",
        "provider_version": "test-fixture",
        "scope_reviewed": True,
    }
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert policy.validate_execution(contract, path)[0].startswith("crawl4ai:")


def test_wrong_repository_execution_receipt_is_rejected(contract):
    path, receipt = execution(contract)
    receipt["source_root"] = str(contract.parent)
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "repository binding" in policy.validate_execution(contract, path)[0]


def test_gate_main_is_read_only_and_machine_readable(contract, capsys):
    before = (contract / "AGENTS.md").read_bytes()
    assert policy.main(["--root", str(contract), "--check", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["entrypoints_checked"] == 2
    assert (contract / "AGENTS.md").read_bytes() == before


@pytest.fixture
def linked_execution(contract):
    path, receipt = execution(contract, navigation=True, web=True)
    base = contract / ".venv/corpus"
    tree = base / "tree/tools"
    tree.mkdir(parents=True)
    source = b"def version():\n    return 42\n"
    (tree / "demo.py").write_bytes(source)
    digest = hashlib.sha256(source).hexdigest()
    manifest = {"source_root": str(contract), "files": {"tools/demo.py": {"sha256": digest, "excluded_reason": None}}}
    manifest_path = base / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    search = {
        "ok": True,
        "query": {"query": "version function", "project_root": str(base / "tree"), "paths": None},
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "response": {
            "success": True,
            "total_returned": 1,
            "offset": 0,
            "results": [
                {"file_path": "tools/demo.py", "start_line": 1, "end_line": 2, "content": source.decode(), "score": 0.8}
            ],
        },
        "source_checks": [{"path": "tools/demo.py", "sha256": digest, "source_span_verified": True}],
    }
    search_path = contract / "search.json"
    search_path.write_text(json.dumps(search), encoding="utf-8")
    crawl = {
        "url": "https://example.org/docs",
        "success": True,
        "status_code": 200,
        "markdown": {"raw_markdown": "Independent test document. " * 8},
    }
    crawl_path = contract / "native.json"
    crawl_path.write_text(json.dumps(crawl), encoding="utf-8")
    receipt["cocoindex_code"] = {
        "path": str(search_path),
        "sha256": hashlib.sha256(search_path.read_bytes()).hexdigest(),
        "corpus": str(base),
    }
    receipt["crawl4ai"] = {
        "path": str(crawl_path),
        "sha256": hashlib.sha256(crawl_path.read_bytes()).hexdigest(),
        "url": crawl["url"],
        "provider_version": "test-fixture",
        "scope_reviewed": True,
    }
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return path, receipt, base


def test_linked_evidence_contract_accepts_matching_source_and_native_result(contract, linked_execution):
    path, _, _ = linked_execution
    assert policy.validate_execution(contract, path) == []


def test_changed_indexed_source_is_rejected(contract, linked_execution):
    path, _, base = linked_execution
    (base / "tree/tools/demo.py").write_bytes(b"different source\n")
    assert "differs from its source binding" in policy.validate_execution(contract, path)[0]


def test_both_altered_evidence_digests_are_reported(contract, linked_execution):
    path, receipt, _ = linked_execution
    for name in ("cocoindex_code", "crawl4ai"):
        Path(receipt[name]["path"]).write_text("{}", encoding="utf-8")
    errors = policy.validate_execution(contract, path)
    assert len(errors) == 2
    assert all("digest mismatch" in error for error in errors)


def test_successful_crawl_for_wrong_url_is_rejected(contract, linked_execution):
    path, receipt, _ = linked_execution
    receipt["crawl4ai"]["url"] = "https://example.org/wrong-document"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert policy.validate_execution(contract, path)[0].startswith("crawl4ai:")


def test_source_index_for_another_repository_is_rejected(contract, linked_execution):
    path, receipt, _ = linked_execution
    receipt["cocoindex_code"]["corpus"] = str(contract.parent)
    path.write_text(json.dumps(receipt), encoding="utf-8")
    assert "outside this repository" in policy.validate_execution(contract, path)[0]

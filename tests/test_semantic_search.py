"""Reject stale or forged retrieval evidence and retain literal query scopes."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import prepare_semantic_corpus as corpus
import pytest
import search_semantic_corpus as search
import yaml


@pytest.fixture
def bound(tmp_path: Path) -> tuple[Path, Path, dict, dict]:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(root)], check=True)
    (root / ".gitignore").write_text(".venv/\n", encoding="utf-8")
    (root / "skills").mkdir()
    (root / "skills/source.md").write_bytes(b"first\r\nprecise evidence\r\nlast\r\n")
    base = root / ".venv/index"
    corpus.prepare(root, base, ["skills"], check=False)
    manifest = json.loads((base / "manifest.json").read_bytes())
    response = {
        "success": True,
        "results": [
            {
                "file_path": "skills/source.md",
                "start_line": 2,
                "end_line": 2,
                "content": "precise evidence",
                "score": 0.5,
            }
        ],
        "total_returned": 1,
        "offset": 0,
    }
    return root, base, manifest, response


def test_exact_source_and_one_based_coordinates(bound):
    _, base, manifest, response = bound
    assert search.verify_response(response, base, manifest, ["skills/**"], 3)[0]["source_span_verified"]
    response["results"][0].update(start_line=1, end_line=3, content="first\r\nprecise evidence\r\nlast")
    assert search.verify_response(response, base, manifest, [], 3)


@pytest.mark.parametrize(
    "change",
    [
        "empty",
        "boolean_count",
        "boolean_offset",
        "nonobject_hit",
        "nonstring_content",
        "count",
        "offset",
        "scope",
        "outside",
        "content",
        "line",
        "boolean_line",
        "nonfinite",
        "boolean_score",
        "excluded",
    ],
)
def test_forged_or_empty_hits_are_rejected(bound, change):
    _, base, manifest, original = bound
    response = copy.deepcopy(original)
    hit = response["results"][0]
    paths = []
    if change == "empty":
        response.update(results=[], total_returned=0)
    elif change == "boolean_count":
        response["total_returned"] = True
    elif change == "boolean_offset":
        response["offset"] = False
    elif change == "nonobject_hit":
        response["results"] = [None]
    elif change == "nonstring_content":
        hit["content"] = None
    elif change == "count":
        response["total_returned"] = 2
    elif change == "offset":
        response["offset"] = 1
    elif change == "scope":
        paths = ["tools/**"]
    elif change == "outside":
        hit["file_path"] = "../outside.md"
    elif change == "content":
        hit["content"] = "invented evidence"
    elif change == "line":
        hit["start_line"] = 0
    elif change == "boolean_line":
        hit["start_line"] = True
    elif change == "nonfinite":
        hit["score"] = float("nan")
    elif change == "boolean_score":
        hit["score"] = True
    else:
        manifest["files"]["skills/source.md"]["excluded_reason"] = "contains_nul"
    with pytest.raises(ValueError):
        search.verify_response(response, base, manifest, paths, 3)


def test_changed_retrieved_bytes_fail_binding(bound):
    _, base, manifest, response = bound
    (base / "tree/skills/source.md").write_text("different", encoding="utf-8")
    with pytest.raises(ValueError, match="source binding"):
        search.verify_response(response, base, manifest, [], 3)


def test_stale_source_rejects_before_provider_call(bound, monkeypatch, capsys):
    root, base, _, _ = bound
    (root / "skills/source.md").write_text("new source", encoding="utf-8")
    monkeypatch.setattr(search, "local_environment", lambda *args: pytest.fail("stale input reached provider"))
    assert (
        search.main(
            [
                "--root",
                str(root),
                "--corpus",
                str(base),
                "--python",
                "missing",
                "--provider-dir",
                "missing",
                "--model-proof",
                "missing",
                "--query",
                "evidence",
                "--json",
            ]
        )
        == 1
    )
    assert "stale corpus" in json.loads(capsys.readouterr().out)["errors"][0]


def test_environment_clears_host_mapping_and_rejects_model_drift(bound, monkeypatch):
    root, base, _, _ = bound
    python = root / ".venv/python.exe"
    python.write_bytes(b"test executable path, not executed")
    providers = root / ".venv/providers"
    providers.mkdir()
    model = root / ".venv/model"
    model.mkdir()
    (model / "model.safetensors").write_bytes(b"fixed fixture bytes")
    proof = root / "proof.json"
    proof.write_text(
        json.dumps(
            {
                "custom_code_present": False,
                "files": {"model.safetensors": hashlib.sha256(b"fixed fixture bytes").hexdigest()},
            }
        )
    )
    (base / "config").mkdir()
    settings = {"embedding": {"provider": "sentence-transformers", "device": "cpu", "model": str(model)}}
    (base / "config/global_settings.yml").write_text(yaml.safe_dump(settings))
    monkeypatch.setenv("COCOINDEX_CODE_HOST_CWD", "unrelated-project")
    monkeypatch.setenv("COCOINDEX_CODE_DB_PATH_MAPPING", "unrelated-index")
    env = search.local_environment(root, base, python, providers, proof)
    assert "COCOINDEX_CODE_HOST_CWD" not in env and "COCOINDEX_CODE_DB_PATH_MAPPING" not in env
    assert env["HF_HUB_OFFLINE"] == env["TRANSFORMERS_OFFLINE"] == "1"
    (model / "model.safetensors").write_bytes(b"changed")
    with pytest.raises(ValueError, match="pinned proof"):
        search.local_environment(root, base, python, providers, proof)


@pytest.mark.parametrize("change_during_query", [False, True])
def test_literal_request_transport_and_source_change_during_query(bound, monkeypatch, capsys, change_during_query):
    root, base, _, response = bound
    python = root / ".venv/python.exe"
    python.write_bytes(b"not executed")
    providers = root / ".venv/providers"
    providers.mkdir()
    proof = root / "proof.json"
    proof.write_text("{}")
    real_run = subprocess.run

    def provider_run(command, **kwargs):
        if command[0] != str(python):
            return real_run(command, **kwargs)
        request = json.loads(kwargs["input"])
        assert request["paths"] == ["skills/**"]
        assert request["query"] == "$UNCHANGED precise evidence"
        if change_during_query:
            (root / "skills/source.md").write_text("changed while querying")
        report = {"response": response, "project_status": {"indexing": False, "index_exists": True}}
        return subprocess.CompletedProcess(command, 0, stdout=json.dumps(report), stderr="")

    monkeypatch.setattr(search.subprocess, "run", provider_run)
    monkeypatch.setattr(search, "local_environment", lambda *args: {})
    code = search.main(
        [
            "--root",
            str(root),
            "--corpus",
            str(base),
            "--python",
            str(python),
            "--provider-dir",
            str(providers),
            "--model-proof",
            str(proof),
            "--query",
            "$UNCHANGED precise evidence",
            "--path",
            "skills/**",
            "--json",
        ]
    )
    assert code == int(change_during_query)
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is (not change_during_query)
    if change_during_query:
        assert "source binding changed" in report["errors"][0]

from __future__ import annotations

import subprocess

import inspect_upstream_sources as upstream

SOURCE = {"repo": "author/skills", "commit_sha": "a" * 40}


def test_release_policy_resolves_commit_rather_than_trusting_tag_target():
    requests = []

    def fetch(endpoint):
        requests.append(endpoint)
        if endpoint.endswith("releases/latest"):
            return {"tag_name": "release/2", "target_commitish": "main"}
        if "/commits/" in endpoint:
            return {"sha": "b" * 40}
        return {"full_name": "new-author/skills", "default_branch": "main", "license": {"spdx_id": "MIT"}}

    result = upstream.inspect_source(SOURCE, fetch)
    assert result["status"] == "update_available"
    assert result["canonical_repo"] == "new-author/skills"
    assert requests[-1].endswith("commits/release%2F2")


def test_only_not_found_release_falls_back_to_default_branch():
    def fetch(endpoint):
        if endpoint.endswith("releases/latest"):
            raise RuntimeError("gh: Not Found (HTTP 404)")
        if "/commits/" in endpoint:
            return {"sha": "a" * 40}
        return {"full_name": "author/skills", "default_branch": "main", "license": None}

    result = upstream.inspect_source(SOURCE, fetch)
    assert result["status"] == "current"
    assert result["selected_ref"] == "main"
    assert result["license"] is None


def test_rate_limit_does_not_masquerade_as_no_release():
    def fetch(endpoint):
        if endpoint.endswith("releases/latest"):
            raise RuntimeError("rate limit (HTTP 403)")
        return {"full_name": "author/skills", "default_branch": "main"}

    result = upstream.inspect_source(SOURCE, fetch)
    assert result["status"] == "error"
    assert "403" in result["error"]
    assert "current_commit" not in result


def test_deferred_sources_never_enter_network_work_queue():
    sources = [SOURCE, {**SOURCE, "repo": "strmt7/project"}, {**SOURCE, "repo": "ZMB-UZH/omero-docker-extended"}]
    eligible, deferred = upstream.partition_sources(sources, include_owner=False)
    assert eligible == [SOURCE]
    assert len(deferred) == 2
    assert all(item["status"] == "deferred" for item in deferred)


def test_github_json_decoding_uses_utf8_on_windows(monkeypatch):
    def run(command, **kwargs):
        assert kwargs["encoding"] == "utf-8"
        return subprocess.CompletedProcess(command, 0, '{"description":"scientific 🧬 data"}', "")

    monkeypatch.setattr(upstream.subprocess, "run", run)
    assert upstream.github("repos/author/skills")["description"] == "scientific 🧬 data"

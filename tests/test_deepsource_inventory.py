from __future__ import annotations

import io
import json
import urllib.error
from email.message import Message
from typing import Any

import deepsource_inventory as inventory
import pytest

REPOSITORY = "example/project"
COMMIT = "a" * 40


def response(identifiers, total, *, cursor=None, more=False, run_id="run-1", repo_id="repo-1", commit=COMMIT):
    nodes = []
    for identifier in identifiers:
        nodes.append(
            {
                "node": {
                    "id": str(identifier),
                    "path": "sample.py",
                    "beginLine": 3,
                    "beginColumn": 2,
                    "endLine": 3,
                    "endColumn": 8,
                    "title": "A finding",
                    "issue": {
                        "shortcode": "TEST-1",
                        "category": "BUG_RISK",
                        "severity": "MAJOR",
                        "analyzer": {"shortcode": "python"},
                    },
                }
            }
        )
    return {
        "data": {
            "run": {
                "id": run_id,
                "commitOid": commit,
                "status": "FAILURE",
                "finishedAt": "2026-10-28T00:00:00Z",
                "repository": {"id": repo_id},
            },
            "repository": {
                "id": "repo-1",
                "name": "project",
                "vcsUrl": "https://github.com/example/project",
                "vcsProvider": "GITHUB",
                "defaultBranch": "main",
                "latestCommitOid": COMMIT,
                "configJson": {"analyzers": []},
                "issueOccurrences": {
                    "totalCount": total,
                    "edges": nodes,
                    "pageInfo": {"hasNextPage": more, "endCursor": cursor},
                },
            },
        }
    }


def fetcher(pages, calls):
    pages = iter(pages)

    def fetch(variables, destination):
        calls.append(variables)
        data = json.dumps(next(pages)).encode()
        destination.write_bytes(data)
        return data

    return fetch


def test_complete_pagination_retains_all_occurrences_and_checks_final_state(tmp_path):
    pages = [
        response(range(100), 205, more=True, cursor="first"),
        response(range(100, 200), 205, more=True, cursor="second"),
        response(range(200, 205), 205),
        response([0], 205, more=True, cursor="first"),
    ]
    calls: list[dict[str, Any]] = []
    result = inventory.capture(fetcher(pages, calls), REPOSITORY, "main", COMMIT, tmp_path / "capture")
    assert result["complete"] is True and result["total_count"] == 205
    assert [call["after"] for call in calls] == [None, "first", "second", None]
    assert calls[-1]["first"] == 1
    lines = (tmp_path / "capture/findings.ndjson").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 205 and len({json.loads(line)["id"] for line in lines}) == 205
    assert result["categories"] == {"BUG_RISK": 205}
    assert result["provider_identity"]["run"]["repository_id"] == "repo-1"
    assert len(result["provider_configuration_sha256"]) == 64
    assert not (tmp_path / "capture/findings.ndjson.partial").exists()


def test_large_inventory_is_streamed_without_truncating_occurrences(tmp_path):
    total = 21_123
    calls = 0

    def fetch(variables, destination):
        nonlocal calls
        calls += 1
        start = int(variables["after"]) if variables["after"] is not None else 0
        stop = min(start + variables["first"], total)
        more = stop < total
        data = json.dumps(response(range(start, stop), total, more=more, cursor=str(stop) if more else None)).encode()
        destination.write_bytes(data)
        return data

    output = tmp_path / "capture"
    result = inventory.capture(fetch, REPOSITORY, "main", COMMIT, output)
    assert result["complete"] and result["total_count"] == total
    assert calls == 213 and len(result["pages"]) == 212
    with (output / "findings.ndjson").open(encoding="utf-8") as stream:
        assert sum(1 for _ in stream) == total


@pytest.mark.parametrize(
    "pages",
    [
        [response([1], 2)],
        [response([1], 2, more=True, cursor="c"), response([1], 2)],
        [response([1], 2, more=True, cursor="c"), response([2], 3)],
        [response([1], 2, more=True, cursor="c"), response([2], 2, run_id="other")],
        [response([1], 2, more=True, cursor="c"), response([2], 2, more=True, cursor="c")],
        [response([1], 1), response([2], 1)],
        [response([1], 1, repo_id="other")],
        [response([1], 1, commit="b" * 40)],
    ],
)
def test_inconsistent_or_incomplete_provider_data_is_not_published(tmp_path, pages):
    output = tmp_path / "capture"
    with pytest.raises(inventory.InventoryError):
        inventory.capture(fetcher(pages, []), REPOSITORY, "main", COMMIT, output)
    assert json.loads((output / "manifest.json").read_text())["complete"] is False
    assert not (output / "findings.ndjson").exists()


def test_empty_inventory_needs_a_second_consistent_observation(tmp_path):
    calls: list[dict[str, Any]] = []
    result = inventory.capture(
        fetcher([response([], 0), response([], 0)], calls), REPOSITORY, "main", COMMIT, tmp_path / "capture"
    )
    assert result["complete"] and result["total_count"] == 0 and len(calls) == 2


def test_documented_null_repository_configuration_is_supported(tmp_path):
    empty = response([], 0)
    empty["data"]["repository"]["configJson"] = None
    result = inventory.capture(fetcher([empty, empty], []), REPOSITORY, "main", COMMIT, tmp_path / "capture")
    assert result["complete"] and result["total_count"] == 0


def test_unfinished_analysis_is_never_reported_as_empty_or_complete(tmp_path):
    pending = response([], 0)
    pending["data"]["run"]["status"] = "PENDING"
    pending["data"]["run"]["finishedAt"] = None
    output = tmp_path / "capture"
    with pytest.raises(inventory.InventoryError):
        inventory.capture(fetcher([pending], []), REPOSITORY, "main", COMMIT, output)
    assert json.loads((output / "manifest.json").read_text())["complete"] is False
    assert not (output / "findings.ndjson").exists()


def test_page_budget_and_existing_output_are_not_silently_overwritten(tmp_path):
    output = tmp_path / "capture"
    with pytest.raises(inventory.InventoryError, match="page limit"):
        inventory.capture(
            fetcher([response([1], 2, more=True, cursor="next")], []), REPOSITORY, "main", COMMIT, output, 1
        )
    before = (output / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        inventory.capture(fetcher([], []), REPOSITORY, "main", COMMIT, output)
    assert (output / "manifest.json").read_bytes() == before


def test_mismatched_retained_page_cannot_become_a_complete_inventory(tmp_path):
    def fetch(variables, destination):
        destination.write_bytes(b"different evidence")
        return json.dumps(response([], 0)).encode()

    output = tmp_path / "capture"
    with pytest.raises(inventory.InventoryError, match="differs"):
        inventory.capture(fetch, REPOSITORY, "main", COMMIT, output)
    assert json.loads((output / "manifest.json").read_text())["complete"] is False
    assert not (output / "findings.ndjson").exists()


@pytest.mark.parametrize("raw", [b'{"data":{},"data":{}}', b'{"number":NaN}', b'{"number":1e9999}', b"\xff"])
def test_json_rejects_ambiguous_or_nonfinite_data(raw):
    with pytest.raises(inventory.InventoryError):
        inventory.decode(raw)


def test_credentials_use_explicit_cloud_token_or_cli_config(tmp_path, monkeypatch):
    config = tmp_path / "config.toml"
    config.write_text('token = "local-value"\nhost = "deepsource.com"\n', encoding="utf-8")
    monkeypatch.delenv("DEEPSOURCE_TOKEN", raising=False)
    assert inventory.credential(config) == "local-value"
    monkeypatch.setenv("DEEPSOURCE_TOKEN", "environment-value")
    assert inventory.credential(config) == "environment-value"
    monkeypatch.setenv("DEEPSOURCE_HOST", "private.example")
    with pytest.raises(inventory.InventoryError, match="reviewed"):
        inventory.credential(config)


def test_http_failure_is_retained_redacted_and_never_retried(tmp_path, monkeypatch):
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append((request.full_url, timeout))
            raise urllib.error.HTTPError(request.full_url, 403, "refused", Message(), io.BytesIO(b"refused test-token"))

    monkeypatch.setattr(inventory.urllib.request, "build_opener", lambda *args: Opener())
    output = tmp_path / "response.json"
    with pytest.raises(inventory.InventoryError, match="redacted"):
        inventory.transport("test-token", {}, output)
    assert calls == [(inventory.API, 45)]
    assert b"test-token" not in output.read_bytes()


def test_provider_forbidden_status_is_retained_and_reported_without_retry(tmp_path, monkeypatch):
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append(request.full_url)
            raise urllib.error.HTTPError(request.full_url, 403, "refused", Message(), io.BytesIO(b"refused"))

    monkeypatch.setattr(inventory.urllib.request, "build_opener", lambda *args: Opener())
    destination = tmp_path / "response.json"
    with pytest.raises(inventory.InventoryError, match="HTTP 403"):
        inventory.transport("test-token", {}, destination)
    assert destination.read_bytes() == b"refused" and calls == [inventory.API]


def test_redirects_and_oversized_responses_are_rejected(tmp_path, monkeypatch):
    with pytest.raises(inventory.InventoryError, match="redirected"):
        inventory._NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.example/")

    class Response(io.BytesIO):
        status = 200

    class Opener:
        def open(self, request, timeout):
            return Response(b"x" * (inventory.LIMIT + 1))

    monkeypatch.setattr(inventory.urllib.request, "build_opener", lambda *args: Opener())
    with pytest.raises(inventory.InventoryError, match="byte limit"):
        inventory.transport("test-token", {}, tmp_path / "response.json")


def test_slow_response_stops_at_deadline_and_retains_partial_bytes(tmp_path, monkeypatch):
    calls = []

    class Response(io.BytesIO):
        status = 200

        def read1(self, size: int | None = -1, /) -> bytes:
            return b"partial"

    class Opener:
        def open(self, request, timeout):
            calls.append(request.full_url)
            return Response()

    times = iter([0.0, 0.0, 91.0])
    monkeypatch.setattr(inventory.time, "monotonic", lambda: next(times, 91.0))
    monkeypatch.setattr(inventory.urllib.request, "build_opener", lambda *args: Opener())
    destination = tmp_path / "response.json"
    with pytest.raises(inventory.InventoryError, match="within its limits"):
        inventory.transport("test-token", {}, destination)
    assert destination.read_bytes() == b"partial" and calls == [inventory.API]


def test_output_inside_publishable_repository_tree_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(inventory, "ROOT", tmp_path)
    with pytest.raises(inventory.InventoryError, match="outside"):
        inventory.capture(fetcher([], []), REPOSITORY, "main", COMMIT, tmp_path / "report")
    assert not (tmp_path / "report").exists()

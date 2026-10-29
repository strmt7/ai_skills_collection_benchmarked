"""Check retry evidence and source stability without contacting a provider."""

import json
import types

import deepsource_inventory as inventory
import pytest
from test_deepsource_inventory import COMMIT, REPOSITORY, response


@pytest.mark.parametrize("server_status", [500, 502, 503, 504])
def test_retryable_server_errors_are_retained_and_retried(tmp_path, monkeypatch, server_status):
    """Record transient failures and complete after bounded retries."""
    calls = []
    delays: list[int] = []
    monkeypatch.setattr(inventory, "time", types.SimpleNamespace(sleep=delays.append))

    def fetch(variables, destination):
        """Fail the first two reads and then return the provider page."""
        calls.append(variables)
        if len(calls) <= 2:
            destination.write_bytes(b"")
            destination.with_name(destination.name + ".transport.json").write_text(
                json.dumps({"status": server_status}), encoding="utf-8"
            )
            raise inventory.RetryableProviderError(server_status)
        raw = json.dumps(response([], 0)).encode()
        destination.write_bytes(raw)
        return raw

    output = tmp_path / "capture"
    result = inventory.capture(fetch, REPOSITORY, "main", COMMIT, output)
    assert result["complete"] and result["total_count"] == 0
    assert delays == [1, 2] and len(calls) == 4
    assert [entry["http_status"] for entry in result["retries"]] == [server_status, server_status]
    for item in result["retries"]:
        assert (output / item["body_file"]).exists()
        assert (output / item["metadata_file"]).exists()
        assert len(item["body_sha256"]) == len(item["metadata_sha256"]) == 64


def test_repeated_server_error_stops_with_all_attempts(tmp_path, monkeypatch):
    """Stop after three server errors and retain every attempt."""
    delays: list[int] = []
    monkeypatch.setattr(inventory, "time", types.SimpleNamespace(sleep=delays.append))

    def fetch(variables, destination):
        """Retain a controlled server error for each attempt."""
        destination.write_bytes(b"")
        destination.with_name(destination.name + ".transport.json").write_text('{"status":503}', encoding="utf-8")
        raise inventory.RetryableProviderError(503)

    output = tmp_path / "capture"
    with pytest.raises(inventory.RetryableProviderError):
        inventory.capture(fetch, REPOSITORY, "main", COMMIT, output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert not manifest["complete"] and delays == [1, 2]
    assert [entry["attempt"] for entry in manifest["retries"]] == [1, 2, 3]
    for item in manifest["retries"]:
        assert (output / item["body_file"]).exists()
        assert (output / item["metadata_file"]).exists()


def test_non_retryable_failures_are_not_retried(tmp_path):
    """Fail immediately on provider errors outside the retry policy."""
    calls = []

    def fetch(variables, destination):
        """Return a controlled non-retryable authorization failure."""
        calls.append(variables)
        destination.write_bytes(b"")
        raise inventory.InventoryError("HTTP 403")

    with pytest.raises(inventory.InventoryError, match="403"):
        inventory.capture(fetch, REPOSITORY, "main", COMMIT, tmp_path / "capture")
    assert len(calls) == 1


def test_implementation_change_rejects_complete_inventory(tmp_path, monkeypatch):
    """Prevent publication if collector implementation bytes change."""
    baseline = inventory.implementation_digests()
    altered = dict(baseline)
    altered["_deepsource_rest_worker.py"] = "0" * 64
    observations = iter([baseline, altered])

    def observed_digests():
        """Fail clearly if the collector requests more observations than expected."""
        try:
            return next(observations)
        except StopIteration as error:
            raise AssertionError("Unexpected extra implementation observation") from error

    monkeypatch.setattr(inventory, "implementation_digests", observed_digests)

    def fetch(variables, destination):
        """Retain a consistent empty provider page."""
        raw = json.dumps(response([], 0)).encode()
        destination.write_bytes(raw)
        return raw

    output = tmp_path / "capture"
    with pytest.raises(inventory.InventoryError, match="implementation changed"):
        inventory.capture(fetch, REPOSITORY, "main", COMMIT, output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert not manifest["complete"]
    assert not (output / "findings.ndjson").exists()


def test_retry_does_not_hide_provider_identity_changes(tmp_path, monkeypatch):
    """Reject a changed provider run even after a transient gateway retry."""
    calls = []
    monkeypatch.setattr(inventory, "time", types.SimpleNamespace(sleep=lambda seconds: None))

    def fetch(variables, destination):
        """Return one page, a server error, then a changed analysis."""
        calls.append(variables)
        if len(calls) == 2:
            destination.write_bytes(b"")
            destination.with_name(destination.name + ".transport.json").write_text('{"status":502}', encoding="utf-8")
            raise inventory.RetryableProviderError(502)
        page = response([1], 2, more=True, cursor="next") if len(calls) == 1 else response([2], 2, run_id="changed")
        raw = json.dumps(page).encode()
        destination.write_bytes(raw)
        return raw

    output = tmp_path / "capture"
    with pytest.raises(inventory.InventoryError, match="identity or occurrence count changed"):
        inventory.capture(fetch, REPOSITORY, "main", COMMIT, output)
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert not manifest["complete"] and len(manifest["retries"]) == 1
    assert not (output / "findings.ndjson").exists()

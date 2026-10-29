"""Reject ambiguous or untrusted worker lifecycle metadata."""

import json

import deepsource_inventory as inventory
import pytest


@pytest.mark.parametrize(
    "event",
    [
        {"event": "headers", "status": True, "retry_after_present": False},
        {"event": "headers", "status": 200, "retry_after_present": "no"},
        {"event": "headers", "status": 200, "retry_after_present": False, "extra": "fixture-token"},
        {"event": "result", "endpoint": inventory.API, "kind": []},
        {"event": "result", "endpoint": inventory.API, "kind": "fixture-token"},
        {"event": "result", "endpoint": "https://other.invalid/", "kind": "redacted"},
        {"event": "result", "endpoint": inventory.API, "kind": "transport_error", "error_type": "token with spaces"},
    ],
)
def test_invalid_events_fail_closed(event):
    """Allow only typed, fixed worker metadata with a trusted endpoint."""
    with pytest.raises(inventory.InventoryError, match="invalid status"):
        inventory._worker_events(json.dumps(event).encode() + b"\n")


def test_duplicate_json_and_reordered_events_fail_closed():
    """Reject ambiguous JSON and invalid event ordering."""
    raw = b'{"event":"headers","event":"headers","status":200,"retry_after_present":false}\n'
    with pytest.raises(inventory.InventoryError):
        inventory._worker_events(raw)
    event = b'{"event":"headers","status":200,"retry_after_present":false}\n'
    with pytest.raises(inventory.InventoryError):
        inventory._worker_events(event + event)


def test_partial_event_is_not_retained():
    """Keep complete metadata while marking an incomplete final event."""
    event = b'{"event":"headers","status":200,"retry_after_present":false}\n'
    values, incomplete = inventory._worker_events(event + b'{"event":"result"')
    assert values == [{"event": "headers", "status": 200, "retry_after_present": False}]
    assert incomplete is True


def test_inconsistent_statuses_are_rejected():
    """Reject a final HTTP status that disagrees with the header event."""
    run = {"termination_reason": None, "exit_code": 0, "request_delivered": True}
    events = [
        {"event": "headers", "status": 200, "retry_after_present": False},
        {"event": "result", "endpoint": inventory.API, "kind": "http_error", "status": 503, "body_retained": True},
    ]
    with pytest.raises(inventory.InventoryError, match="inconsistent status"):
        inventory._completed_worker_status(run, events, False)


@pytest.mark.parametrize(
    "mode", ["timeout", "output_limit", "missing_result", "invalid_event", "invalid_json", "unretained_http"]
)
def test_unverified_worker_output_is_withheld(mode, tmp_path, monkeypatch):
    """Never retain output when the worker cannot attest to a complete safe body."""
    headers = {"event": "headers", "status": 200, "retry_after_present": False}
    result: dict[str, object] | None = {"event": "result", "endpoint": inventory.API, "kind": "ok", "status": 200}
    run = {"stdout": b"unverified bytes", "termination_reason": None, "exit_code": 0, "request_delivered": True}
    if mode in {"timeout", "output_limit"}:
        run.update(termination_reason=mode, exit_code=None)
    elif mode == "missing_result":
        result = None
    elif mode == "invalid_event":
        result = {"event": "result", "endpoint": inventory.API, "kind": "unexpected"}
    elif mode == "invalid_json":
        result = {"event": "result", "endpoint": inventory.API, "kind": "invalid_json", "status": 200}
    else:
        headers["status"] = 403
        result = {
            "event": "result",
            "endpoint": inventory.API,
            "kind": "http_error",
            "status": 403,
            "body_retained": False,
        }
    events = [headers] + ([result] if result is not None else [])
    run["stderr"] = b"".join(json.dumps(event).encode() + b"\n" for event in events)
    monkeypatch.setattr(inventory, "_supervised_request", lambda payload: run)
    target = tmp_path / "page.json"
    with pytest.raises(inventory.InventoryError):
        inventory.transport("fixture-token", {}, target)
    assert target.read_bytes() == b""
    receipt = json.loads((tmp_path / "page.json.transport.json").read_text(encoding="utf-8"))
    assert receipt["retained_bytes"] == 0


@pytest.mark.parametrize("mode", ["ok_non_200", "oversized_ok", "http_200"])
def test_inconsistent_worker_result_withholds_body(mode, tmp_path, monkeypatch):
    """Reject impossible status or size combinations before retaining output."""
    status = 201 if mode == "ok_non_200" else 200
    headers = {"event": "headers", "status": status, "retry_after_present": False}
    result = {"event": "result", "endpoint": inventory.API, "kind": "ok", "status": status}
    if mode == "http_200":
        result.update(kind="http_error", body_retained=True)
    raw = b"x" * (inventory.LIMIT + 1) if mode == "oversized_ok" else b"unverified bytes"
    events = b"".join(json.dumps(event).encode() + b"\n" for event in (headers, result))
    run = {"stdout": raw, "stderr": events, "termination_reason": None, "exit_code": 0, "request_delivered": True}
    monkeypatch.setattr(inventory, "_supervised_request", lambda payload: run)
    target = tmp_path / "page.json"
    with pytest.raises(inventory.InventoryError):
        inventory.transport("fixture-token", {}, target)
    assert target.read_bytes() == b""
    receipt = json.loads((tmp_path / "page.json.transport.json").read_text(encoding="utf-8"))
    assert receipt["retained_bytes"] == 0

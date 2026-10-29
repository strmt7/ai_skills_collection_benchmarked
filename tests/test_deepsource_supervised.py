"""Qualify real supervised DeepSource requests against owned local servers."""

import json
import logging
import sys
import threading
import time
from contextlib import suppress
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import _bounded_process as bounded
import _deepsource_rest_worker as worker
import deepsource_inventory as inventory
import pytest


@pytest.mark.parametrize(
    "mode", ["complete", "truncated", "redacted", "forbidden", "slow", "retry_after", "rate_limited"]
)
def test_supervised_local_http(mode, tmp_path, monkeypatch):
    """Verify supervised success and explicit failure behavior against an owned server."""
    token = "fixture-token"
    body = b'{"data":{"value":1}}'
    if mode == "redacted":
        body = b"prefix-" + token.encode() + b"-suffix"

    class Handler(BaseHTTPRequestHandler):
        """Serve controlled status, framing, credential and delay cases."""

        def do_POST(self):
            """Consume the request and emit the selected response scenario."""
            self.rfile.read(int(self.headers["Content-Length"]))
            status = {"forbidden": 403, "retry_after": 503, "rate_limited": 429}.get(mode, 200)
            self.send_response(status)
            if mode in {"retry_after", "rate_limited"}:
                self.send_header("Retry-After", "120")
            self.send_header("Content-Length", str(len(body) + (5 if mode == "truncated" else 0)))
            self.end_headers()
            if mode == "slow":
                self.wfile.write(b"p")
                self.wfile.flush()
                time.sleep(3)
            with suppress(BrokenPipeError, ConnectionResetError):
                self.wfile.write(body)

        def log_message(self, message, *args):
            """Send fixture HTTP diagnostics to the configured debug logger."""
            logging.getLogger(__name__).debug(message, *args)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.server_port}/"
    actual = Path(worker.__file__).resolve()
    wrapper = (
        "import importlib.util,urllib.request\n"
        f"spec=importlib.util.spec_from_file_location('worker',{str(actual)!r})\n"
        "w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)\n"
        f"w.API={endpoint!r}\n"
        "builder=urllib.request.build_opener\n"
        "w.urllib.request.build_opener=lambda *args: builder(urllib.request.ProxyHandler({}))\n"
        "raise SystemExit(w.main())\n"
    )
    (tmp_path / "_deepsource_rest_worker.py").write_text(wrapper, encoding="utf-8")
    leader = Path(inventory.__file__).with_name("_bounded_worker_leader.py")
    (tmp_path / "_bounded_worker_leader.py").write_bytes(leader.read_bytes())
    monkeypatch.setattr(inventory, "__file__", str(tmp_path / "deepsource_inventory.py"))
    monkeypatch.setattr(inventory, "API", endpoint)
    if mode == "slow":
        name = "run_windows" if sys.platform == "win32" else "run_posix"
        real = getattr(bounded, name)

        def shortened(command, timeout, output_limit, stdin=None):
            """Shorten only the test supervisor deadline for the stalled server."""
            return real(command, 1.0, output_limit, stdin=stdin)

        monkeypatch.setattr(bounded, name, shortened)
    destination = tmp_path / "response.bin"
    start = time.monotonic()
    try:
        if mode == "complete":
            assert inventory.transport(token, {}, destination) == body
        else:
            expected = {
                "truncated": "incomplete",
                "redacted": "credential",
                "forbidden": "HTTP 403",
                "slow": "time limit",
                "retry_after": "Retry-After",
                "rate_limited": "Retry-After",
            }[mode]
            with pytest.raises(inventory.InventoryError, match=expected) as caught:
                inventory.transport(token, {}, destination)
            if mode in {"retry_after", "rate_limited"}:
                assert type(caught.value) is inventory.InventoryError
    finally:
        elapsed = time.monotonic() - start
        thread.join(timeout=6)
        server.server_close()
    assert not thread.is_alive()
    assert destination.exists()
    assert destination.with_name(destination.name + ".transport.json").exists()
    assert token.encode() not in destination.read_bytes()
    if mode == "forbidden":
        assert destination.read_bytes() == body
    if mode == "redacted":
        assert destination.read_bytes() == b""
    metadata = json.loads(destination.with_name(destination.name + ".transport.json").read_text(encoding="utf-8"))
    expected_status = {"forbidden": 403, "retry_after": 503, "rate_limited": 429}.get(mode, 200)
    assert metadata["events"][0] == {
        "event": "headers",
        "status": expected_status,
        "retry_after_present": mode in {"retry_after", "rate_limited"},
    }
    if mode == "slow":
        assert elapsed < 2.5 and metadata["termination_reason"] == "timeout"
        assert metadata["events"] == [{"event": "headers", "status": 200, "retry_after_present": False}]
        assert destination.read_bytes() == b""
    if mode == "truncated":
        assert metadata["events"][-1]["kind"] == "incomplete_response"
        assert destination.read_bytes() == b""


def test_timeout_during_worker_output_withholds_partial_body(tmp_path, monkeypatch):
    """An interrupted output pipe must not publish a partial worker response."""
    child = (
        "import sys,time\n"
        "sys.stdin.buffer.read()\n"
        'sys.stderr.write(\'{"event":"headers","status":200,"retry_after_present":false}\\n\')\n'
        "sys.stderr.flush()\n"
        "sys.stdout.buffer.write(b'partial body')\n"
        "sys.stdout.buffer.flush()\n"
        "time.sleep(10)\n"
    )
    (tmp_path / "_deepsource_rest_worker.py").write_text(child, encoding="utf-8")
    leader = Path(inventory.__file__).with_name("_bounded_worker_leader.py")
    (tmp_path / "_bounded_worker_leader.py").write_bytes(leader.read_bytes())
    monkeypatch.setattr(inventory, "__file__", str(tmp_path / "deepsource_inventory.py"))
    name = "run_windows" if sys.platform == "win32" else "run_posix"
    real = getattr(bounded, name)

    def shortened(command, timeout, output_limit, stdin=None):
        """Use a short deadline for the owned worker."""
        return real(command, 1.0, output_limit, stdin=stdin)

    monkeypatch.setattr(bounded, name, shortened)
    target = tmp_path / "response.json"
    with pytest.raises(inventory.InventoryError, match="time limit"):
        inventory.transport("fixture-token", {}, target)
    assert target.read_bytes() == b""
    metadata = json.loads(target.with_name(target.name + ".transport.json").read_text(encoding="utf-8"))
    assert metadata["termination_reason"] == "timeout"
    assert metadata["retained_bytes"] == 0

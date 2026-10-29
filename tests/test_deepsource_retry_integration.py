"""Exercise a real retryable server failure through the complete collector."""

import json
import logging
import threading
import types
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import _deepsource_rest_worker as worker
import deepsource_inventory as inventory
import pytest
from test_deepsource_inventory import COMMIT, REPOSITORY, response


@pytest.mark.parametrize("server_status", [500, 502])
def test_server_retry_retains_receipt_and_completes(tmp_path, monkeypatch, server_status):
    """Retry a real local 502 once and retain its sanitized receipt."""
    body = json.dumps(response([], 0)).encode()
    calls = []

    class Handler(BaseHTTPRequestHandler):
        """Serve a retryable server failure followed by valid provider pages."""

        def do_POST(self):
            """Consume the request and emit the next controlled response."""
            self.rfile.read(int(self.headers["Content-Length"]))
            calls.append(1)
            status = server_status if len(calls) == 1 else 200
            payload = b"Provider Failure" if status == server_status else body
            self.send_response(status)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, message, *args):
            """Send fixture HTTP diagnostics to the configured debug logger."""
            logging.getLogger(__name__).debug(message, *args)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
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
    original_digests = inventory.implementation_digests()
    monkeypatch.setattr(inventory, "__file__", str(tmp_path / "deepsource_inventory.py"))
    monkeypatch.setattr(inventory, "API", endpoint)
    monkeypatch.setattr(inventory, "implementation_digests", lambda: original_digests)
    delays: list[int] = []
    monkeypatch.setattr(inventory, "time", types.SimpleNamespace(sleep=delays.append))
    output = tmp_path / "capture"
    try:
        result = inventory.capture(
            lambda variables, path: inventory.transport("fixture-token", variables, path),
            REPOSITORY,
            "main",
            COMMIT,
            output,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()
    assert not thread.is_alive()
    assert result["complete"] and result["total_count"] == 0
    assert len(calls) == 3 and delays == [1]
    assert len(result["retries"]) == 1
    retry = result["retries"][0]
    assert retry["http_status"] == server_status
    assert (output / retry["body_file"]).read_bytes() == b""
    metadata = json.loads((output / retry["metadata_file"]).read_text(encoding="utf-8"))
    assert metadata["events"][-1]["body_retained"] is False
    assert metadata["events"][-1]["status"] == server_status
    assert result["pages"][0]["transport_file"].endswith(".transport.json")
    assert result["final_transport_file"].endswith(".transport.json")
    assert "fixture-token" not in (output / retry["metadata_file"]).read_text(encoding="utf-8")

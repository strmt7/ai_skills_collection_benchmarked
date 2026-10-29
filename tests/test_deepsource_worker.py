"""Exercise DeepSource response integrity and streaming credential protection."""

import io
import threading
import urllib.request
from email.message import Message
from http.server import BaseHTTPRequestHandler, HTTPServer

import _deepsource_rest_worker as worker
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


@given(token=st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=8, max_size=24))
@settings(max_examples=500, deadline=None)
def test_decoded_json_credentials_are_detected_even_in_duplicate_keys(token):
    """Detect escaped credentials even when JSON repeats an object key."""
    escaped = "".join(f"\\u{ord(char):04x}" for char in token)
    body = ('{"value":"' + escaped + '","value":"safe"}').encode()
    assert token.encode() not in body
    assert worker._body_disposition(body, token) == "redacted"


def test_incomplete_or_unparseable_json_is_never_emitted():
    """Reject malformed and non-finite JSON before retaining a response."""
    assert worker._body_disposition(b"not-json", "fixture-token") == "invalid_json"
    assert worker._body_disposition(b'{"value":', "fixture-token") == "invalid_json"
    assert worker._body_disposition(b'{"value":NaN}', "fixture-token") == "invalid_json"
    assert worker._body_disposition(b'{"value":1e9999}', "fixture-token") == "invalid_json"


@pytest.mark.parametrize(("extra", "expected"), [(0, "ok"), (5, "incomplete_response")])
def test_real_http_declared_length(extra, expected, monkeypatch):
    """Compare complete and truncated bodies against their declared lengths."""
    body = b'{"data":{"value":1}}'

    class Handler(BaseHTTPRequestHandler):
        """Serve a controlled local response with a chosen declared length."""

        def do_POST(self):
            """Consume the request and send the controlled response."""
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(200)
            self.send_header("Content-Length", str(len(body) + extra))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            """Keep the owned local server quiet."""
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    monkeypatch.setattr(worker, "API", f"http://127.0.0.1:{server.server_port}/")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    monkeypatch.setattr(worker.urllib.request, "build_opener", lambda *args: opener)
    output = io.BytesIO()
    try:
        result = worker.request_page("fixture-token", {}, "query", output)
    finally:
        thread.join(timeout=3)
        server.server_close()
    assert not thread.is_alive()
    assert result["kind"] == expected
    if expected == "ok":
        assert output.getvalue() == body
    else:
        assert len(output.getvalue()) < len(body)


def test_provider_credential_is_never_emitted(monkeypatch):
    """Withhold an entire response that contains the credential."""
    body = b'prefix-"fixture-token"-suffix'

    class Response(io.BytesIO):
        """Provide a framed response that echoes a fixture credential."""

        status = 200
        length = None

        def __init__(self, data):
            """Attach the exact body length to the controlled response."""
            super().__init__(data)
            self.headers = Message()
            self.headers["Content-Length"] = str(len(data))

    class Opener:
        """Return the controlled credential-bearing response."""

        @staticmethod
        def open(request, timeout):
            """Supply the response without sending a network request."""
            return Response(body)

    monkeypatch.setattr(worker.urllib.request, "build_opener", lambda *args: Opener())
    output = io.BytesIO()
    result = worker.request_page("fixture-token", {}, "query", output)
    assert result == {"kind": "redacted"}
    assert output.getvalue() == b""
    assert b"fixture-token" not in output.getvalue()


def test_response_size_limit(monkeypatch):
    """Withhold responses larger than the configured limit."""

    class Response(io.BytesIO):
        """Provide a framed response exceeding the body limit."""

        status = 200
        length = None

        def __init__(self, data):
            """Attach the exact body length to the oversized response."""
            super().__init__(data)
            self.headers = Message()
            self.headers["Content-Length"] = str(len(data))

    class Opener:
        """Return the controlled oversized response."""

        @staticmethod
        def open(request, timeout):
            """Supply the oversized response without network access."""
            return Response(b"x" * (worker.LIMIT + 1))

    monkeypatch.setattr(worker.urllib.request, "build_opener", lambda *args: Opener())
    output = io.BytesIO()
    result = worker.request_page("fixture-token", {}, "query", output)
    assert result == {"kind": "response_too_large"}
    assert len(output.getvalue()) <= worker.LIMIT + 1


def test_redirects_are_refused():
    """Reject redirects before forwarding an authentication header."""
    with pytest.raises(ValueError, match="redirected"):
        worker.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid/")


def test_incomplete_chunked_response_is_withheld(monkeypatch):
    """Reject a chunked response that omits its terminating chunk."""

    class Handler(BaseHTTPRequestHandler):
        """Serve a chunked response without its terminating chunk."""

        def do_POST(self):
            """Consume the request and send an incomplete chunk stream."""
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(200)
            self.send_header("Transfer-Encoding", "chunked")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(b"2\r\n{}\r\n")
            self.wfile.flush()
            self.close_connection = True

        def log_message(self, *args):
            """Keep the owned local server quiet."""
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    monkeypatch.setattr(worker, "API", f"http://127.0.0.1:{server.server_port}/")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    monkeypatch.setattr(worker.urllib.request, "build_opener", lambda *args: opener)
    output = io.BytesIO()
    try:
        result = worker.request_page("fixture-token", {}, "query", output)
    finally:
        thread.join(timeout=3)
        server.server_close()
    assert not thread.is_alive()
    assert result["kind"] == "transport_error"
    assert output.getvalue() == b""


@pytest.mark.parametrize(
    ("headers", "status", "expected"),
    [
        ([("Content-Length", "2"), ("Transfer-Encoding", "chunked")], 200, "invalid_response"),
        ([("Content-Length", "2"), ("Content-Length", "3")], 200, "invalid_response"),
        ([("Content-Length", "invalid")], 200, "invalid_response"),
        ([("Transfer-Encoding", "gzip")], 200, "invalid_response"),
        ([], 200, "unframed_response"),
        ([], 502, "http_error"),
    ],
)
def test_ambiguous_or_unframed_response_is_not_admitted(headers, status, expected, monkeypatch):
    """Reject ambiguous framing and withhold unframed response bodies."""

    class Response(io.BytesIO):
        """Provide controlled response headers and a JSON body."""

        length = None

        def __init__(self):
            """Attach the selected framing headers to the response."""
            super().__init__(b"{}")
            self.status = status
            self.headers = Message()
            for name, value in headers:
                self.headers.add_header(name, value)

    class Opener:
        """Return the controlled framing example."""

        @staticmethod
        def open(request, timeout):
            """Supply the framing example without network access."""
            return Response()

    monkeypatch.setattr(worker.urllib.request, "build_opener", lambda *args: Opener())
    output = io.BytesIO()
    result = worker.request_page("fixture-token", {}, "query", output)
    assert result["kind"] == expected and output.getvalue() == b""
    if expected == "http_error":
        assert result["status"] == 502 and result["body_retained"] is False


def test_complete_chunked_response_is_admitted(monkeypatch):
    """Accept a correctly terminated chunked JSON response."""

    class Handler(BaseHTTPRequestHandler):
        """Serve a correctly terminated chunked response."""

        def do_POST(self):
            """Consume the request and send complete chunked JSON."""
            self.rfile.read(int(self.headers["Content-Length"]))
            self.send_response(200)
            self.send_header("Transfer-Encoding", "chunked")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(b"2\r\n{}\r\n0\r\n\r\n")
            self.wfile.flush()
            self.close_connection = True

        def log_message(self, *args):
            """Keep the owned local server quiet."""
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    monkeypatch.setattr(worker, "API", f"http://127.0.0.1:{server.server_port}/")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    monkeypatch.setattr(worker.urllib.request, "build_opener", lambda *args: opener)
    output = io.BytesIO()
    try:
        result = worker.request_page("fixture-token", {}, "query", output)
    finally:
        thread.join(timeout=3)
        server.server_close()
    assert not thread.is_alive()
    assert result["kind"] == "ok" and output.getvalue() == b"{}"

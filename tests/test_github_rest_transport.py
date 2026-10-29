"""Security and lifecycle controls for the GitHub code-scanning transport."""

from __future__ import annotations

import http.server
import io
import json
import subprocess
import sys
import threading
import urllib.request
from email.message import Message
from pathlib import Path

import _github_rest_worker as worker
import check_code_scanning_alerts as gate
import pytest


def frame(body=b"{}", metadata=None):
    """Encode a worker response in the bounded wire format."""
    payload = json.dumps({"links": []} if metadata is None else metadata, separators=(",", ":")).encode("ascii")
    return len(payload).to_bytes(4, "big") + payload + body


def install_result(monkeypatch, data=b"", code=0, reason=None, stderr=b""):
    """Replace process launch while retaining parent-side response validation."""

    def run(command, timeout, limit):
        """Return a controlled worker outcome."""
        assert command[0] and command[1:3] == ["-I", "-S"]
        assert timeout == 45 and limit == gate.MAX_OUTPUT
        return {"exit_code": code, "termination_reason": reason, "stdout": data, "stderr": stderr}

    monkeypatch.setattr(gate, "_run_windows", run)
    monkeypatch.setattr(gate, "_run_posix", run)


def test_valid_unicode_and_pagination(monkeypatch):
    """Decode UTF-8 and preserve a correctly formed next-page link."""
    link = '<https://api.github.com/a?page=2>; rel="next"'
    install_result(monkeypatch, frame('{"value":"καλημέρα"}'.encode(), {"links": [link]}))
    result, next_url = gate.github("repos/owner/name")
    assert result == {"value": "καλημέρα"}
    assert next_url == "https://api.github.com/a?page=2"


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"abc",
        b"\x00\x01\x00\x01",
        b"\x00\x00\x00\x02{}",
        frame(b"\xff"),
        frame(b"{"),
        frame(b'{"x":1,"x":2}'),
        frame(b'{"x":NaN}'),
        frame(b'{"x":1e999}'),
        frame(metadata={"links": [], "extra": 1}),
        frame(metadata={"links": "bad"}),
        frame(metadata={"links": [1]}),
    ],
)
def test_invalid_frames_fail_closed(monkeypatch, data):
    """Reject truncated, ambiguous, non-finite or malformed worker responses."""
    install_result(monkeypatch, data)
    with pytest.raises(gate.GateError):
        gate.github("repos/owner/name")


@pytest.mark.parametrize(
    "links",
    [
        ["invalid"],
        ['<a>; rel="next"', '<b>; rel="next"'],
        ['<a>; rel="next", <b>; rel="next"'],
    ],
)
def test_invalid_pagination_fails_closed(monkeypatch, links):
    """Reject malformed or ambiguous pagination headers."""
    install_result(monkeypatch, frame(metadata={"links": links}))
    with pytest.raises(gate.GateError):
        gate.github("repos/owner/name")


@pytest.mark.parametrize(
    ("reason", "code", "stderr", "expected"),
    [
        ("timeout", 124, b"", "time limit"),
        ("output_limit", 124, b"", "output limit"),
        (None, 2, b"invalid_token", "invalid_token"),
        (None, 2, b"incomplete_response", "incomplete_response"),
        (None, 2, b"untrusted raw output", "unavailable"),
    ],
)
def test_worker_errors_are_sanitized(monkeypatch, reason, code, stderr, expected):
    """Report useful failure categories without copying untrusted output."""
    install_result(monkeypatch, code=code, reason=reason, stderr=stderr)
    with pytest.raises(gate.GateError, match=expected) as exc:
        gate.github("repos/owner/name")
    assert "untrusted raw output" not in str(exc.value)


class Response:
    """Provide a controlled HTTP response for request validation."""

    def __init__(self, body=b"{}", status=200, links=()):
        self.status = status
        self.headers = Message()
        self.data = io.BytesIO(body)
        self.length = None
        for link in links:
            self.headers.add_header("Link", link)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.data.close()

    def read(self, size):
        """Return up to the requested number of bytes."""
        return self.data.read(size)


class Opener:
    """Record requests without sending a token over the network."""

    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, request, timeout):
        """Record and return the configured response."""
        self.requests.append((request, timeout))
        return self.response


@pytest.fixture
def provision(monkeypatch):
    """Supply a non-secret token and a controlled HTTP opener."""
    monkeypatch.setenv("GH_TOKEN", "fixture")

    def install(response):
        """Install one response and expose recorded requests."""
        opener = Opener(response)
        monkeypatch.setattr(worker.urllib.request, "build_opener", lambda *args: opener)
        return opener

    return install


def test_request_authentication_and_version(provision):
    """Send credentials only in the API request header."""
    opener = provision(Response(b'{"status":"ok"}', links=['<https://api.github.com/a?page=2>; rel="next"']))
    body, links = worker.fetch("repos/owner/name")
    assert body == b'{"status":"ok"}' and len(links) == 1
    request, timeout = opener.requests[0]
    assert request.full_url == "https://api.github.com/repos/owner/name" and timeout == 45
    assert request.get_header("Authorization") == "Bearer fixture"
    assert request.get_header("X-github-api-version") == "2026-03-10"


@pytest.mark.parametrize(
    "url",
    [
        "http://evil.invalid/x",
        "https://evil.invalid/x",
        "//evil.invalid/x",
        "https://api.github.com@evil.invalid/x",
        "https://api.github.com:443/x",
        "/absolute",
        "https://api.github.com/x#fragment",
    ],
)
def test_wrong_origins_fail_before_request(provision, url):
    """Never send the bearer credential to an unrelated origin."""
    opener = provision(Response())
    with pytest.raises(worker.WorkerError):
        worker.fetch(url)
    assert not opener.requests


@pytest.mark.parametrize(
    "url", ["http://evil.invalid/x", "https://evil.invalid/x", "https://api.github.com@evil.invalid/x"]
)
def test_cross_origin_redirect_is_rejected(url):
    """Reject redirects that could expose the authorization header."""
    handler = worker.Redirect()
    request = urllib.request.Request("https://api.github.com/a", headers={"Authorization": "Bearer fixture"})
    with pytest.raises(worker.WorkerError):
        handler.redirect_request(request, None, 302, "Found", Message(), url)


def test_same_origin_redirect_is_allowed():
    """Preserve authenticated redirects within the public GitHub API origin."""
    handler = worker.Redirect()
    request = urllib.request.Request("https://api.github.com/a", headers={"Authorization": "Bearer fixture"})
    redirected = handler.redirect_request(request, None, 302, "Found", Message(), "https://api.github.com/b")
    assert redirected.full_url == "https://api.github.com/b"
    assert redirected.get_header("Authorization") == "Bearer fixture"


def test_response_size_limit(provision):
    """Reject a body larger than the documented byte bound."""
    provision(Response(b"x" * (worker.MAX_BODY + 1)))
    with pytest.raises(worker.WorkerError, match="response_too_large"):
        worker.fetch("repos/owner/name")


@pytest.mark.parametrize("links", [["a", "b"], ["a" * (worker.MAX_LINK + 1)]])
def test_link_limits(provision, links):
    """Reject multiple or excessively large pagination headers."""
    provision(Response(links=links))
    with pytest.raises(worker.WorkerError, match="invalid_link_headers"):
        worker.fetch("repos/owner/name")


def test_http_status_is_checked(provision):
    """Reject a non-success API status."""
    provision(Response(status=403))
    with pytest.raises(worker.WorkerError, match="unexpected_status"):
        worker.fetch("repos/owner/name")


@pytest.mark.parametrize("value", ["", "bad\nvalue", "spaces are bad"])
def test_invalid_token_is_rejected(monkeypatch, provision, value):
    """Reject invalid bearer tokens before making a request."""
    opener = provision(Response())
    monkeypatch.setenv("GH_TOKEN", value)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    with pytest.raises(worker.WorkerError):
        worker.fetch("repos/owner/name")
    assert not opener.requests


class TruncatedHandler(http.server.BaseHTTPRequestHandler):
    """Return valid JSON while violating the declared response length."""

    def do_GET(self):
        """Close the response before all declared bytes are sent."""
        self.send_response(200)
        self.send_header("Content-Length", "20")
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *args):
        """Keep the owned test server quiet."""


def test_incomplete_http_response_fails(monkeypatch):
    """A parseable partial payload must not become accepted API evidence."""
    server = http.server.HTTPServer(("127.0.0.1", 0), TruncatedHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.start()
    native_opener = urllib.request.build_opener()

    class LocalOpener:
        """Route the test request to the owned local server."""

        @staticmethod
        def open(request, timeout):
            """Return the real local HTTP response."""
            return native_opener.open(f"http://127.0.0.1:{server.server_port}/", timeout=timeout)

    monkeypatch.setenv("GH_TOKEN", "fixture")
    monkeypatch.setattr(worker.urllib.request, "build_opener", lambda *args: LocalOpener())
    try:
        with pytest.raises(worker.WorkerError, match="incomplete_response"):
            worker.fetch("repos/owner/name")
    finally:
        thread.join(timeout=3)
        server.server_close()
    assert not thread.is_alive()


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups are unavailable on Windows")
@pytest.mark.parametrize(("mode", "expected"), [("normal", None), ("stalled", "timeout"), ("flood", "output_limit")])
def test_posix_owned_worker_is_bounded(tmp_path, mode, expected):
    """Exercise the real process-group supervisor under normal and hostile output."""
    leader = tmp_path / "_github_rest_leader.py"
    leader.write_bytes(Path(gate.__file__).with_name("_github_rest_leader.py").read_bytes())
    script = (
        "import sys,time\n"
        "mode=sys.argv[1]\n"
        "if mode=='stalled': time.sleep(30)\n"
        "if mode=='flood': sys.stdout.write('x'*100000); sys.stdout.flush()\n"
        "if mode=='normal': print('ok')\n"
    )
    (tmp_path / "_github_rest_worker.py").write_text(script, encoding="utf-8")
    result = gate._run_posix([sys.executable, "-I", "-S", str(leader), mode], 2, 4096)
    assert result["termination_reason"] == expected
    if mode == "normal":
        assert result["exit_code"] == 0 and result["stdout"] == b"ok\n"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows jobs are unavailable on this platform")
@pytest.mark.parametrize(("mode", "expected"), [("normal", None), ("stalled", "timeout"), ("flood", "output_limit")])
def test_windows_owned_worker_is_bounded(mode, expected):
    """Exercise the real Windows job for normal output, timeouts and output limits."""
    code = {
        "normal": "print('ok')",
        "stalled": "import time; time.sleep(30)",
        "flood": "print('x'*100000)",
    }[mode]
    result = gate._run_windows([sys.executable, "-I", "-S", "-c", code], 2, 4096)
    assert result["termination_reason"] == expected
    if mode == "normal":
        assert result["exit_code"] == 0 and result["stdout"] == b"ok\r\n"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups are unavailable on Windows")
@pytest.mark.parametrize("stalled", [True, False])
def test_posix_leader_self_cleans_without_parent(tmp_path, stalled):
    """A surviving leader must terminate its owned group after a bounded deadline."""
    source = Path(gate.__file__).with_name("_github_rest_leader.py").read_text(encoding="utf-8")
    assert "WORKER_TIMEOUT = 45" in source and "CLEANUP_TIMEOUT = 50" in source
    source = source.replace("WORKER_TIMEOUT = 45", "WORKER_TIMEOUT = 1")
    source = source.replace("CLEANUP_TIMEOUT = 50", "CLEANUP_TIMEOUT = 2")
    leader = tmp_path / "_github_rest_leader.py"
    leader.write_text(source, encoding="utf-8")
    worker_source = "import time; time.sleep(30)" if stalled else "print('done')"
    (tmp_path / "_github_rest_worker.py").write_text(worker_source, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(leader), "fixture"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == -9


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX process groups are unavailable on Windows")
def test_posix_leader_rejects_unisolated_session():
    """Never terminate a process group owned by the calling shell."""
    leader = Path(gate.__file__).with_name("_github_rest_leader.py")
    result = subprocess.run(
        [sys.executable, "-I", "-S", str(leader), "fixture"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
        check=False,
    )
    assert result.returncode == 2

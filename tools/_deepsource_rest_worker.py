"""Fetch and validate a DeepSource page before emitting its response bytes."""

from __future__ import annotations

import json
import math
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any, BinaryIO

API = "https://api.deepsource.com/graphql/"
LIMIT = 4 * 1024 * 1024
REQUEST_LIMIT = 128 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward the provider credential to another endpoint."""

    def redirect_request(self, request, fp, code, message, headers, url):
        """Reject every redirect without logging the destination."""
        raise ValueError("redirected")


def _contains_credential(value: Any, token: str) -> bool:
    """Inspect all decoded JSON strings, including duplicate object keys."""
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, str) and token in item:
            return True
        if isinstance(item, (list, tuple)):
            pending.extend(item)
    return False


def _nonfinite(value: str) -> None:
    """Reject nonstandard JSON constants."""
    raise ValueError("nonfinite JSON constant")


def _finite_float(value: str) -> float:
    """Reject numeric values that overflow to infinity."""
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite JSON number")
    return number


def _body_disposition(raw: bytes, token: str) -> str:
    """Admit complete JSON only after raw and decoded credential checks."""
    if token.encode() in raw:
        return "redacted"
    try:
        value = json.loads(
            raw, object_pairs_hook=lambda pairs: pairs, parse_constant=_nonfinite, parse_float=_finite_float
        )
    except (ValueError, RecursionError):
        return "invalid_json"
    return "redacted" if _contains_credential(value, token) else "ok"


class ResponseError(ValueError):
    """Describe a rejected response without retaining provider content."""


def _validated_framing(response: Any) -> tuple[bool, int | None]:
    """Apply the shared HTTP framing contract in isolated Python mode."""
    root = str(Path(__file__).resolve().parent)
    sys.path.insert(0, root)
    try:
        from _http_framing import FramingError, response_framing
    finally:
        sys.path.pop(0)
    try:
        return response_framing(response, LIMIT)
    except FramingError as error:
        raise ResponseError(str(error)) from error


def _read_body(response: Any, expected_length: int | None) -> bytes:
    """Read only a complete, size-bounded HTTP response."""
    reader = getattr(response, "read1", None)
    if not callable(reader):
        raise ResponseError("invalid_response")
    body = bytearray()
    while len(body) <= LIMIT:
        requested = min(65536, LIMIT + 1 - len(body))
        chunk = reader(requested)
        if not isinstance(chunk, bytes) or len(chunk) > requested:
            raise ResponseError("invalid_response")
        if not chunk:
            if getattr(response, "length", None) not in (None, 0):
                raise ResponseError("incomplete_response")
            if expected_length is not None and len(body) != expected_length:
                raise ResponseError("incomplete_response")
            return bytes(body)
        body.extend(chunk)
    raise ResponseError("response_too_large")


def _finish_page(status: int, raw: bytes, token: str, output: BinaryIO) -> dict:
    """Emit only complete JSON without raw or decoded credential echoes."""
    disposition = _body_disposition(raw, token)
    if disposition == "redacted":
        return {"kind": "redacted"}
    if disposition == "ok":
        output.write(raw)
        output.flush()
    if status != 200:
        return {"kind": "http_error", "status": status, "body_retained": disposition == "ok"}
    return {"kind": disposition, "status": status}


def request_page(
    token: str,
    variables: dict,
    query: str,
    output: BinaryIO,
    report: Callable[[dict], None] = lambda event: None,
) -> dict:
    """Read one bounded page and emit bytes only after validation."""
    if not token or any(char.isspace() for char in token):
        return {"kind": "invalid_token"}
    request = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "skills-collection-inventory/1.0",
            "Cache-Control": "no-cache",
        },
    )
    opener = urllib.request.build_opener(NoRedirect())
    try:
        try:
            response = opener.open(request, timeout=45)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            status = response.status
            if type(status) is not int or not 100 <= status <= 599:
                return {"kind": "invalid_response"}
            headers = getattr(response, "headers", None)
            retry_after_present = headers is None or bool(headers.get_all("Retry-After", []))
            report({"event": "headers", "status": status, "retry_after_present": retry_after_present})
            framed, expected_length = _validated_framing(response)
            if not framed:
                if status == 200:
                    return {"kind": "unframed_response"}
                return {"kind": "http_error", "status": status, "body_retained": False}
            return _finish_page(status, _read_body(response, expected_length), token, output)
    except ResponseError as error:
        return {"kind": str(error)}
    except Exception as error:
        return {"kind": "transport_error", "error_type": type(error).__name__}


def _report(event: dict) -> None:
    """Emit only bounded machine-readable lifecycle metadata."""
    sys.stderr.write(json.dumps(event, separators=(",", ":")) + "\n")
    sys.stderr.flush()


def main() -> int:
    """Read the request from the private pipe and report a sanitized result."""
    try:
        raw = sys.stdin.buffer.read(REQUEST_LIMIT + 1)
        if len(raw) > REQUEST_LIMIT:
            raise ValueError("request too large")
        request = json.loads(raw)
        if (
            not isinstance(request, dict)
            or set(request) != {"token", "variables", "query"}
            or not isinstance(request["token"], str)
            or not isinstance(request["variables"], dict)
            or not isinstance(request["query"], str)
        ):
            raise ValueError("invalid request")
        result = request_page(request["token"], request["variables"], request["query"], sys.stdout.buffer, _report)
    except Exception as error:
        result = {"kind": "invalid_request", "error_type": type(error).__name__}
    _report({"event": "result", "endpoint": API, **result})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

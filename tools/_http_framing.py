"""Validate HTTP/1.1 framing before an API response is admitted."""

from __future__ import annotations

from typing import Any


class FramingError(ValueError):
    """An HTTP response has unsafe or unsupported framing."""


def _content_length(value: Any, limit: int) -> int:
    """Validate a single declared length before reading its body."""
    if not isinstance(value, str):
        raise FramingError("invalid_response")
    value = value.strip()
    if not value.isascii() or not value.isdecimal() or len(value) > 20:
        raise FramingError("invalid_response")
    length = int(value)
    if length > limit:
        raise FramingError("response_too_large")
    return length


def response_framing(response: Any, limit: int) -> tuple[bool, int | None]:
    """Return whether framing is explicit and its declared length, if any."""
    headers = getattr(response, "headers", None)
    if headers is None or not callable(getattr(headers, "get_all", None)):
        raise FramingError("invalid_response")
    lengths = headers.get_all("Content-Length", [])
    transfers = headers.get_all("Transfer-Encoding", [])
    if len(lengths) > 1 or len(transfers) > 1 or (lengths and transfers):
        raise FramingError("invalid_response")
    if transfers:
        if not isinstance(transfers[0], str) or transfers[0].strip().lower() != "chunked":
            raise FramingError("invalid_response")
        return True, None
    if lengths:
        return True, _content_length(lengths[0], limit)
    return False, None

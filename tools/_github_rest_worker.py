"""Fetch one bounded GitHub API response for the code-scanning gate."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit

MAX_BODY = 8 * 1024 * 1024
MAX_LINK = 8192


class WorkerError(Exception):
    """Reject an API request or response that violates the worker contract."""


def api_url(endpoint):
    """Accept only HTTPS requests to the public GitHub API origin."""
    if endpoint.startswith("https://"):
        url = endpoint
    else:
        parts = urlsplit(endpoint)
        if parts.scheme or parts.netloc or endpoint.startswith("/"):
            raise WorkerError("invalid_url")
        url = "https://api.github.com/" + endpoint
    p = urlsplit(url)
    if p.scheme != "https" or p.netloc != "api.github.com" or p.fragment or not p.path.startswith("/"):
        raise WorkerError("invalid_url")
    return url


class Redirect(urllib.request.HTTPRedirectHandler):
    """Keep redirect targets on the authenticated GitHub API origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """Reject redirects that could disclose the request credentials."""
        if api_url(newurl) != newurl:
            raise WorkerError("invalid_redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch(endpoint):
    """Fetch a size-bounded response without exposing credentials in diagnostics."""
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")
    if not token or any(not 33 <= ord(c) <= 126 for c in token):
        raise WorkerError("invalid_token")
    request = urllib.request.Request(
        api_url(endpoint),
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
            "User-Agent": "ai-skills-code-scanning-gate/1.0",
        },
    )
    with urllib.request.build_opener(Redirect()).open(request, timeout=45) as response:
        if response.status != 200:
            raise WorkerError("unexpected_status")
        links = response.headers.get_all("Link", [])
        if len(links) > 1 or any(len(x) > MAX_LINK for x in links):
            raise WorkerError("invalid_link_headers")
        body = response.read(MAX_BODY + 1)
        if len(body) > MAX_BODY:
            raise WorkerError("response_too_large")
        if response.length not in (None, 0):
            raise WorkerError("incomplete_response")
    return body, links


def main(argv=None):
    """Emit a framed response or a sanitized failure category."""
    args = sys.argv[1:] if argv is None else argv
    try:
        if len(args) != 1:
            raise WorkerError("invalid_arguments")
        body, links = fetch(args[0])
        metadata = json.dumps({"links": links}, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        if len(metadata) > 65536:
            raise WorkerError("metadata_too_large")
        sys.stdout.buffer.write(len(metadata).to_bytes(4, "big") + metadata + body)
        sys.stdout.buffer.flush()
    except WorkerError as error:
        sys.stderr.write(str(error))
        return 2
    except urllib.error.URLError as error:
        sys.stderr.write("transport_" + type(error.reason).__name__)
        return 2
    except Exception as error:
        sys.stderr.write("unexpected_" + type(error).__name__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

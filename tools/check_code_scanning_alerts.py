"""Check the complete default-branch code-scanning alert budget.

The API has no atomic snapshot: two matching inventories, stable branch head,
and stable exact-commit CodeQL analyses detect, but cannot exclude, races.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import selectors
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from contextlib import suppress
from pathlib import Path
from typing import IO, Any, BinaryIO, cast
from urllib.parse import parse_qs, urlencode, urlsplit

CATEGORIES = frozenset({"/language:python", "/language:javascript-typescript", "/language:actions"})
REPOSITORY = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
ALERT_LIMIT = 2


class GateError(Exception):
    """GitHub evidence is missing, inconsistent, or violates the gate contract."""


MAX_BODY = 8 * 1024 * 1024
MAX_META = 65536
MAX_STDERR = 4096
MAX_OUTPUT = MAX_BODY + MAX_META + MAX_STDERR + 4


def _next_link(headers: list[str]) -> str | None:
    """Read one unambiguous next link; the caller validates its scope."""
    if len(headers) > 1:
        raise GateError("Invalid GitHub response")
    if not headers:
        return None
    seen_relations = set()
    next_url = None
    for part in headers[0].split(","):
        match = re.fullmatch(r'\s*<([^<>]+)>;\s*rel="(next|prev|first|last)"\s*', part)
        if not match or match.group(2) in seen_relations:
            raise GateError("Invalid GitHub response")
        seen_relations.add(match.group(2))
        if match.group(2) == "next":
            next_url = match.group(1)
    return next_url


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject ambiguous JSON objects with repeated keys."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    """Reject JSON constants outside the finite-number contract."""
    raise ValueError("nonfinite JSON number")


def _finite_float(value: str) -> float:
    """Reject numbers that overflow to infinity during JSON decoding."""
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("nonfinite JSON number")
    return number


if sys.platform != "win32":
    from os import killpg
    from signal import SIGKILL

    def _kill_group(pid: int) -> None:
        """Terminate the isolated worker process group."""
        killpg(pid, SIGKILL)

else:

    def _kill_group(pid: int) -> None:
        """Reject the POSIX cleanup path on Windows."""
        raise RuntimeError("POSIX process groups are unavailable on Windows")


_EXIT_MARKER = re.compile(rb"\n__GH_WORKER_EXIT__:(-?[0-9]{1,10})\n\Z")


def _collect_posix_output(
    stdout: IO[bytes], stderr: IO[bytes], deadline: float, output_limit: int
) -> tuple[dict[str, bytearray], str | None, int | None]:
    """Collect pipes until worker status and stdout EOF, with one deadline and limit."""
    outputs = {"stdout": bytearray(), "stderr": bytearray()}
    worker_exit = None
    with selectors.DefaultSelector() as selector:
        selector.register(stdout.fileno(), selectors.EVENT_READ, "stdout")
        selector.register(stderr.fileno(), selectors.EVENT_READ, "stderr")
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return outputs, "timeout", None
            for key, _ in selector.select(remaining):
                available = output_limit + 1 - sum(len(value) for value in outputs.values())
                chunk = os.read(key.fd, min(65536, available))
                if not chunk:
                    selector.unregister(key.fd)
                    continue
                outputs[key.data].extend(chunk)
                if sum(len(value) for value in outputs.values()) > output_limit or len(outputs["stderr"]) > MAX_STDERR:
                    return outputs, "output_limit", None
                if key.data == "stderr":
                    match = _EXIT_MARKER.search(outputs["stderr"])
                    if match:
                        worker_exit = int(match.group(1))
                        del outputs["stderr"][match.start() :]
                        selector.unregister(key.fd)
    return outputs, None if worker_exit is not None else "missing_status", worker_exit


def _cleanup_posix(process: subprocess.Popen[bytes]) -> None:
    """Kill the owned group, reap its leader, and close both output pipes."""
    try:
        try:
            with suppress(ProcessLookupError):
                _kill_group(process.pid)
        finally:
            process.wait(timeout=5)
    finally:
        try:
            if process.stdout is not None:
                process.stdout.close()
        finally:
            if process.stderr is not None:
                process.stderr.close()


def _run_posix(command: list[str], timeout: float, output_limit: int) -> dict[str, Any]:
    """Keep the leader unreaped until its owned process group is terminated."""
    if not command or not os.path.isabs(command[0]) or timeout <= 0 or output_limit <= 0:
        raise ValueError("invalid worker bounds")
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    deadline = time.monotonic() + timeout
    try:
        if process.stdout is None or process.stderr is None:
            raise RuntimeError("worker output pipes are unavailable")
        outputs, reason, worker_exit = _collect_posix_output(process.stdout, process.stderr, deadline, output_limit)
    finally:
        _cleanup_posix(process)
    return {
        "exit_code": worker_exit,
        "termination_reason": reason,
        "stdout": bytes(outputs["stdout"]),
        "stderr": bytes(outputs["stderr"]),
    }


def _run_windows(command, timeout, output_limit):
    """Use a job to stop the worker and its job-associated descendants."""
    root = str(Path(__file__).resolve().parent)
    sys.path.insert(0, root)
    try:
        from _windows_trial_process import run_owned
    finally:
        sys.path.pop(0)
    with (
        tempfile.TemporaryFile() as stdin,
        tempfile.TemporaryFile() as stdout,
        tempfile.TemporaryFile() as stderr,
    ):
        report = run_owned(
            command,
            cwd=Path(root),
            stdin=cast(BinaryIO, stdin),
            stdout=cast(BinaryIO, stdout),
            stderr=cast(BinaryIO, stderr),
            timeout=timeout,
            output_limit=output_limit,
        )
        stdout.seek(0)
        stderr.seek(0)
        return {
            "exit_code": report["exit_code"],
            "termination_reason": report["termination_reason"],
            "stdout": stdout.read(output_limit + 1),
            "stderr": stderr.read(output_limit + 1),
        }


def _check_worker_result(run: dict[str, Any]) -> bytes:
    """Reject timeouts, output overruns and sanitized worker failures."""
    if len(run["stderr"]) > MAX_STDERR:
        raise GateError("GitHub API worker exceeded its output limit")
    reason = run["termination_reason"]
    if reason == "timeout":
        raise GateError("GitHub API worker exceeded its time limit")
    if reason == "output_limit":
        raise GateError("GitHub API worker exceeded its output limit")
    if reason is not None:
        raise GateError("GitHub API worker was terminated")
    if run["exit_code"] != 0:
        diagnostic = run["stderr"].decode("ascii", errors="replace")
        if not re.fullmatch(
            r"(?:invalid_url|invalid_redirect|invalid_token|unexpected_status|invalid_link_headers|"
            r"response_too_large|incomplete_response|invalid_arguments|metadata_too_large|"
            r"transport_[A-Za-z0-9_]+|unexpected_[A-Za-z0-9_]+)",
            diagnostic,
        ):
            diagnostic = "unavailable"
        raise GateError("GitHub API worker failed: " + diagnostic)
    return run["stdout"]


def _decode_worker_result(data: bytes) -> tuple[Any, str | None]:
    """Validate the bounded frame, strict JSON body and pagination header."""
    if len(data) < 4 or len(data) > MAX_OUTPUT:
        raise ValueError("invalid frame")
    length = int.from_bytes(data[:4], "big")
    if length > MAX_META or len(data) < 4 + length or len(data) - 4 - length > MAX_BODY:
        raise ValueError("invalid frame")
    metadata = json.loads(
        data[4 : 4 + length].decode("ascii"),
        object_pairs_hook=_object_pairs,
        parse_constant=_nonfinite,
        parse_float=_finite_float,
    )
    if (
        not isinstance(metadata, dict)
        or set(metadata) != {"links"}
        or not isinstance(metadata["links"], list)
        or any(not isinstance(item, str) for item in metadata["links"])
    ):
        raise ValueError("invalid headers")
    body = json.loads(
        data[4 + length :].decode("utf8"),
        object_pairs_hook=_object_pairs,
        parse_constant=_nonfinite,
        parse_float=_finite_float,
    )
    return body, _next_link(metadata["links"])


def github(endpoint: str) -> tuple[Any, str | None]:
    """Read one bounded authenticated API response in a supervised worker."""
    worker = Path(__file__).resolve().with_name("_github_rest_worker.py")
    executable = Path(sys.executable)
    if not executable.is_absolute() or not executable.is_file() or not worker.is_file():
        raise GateError("GitHub API worker is unavailable")
    script = worker if sys.platform == "win32" else worker.with_name("_github_rest_leader.py")
    if not script.is_file():
        raise GateError("GitHub API process supervisor is unavailable")
    command = [str(executable), "-I", "-S", str(script), endpoint]
    try:
        run = _run_windows(command, 45, MAX_OUTPUT) if sys.platform == "win32" else _run_posix(command, 45, MAX_OUTPUT)
        return _decode_worker_result(_check_worker_result(run))
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        raise GateError("GitHub API worker failed or returned invalid data") from exc


def _validate_link_origin(link: str, endpoint: str, repo_id: int) -> dict[str, list[str]]:
    """Require a next link to stay on the same GitHub API endpoint."""
    parsed = urlsplit(link)
    if (
        parsed.scheme != "https"
        or parsed.netloc != "api.github.com"
        or parsed.path != f"/repositories/{repo_id}/{endpoint}"
        or parsed.fragment
    ):
        raise GateError("Invalid or repeated pagination link")
    return parse_qs(parsed.query, keep_blank_values=True)


def _validate_link_query(query: dict[str, list[str]], fixed: dict[str, str]) -> None:
    """Require unchanged filters and exactly one nonempty cursor."""
    if (
        any(query.get(k) != [v] for k, v in fixed.items())
        or set(query) - (set(fixed) | {"page", "after", "before"})
        or sum(k in query for k in ("page", "after", "before")) != 1
        or any(len(v) != 1 or not v[0] for v in query.values())
    ):
        raise GateError("Invalid or repeated pagination link")


def _validated_page_link(link: str, endpoint: str, repo_id: int, fixed: dict[str, str], seen: set[str]) -> None:
    """Reject links that change origin, filters or previously visited pages."""
    query = _validate_link_origin(link, endpoint, repo_id)
    _validate_link_query(query, fixed)
    if link in seen:
        raise GateError("Invalid or repeated pagination link")


def _analysis_values(row: dict[str, Any]) -> tuple[str, str, int]:
    """Validate the commit, error state and identity of one CodeQL analysis."""
    sha, error, ident = row.get("commit_sha"), row.get("error"), row.get("id")
    if not isinstance(sha, str) or not isinstance(error, str) or type(ident) is not int or ident <= 0:
        raise GateError("Malformed CodeQL analysis")
    return sha, error, ident


def _analysis_row(row: Any, latest: dict[str, tuple[str, str, int]]) -> None:
    """Retain the newest valid CodeQL analysis for a required category."""
    if not isinstance(row, dict) or not isinstance(row.get("tool"), dict):
        raise GateError("Invalid analysis row")
    category = row.get("category")
    if (
        isinstance(category, str)
        and row["tool"].get("name") == "CodeQL"
        and category in CATEGORIES
        and category not in latest
    ):
        latest[category] = _analysis_values(row)


def _alert_number(row: Any, ids: set[int]) -> int:
    """Validate one open alert and reject repeated identifiers."""
    if (
        not isinstance(row, dict)
        or type(row.get("number")) is not int
        or row["number"] <= 0
        or row.get("state") != "open"
    ):
        raise GateError("Invalid alert row")
    if row["number"] in ids:
        raise GateError("Duplicate alert")
    return row["number"]


class _Inventory:
    """Read a source-bound, paginated GitHub code-scanning inventory."""

    def __init__(self, fetch: Callable[[str], tuple[Any, str | None]], prefix: str, repo_id: int):
        self.fetch = fetch
        self.prefix = prefix
        self.repo_id = repo_id

    def one(self, endpoint: str) -> Any:
        """Read a singleton API object and reject unexpected pagination."""
        value, link = self.fetch(endpoint)
        if link is not None:
            raise GateError("Unexpected pagination on singleton response")
        return value

    def head(self) -> str:
        """Read and validate the current main-branch commit."""
        try:
            value = self.one(f"{self.prefix}/branches/main")["commit"]["sha"]
        except (KeyError, TypeError) as exc:
            raise GateError("Invalid branch response") from exc
        if not isinstance(value, str) or not COMMIT.fullmatch(value):
            raise GateError("Invalid branch head")
        return value

    def pages(self, endpoint: str, params: dict[str, str]) -> Iterator[list[Any]]:
        """Read all pages without allowing a link to escape its fixed scope."""
        fixed = {**params, "per_page": "100"}
        url = f"{self.prefix}/{endpoint}?{urlencode(fixed)}"
        seen = {url}
        for _ in range(1000):
            value, link = self.fetch(url)
            if not isinstance(value, list) or len(value) > 100:
                raise GateError("Invalid paginated response")
            yield value
            if link is None:
                return
            _validated_page_link(link, endpoint, self.repo_id, fixed, seen)
            seen.add(link)
            url = link
        raise GateError("Page limit exceeded")

    def analyses(self, commit: str) -> dict[str, tuple[str, str, int]]:
        """Require fresh successful analyses for all required CodeQL categories."""
        latest: dict[str, tuple[str, str, int]] = {}
        for page in self.pages("code-scanning/analyses", {"ref": "refs/heads/main", "direction": "desc"}):
            for row in page:
                _analysis_row(row, latest)
            if len(latest) == len(CATEGORIES):
                break
        if set(latest) != CATEGORIES or any(sha != commit or error for sha, error, _ in latest.values()):
            raise GateError("CodeQL analyses missing, stale, or failed")
        return latest

    def alerts(self) -> set[int]:
        """Read a complete inventory of unique open alert numbers."""
        ids: set[int] = set()
        for page in self.pages("code-scanning/alerts", {"ref": "refs/heads/main", "state": "open"}):
            for row in page:
                ids.add(_alert_number(row, ids))
        return ids


def _repository_id(fetch: Callable[[str], tuple[Any, str | None]], repository: str) -> int:
    """Bind the API response to the requested repository and default branch."""
    metadata, link = fetch(f"repos/{repository}")
    if link is not None:
        raise GateError("Unexpected pagination on singleton response")
    if (
        not isinstance(metadata, dict)
        or type(metadata.get("id")) is not int
        or metadata["id"] <= 0
        or metadata.get("default_branch") != "main"
        or not isinstance(metadata.get("full_name"), str)
        or metadata["full_name"].lower() != repository.lower()
    ):
        raise GateError("Invalid repository identity")
    return metadata["id"]


def check(fetch: Callable[[str], tuple[Any, str | None]], repository: str, commit: str) -> dict[str, Any]:
    """Return the observed budget after independent source and inventory checks."""
    if not REPOSITORY.fullmatch(repository) or repository.split("/")[-1] in {".", ".."}:
        raise GateError("Invalid repository")
    if not COMMIT.fullmatch(commit):
        raise GateError("Invalid commit")
    inventory = _Inventory(fetch, f"repos/{repository}", _repository_id(fetch, repository))
    if inventory.head() != commit:
        raise GateError("Main changed before inventory")
    before = inventory.analyses(commit)
    ids = inventory.alerts()
    if inventory.alerts() != ids:
        raise GateError("Alert inventory changed between observations")
    if inventory.head() != commit or inventory.analyses(commit) != before or inventory.head() != commit:
        raise GateError("Source or analysis changed during inventory")
    return {
        "repository": repository,
        "commit": commit,
        "open_alerts": len(ids),
        "limit": ALERT_LIMIT,
        "passed": len(ids) <= ALERT_LIMIT,
        "fresh_codeql_categories": sorted(before),
        "atomic_snapshot": False,
    }


def build_parser() -> argparse.ArgumentParser:
    """Define the repository and commit arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--commit", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the gate and return a machine-readable result."""
    args = build_parser().parse_args(argv)
    try:
        result = check(github, args.repository, args.commit)
    except GateError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

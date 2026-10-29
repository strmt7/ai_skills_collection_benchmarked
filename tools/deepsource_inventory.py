"""Capture a checked, paginated DeepSource default-branch occurrence inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import threading
import time
import tomllib
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from _windows_appcontainer import checked_path

API = "https://api.deepsource.com/graphql/"
ROOT = Path(__file__).resolve().parents[1]
LIMIT = 4 * 1024 * 1024
QUERY = """query Inventory($owner: String!, $name: String!, $commit: String!, $after: String, $first: Int!) {
  run(commitOid: $commit) { id commitOid status finishedAt repository { id } }
  repository(login: $owner, name: $name, vcsProvider: GITHUB) {
    id name vcsUrl vcsProvider defaultBranch latestCommitOid configJson
    issueOccurrences(first: $first, after: $after) {
      totalCount pageInfo { hasNextPage endCursor }
      edges { node { id path beginLine beginColumn endLine endColumn title
        issue { shortcode category severity shortDescription analyzer { name shortcode } }
      } }
    }
  }
}"""


class InventoryError(ValueError):
    """A sanitized retrieval or integrity failure."""


class RetryableProviderError(InventoryError):
    """An explicitly retryable provider server error."""

    def __init__(self, status: int):
        """Accept only the server statuses eligible for bounded retries."""
        if status not in {500, 502, 503, 504}:
            raise ValueError("Unsupported retryable status")
        self.status = status
        super().__init__(f"DeepSource returned HTTP {status}; inspect retained transport metadata")


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject JSON objects with repeated keys."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InventoryError("Duplicate JSON field")
        result[key] = value
    return result


def _finite(value: str) -> float:
    """Reject floating-point values that overflow to infinity."""
    number = float(value)
    if not math.isfinite(number):
        raise InventoryError("Non-finite JSON number")
    return number


def _constant(value: str) -> None:
    """Reject nonstandard non-finite JSON constants."""
    raise InventoryError("Non-finite JSON constant")


def decode(raw: bytes) -> Any:
    """Decode provider JSON without accepting ambiguous or non-finite values."""
    try:
        return json.loads(raw, object_pairs_hook=_unique, parse_float=_finite, parse_constant=_constant)
    except (ValueError, RecursionError) as error:
        raise InventoryError("Invalid or ambiguous provider JSON") from error


def _object(value: Any) -> dict[str, Any]:
    """Require a JSON object before accessing provider fields."""
    if not isinstance(value, dict):
        raise InventoryError("Provider response has an invalid object")
    return value


def _text(value: Any) -> str:
    """Require a nonempty text field from the provider."""
    if not isinstance(value, str) or not value:
        raise InventoryError("Provider response is missing required text")
    return value


def _count(value: Any) -> int:
    """Require a nonnegative integer without accepting booleans."""
    if type(value) is not int or value < 0:
        raise InventoryError("Provider response has an invalid count")
    return value


def credential(config: Path) -> str:
    """Use the explicit token or the official CLI's existing cloud login."""
    token = os.environ.get("DEEPSOURCE_TOKEN")
    if token:
        host = os.environ.get("DEEPSOURCE_HOST", "deepsource.com")
    else:
        with config.open("rb") as stream:
            settings = tomllib.load(stream)
        token, host = settings.get("token"), settings.get("host", "deepsource.com")
    if host not in {"deepsource.com", "deepsource.io", "app.deepsource.com"}:
        raise InventoryError("The configured provider is not the reviewed DeepSource cloud")
    if not isinstance(token, str) or not token or any(char.isspace() for char in token):
        raise InventoryError("Use the official DeepSource CLI login or DEEPSOURCE_TOKEN")
    return token


def _supervisor():
    """Load the source-bound worker supervisor in isolated Python mode."""
    root = str(Path(__file__).resolve().parent)
    sys.path.insert(0, root)
    try:
        import _bounded_process as bounded
    finally:
        sys.path.pop(0)
    return bounded


def _send_request(writer, payload: bytes, result: list[str]) -> None:
    """Send credentials through an anonymous pipe without exposing them."""
    try:
        view = memoryview(payload)
        while view:
            count = writer.write(view)
            if not isinstance(count, int) or count <= 0:
                raise OSError("request pipe made no progress")
            view = view[count:]
        result.append("sent")
    except OSError:
        result.append("closed")
    finally:
        try:
            writer.close()
        except OSError:
            result.append("close_failed")


def _worker_command() -> list[str]:
    """Select the repository-owned worker and platform supervisor."""
    root = Path(__file__).resolve().parent
    worker = root / "_deepsource_rest_worker.py"
    leader = root / "_bounded_worker_leader.py"
    executable = Path(sys.executable)
    if not executable.is_absolute() or not executable.is_file() or not worker.is_file():
        raise InventoryError("DeepSource worker is unavailable")
    if sys.platform != "win32" and not leader.is_file():
        raise InventoryError("DeepSource process supervisor is unavailable")
    command = [str(executable), "-I", "-S", str(worker if sys.platform == "win32" else leader)]
    if sys.platform != "win32":
        command.append(worker.name)
    command.append("request")
    return command


def _request_pipe():
    """Create an owned anonymous pipe, closing both sides on setup failure."""
    read_fd, write_fd = os.pipe()
    try:
        reader = os.fdopen(read_fd, "rb", buffering=0)
    except BaseException:
        try:
            os.close(read_fd)
        finally:
            os.close(write_fd)
        raise
    try:
        writer = os.fdopen(write_fd, "wb", buffering=0)
    except BaseException:
        try:
            reader.close()
        finally:
            os.close(write_fd)
        raise
    return reader, writer


def _supervised_request(payload: bytes) -> dict[str, Any]:
    """Run the private API worker with bounded time, output and owned cleanup."""
    command = _worker_command()
    reader, writer = _request_pipe()
    sent: list[str] = []
    thread = threading.Thread(target=_send_request, args=(writer, payload, sent), daemon=True)
    try:
        thread.start()
    except BaseException:
        try:
            reader.close()
        finally:
            writer.close()
        raise
    try:
        bounded = _supervisor()
        run = (
            bounded.run_windows(command, 90, LIMIT + 4097, stdin=reader)
            if sys.platform == "win32"
            else bounded.run_posix(command, 90, LIMIT + 4097, stdin=reader)
        )
    finally:
        try:
            reader.close()
        finally:
            thread.join(timeout=5)
    if thread.is_alive():
        raise InventoryError("DeepSource request pipe did not close")
    run["request_delivered"] = sent == ["sent"]
    return run


def _validate_event_fields(event: dict[str, Any]) -> None:
    """Reject invalid status, retention or error-type metadata."""
    if "status" in event and (type(event["status"]) is not int or not 100 <= event["status"] <= 599):
        raise InventoryError("DeepSource worker returned invalid status")
    if "body_retained" in event and type(event["body_retained"]) is not bool:
        raise InventoryError("DeepSource worker returned invalid status")
    if "error_type" in event and (
        not isinstance(event["error_type"], str)
        or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,79}", event["error_type"])
    ):
        raise InventoryError("DeepSource worker returned invalid status")


def _validate_result_event(event: dict[str, Any]) -> dict[str, Any]:
    """Require a known result kind and its exact allowed fields."""
    base = {"event", "endpoint", "kind"}
    fields = {
        "ok": base | {"status"},
        "http_error": base | {"status", "body_retained"},
        "transport_error": base | {"error_type"},
        "invalid_request": base | {"error_type"},
        "redacted": base,
        "response_too_large": base,
        "incomplete_response": base,
        "invalid_json": base | {"status"},
        "invalid_token": base,
        "invalid_response": base,
        "unframed_response": base,
    }
    kind = event.get("kind")
    if event.get("endpoint") != API or not isinstance(kind, str) or kind not in fields:
        raise InventoryError("DeepSource worker returned invalid status")
    if set(event) != fields[kind]:
        raise InventoryError("DeepSource worker returned invalid status")
    _validate_event_fields(event)
    return event


def _validate_worker_event(event: Any) -> dict[str, Any]:
    """Reject status fields that could carry untrusted provider content."""
    if not isinstance(event, dict):
        raise InventoryError("DeepSource worker returned invalid status")
    if event.get("event") == "headers":
        if (
            set(event) != {"event", "status", "retry_after_present"}
            or type(event["status"]) is not int
            or type(event["retry_after_present"]) is not bool
        ):
            raise InventoryError("DeepSource worker returned invalid status")
        _validate_event_fields(event)
        return event
    if event.get("event") == "result":
        return _validate_result_event(event)
    raise InventoryError("DeepSource worker returned invalid status")


def _worker_events(data: bytes) -> tuple[list[dict[str, Any]], bool]:
    """Validate complete, ordered lifecycle events without retaining raw stderr."""
    lines = data.splitlines(keepends=True)
    incomplete = bool(lines and not lines[-1].endswith(b"\n"))
    complete_lines = lines[:-1] if incomplete else lines
    events = [_validate_worker_event(decode(line)) for line in complete_lines]
    names = [event["event"] for event in events]
    if names not in ([], ["headers"], ["result"], ["headers", "result"]):
        raise InventoryError("DeepSource worker returned invalid status")
    return events, incomplete


def _retain_worker_metadata(run: dict[str, Any], destination: Path, raw: bytes) -> tuple[list[dict[str, Any]], bool]:
    """Retain bounded, validated lifecycle metadata even on failures."""
    metadata_path = destination.with_name(destination.name + ".transport.json")
    metadata: dict[str, Any] = {
        "schema_version": 1,
        "termination_reason": run["termination_reason"],
        "exit_code": run["exit_code"],
        "request_delivered": run["request_delivered"],
        "retained_bytes": len(raw),
    }
    try:
        events, incomplete = _worker_events(run["stderr"])
        metadata.update(events=events, incomplete_event=incomplete)
    except InventoryError:
        metadata["invalid_worker_status"] = True
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        raise
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return events, incomplete


def _validate_process_outcome(run: dict[str, Any]) -> None:
    """Require a successful bounded worker and complete request delivery."""
    reason = run["termination_reason"]
    if reason == "timeout":
        raise InventoryError("DeepSource response exceeded its time limit; unverified body was withheld")
    if reason == "output_limit":
        raise InventoryError("Provider response exceeds the byte limit")
    if reason is not None or run["exit_code"] != 0:
        raise InventoryError("DeepSource worker failed; unverified body was withheld")
    if not run["request_delivered"]:
        raise InventoryError("DeepSource request pipe closed before delivery")


def _completed_worker_status(run: dict[str, Any], events: list[dict[str, Any]], incomplete: bool) -> dict[str, Any]:
    """Require a consistent final status after a successful process."""
    _validate_process_outcome(run)
    results = [event for event in events if event["event"] == "result"]
    if incomplete or len(results) != 1:
        raise InventoryError("DeepSource worker returned invalid status")
    status = results[0]
    headers = [event for event in events if event["event"] == "headers"]
    if "status" in status and (not headers or headers[0]["status"] != status["status"]):
        raise InventoryError("DeepSource worker returned inconsistent status")
    return {**status, "retry_after_present": headers[0]["retry_after_present"] if headers else True}


def _admit_worker_body(status: dict[str, Any], raw: bytes) -> bytes:
    """Interpret the final provider status without exposing response content."""
    kind = status["kind"]
    failures = {
        "redacted": "Provider response contained the credential; response body was withheld",
        "response_too_large": "Provider response exceeds the byte limit",
        "incomplete_response": "DeepSource response was incomplete; response body was withheld",
        "unframed_response": "DeepSource response lacked verifiable framing; response body was withheld",
    }
    if kind in failures:
        raise InventoryError(failures[kind])
    if kind == "http_error":
        if status["status"] in {500, 502, 503, 504} and not status["retry_after_present"]:
            raise RetryableProviderError(status["status"])
        if status["retry_after_present"]:
            raise InventoryError(
                f"DeepSource returned HTTP {status['status']} with Retry-After; automatic retry skipped"
            )
        raise InventoryError(f"DeepSource returned HTTP {status['status']}; inspect retained transport metadata")
    if kind != "ok":
        raise InventoryError("DeepSource response could not be safely read; inspect retained transport metadata")
    if status.get("status") != 200 or len(raw) > LIMIT:
        raise InventoryError("DeepSource worker returned invalid status")
    return raw


def transport(token: str, variables: dict[str, Any], destination: Path) -> bytes:
    """Capture a bounded, complete provider response or explicit failure metadata."""
    if not isinstance(token, str) or not token or any(char.isspace() for char in token):
        raise InventoryError("A valid DeepSource credential is required")
    payload = json.dumps({"token": token, "variables": variables, "query": QUERY}).encode("utf-8")
    if len(payload) > 128 * 1024:
        raise InventoryError("DeepSource request exceeds the input limit")
    try:
        run = _supervised_request(payload)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        raise InventoryError("DeepSource worker could not be supervised") from exc
    retained = b""
    try:
        events, incomplete = _worker_events(run["stderr"])
        status = _completed_worker_status(run, events, incomplete)
        if len(run["stdout"]) > LIMIT:
            raise InventoryError("Provider response exceeds the byte limit")
        success_body = status["kind"] == "ok" and status["status"] == 200
        error_body = status["kind"] == "http_error" and status["status"] != 200 and status["body_retained"]
        if success_body or error_body:
            retained = run["stdout"]
    finally:
        destination.write_bytes(retained)
        _retain_worker_metadata(run, destination, retained)
    return _admit_worker_body(status, retained)


def _provider_identity(data: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Extract the provider repository and analysis identity."""
    run, repo = _object(data.get("run")), _object(data.get("repository"))
    config = repo.get("configJson")
    if config is not None and not isinstance(config, dict):
        raise InventoryError("Provider response has an invalid repository configuration")
    identity: dict[str, Any] = {
        "id": _text(repo.get("id")),
        "name": _text(repo.get("name")),
        "vcsUrl": _text(repo.get("vcsUrl")),
        "vcsProvider": _text(repo.get("vcsProvider")),
        "defaultBranch": _text(repo.get("defaultBranch")),
        "latestCommitOid": _text(repo.get("latestCommitOid")),
        "configJson": config,
        "run": {
            "id": _text(run.get("id")),
            "commitOid": _text(run.get("commitOid")),
            "status": _text(run.get("status")),
            "finishedAt": _text(run.get("finishedAt")),
            "repository_id": _text(_object(run.get("repository")).get("id")),
        },
    }
    return identity, repo


def _validate_identity(identity: dict[str, Any], repository: str, branch: str, commit: str) -> None:
    """Require the completed analysis to match the requested repository and head."""
    if (
        identity["name"] != repository.split("/")[1]
        or identity["vcsUrl"] != f"https://github.com/{repository}"
        or identity["vcsProvider"] != "GITHUB"
        or identity["defaultBranch"] != branch
        or identity["latestCommitOid"] != commit
        or identity["run"]["commitOid"] != commit
        or identity["run"]["repository_id"] != identity["id"]
        or identity["run"]["status"] not in {"SUCCESS", "FAILURE"}
    ):
        raise InventoryError("Repository, branch or completed analysis does not match the requested commit")


def _occurrence_entries(edges: Any) -> list[dict[str, Any]]:
    """Validate every occurrence before adding it to the inventory."""
    entries = []
    for edge in edges:
        item = _object(_object(edge).get("node"))
        for field in ("id", "path", "title"):
            _text(item.get(field))
        for field in ("beginLine", "beginColumn", "endLine", "endColumn"):
            _count(item.get(field))
        issue = _object(item.get("issue"))
        for field in ("shortcode", "category", "severity"):
            _text(issue.get(field))
        _text(_object(issue.get("analyzer")).get("shortcode"))
        entries.append(item)
    return entries


def page(
    raw: bytes, repository: str, branch: str, commit: str
) -> tuple[dict[str, Any], list[dict[str, Any]], int, bool, str | None]:
    """Validate one provider page, its source identity and pagination fields."""
    envelope = _object(decode(raw))
    if envelope.get("errors"):
        raise InventoryError("DeepSource returned GraphQL errors")
    identity, repo = _provider_identity(_object(envelope.get("data")))
    _validate_identity(identity, repository, branch, commit)
    connection = _object(repo.get("issueOccurrences"))
    total, edges, info = (
        _count(connection.get("totalCount")),
        connection.get("edges"),
        _object(connection.get("pageInfo")),
    )
    if not isinstance(edges, list) or len(edges) > 100 or type(info.get("hasNextPage")) is not bool:
        raise InventoryError("Invalid occurrence pagination")
    entries = _occurrence_entries(edges)
    more = info["hasNextPage"]
    return identity, entries, total, more, _text(info.get("endCursor")) if more else None


def _retain_retry(path: Path, attempt: int, error: RetryableProviderError) -> dict[str, Any]:
    """Preserve a failed server response and its sanitized transport metadata."""
    metadata = path.with_name(path.name + ".transport.json")
    if not path.is_file() or not metadata.is_file():
        raise InventoryError("Retryable provider failure lacks retained evidence") from error
    if attempt < 3:
        failed = path.with_name(path.name + f".attempt-{attempt}.failed")
        failed_metadata = failed.with_name(failed.name + ".transport.json")
        if failed.exists() or failed_metadata.exists():
            raise InventoryError("Retry evidence already exists") from error
        path.replace(failed)
        metadata.replace(failed_metadata)
    else:
        failed, failed_metadata = path, metadata
    return {
        "page": path.name,
        "attempt": attempt,
        "http_status": error.status,
        "body_file": failed.name,
        "body_sha256": hashlib.sha256(failed.read_bytes()).hexdigest(),
        "metadata_file": failed_metadata.name,
        "metadata_sha256": hashlib.sha256(failed_metadata.read_bytes()).hexdigest(),
    }


def observed(
    fetch: Callable[[dict[str, Any], Path], bytes],
    variables: dict[str, Any],
    path: Path,
    retries: list[dict[str, Any]],
) -> bytes:
    """Retain every retryable server failure while retrying a read-only query."""
    for attempt in range(1, 4):
        try:
            raw = fetch(variables.copy(), path)
        except RetryableProviderError as error:
            retries.append(_retain_retry(path, attempt, error))
            if attempt == 3:
                raise
            time.sleep(2 ** (attempt - 1))
            continue
        if not isinstance(raw, bytes) or len(raw) > LIMIT or path.read_bytes() != raw:
            raise InventoryError("Retained provider response differs from the received bytes")
        return raw
    raise InventoryError("DeepSource retries were exhausted")


def implementation_digests() -> dict[str, str]:
    """Bind the collector, worker and platform supervisors to the evidence."""
    root = Path(__file__).resolve().parent
    names = (
        "deepsource_inventory.py",
        "_deepsource_rest_worker.py",
        "_bounded_process.py",
        "_http_framing.py",
        "_bounded_worker_leader.py",
        "_windows_trial_process.py",
        "_windows_appcontainer.py",
        "_windows_owned_python.py",
    )
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names}


class _Traversal:
    """Collect and reconcile a source-bound sequence of provider pages."""

    def __init__(self, fetch, repository, branch, commit, output, retries):
        """Bind traversal state to one repository, commit and output directory."""
        self.fetch = fetch
        self.repository = repository
        self.branch = branch
        self.commit = commit
        self.output = output
        self.retries = retries
        self.variables = {
            "owner": repository.split("/")[0],
            "name": repository.split("/")[1],
            "commit": commit,
            "first": 100,
            "after": None,
        }
        self.identity = None
        self.expected = 0
        self.identifiers: set[str] = set()
        self.cursors: set[str] = set()
        self.counts: Counter[str] = Counter()
        self.pages: list[dict[str, Any]] = []
        self.first_id: str | None = None

    def _write_occurrences(self, entries, stream) -> None:
        """Reject duplicate IDs and stream admitted findings."""
        for item in entries:
            identifier = item["id"]
            if identifier in self.identifiers:
                raise InventoryError("Duplicate occurrence ID")
            self.identifiers.add(identifier)
            if self.first_id is None:
                self.first_id = identifier
            self.counts[item["issue"]["category"]] += 1
            stream.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n")

    def _record_page(self, name, raw, entries) -> None:
        """Bind page and transport evidence to their content hashes."""
        record = {"file": name, "sha256": hashlib.sha256(raw).hexdigest(), "count": len(entries)}
        metadata = self.output / (name + ".transport.json")
        if metadata.is_file():
            record["transport_file"] = metadata.name
            record["transport_sha256"] = hashlib.sha256(metadata.read_bytes()).hexdigest()
        self.pages.append(record)

    def _advance(self, entries, more, cursor) -> bool:
        """Check the provider cursor and the declared occurrence total."""
        if not more:
            if len(self.identifiers) != self.expected:
                raise InventoryError("Occurrence count does not match the provider total")
            return False
        if not entries or cursor in self.cursors or len(self.identifiers) >= self.expected:
            raise InventoryError("Occurrence pagination did not advance consistently")
        self.cursors.add(_text(cursor))
        self.variables["after"] = cursor
        return True

    def run(self, max_pages: int) -> None:
        """Traverse every page while checking identity, count and uniqueness."""
        temporary = self.output / "findings.ndjson.partial"
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            for number in range(1, max_pages + 1):
                name = f"page-{number:04d}.json"
                raw = observed(self.fetch, self.variables, self.output / name, self.retries)
                current, entries, total, more, cursor = page(raw, self.repository, self.branch, self.commit)
                if self.identity is None:
                    self.identity, self.expected = current, total
                if current != self.identity or total != self.expected:
                    raise InventoryError("Analysis identity or occurrence count changed during retrieval")
                self._write_occurrences(entries, stream)
                self._record_page(name, raw, entries)
                if not self._advance(entries, more, cursor):
                    return
        raise InventoryError("Occurrence retrieval exceeded the page limit")

    def final_observation(self) -> bytes:
        """Recheck the provider identity, count and first occurrence."""
        self.variables.update(first=1, after=None)
        raw = observed(self.fetch, self.variables, self.output / "final-observation.json", self.retries)
        current, entries, total, more, _ = page(raw, self.repository, self.branch, self.commit)
        if (
            current != self.identity
            or total != self.expected
            or len(entries) != min(1, self.expected)
            or more != (self.expected > 1)
            or (entries and entries[0]["id"] != self.first_id)
        ):
            raise InventoryError("The final observation differs from the completed traversal")
        return raw


def _publish_inventory(
    traversal: _Traversal, manifest: dict[str, Any], raw: bytes, implementation: dict[str, str]
) -> dict[str, Any]:
    """Publish complete findings only after rechecking implementation bytes."""
    output = traversal.output
    final_metadata = output / "final-observation.json.transport.json"
    if final_metadata.is_file():
        manifest["final_transport_file"] = final_metadata.name
        manifest["final_transport_sha256"] = hashlib.sha256(final_metadata.read_bytes()).hexdigest()
    temporary = output / "findings.ndjson.partial"
    digest = hashlib.sha256()
    with temporary.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    identity = traversal.identity
    if identity is None:
        raise InventoryError("Analysis identity was not observed")
    config_digest = hashlib.sha256(
        json.dumps(identity["configJson"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    if implementation_digests() != implementation:
        raise InventoryError("Collector implementation changed during retrieval")
    temporary.replace(output / "findings.ndjson")
    manifest.update(
        complete=True,
        total_count=traversal.expected,
        pages=traversal.pages,
        categories=dict(sorted(traversal.counts.items())),
        provider_identity={key: value for key, value in identity.items() if key != "configJson"},
        provider_configuration_sha256=config_digest,
        final_observation_sha256=hashlib.sha256(raw).hexdigest(),
        findings_sha256=digest.hexdigest(),
        consistency="Stable identity, count and first occurrence; provider snapshot isolation is not guaranteed",
    )
    return manifest


def _capture_output(repository: str, branch: str, commit: str, output: Path, max_pages: int) -> Path:
    """Validate the requested inventory identity, bounds and output location."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise InventoryError("Use owner/repository and a complete lowercase commit SHA")
    if not branch or type(max_pages) is not int or not 1 <= max_pages <= 1000:
        raise InventoryError("Invalid branch or page limit")
    output = checked_path(output)
    if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / ".venv"):
        raise InventoryError("Use an output outside the repository or under its .venv directory")
    return output


def capture(
    fetch: Callable[[dict[str, Any], Path], bytes],
    repository: str,
    branch: str,
    commit: str,
    output: Path,
    max_pages: int = 1000,
) -> dict[str, Any]:
    """Capture all occurrences only when source and final observations agree."""
    output = _capture_output(repository, branch, commit, output, max_pages)
    implementation = implementation_digests()
    output.mkdir(exist_ok=False)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "complete": False,
        "endpoint": API,
        "requested_repository": repository,
        "requested_branch": branch,
        "requested_commit": commit,
        "query_sha256": hashlib.sha256(QUERY.encode()).hexdigest(),
        "tool_sha256": implementation["deepsource_inventory.py"],
        "implementation_sha256": implementation,
        "retries": [],
    }
    try:
        traversal = _Traversal(fetch, repository, branch, commit, output, manifest["retries"])
        traversal.run(max_pages)
        return _publish_inventory(traversal, manifest, traversal.final_observation(), implementation)
    except (InventoryError, OSError, RecursionError) as error:
        manifest["failure"] = (
            str(error) if isinstance(error, InventoryError) else "Local I/O or response processing failed"
        )
        raise
    finally:
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Define the inventory identity and output arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", default="main")
    parser.add_argument("--commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path.home() / ".deepsource" / "config.toml")
    parser.add_argument("--max-pages", type=int, default=1000)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Capture a provider inventory and report its result."""
    args = build_parser().parse_args(argv)
    try:
        token = credential(args.config)
        result = capture(
            lambda variables, destination: transport(token, variables, destination),
            args.repository,
            args.branch,
            args.commit,
            args.output,
            args.max_pages,
        )
    except InventoryError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, ValueError, RecursionError):
        print("DeepSource inventory failed; inspect the retained evidence and provider access.", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {"complete": result["complete"], "total_count": result["total_count"], "categories": result["categories"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

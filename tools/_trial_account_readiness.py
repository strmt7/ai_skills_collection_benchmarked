"""Read native account capabilities without exporting tokens or starting a model turn."""

from __future__ import annotations

import hashlib
import io
import json
import os
import threading
import time
from typing import TYPE_CHECKING, Any

from _trial_provider import credential_lease, provider_options, validate_provider
from _trial_signin import SigninAdmissionError
from _trial_transcript import strict_json

if TYPE_CHECKING:
    from _trial_context import TrialContext

TIMEOUT = 60
OUTPUT_LIMIT = 2 * 1024**2
MEMORY_LIMIT = 1024**3
PROCESS_LIMIT = 12
WRITE_LIMIT = 32 * 1024**2


class _Capture(io.BytesIO):
    """Synchronize native output writes and bounded protocol snapshots."""

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()

    def write(self, value: Any, /) -> int:
        with self._lock:
            if self.tell() + memoryview(value).nbytes > OUTPUT_LIMIT:
                raise ValueError("Native account output exceeds its capture budget")
            return super().write(value)

    def snapshot(self) -> bytes:
        with self._lock:
            return self.getvalue()


def _reply(capture: _Capture, identifier: int, worker: threading.Thread, deadline: float) -> dict[str, Any]:
    while time.monotonic() < deadline:
        stopped = not worker.is_alive()
        raw = capture.snapshot()
        if len(raw) > OUTPUT_LIMIT:
            raise ValueError("Native account output exceeds its protocol budget")
        for line in raw.splitlines(keepends=True):
            if not line.endswith(b"\n"):
                continue
            row = strict_json(line.decode("utf-8"))
            if isinstance(row, dict) and type(row.get("id")) is int and row["id"] == identifier:
                if ("result" in row) == ("error" in row):
                    raise ValueError("Native account response has an ambiguous envelope")
                return row
        if stopped:
            raise RuntimeError("Native account process stopped before its reply")
        time.sleep(0.02)
    raise TimeoutError("Native account response deadline exceeded")


def _result(reply: Any) -> dict[str, Any]:
    if not isinstance(reply, dict) or "error" in reply or not isinstance(reply.get("result"), dict):
        return {}
    return reply["result"]


def _account_id(reply: Any) -> str | None:
    result = _result(reply)
    account, routing = result.get("account"), result.get("workspaceRouting")
    if (
        result.get("requiresOpenaiAuth") is not True
        or not isinstance(account, dict)
        or account.get("type") != "chatgpt"
        or not isinstance(routing, dict)
    ):
        return None
    value = routing.get("chatgptAccountId")
    return value if isinstance(value, str) and 0 < len(value) <= 256 and all(ord(c) >= 32 for c in value) else None


def assess(account: Any, quota: Any, models: Any, confirmed: Any, model: str, effort: str) -> dict[str, Any]:
    """Require explicit included-usage permission, stable identity and model metadata.

    This observes current capabilities. It proves neither refresh success nor
    future quota, backend weights, inference success or the complete trial boundary.
    """
    reasons = []
    before, after = _account_id(account), _account_id(confirmed)
    if before is None or after is None:
        reasons.append("chatgpt_account_unconfirmed")
    usage = _result(quota)
    allowed = usage.get("ordinaryUsageAllowed")
    if allowed is not True:
        reasons.append("ordinary_usage_blocked" if allowed is False else "ordinary_usage_unconfirmed")
    identity = usage.get("accountId")
    if before is None or before != after or before != identity:
        reasons.append("account_binding_unconfirmed")
    inventory = _result(models)
    data = inventory.get("data")
    if not isinstance(data, list) or any(not isinstance(row, dict) for row in data):
        data = []
        reasons.append("model_inventory_invalid")
    if "nextCursor" not in inventory or inventory["nextCursor"] is not None:
        reasons.append("model_inventory_incomplete")
    matches = [row for row in data if row.get("id") == model and row.get("model") == model]
    if len(matches) != 1:
        reasons.append("requested_model_unconfirmed")
    else:
        efforts = matches[0].get("supportedReasoningEfforts")
        if not isinstance(efforts, list) or not any(
            isinstance(row, dict) and row.get("reasoningEffort") == effort for row in efforts
        ):
            reasons.append("reasoning_effort_unconfirmed")
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "model": model,
        "reasoning_effort": effort,
        "account_binding_sha256": hashlib.sha256(before.encode()).hexdigest() if before is not None else None,
        "ordinary_usage_allowed": allowed if type(allowed) is bool else None,
        "refresh_success_established": False,
        "subject_configuration_match_established": False,
        "whole_model_trial_boundary_qualified": False,
    }


def assess_configuration(before: Any, after: Any, model: str, effort: str) -> dict[str, Any]:
    """Reject invalid, changed or explicitly substituted catalog metadata.

    Compare complete config/read results in memory, including origin versions.
    Equal snapshots do not freeze a profile or prove equivalence to isolated exec.
    Native model metadata can still come from a bundled or cached catalog.
    """
    reasons = []
    results = [_result(value) for value in (before, after)]
    valid = all(
        isinstance(value.get("config"), dict)
        and isinstance(value.get("origins"), dict)
        and value.get("layers") is None
        and value["config"].get("model") == model
        and value["config"].get("model_provider") == "openai"
        and value["config"].get("model_reasoning_effort") == effort
        and "model_catalog_json" in value["config"]
        for value in results
    )
    match = valid and json.dumps({**results[0], "layers": None}, sort_keys=True) == json.dumps(
        {**results[1], "layers": None}, sort_keys=True
    )
    override = any(
        isinstance(value.get("config"), dict) and value["config"].get("model_catalog_json") is not None
        for value in results
    )
    if not valid:
        reasons.append("configuration_unconfirmed")
    elif not match:
        reasons.append("configuration_changed")
    if override:
        reasons.append("selected_profile_catalog_override")
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "configuration_metadata_confirmed": valid,
        "configuration_snapshots_match": match,
        "explicit_model_catalog_override": override,
        "raw_configuration_retained": False,
    }


def _completed(process: Any, captured_bytes: int) -> bool:
    if not isinstance(process, dict):
        return False
    expected = {
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "explicit_environment": True,
        "exit_code": 0,
        "job_active_processes_after_cleanup": 0,
        "output_limit_bytes": OUTPUT_LIMIT,
        "job_memory_limit_bytes": MEMORY_LIMIT,
        "active_process_limit": PROCESS_LIMIT,
        "write_io_limit_bytes": WRITE_LIMIT,
        "output_bytes": captured_bytes,
    }
    return (
        type(captured_bytes) is int
        and 0 <= captured_bytes <= OUTPUT_LIMIT
        and all(type(process.get(key)) is type(value) and process[key] == value for key, value in expected.items())
        and type(process.get("wall_time_limit_seconds")) in (int, float)
        and process["wall_time_limit_seconds"] == TIMEOUT
        and process.get("termination_reason") is None
        and type(process.get("job_write_io_bytes")) is int
        and 0 <= process["job_write_io_bytes"] <= WRITE_LIMIT
        and process.get("write_io_observation_error") is None
        and process.get("write_io_enforcement") == "polled_job_transfer_accounting"
        and process.get("hard_storage_quota") is False
    )


def probe(context: TrialContext, provider: Any, model: str, effort: str) -> dict[str, Any]:
    """Use only initialize, config/read, account/read, account/rateLimits/read and model/list.

    Raw stdout, stderr and account details stay in memory and are discarded.
    No thread, turn, command execution, interactive login, token export or Reserve operation is sent.
    A failed or interrupted probe is not automatically retried.
    """
    from _trial_context import options
    from _windows_trial_process import run_owned

    declared = validate_provider(provider)
    if declared.get("authentication") != "codex_signin":
        raise ValueError("Native readiness requires explicit official CLI sign-in")
    report: dict[str, Any] = {
        "schema_version": 1,
        "scope": "account_quota_model_metadata",
        "status": "harness_error",
        "stage": "signin_admission",
        "eligible": False,
        "model_inferences": 0,
        "whole_model_trial_boundary_qualified": False,
        "raw_account_metadata_retained": False,
    }
    observed: dict[str, Any] = {}
    methods: list[str] = []
    try:
        with credential_lease(context, declared, {}) as selected, _Capture() as stdout, _Capture() as stderr:
            report["stage"] = "account_metadata"
            invocation = [
                str(selected.cli),
                *options(selected, model, effort),
                *provider_options(declared),
                "-c",
                "mcp_servers={}",
                "app-server",
                "--stdio",
            ]
            report["command_sha256"] = hashlib.sha256(json.dumps(invocation).encode()).hexdigest()
            read_fd, write_fd = os.pipe()

            def execute() -> None:
                try:
                    with os.fdopen(read_fd, "rb", buffering=0) as stdin:
                        observed["process"] = run_owned(
                            invocation,
                            cwd=selected.workspace,
                            environment=selected.controller_environment,
                            stdin=stdin,
                            stdout=stdout,
                            stderr=stderr,
                            timeout=TIMEOUT,
                            output_limit=OUTPUT_LIMIT,
                            memory_limit=MEMORY_LIMIT,
                            process_limit=PROCESS_LIMIT,
                            write_io_limit=WRITE_LIMIT,
                        )
                except (OSError, RuntimeError, ValueError) as error:
                    observed["process_error"] = type(error).__name__

            worker = threading.Thread(target=execute, name="native-account-readiness")
            try:
                worker.start()
            except BaseException:
                os.close(read_fd)
                os.close(write_fd)
                raise
            deadline = time.monotonic() + TIMEOUT - 5
            try:
                with os.fdopen(write_fd, "wb", buffering=0) as writer:
                    identifier = 0

                    def request(method: str, params: dict[str, Any]) -> dict[str, Any]:
                        nonlocal identifier
                        if method not in {
                            "initialize",
                            "config/read",
                            "account/read",
                            "account/rateLimits/read",
                            "model/list",
                        }:
                            raise ValueError("Native readiness method is outside its whitelist")
                        identifier += 1
                        methods.append(method)
                        writer.write(
                            (json.dumps({"id": identifier, "method": method, "params": params}) + "\n").encode()
                        )
                        return _reply(stdout, identifier, worker, deadline)

                    initialized = request("initialize", {"clientInfo": {"name": "ai-skills-readiness", "version": "1"}})
                    if "error" in initialized:
                        raise ValueError("Native readiness initialization failed")
                    writer.write(b'{"method":"initialized","params":{}}\n')
                    config_params = {"includeLayers": False, "cwd": str(selected.workspace)}
                    configuration = request("config/read", config_params)
                    account = request("account/read", {"refreshToken": False})
                    quota = request(
                        "account/rateLimits/read", {"supportsLunaReserve": False, "excludeResetCreditDetails": True}
                    )
                    data, cursors, cursor = [], set(), None
                    models: dict[str, Any] = {}
                    for _ in range(32):
                        page = request("model/list", {"cursor": cursor, "limit": 100, "includeHidden": True})
                        value = _result(page)
                        if not isinstance(value.get("data"), list):
                            models = page
                            break
                        if len(value["data"]) > 100:
                            raise ValueError("Native model page exceeds its requested size")
                        if "nextCursor" not in value:
                            raise ValueError("Native model page omits its continuation state")
                        data.extend(value["data"])
                        cursor = value.get("nextCursor")
                        if cursor is None:
                            models = {"result": {"data": data, "nextCursor": None}}
                            break
                        if not isinstance(cursor, str) or not cursor or cursor in cursors or len(cursor) > 4096:
                            raise ValueError("Native model pagination is invalid")
                        cursors.add(cursor)
                    else:
                        raise ValueError("Native model pagination exceeds its page budget")
                    confirmed = request("account/read", {"refreshToken": False})
                    config_confirmed = request("config/read", config_params)
                    assessment = assess(account, quota, models, confirmed, model, effort)
                    config_assessment = assess_configuration(configuration, config_confirmed, model, effort)
                    reasons = assessment["reasons"] + config_assessment.pop("reasons")
                    observed["assessment"] = {
                        **assessment,
                        **config_assessment,
                        "eligible": not reasons,
                        "reasons": reasons,
                    }
            finally:
                worker.join(TIMEOUT + 10)
                if worker.is_alive():
                    raise RuntimeError("Native readiness worker did not stop")
                report["process"] = observed.get("process")
            size = len(stdout.snapshot()) + len(stderr.snapshot())
            report["stage"] = "process_completion"
            if observed.get("process_error") or not _completed(report["process"], size):
                raise RuntimeError("Native readiness process did not complete its owned contract")
            report.update(observed["assessment"])
            report["status"] = "eligible" if report["eligible"] else "ineligible"
            report["stage"] = "complete"
    except (OSError, RuntimeError, ValueError, TimeoutError) as error:
        report.update(status="harness_error", eligible=False, error_type=type(error).__name__)
        if isinstance(error, SigninAdmissionError):
            report["native_signin_admission"] = error.admission
    report["methods"] = methods
    return report

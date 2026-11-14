from __future__ import annotations

import copy
import json
import tomllib
from typing import Any

import _trial_account_readiness as readiness
import pytest
from _trial_context import TrialContext


def account(identity="account-a"):
    return {
        "result": {
            "requiresOpenaiAuth": True,
            "account": {"type": "chatgpt", "email": "private-account-canary@example.invalid"},
            "workspaceRouting": {"chatgptAccountId": identity},
        }
    }


def model_row(name="gpt-6.1-sol"):
    return {"id": name, "model": name, "supportedReasoningEfforts": [{"reasoningEffort": "high"}]}


def configuration():
    return {
        "result": {
            "config": {
                "model": "gpt-6.1-sol",
                "model_provider": "openai",
                "model_reasoning_effort": "high",
                "model_catalog_json": None,
                "developer_instructions": "private-instruction-canary",
            },
            "origins": {"model": {"name": {"type": "sessionFlags"}, "version": "sha256:fixture"}},
        }
    }


@pytest.fixture
def metadata():
    return [
        account(),
        {"result": {"ordinaryUsageAllowed": True, "accountId": "account-a"}},
        {"result": {"data": [model_row()], "nextCursor": None}},
        account(),
    ]


def test_current_metadata_requires_no_claim_of_refresh_or_full_trial_qualification(metadata):
    value = readiness.assess(metadata[0], metadata[1], metadata[2], metadata[3], "gpt-6.1-sol", "high")
    assert value["eligible"] and value["reasons"] == []
    assert value["refresh_success_established"] is False
    assert value["whole_model_trial_boundary_qualified"] is False
    assert "account-a" not in json.dumps(value) and "private-account-canary" not in json.dumps(value)


@pytest.mark.parametrize("allowed", [False, None, 1, "true", [], {}])
def test_missing_blocked_or_non_boolean_usage_is_never_permission(metadata, allowed):
    metadata[1]["result"]["ordinaryUsageAllowed"] = allowed
    assert (
        readiness.assess(metadata[0], metadata[1], metadata[2], metadata[3], "gpt-6.1-sol", "high")["eligible"] is False
    )


@pytest.mark.parametrize(
    "fault",
    [
        "account-error",
        "account-none",
        "account-key",
        "account-id-missing",
        "quota-error",
        "quota-id-missing",
        "quota-id-other",
        "confirmation-other",
        "models-error",
        "models-malformed",
        "model-missing",
        "model-duplicate",
        "model-selector-other",
        "effort-missing",
        "partial-page",
    ],
)
def test_partial_or_mismatched_native_evidence_is_not_admission(metadata, fault):
    if fault == "account-error":
        metadata[0] = {"error": {"message": "private-error-canary"}}
    elif fault == "account-none":
        metadata[0]["result"]["account"] = None
    elif fault == "account-key":
        metadata[0]["result"]["account"]["type"] = "apiKey"
    elif fault == "account-id-missing":
        del metadata[0]["result"]["workspaceRouting"]
    elif fault == "quota-error":
        metadata[1] = {"error": {"message": "private-error-canary"}}
    elif fault == "quota-id-missing":
        del metadata[1]["result"]["accountId"]
    elif fault == "quota-id-other":
        metadata[1]["result"]["accountId"] = "account-b"
    elif fault == "confirmation-other":
        metadata[3] = account("account-b")
    elif fault == "models-error":
        metadata[2] = {"error": {"message": "private-error-canary"}}
    elif fault == "models-malformed":
        metadata[2]["result"]["data"] = [None]
    elif fault == "model-missing":
        metadata[2]["result"]["data"] = []
    elif fault == "model-duplicate":
        metadata[2]["result"]["data"] *= 2
    elif fault == "model-selector-other":
        metadata[2]["result"]["data"][0]["model"] = "other-model"
    elif fault == "effort-missing":
        metadata[2]["result"]["data"][0]["supportedReasoningEfforts"] = []
    elif fault == "partial-page":
        metadata[2]["result"]["nextCursor"] = "unread-page"
    value = readiness.assess(metadata[0], metadata[1], metadata[2], metadata[3], "gpt-6.1-sol", "high")
    assert value["eligible"] is False and value["reasons"]
    assert "private-error-canary" not in json.dumps(value)


def process(limits, output):
    return {
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "explicit_environment": True,
        "exit_code": 0,
        "termination_reason": None,
        "job_active_processes_after_cleanup": 0,
        "output_limit_bytes": limits["output_limit"],
        "wall_time_limit_seconds": float(limits["timeout"]),
        "job_memory_limit_bytes": limits["memory_limit"],
        "active_process_limit": limits["process_limit"],
        "write_io_limit_bytes": limits["write_io_limit"],
        "job_write_io_bytes": 64,
        "write_io_observation_error": None,
        "write_io_enforcement": "polled_job_transfer_accounting",
        "hard_storage_quota": False,
        "output_bytes": output,
    }


@pytest.fixture
def native(tmp_path, monkeypatch, metadata):
    home, workspace, runtime, auth = (tmp_path / name for name in ("controller", "workspace", "runtime", "auth"))
    for path in (home, workspace, runtime, auth):
        path.mkdir()
    context = TrialContext(
        home,
        workspace,
        runtime / "codex.exe",
        runtime / "python.exe",
        (runtime,),
        {"CODEX_HOME": str(home / "profile"), "HOME": str(home / "user")},
        {"HOME": str(workspace / "profile")},
    )
    declaration = {"authentication": "codex_signin", "codex_home": str(auth), "credential_store": "file"}
    state: dict[str, Any] = {"calls": [], "requests": [], "fault": None, "metadata": metadata, "page_count": 0}

    def run_owned(argv, **limits):
        state["calls"].append((argv, limits))
        if argv[-2:] == ["login", "status"]:
            limits["stderr"].write(b"Logged in using ChatGPT\n")
            return process(limits, 24)
        limits["stderr"].write(b"private-native-stderr-canary")
        for raw in limits["stdin"]:
            request = json.loads(raw)
            state["requests"].append(request)
            method = request["method"]
            if method == "initialized":
                continue
            body: dict[str, Any]
            if method == "initialize":
                body = {"result": {}}
            elif method == "config/read":
                body = configuration()
                if state["fault"] == "config-catalog":
                    body["result"]["config"]["model_catalog_json"] = "private-catalog-path-canary"
                elif state["fault"] == "config-error":
                    body = {"error": {"message": "private-config-error-canary"}}
                elif state["fault"] == "config-drift" and state["page_count"]:
                    body["result"]["origins"]["model"]["version"] = "sha256:changed"
            elif method == "account/read":
                index = 3 if any(row["method"] == "model/list" for row in state["requests"]) else 0
                body = copy.deepcopy(state["metadata"][index])
            elif method == "account/rateLimits/read":
                body = copy.deepcopy(state["metadata"][1])
            elif method == "model/list":
                body = copy.deepcopy(state["metadata"][2])
                if state["fault"] == "pagination":
                    if state["page_count"] == 0:
                        body = {"result": {"data": [model_row("other")], "nextCursor": "page-2"}}
                    state["page_count"] += 1
                elif state["fault"] == "cursor-cycle":
                    body["result"]["nextCursor"] = "same-page"
                elif state["fault"] == "oversized-page":
                    body["result"]["data"] *= 101
                elif state["fault"] == "config-drift":
                    state["page_count"] += 1
            else:
                raise ValueError("Unexpected method reached the fake native server")
            if state["fault"] == "early-exit" and method == "account/read":
                break
            body["id"] = request["id"]
            limits["stdout"].write((json.dumps(body) + "\n").encode())
        size = len(limits["stdout"].snapshot()) + len(limits["stderr"].snapshot())
        result = process(limits, size)
        if state["fault"] == "cleanup":
            result["job_active_processes_after_cleanup"] = 1
        elif state["fault"] == "exit":
            result["exit_code"] = 1
        elif state["fault"] == "accounting":
            result["write_io_observation_error"] = {"winerror": 5}
        elif state["fault"] == "boolean-counter":
            result["output_bytes"] = True
        return result

    monkeypatch.setattr("_windows_trial_process.run_owned", run_owned)
    return context, declaration, state


def test_native_preflight_has_no_subject_turn_token_export_or_raw_metadata_artifact(native):
    context, declaration, state = native
    original = context.controller_environment.copy()
    report = readiness.probe(context, declaration, "gpt-6.1-sol", "high")
    assert report["status"] == "eligible" and report["eligible"]
    assert report["model_inferences"] == 0 and report["raw_account_metadata_retained"] is False
    assert "private-" not in json.dumps(report) and "account-a" not in json.dumps(report)
    assert context.controller_environment == original
    assert [row["method"] for row in state["requests"]] == [
        "initialize",
        "initialized",
        "config/read",
        "account/read",
        "account/rateLimits/read",
        "model/list",
        "account/read",
        "config/read",
    ]
    assert state["requests"][4]["params"] == {"supportsLunaReserve": False, "excludeResetCreditDetails": True}
    assert all(
        row["params"] == {"includeLayers": False, "cwd": str(context.workspace)}
        for row in state["requests"]
        if row["method"] == "config/read"
    )
    assert all(row["params"] == {"refreshToken": False} for row in state["requests"] if row["method"] == "account/read")
    invocation, limits = state["calls"][-1]
    assert "mcp_servers={}" in invocation and "app-server" in invocation
    assert limits["stdout"].closed and limits["stderr"].closed
    settings = tomllib.loads(next(value for value in invocation if value.startswith("permissions.trial.filesystem=")))
    assert settings["permissions"]["trial"]["filesystem"][declaration["codex_home"]] == "deny"


@pytest.mark.parametrize(
    "fault", ["early-exit", "cleanup", "exit", "accounting", "boolean-counter", "cursor-cycle", "oversized-page"]
)
def test_incomplete_or_invalid_native_execution_is_never_readiness(native, fault):
    context, declaration, state = native
    state["fault"] = fault
    report = readiness.probe(context, declaration, "gpt-6.1-sol", "high")
    assert report["status"] == "harness_error" and report["eligible"] is False
    assert "private-" not in json.dumps(report)
    assert all(limits["stdout"].closed and limits["stderr"].closed for _, limits in state["calls"])


def test_model_inventory_pagination_is_consumed_before_admission(native):
    context, declaration, state = native
    state["fault"] = "pagination"
    report = readiness.probe(context, declaration, "gpt-6.1-sol", "high")
    assert report["status"] == "eligible" and state["page_count"] == 2
    assert [row["params"]["cursor"] for row in state["requests"] if row["method"] == "model/list"] == [None, "page-2"]


@pytest.mark.parametrize(
    ("fault", "reason"),
    [
        ("config-error", "configuration_unconfirmed"),
        ("config-drift", "configuration_changed"),
        ("config-catalog", "selected_profile_catalog_override"),
    ],
)
def test_native_configuration_failures_withhold_metadata_eligibility_and_private_values(native, fault, reason):
    context, declaration, state = native
    state["fault"] = fault
    report = readiness.probe(context, declaration, "gpt-6.1-sol", "high")
    assert report["status"] == "ineligible" and report["eligible"] is False
    assert reason in report["reasons"]
    assert report["subject_configuration_match_established"] is False
    assert report["whole_model_trial_boundary_qualified"] is False
    assert report["raw_configuration_retained"] is False
    assert "private-" not in json.dumps(report)


@pytest.mark.parametrize(
    "fault", ["none", "error", "missing-config", "origins", "layers", "model", "provider", "effort", "catalog-omitted"]
)
def test_configuration_protocol_failures_are_not_metadata_confirmation(fault):
    before, after = configuration(), configuration()
    if fault == "none":
        after = None
    elif fault == "error":
        after = {"error": {"message": "private-config-error-canary"}}
    elif fault == "missing-config":
        del after["result"]["config"]
    elif fault == "origins":
        after["result"]["origins"] = None
    elif fault == "layers":
        after["result"]["layers"] = []
    elif fault == "catalog-omitted":
        del after["result"]["config"]["model_catalog_json"]
    else:
        key = {"model": "model", "provider": "model_provider", "effort": "model_reasoning_effort"}[fault]
        after["result"]["config"][key] = "other"
    result = readiness.assess_configuration(before, after, "gpt-6.1-sol", "high")
    assert result["eligible"] is False
    assert "configuration_unconfirmed" in result["reasons"]
    assert result["configuration_metadata_confirmed"] is False
    assert "private-" not in json.dumps(result)


@pytest.mark.parametrize("catalog", ["private-catalog-path-canary", "", False, 0, {}, []])
def test_any_explicit_catalog_substitution_withholds_readiness(catalog):
    before = configuration()
    before["result"]["config"]["model_catalog_json"] = catalog
    result = readiness.assess_configuration(before, copy.deepcopy(before), "gpt-6.1-sol", "high")
    assert result["eligible"] is False and result["explicit_model_catalog_override"] is True
    assert result["reasons"] == ["selected_profile_catalog_override"]
    assert "private-" not in json.dumps(result)


@pytest.mark.parametrize("field", ["origin", "instructions", "boolean-type"])
def test_configuration_comparison_includes_origin_and_full_typed_values(field):
    before, after = configuration(), configuration()
    if field == "origin":
        after["result"]["origins"]["model"]["version"] = "sha256:changed"
    elif field == "instructions":
        after["result"]["config"]["developer_instructions"] = "private-new-instruction-canary"
    else:
        before["result"]["config"]["features"] = {"owned": False}
        after["result"]["config"]["features"] = {"owned": 0}
    result = readiness.assess_configuration(before, after, "gpt-6.1-sol", "high")
    assert result["eligible"] is False and result["reasons"] == ["configuration_changed"]
    assert result["configuration_snapshots_match"] is False


def test_clean_stable_config_does_not_export_profile_or_prove_remote_catalog_entitlement():
    before = configuration()
    result = readiness.assess_configuration(before, copy.deepcopy(before), "gpt-6.1-sol", "high")
    assert result == {
        "eligible": True,
        "reasons": [],
        "configuration_metadata_confirmed": True,
        "configuration_snapshots_match": True,
        "explicit_model_catalog_override": False,
        "raw_configuration_retained": False,
    }


@pytest.mark.parametrize("explicit_null", [False, True])
def test_native_omitted_optional_layers_and_explicit_null_have_the_same_snapshot_meaning(explicit_null):
    before, after = configuration(), configuration()
    if explicit_null:
        after["result"]["layers"] = None
    result = readiness.assess_configuration(before, after, "gpt-6.1-sol", "high")
    assert result["eligible"] is True and result["configuration_snapshots_match"] is True


def test_readiness_rejects_non_native_provider_before_credential_or_process_use(native):
    context, _, state = native
    with pytest.raises(ValueError, match="official CLI"):
        readiness.probe(context, {"base_url": "http://127.0.0.1:1234", "authentication": "none"}, "gpt-6.1-sol", "high")
    assert state["calls"] == []


def test_raw_metadata_capture_rejects_oversized_output_before_retaining_it():
    with readiness._Capture() as capture:
        with pytest.raises(ValueError, match="capture budget"):
            capture.write(b"x" * (readiness.OUTPUT_LIMIT + 1))
        assert capture.snapshot() == b""


@pytest.mark.parametrize("missing", ["native-auth", "pagination-state"])
def test_required_native_protocol_evidence_is_not_inferred_from_omission(metadata, missing):
    if missing == "native-auth":
        del metadata[0]["result"]["requiresOpenaiAuth"]
    else:
        del metadata[2]["result"]["nextCursor"]
    assert (
        readiness.assess(metadata[0], metadata[1], metadata[2], metadata[3], "gpt-6.1-sol", "high")["eligible"] is False
    )

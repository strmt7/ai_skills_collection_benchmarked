"""Native sign-in admission must not import personal context or expose status text."""

from __future__ import annotations

import json
import tomllib
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
from typing import Any

import _trial_rpc as rpc
import _trial_signin as signin
import pytest
from _trial_context import TrialContext, command
from _trial_execution_evidence import context_record
from _trial_provider import bind_credentials, credential_lease, validate_provider
from run_agent_trial import exception_metadata


@pytest.mark.parametrize(
    "home", ["//server/share/profile", r"\\server\share\profile", "//?/C:/profile", r"\\?\C:\profile"]
)
def test_native_storage_rejects_network_and_device_namespaces_before_any_io(home):
    with pytest.raises(ValueError, match="local"):
        validate_provider({"authentication": "codex_signin", "codex_home": home, "credential_store": "file"})


@pytest.fixture
def native(tmp_path, monkeypatch):
    home, workspace, runtime, auth = (tmp_path / name for name in ("controller", "subject", "runtime", "signin"))
    for path in (home, workspace, runtime, auth):
        path.mkdir()
    context = TrialContext(
        home,
        workspace,
        runtime / "codex.exe",
        runtime / "python.exe",
        (runtime,),
        {"CODEX_HOME": str(home / "profile"), "HOME": str(home / "private-user")},
        {"HOME": str(workspace / ".trial-profile/profile")},
    )
    declaration = {"authentication": "codex_signin", "codex_home": str(auth), "credential_store": "file"}
    state: dict[str, Any] = {
        "calls": [],
        "text": b"Logged in using ChatGPT\n",
        "process": {
            "windows_job": True,
            "assigned_before_resume": True,
            "kill_on_close": True,
            "explicit_environment": True,
            "exit_code": 0,
            "termination_reason": None,
            "job_active_processes_after_cleanup": 0,
            "output_limit_bytes": 65536,
            "wall_time_limit_seconds": 20.0,
            "job_memory_limit_bytes": 1024**3,
            "active_process_limit": 8,
            "write_io_limit_bytes": 1024**2,
            "job_write_io_bytes": 24,
            "write_io_observation_error": None,
            "write_io_enforcement": "polled_job_transfer_accounting",
            "hard_storage_quota": False,
        },
    }

    def status(arguments, **options):
        state["calls"].append((arguments, options))
        options["stderr"].write(state["text"])
        return state["process"].copy()

    monkeypatch.setattr("_windows_trial_process.run_owned", status)
    return context, declaration, state


@pytest.mark.parametrize("store", ["file", "keyring", "auto"])
def test_existing_native_storage_is_explicit_and_does_not_require_a_key(native, store, native_catalog_pin):
    context, declaration, state = native
    declaration["credential_store"] = store
    original = context.controller_environment.copy()
    selected = bind_credentials(context, declaration, {})
    args, options = state["calls"][0]
    assert args == [str(context.cli), "-c", 'cli_auth_credentials_store="' + store + '"', "login", "status"]
    assert options["environment"]["CODEX_HOME"] == declaration["codex_home"]
    assert options["environment"]["HOME"] == original["HOME"]
    assert options["timeout"] == 20 and options["output_limit"] == 65536
    assert options["write_io_limit"] == 1024**2
    assert options["stdout"].closed and options["stderr"].closed
    assert context.controller_environment == original
    assert selected.tool_environment == context.tool_environment
    assert selected.signin is not None
    assert selected.signin.home == Path(declaration["codex_home"])
    assert "Logged in" not in json.dumps(context_record(selected))
    settings = {}
    invocation = command(
        replace(selected, native_catalog=native_catalog_pin(selected.cli)),
        "gpt-6.1-sol",
        "high",
        provider=declaration,
    )
    for index, option in enumerate(invocation[:-1]):
        if option == "-c":
            key, value = invocation[index + 1].split("=", 1)
            settings[key] = tomllib.loads("value=" + value)["value"]
    assert settings["model_provider"] == "openai"
    assert settings["cli_auth_credentials_store"] == store
    assert not any(key.startswith("model_providers.") for key in settings)
    assert settings["permissions.trial.filesystem"][declaration["codex_home"]] == "deny"
    assert not any(key.endswith(("env_key", "base_url")) for key in settings)
    assert "--ignore-user-config" in invocation and "--ephemeral" in invocation


@pytest.mark.parametrize("name", ["AGENTS.md", "AGENTS.override.md"])
@pytest.mark.parametrize("kind", ["file", "directory"])
def test_global_instructions_are_rejected_before_status_without_reading_content(native, name, kind):
    context, declaration, state = native
    entry = Path(declaration["codex_home"]) / name
    if kind == "directory":
        entry.mkdir()
    else:
        entry.write_bytes(b"private-instructions-canary")
    with pytest.raises(ValueError, match="global instructions"):
        bind_credentials(context, declaration, {})
    assert not state["calls"]
    assert entry.exists()


def test_global_instructions_created_during_status_are_also_rejected(native, monkeypatch):
    context, declaration, state = native
    original = signin.require_instruction_free_home

    def check(home):
        if state["calls"]:
            (home / "AGENTS.md").write_bytes(b"late-private-canary")
        original(home)

    monkeypatch.setattr(signin, "require_instruction_free_home", check)
    with pytest.raises(ValueError, match="global instructions"):
        bind_credentials(context, declaration, {})
    assert len(state["calls"]) == 1


@pytest.mark.parametrize(
    "text",
    [
        b"Logged in using an API key - private-status-canary",
        b"API key configured - private-status-canary\nAuthentication is checked when you send a request.\n",
        b"Not logged in",
        b"",
        b"Logged in using ChatGPT\nprivate-status-canary",
    ],
)
def test_non_chatgpt_or_ambiguous_status_is_retained_without_raw_output(native, text):
    context, declaration, state = native
    state["text"] = text
    with pytest.raises(signin.SigninAdmissionError) as error:
        bind_credentials(context, declaration, {})
    metadata = exception_metadata(error.value)
    assert metadata["native_signin_admission"]["admitted"] is False
    expected = (
        "apikey" if text.startswith((b"Logged in using an API key - ", b"API key configured - ")) else "unclassified"
    )
    assert metadata["native_signin_admission"]["mode"] == expected
    assert "private-status-canary" not in str(error.value) + json.dumps(metadata)
    assert context.signin is None
    assert state["calls"][0][1]["stderr"].closed


@pytest.mark.parametrize(
    "field,value",
    [
        ("exit_code", 1),
        ("exit_code", False),
        ("job_active_processes_after_cleanup", 1),
        ("job_active_processes_after_cleanup", False),
        ("kill_on_close", False),
        ("explicit_environment", False),
        ("termination_reason", "timeout"),
        ("wall_time_limit_seconds", True),
        ("active_process_limit", 9),
        ("job_write_io_bytes", False),
        ("job_write_io_bytes", 1024**2 + 1),
        ("write_io_observation_error", "owned-error"),
    ],
)
def test_status_must_prove_completed_owned_execution(native, field, value):
    context, declaration, state = native
    state["process"][field] = value
    with pytest.raises(signin.SigninAdmissionError) as error:
        bind_credentials(context, declaration, {})
    assert error.value.admission["mode"] == "chatgpt"
    assert error.value.admission["admitted"] is False


@pytest.mark.parametrize("interrupt", [False, True])
def test_lease_uses_no_key_source_and_cannot_be_reused_after_exit(native, interrupt):
    context, declaration, _ = native

    class Unselected(dict):
        def get(self, *arguments):
            pytest.fail("Native sign-in consulted an API credential mapping")

    with (
        pytest.raises(InterruptedError) if interrupt else nullcontext(),
        credential_lease(context, declaration, Unselected()) as selected,
    ):
        assert selected.signin is not None
        if interrupt:
            raise InterruptedError
    assert selected is not None
    assert selected.controller_environment["CODEX_HOME"] == context.controller_environment["CODEX_HOME"]
    with pytest.raises(ValueError, match="active admitted"):
        command(selected, "gpt-6.1-sol", "high", provider=declaration)


@pytest.mark.parametrize("kind", ["controller", "subject", "runtime", "parent", "missing"])
def test_authentication_store_is_not_a_subject_or_runtime_grant(native, kind):
    context, declaration, state = native
    paths = {
        "controller": context.home,
        "subject": context.workspace,
        "runtime": context.readable_roots[0],
        "parent": context.home.parent,
        "missing": context.home.parent / "missing",
    }
    declaration["codex_home"] = str(paths[kind])
    with pytest.raises(ValueError, match="disjoint"):
        bind_credentials(context, declaration, {})
    assert state["calls"] == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("codex_home", "relative"),
        ("codex_home", "/"),
        ("codex_home", "C:\\"),
        ("codex_home", "\\\\server\\share\\signin"),
        ("codex_home", "C:/parent/../signin"),
        ("codex_home", "C:/signin\n"),
        ("credential_store", "ephemeral"),
        ("credential_store", None),
    ],
)
def test_native_declarations_reject_ambiguous_or_unavailable_authentication_modes(native, field, value):
    _, declaration, state = native
    declaration[field] = value
    with pytest.raises(ValueError):
        validate_provider(declaration)
    assert state["calls"] == []


@pytest.mark.parametrize(
    "extra", [{"credential_env": "OTHER"}, {"base_url": "https://example.test"}, {"api_key": "private-mode-canary"}]
)
def test_native_authentication_cannot_be_mixed_with_another_provider_route(native, extra):
    _, declaration, _ = native
    with pytest.raises(ValueError):
        validate_provider({**declaration, **extra})


def test_native_binding_cannot_be_reused_for_a_different_store_or_rpc_control(native):
    context, declaration, state = native
    selected = bind_credentials(context, declaration, {})
    with pytest.raises(ValueError):
        command(selected, "gpt-6.1-sol", "high")
    with pytest.raises(ValueError):
        command(selected, "gpt-6.1-sol", "high", provider={**declaration, "credential_store": "auto"})
    with pytest.raises(ValueError, match="credential-free"):
        rpc.command_control(selected, ["fixture"], context.home.parent / "forbidden-observations")
    with pytest.raises(ValueError, match="disjoint"):
        bind_credentials(selected, declaration, {})
    assert len(state["calls"]) == 1

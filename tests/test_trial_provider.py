"""Provider declarations and credentials must remain separate from subject tools."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest
from _trial_context import TrialContext, command
from _trial_execution_evidence import context_record
from _trial_provider import bind_credentials, validate_provider


@pytest.fixture
def context(tmp_path: Path) -> TrialContext:
    return TrialContext(
        tmp_path / "controller",
        tmp_path / "workspace",
        tmp_path / "runtime/codex.exe",
        tmp_path / "runtime/python.exe",
        (tmp_path / "runtime",),
        {"PATH": "owned-runtime", "CODEX_HOME": "private-controller"},
        {"PATH": "owned-runtime", "HOME": "subject-profile"},
    )


def declaration(url: str = "https://model.example.test/v1") -> dict[str, str]:
    return {"base_url": url, "credential_env": "TRIAL_TOKEN"}


@pytest.mark.parametrize("url", ["https://model.example.test/v1", "http://127.0.0.1:8041/v1", "http://[::1]:8041/v1"])
def test_explicit_remote_tls_and_numeric_loopback_providers_are_valid(url):
    assert validate_provider(declaration(url)) == declaration(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://model.example.test/v1",
        "http://localhost/v1",
        "http://127.0.0.2.example.test/v1",
        "file:///private/config",
        "https://user:fixture-value@model.example.test/v1",
        "https://model.example.test/v1?token=fixture-value",
        "https://model.example.test/v1#fragment",
        "https://model.example.test:0/v1",
        "https://model.example.test:70000/v1",
        "https://model.example.test\\v1",
        "https://model.example.test/\nv1",
        "https:///v1",
    ],
)
def test_ambiguous_or_unprotected_provider_routes_are_rejected(url):
    with pytest.raises(ValueError):
        validate_provider(declaration(url))


@pytest.mark.parametrize(
    "value", [None, {}, {**declaration(), "api_key": "fixture-value"}, {**declaration(), "credential_env": "bad-name"}]
)
def test_provider_declarations_cannot_embed_credentials_or_arbitrary_options(value):
    with pytest.raises(ValueError):
        validate_provider(value)


def test_selected_credential_is_copied_only_to_the_controller(context):
    original = context.controller_environment.copy()
    selected = bind_credentials(context, declaration(), {"TRIAL_TOKEN": "controller-value", "OTHER": "parent-only"})
    assert selected.controller_environment == {**original, "TRIAL_TOKEN": "controller-value"}
    assert context.controller_environment == original
    assert selected.tool_environment == context.tool_environment
    assert "controller-value" not in json.dumps(context_record(selected))
    assert "parent-only" not in json.dumps(selected.controller_environment)
    invocation = command(selected, "fixture-model", "high", provider=declaration())
    assert "controller-value" not in json.dumps(invocation)
    settings = {}
    for index, option in enumerate(invocation[:-1]):
        if option == "-c":
            name, value = invocation[index + 1].split("=", 1)
            settings[name] = tomllib.loads("value=" + value)["value"]
    assert settings["model_providers.trial_provider.env_key"] == "TRIAL_TOKEN"
    assert settings["model_providers.trial_provider.base_url"] == declaration()["base_url"]
    assert settings["model_providers.trial_provider.requires_openai_auth"] is False
    assert settings["model_providers.trial_provider.request_max_retries"] == 0
    assert settings["model_providers.trial_provider.supports_websockets"] is False
    assert "TRIAL_TOKEN" not in settings["shell_environment_policy.set"]
    assert settings["permissions.trial.network.enabled"] is False


@pytest.mark.parametrize("key", ["PATH", "path", "HOME", "CODEX_HOME"])
def test_credentials_cannot_replace_runtime_or_profile_settings(context, key):
    provider = {**declaration(), "credential_env": key}
    with pytest.raises(ValueError, match="isolated runtime"):
        bind_credentials(context, provider, {key: "controller-value"})


@pytest.mark.parametrize("secret", [None, "", " ", "value\0suffix", "value\r\nsuffix", "x" * 8193])
def test_missing_or_invalid_credentials_fail_without_printing_the_value(context, secret):
    with pytest.raises(ValueError) as error:
        bind_credentials(context, declaration(), {"TRIAL_TOKEN": secret})
    assert str(error.value) == "The selected provider credential is missing or invalid"

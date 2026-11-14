"""Bind a declared Responses provider without exposing controller credentials."""

from __future__ import annotations

import ipaddress
import json
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import replace
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from _trial_signin import bind_signin, validate_signin

if TYPE_CHECKING:
    from _trial_context import TrialContext


def validate_provider(value: Any) -> dict[str, str]:
    """Require explicit credential binding or deliberately unauthenticated loopback."""
    if not isinstance(value, dict):
        raise ValueError("A trial provider requires an explicit authentication declaration")
    if value.get("authentication") == "codex_signin":
        return validate_signin(value)
    anonymous = set(value) == {"base_url", "authentication"} and value["authentication"] == "none"
    if set(value) != {"base_url", "credential_env"} and not anonymous:
        raise ValueError(
            "A trial provider requires exactly base_url and credential_env, "
            "or base_url and authentication=none for numeric loopback"
        )
    url = value["base_url"]
    if not isinstance(url, str) or not url or any(ord(char) <= 32 for char in url) or "\\" in url:
        raise ValueError("Invalid trial provider endpoint")
    parsed = urlsplit(url)
    if (
        not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Trial endpoints must not contain credentials, queries or fragments")
    if parsed.port is not None and not 1 <= parsed.port <= 65535:
        raise ValueError("Invalid trial provider port")
    try:
        local = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        local = False
    if parsed.scheme != "https" and not (parsed.scheme == "http" and local):
        raise ValueError("Trial providers require HTTPS or an explicit numeric loopback HTTP endpoint")
    if anonymous:
        if not local:
            raise ValueError("Unauthenticated trial providers require an explicit numeric loopback endpoint")
        return {"base_url": url, "authentication": "none"}
    key = value["credential_env"]
    if not isinstance(key, str) or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", key) is None:
        raise ValueError("Invalid provider credential environment-variable name")
    return {"base_url": url, "credential_env": key}


def provider_options(value: Any) -> list[str]:
    """Keep native sign-in on the built-in provider; freeze custom transports."""
    provider = validate_provider(value)
    if provider.get("authentication") == "codex_signin":
        settings: dict[str, str | int | bool] = {
            "model_provider": "openai",
            "cli_auth_credentials_store": provider["credential_store"],
        }
        return [argument for name, setting in settings.items() for argument in ("-c", name + "=" + json.dumps(setting))]
    settings = {
        "model_provider": "trial_provider",
        "model_providers.trial_provider.name": "Frozen trial provider",
        "model_providers.trial_provider.base_url": provider["base_url"],
        **(
            {"model_providers.trial_provider.env_key": provider["credential_env"]}
            if "credential_env" in provider
            else {}
        ),
        "model_providers.trial_provider.wire_api": "responses",
        "model_providers.trial_provider.requires_openai_auth": False,
        "model_providers.trial_provider.request_max_retries": 0,
        "model_providers.trial_provider.stream_max_retries": 0,
        "model_providers.trial_provider.supports_websockets": False,
    }
    return [argument for name, setting in settings.items() for argument in ("-c", name + "=" + json.dumps(setting))]


def bind_credentials(context: TrialContext, value: Any, credentials: Mapping[str, str]) -> TrialContext:
    """Copy only a selected credential; anonymous local providers read none."""
    provider = validate_provider(value)
    if provider.get("authentication") == "codex_signin":
        return bind_signin(context, provider)
    key = provider.get("credential_env")
    if key is None:
        return context
    reserved = {
        name.upper()
        for environment in (context.controller_environment, context.tool_environment)
        for name in environment
    }
    if key.upper() in reserved:
        raise ValueError("A provider credential must not replace the isolated runtime environment")
    secret = credentials.get(key)
    if not isinstance(secret, str) or not secret.strip() or len(secret) > 8192 or any(c in secret for c in "\0\r\n"):
        raise ValueError("The selected provider credential is missing or invalid")
    return replace(context, controller_environment={**context.controller_environment, key: secret})


@contextmanager
def credential_lease(context: TrialContext, value: Any, credentials: Mapping[str, str]) -> Iterator[TrialContext]:
    """Own one attempt's credential entry and release it on every exit path.

    The caller owns token acquisition and renewal. This copies no authentication
    cache and makes no promise to erase immutable strings from process memory.
    """
    provider = validate_provider(value)
    key = provider.get("credential_env")
    selected = bind_credentials(context, provider, credentials)
    try:
        yield selected
    finally:
        if key is not None:
            selected.controller_environment.pop(key, None)
        if provider.get("authentication") == "codex_signin":
            selected.controller_environment["CODEX_HOME"] = context.controller_environment["CODEX_HOME"]

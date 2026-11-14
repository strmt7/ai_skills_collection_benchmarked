"""Bind a declared Responses provider without exposing controller credentials."""

from __future__ import annotations

import ipaddress
import json
import re
from collections.abc import Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from _trial_context import TrialContext


def validate_provider(value: Any) -> dict[str, str]:
    """Require an explicit endpoint and environment-variable name, never a key value."""
    if not isinstance(value, dict) or set(value) != {"base_url", "credential_env"}:
        raise ValueError("A trial provider requires exactly base_url and credential_env")
    url, key = value["base_url"], value["credential_env"]
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
    if not isinstance(key, str) or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,127}", key) is None:
        raise ValueError("Invalid provider credential environment-variable name")
    return {"base_url": url, "credential_env": key}


def provider_options(value: Any) -> list[str]:
    """Use the declared endpoint, bounded retries and the qualified SSE transport."""
    provider = validate_provider(value)
    settings = {
        "model_provider": "trial_provider",
        "model_providers.trial_provider.name": "Frozen trial provider",
        "model_providers.trial_provider.base_url": provider["base_url"],
        "model_providers.trial_provider.env_key": provider["credential_env"],
        "model_providers.trial_provider.wire_api": "responses",
        "model_providers.trial_provider.requires_openai_auth": False,
        "model_providers.trial_provider.request_max_retries": 0,
        "model_providers.trial_provider.stream_max_retries": 0,
        "model_providers.trial_provider.supports_websockets": False,
    }
    return [argument for name, setting in settings.items() for argument in ("-c", name + "=" + json.dumps(setting))]


def bind_credentials(context: TrialContext, value: Any, credentials: Mapping[str, str]) -> TrialContext:
    """Copy only the selected credential into the CLI controller, never its tools."""
    key = validate_provider(value)["credential_env"]
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

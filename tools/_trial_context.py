"""Construct private Codex trial contexts without importing host agent state."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from _trial_catalog import NativeCatalog
from _trial_provider import provider_options, validate_provider
from _trial_signin import NativeSignin, home_identity
from _windows_appcontainer import checked_path

DISABLED_FEATURES = (
    "daemon_auto_start",
    "memories",
    "plugins",
    "apps",
    "multi_agent",
    "browser_use",
    "computer_use",
    "skill_search",
    "skill_mcp_dependency_install",
)
SYSTEM_VARIABLES = ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "SYSTEMDRIVE")


def temporary_home() -> Path:
    """Reserve a private controller location independent of checkout depth."""
    return checked_path(Path(tempfile.mkdtemp(prefix="skills-agent-controller-"))) / "private"


@dataclass(frozen=True)
class TrialContext:
    """Controller state stays outside the writable subject workspace."""

    home: Path
    workspace: Path
    cli: Path
    python: Path
    readable_roots: tuple[Path, ...]
    controller_environment: dict[str, str] = field(repr=False)
    tool_environment: dict[str, str]
    signin: NativeSignin | None = field(default=None, repr=False)
    native_catalog: NativeCatalog | None = field(default=None, repr=False)


def profile_directories(home: Path) -> dict[str, str]:
    """Create only the declared private profile directories."""
    environment = {}
    for key, relative in {
        "HOME": "profile",
        "USERPROFILE": "profile",
        "APPDATA": "profile/AppData/Roaming",
        "LOCALAPPDATA": "profile/AppData/Local",
        "TEMP": "temporary",
        "TMP": "temporary",
    }.items():
        path = home / relative
        path.mkdir(parents=True, exist_ok=True)
        environment[key] = str(path)
    return environment


def create_context(
    home: Path,
    workspace: Path,
    cli: Path,
    python: Path,
    readable_roots: tuple[Path, ...],
    *,
    parent: Mapping[str, str] | None = None,
) -> TrialContext:
    """Create a new empty controller home and a separate shell profile."""
    home, workspace, cli, python = (checked_path(path) for path in (home, workspace, cli, python))
    roots = tuple(dict.fromkeys(checked_path(path) for path in readable_roots))
    if home.exists() or not workspace.is_dir() or not cli.is_file() or not python.is_file() or not roots:
        raise ValueError("A fresh controller home, existing workspace, CLI and runtime roots are required")
    if home.is_relative_to(workspace) or workspace.is_relative_to(home):
        raise ValueError("Controller home and subject workspace must not overlap")
    for root in roots:
        if (
            not root.is_dir()
            or root == Path(root.anchor)
            or home.is_relative_to(root)
            or root.is_relative_to(home)
            or workspace.is_relative_to(root)
            or root.is_relative_to(workspace)
        ):
            raise ValueError("Runtime read grants must be disjoint from controller and subject state")
    if any(not any(executable.is_relative_to(root) for root in roots) for executable in (cli, python)):
        raise ValueError("Explicit read grants must cover the CLI and Python runtime")
    tool_home = checked_path(workspace / ".trial-profile")
    if tool_home.exists():
        raise ValueError("The subject profile path is reserved for the runner")
    inherited = {key.upper(): value for key, value in (os.environ if parent is None else parent).items()}
    if any(not inherited.get(key) for key in SYSTEM_VARIABLES):
        raise ValueError("The native Windows system environment is incomplete")
    core = {key: inherited[key] for key in SYSTEM_VARIABLES}
    system = Path(core["SYSTEMROOT"])
    core["PATH"] = os.pathsep.join(
        str(path)
        for path in (
            python.parent,
            cli.parent,
            *(root / "codex-path" for root in roots if (root / "codex-path").is_dir()),
            system / "System32",
            system / "System32/WindowsPowerShell/v1.0",
        )
    )
    home.mkdir(parents=True, exist_ok=False)
    controller = {**core, **profile_directories(home), "CODEX_HOME": str(home / "profile")}
    tools = {**core, **profile_directories(tool_home), "PYTHONNOUSERSITE": "1", "PYTHONUTF8": "1"}
    return TrialContext(home, workspace, cli, python, roots, controller, tools)


def inline_table(values: Mapping[str, str | Mapping[str, str]]) -> str:
    """Encode Windows paths as quoted TOML keys and values."""
    return (
        "{"
        + ",".join(
            json.dumps(key) + "=" + (inline_table(value) if isinstance(value, Mapping) else json.dumps(value))
            for key, value in sorted(values.items())
        )
        + "}"
    )


def options(context: TrialContext, model: str, reasoning_effort: str) -> list[str]:
    """Use the same context and permission settings in probes and model trials."""
    if not model or "\0" in model or reasoning_effort not in {"low", "medium", "high", "xhigh", "max"}:
        raise ValueError("An explicit model and supported reasoning effort are required")
    filesystem: dict[str, str | Mapping[str, str]] = {
        ":minimal": "read",
        **{str(path): "read" for path in context.readable_roots},
        ":workspace_roots": {".": "write", ".git": "read", ".agents": "read", ".codex": "read", ".aws": "read"},
    }
    if context.signin is not None:
        filesystem[str(context.signin.home)] = "deny"
    settings = {
        "model": json.dumps(model),
        "model_reasoning_effort": json.dumps(reasoning_effort),
        "approval_policy": '"never"',
        "default_permissions": '"trial"',
        "windows.sandbox": '"mxc"',
        "permissions.trial.filesystem": inline_table(filesystem),
        "permissions.trial.network.enabled": "false",
        "shell_environment_policy.inherit": '"none"',
        "shell_environment_policy.set": inline_table(context.tool_environment),
        "project_doc_max_bytes": "0",
        "skills.include_instructions": "false",
        "skills.bundled.enabled": "false",
        "tools.experimental_request_user_input.enabled": "false",
        "features.skip_host_skill_discovery": "true",
        "features.multi_agent_v2.enabled": "false",
        "features.multi_agent_v2.disable_native_tools": "true",
        "web_search": '"disabled"',
        **{f"features.{name}": "false" for name in DISABLED_FEATURES},
    }
    return [argument for key, value in settings.items() for argument in ("-c", f"{key}={value}")]


def command(
    context: TrialContext, model: str, reasoning_effort: str, *, provider: dict[str, str] | None = None
) -> list[str]:
    if provider is not None and validate_provider(provider).get("authentication") == "codex_signin":
        if (
            context.signin is None
            or home_identity(str(context.signin.home)) != home_identity(provider["codex_home"])
            or context.signin.store != provider["credential_store"]
            or context.controller_environment.get("CODEX_HOME") != str(context.signin.home)
            or context.native_catalog is None
        ):
            raise ValueError("The native sign-in declaration lacks its active admitted controller binding")
    elif context.signin is not None or context.native_catalog is not None:
        raise ValueError("A native sign-in binding requires its explicit provider declaration")
    return [
        str(context.cli),
        *options(context, model, reasoning_effort),
        *(provider_options(provider) if provider is not None else []),
        *(
            ["-c", "model_catalog_json=" + json.dumps(str(context.native_catalog.path(context.cli)))]
            if context.native_catalog is not None
            else []
        ),
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--skip-git-repo-check",
        "--json",
        "-C",
        str(context.workspace),
        "-",
    ]

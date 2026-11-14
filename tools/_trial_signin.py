"""Use native CLI sign-in storage without copying credentials or personal context."""

from __future__ import annotations

import io
import os
from dataclasses import dataclass, replace
from pathlib import Path, PurePath, PureWindowsPath
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from _trial_context import TrialContext

STORES = {"file", "keyring", "auto"}


class SigninAdmissionError(ValueError):
    """Retain safe process evidence while discarding native status text."""

    def __init__(self, admission: dict[str, Any]) -> None:
        message = (
            "Native sign-in storage contains global instructions outside the benchmark conditions"
            if admission.get("reason") == "global_instructions_present"
            else "The official CLI did not admit a completed ChatGPT sign-in status check"
        )
        super().__init__(message)
        self.admission = admission


def home_identity(value: str) -> PurePath:
    """Compare local Windows declarations and native paths without opening them."""
    windows = PureWindowsPath(value)
    if windows.drive.startswith("\\\\"):
        raise ValueError("Native sign-in storage requires an absolute local directory")
    if windows.is_absolute() and len(windows.drive) == 2:
        return windows
    native = Path(value)
    if native.is_absolute() and not value.startswith("\\\\"):
        return native
    raise ValueError("Native sign-in storage requires an absolute local directory")


def validate_signin(value: dict[str, Any]) -> dict[str, str]:
    fields = {"authentication", "codex_home", "credential_store"}
    if set(value) != fields or value["authentication"] != "codex_signin":
        raise ValueError("Native sign-in requires exactly authentication, codex_home and credential_store")
    home, store = value["codex_home"], value["credential_store"]
    if not isinstance(home, str) or not home or any(ord(char) < 32 for char in home):
        raise ValueError("Invalid native sign-in storage directory")
    path = home_identity(home)
    if ".." in path.parts or path == type(path)(path.anchor):
        raise ValueError("Native sign-in storage must name a bounded local directory")
    if not isinstance(store, str) or store not in STORES:
        raise ValueError("Native sign-in storage must explicitly select file, keyring or auto")
    return {"authentication": "codex_signin", "codex_home": home, "credential_store": store}


@dataclass(frozen=True)
class NativeSignin:
    home: Path
    store: str
    status_process: dict[str, Any]

    def record(self) -> dict[str, Any]:
        return {
            "home": str(self.home),
            "credential_store": self.store,
            "mode": "chatgpt",
            "status_process": self.status_process,
        }


def status_completed(value: Any) -> bool:
    """Require a stopped bounded native process, not truthy stand-ins for counts."""
    return (
        isinstance(value, dict)
        and all(
            value.get(name) is True
            for name in ("windows_job", "assigned_before_resume", "kill_on_close", "explicit_environment")
        )
        and all(
            type(value.get(name)) is int and value[name] == expected
            for name, expected in (
                ("exit_code", 0),
                ("job_active_processes_after_cleanup", 0),
                ("output_limit_bytes", 65536),
                ("job_memory_limit_bytes", 1024**3),
                ("active_process_limit", 8),
                ("write_io_limit_bytes", 1024**2),
            )
        )
        and type(value.get("wall_time_limit_seconds")) in (int, float)
        and value["wall_time_limit_seconds"] == 20
        and value.get("termination_reason") is None
        and type(value.get("job_write_io_bytes")) is int
        and 0 <= value["job_write_io_bytes"] <= 1024**2
        and value.get("write_io_observation_error") is None
        and value.get("write_io_enforcement") == "polled_job_transfer_accounting"
        and value.get("hard_storage_quota") is False
    )


def bind_signin(context: TrialContext, declaration: dict[str, str]) -> TrialContext:
    """Admit the selected existing login through a bounded official status command."""
    from _windows_appcontainer import checked_path
    from _windows_trial_process import run_owned

    home = checked_path(Path(declaration["codex_home"]))
    if (
        context.signin is not None
        or not home.is_dir()
        or any(
            home.is_relative_to(root) or root.is_relative_to(home)
            for root in (context.home, context.workspace, *context.readable_roots)
        )
    ):
        raise ValueError("Native sign-in storage must be disjoint from controller, subject and runtime grants")
    require_instruction_free_home(home)
    environment = {**context.controller_environment, "CODEX_HOME": str(home)}
    with io.BytesIO() as stdout, io.BytesIO() as stderr, open(os.devnull, "rb") as stdin:
        process = run_owned(
            [
                str(context.cli),
                "-c",
                "cli_auth_credentials_store=" + '"' + declaration["credential_store"] + '"',
                "login",
                "status",
            ],
            cwd=context.home,
            environment=environment,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=20,
            output_limit=65536,
            memory_limit=1024**3,
            process_limit=8,
            write_io_limit=1024**2,
        )
        raw_status = (stdout.getvalue() + stderr.getvalue()).strip()
        mode = (
            "chatgpt"
            if raw_status == b"Logged in using ChatGPT"
            else (
                "apikey"
                if raw_status.startswith((b"Logged in using an API key - ", b"API key configured - "))
                else "unclassified"
            )
        )
        del raw_status
    admitted = mode == "chatgpt" and status_completed(process)
    if not admitted:
        raise SigninAdmissionError({"admitted": False, "mode": mode, "process": process})
    require_instruction_free_home(home)
    return replace(
        context, controller_environment=environment, signin=NativeSignin(home, declaration["credential_store"], process)
    )


def require_instruction_free_home(home: Path) -> None:
    """Reject global instruction entries without reading or changing user content.

    The pinned CLI loads these separately from config.toml and the project byte
    limit. These checks do not freeze a shared profile against concurrent writes.
    """
    for name in ("AGENTS.override.md", "AGENTS.md"):
        try:
            (home / name).lstat()
        except FileNotFoundError:
            continue
        raise SigninAdmissionError({"admitted": False, "mode": "not_checked", "reason": "global_instructions_present"})

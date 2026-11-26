"""Use native CLI sign-in storage without copying credentials or personal context."""

from __future__ import annotations

import io
import os
import stat
from dataclasses import dataclass, replace
from pathlib import Path, PurePath, PureWindowsPath
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from _trial_context import TrialContext

STORES = {"file", "keyring", "auto"}
HOME_REJECTIONS = {
    "global_instructions_present": "Native sign-in storage contains global instructions outside the benchmark conditions",
    "global_rules_present": "Native sign-in storage contains execution rules outside the benchmark conditions",
}


class SigninAdmissionError(ValueError):
    """Retain safe process evidence while discarding native status text."""

    def __init__(self, admission: dict[str, Any]) -> None:
        reason = admission.get("reason")
        fallback = "The official CLI did not admit a completed ChatGPT sign-in status check"
        message = HOME_REJECTIONS.get(reason, fallback) if isinstance(reason, str) else fallback
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


def verify_failed_signin_admission(value: Any) -> None:
    """Verify the safe metadata emitted for a rejected official CLI sign-in."""
    if not isinstance(value, dict) or value.get("admitted") is not False or not isinstance(value.get("mode"), str):
        raise ValueError("Invalid native sign-in failure metadata")
    mode = value["mode"]
    if mode == "not_checked":
        if (
            set(value) != {"admitted", "mode", "reason"}
            or not isinstance(value["reason"], str)
            or value["reason"] not in HOME_REJECTIONS
        ):
            raise ValueError("Invalid native sign-in profile rejection")
        return

    process = value.get("process")
    fixed = {
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "explicit_environment": True,
        "service_created_processes_tracked": False,
        "job_active_processes_after_cleanup": 0,
        "output_limit_bytes": 65536,
        "job_memory_limit_bytes": 1024**3,
        "active_process_limit": 8,
    }
    counters = {"exit_code", "output_bytes", "job_peak_memory_used_bytes"}
    io_fields = {
        "write_io_limit_bytes",
        "job_write_io_bytes",
        "write_io_overshoot_bytes",
        "write_io_observation_error",
        "write_io_enforcement",
        "hard_storage_quota",
    }
    if (
        mode not in {"chatgpt", "apikey", "unclassified"}
        or set(value) != {"admitted", "mode", "process"}
        or not isinstance(process, dict)
        or set(process) != fixed.keys() | counters | io_fields | {"termination_reason", "wall_time_limit_seconds"}
        or any(type(process[key]) is not type(expected) or process[key] != expected for key, expected in fixed.items())
        or any(type(process[key]) is not int or process[key] < 0 for key in counters)
        or type(process["wall_time_limit_seconds"]) not in (int, float)
        or process["wall_time_limit_seconds"] != 20
        or process["termination_reason"]
        not in (None, "timeout", "output_limit", "write_io_limit", "resource_observation_error")
        or (mode == "chatgpt" and status_completed(process))
    ):
        raise ValueError("Invalid native sign-in status failure")

    from _windows_trial_process import verify_write_io_budget

    verify_write_io_budget(process, 1024**2)


def signin_home(context: TrialContext, declaration: dict[str, str]) -> Path:
    """Resolve the existing sign-in directory outside controller and subject grants."""
    from _windows_appcontainer import checked_path

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
    return home


def read_signin_status(context: TrialContext, home: Path, store: str) -> dict[str, Any]:
    """Verify a completed official status command without retaining its text."""
    from _windows_trial_process import run_owned

    environment = {**context.controller_environment, "CODEX_HOME": str(home)}
    with io.BytesIO() as stdout, io.BytesIO() as stderr, open(os.devnull, "rb") as stdin:
        process = run_owned(
            [
                str(context.cli),
                "-c",
                "cli_auth_credentials_store=" + '"' + store + '"',
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
    return process


def bind_signin(context: TrialContext, declaration: dict[str, str]) -> TrialContext:
    """Admit a ChatGPT sign-in from an independent profile for trial execution."""
    home = signin_home(context, declaration)
    store = declaration["credential_store"]
    require_independent_home(home)
    process = read_signin_status(context, home, store)
    require_independent_home(home)
    environment = {**context.controller_environment, "CODEX_HOME": str(home)}
    return replace(context, controller_environment=environment, signin=NativeSignin(home, store, process))


def global_instructions_present(home: Path) -> bool:
    """Observe entry presence without opening any instruction contents."""
    for name in ("AGENTS.override.md", "AGENTS.md"):
        try:
            (home / name).lstat()
        except FileNotFoundError:
            continue
        return True
    return False


def global_rules_present(home: Path) -> bool:
    """Observe the pinned CLI's top-level user rule scope without opening files."""
    directory = home / "rules"
    try:
        info = directory.lstat()
    except FileNotFoundError:
        return False
    if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        return True
    with os.scandir(directory) as entries:
        return any(Path(entry.name).suffix == ".rules" and entry.is_file(follow_symlinks=False) for entry in entries)


def require_independent_home(home: Path) -> None:
    """Require only declared profile context and preserve the normal execution policy."""
    if global_instructions_present(home):
        raise SigninAdmissionError({"admitted": False, "mode": "not_checked", "reason": "global_instructions_present"})
    if global_rules_present(home):
        raise SigninAdmissionError({"admitted": False, "mode": "not_checked", "reason": "global_rules_present"})

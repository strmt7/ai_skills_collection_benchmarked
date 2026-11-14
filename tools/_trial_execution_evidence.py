"""Check version-4 launch and process records without executing trial code."""

from __future__ import annotations

import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from _trial_catalog import PIN_SOURCE, decode_record
from _trial_context import SYSTEM_VARIABLES, TrialContext, command
from _trial_grading_process import DRIVER_PROCESS, DRIVER_STDERR, DRIVER_STDOUT
from _trial_protocol import relative_path
from _trial_signin import STORES, NativeSignin, status_completed
from _trial_transcript import parse_events, strict_json

SETUP_STAGES = {"workspace", "prepare", "context", "prompt", "command", "launch_record"}
CONTROLLER_STAGES = {"agent", "transcript", "submission", "grader", "evidence", "result"}
FAILURE_OBSERVATIONS = {
    "setup_failed": {"attempt.json", "setup-error.json", "prompt.txt", "launch.json"},
    "controller_failed": {
        "attempt.json",
        "controller-error.json",
        "prompt.txt",
        "launch.json",
        "input.native",
        "process.json",
        "transcript.jsonl",
        "stderr.txt",
        "patch.diff",
        "workspace-changes.json",
        DRIVER_STDOUT,
        DRIVER_STDERR,
        DRIVER_PROCESS,
        *(
            f"collection/{name}"
            for name in ("launch.json", "input.native", "process.json", "result.json", "stdout.native", "stderr.native")
        ),
    },
}


def failure_measurements(transcript: bytes | None, process: bytes | None) -> dict[str, Any]:
    """Recover only measurements supported by retained native observations."""
    measured: dict[str, Any] = {
        "usage": None,
        "commands_completed": None,
        "process_exit_code": None,
        "transcript_error": None,
    }
    if process is not None:
        try:
            record = strict_json(process.decode("utf-8"))
            if isinstance(record, dict) and type(record.get("exit_code")) is int:
                measured["process_exit_code"] = record["exit_code"]
        except (UnicodeError, ValueError):
            pass
    if transcript is not None:
        try:
            events = parse_events(transcript, allow_truncated_final=True)
        except ValueError as exc:
            measured["transcript_error"] = str(exc)
        else:
            measured["usage"] = next(
                (event.get("usage") for event in events if event["type"] == "turn.completed"), None
            )
            measured["commands_completed"] = sum(
                event["type"] == "item.completed" and event["item"].get("type") == "command_execution"
                for event in events
            )
    return measured


def verify_attempt(record: Any, protocol_hash: str, condition: str, phase: str) -> None:
    """Validate terminal controller state without inferring liveness from a state file."""
    expected = {
        "attempt_version": 1,
        "protocol_sha256": protocol_hash,
        "condition": condition,
        "phase": phase,
        "model_launch_attempted": phase != "setup_failed",
    }
    if (
        not isinstance(record, dict)
        or set(record) != set(expected) | {"stage", "workspace"}
        or any(type(record.get(key)) is not type(value) or record[key] != value for key, value in expected.items())
        or not isinstance(record.get("stage"), str)
        or record["stage"]
        not in {"setup_failed": SETUP_STAGES, "controller_failed": CONTROLLER_STAGES, "finished": {"result"}}.get(
            phase, set()
        )
        or phase not in {"setup_failed", "controller_failed", "finished"}
    ):
        raise ValueError("attempt lifecycle record contradicts its terminal result")
    workspace = record["workspace"]
    if workspace is not None and (
        not isinstance(workspace, str)
        or "\0" in workspace
        or not (PureWindowsPath(workspace).is_absolute() or PurePosixPath(workspace).is_absolute())
    ):
        raise ValueError("attempt workspace is not an absolute recorded path")
    if workspace is None and (phase != "setup_failed" or record["stage"] != "workspace"):
        raise ValueError("attempt lost its reserved workspace identity")


def context_record(context: TrialContext) -> dict[str, Any]:
    """Record declared shell settings, excluding the controller's authentication environment."""
    return {
        **{name: str(getattr(context, name)) for name in ("home", "workspace", "cli", "python")},
        "readable_roots": [str(path) for path in context.readable_roots],
        "tool_environment": context.tool_environment,
        **({"signin": context.signin.record()} if context.signin is not None else {}),
        **({"native_catalog": context.native_catalog.record()} if context.native_catalog is not None else {}),
    }


def _path(value: Any) -> PureWindowsPath:
    if not isinstance(value, str) or not value or "\0" in value:
        raise ValueError("trial context paths must be absolute local Windows paths")
    path = PureWindowsPath(value)
    if (
        not path.is_absolute()
        or len(path.drive) != 2
        or path.drive[1] != ":"
        or ".." in path.parts
        or str(path) != value
    ):
        raise ValueError("trial context paths must be absolute local Windows paths")
    if len(path.parts) > 1:
        relative_path("/".join(path.parts[1:]))
    return path


def _context(value: Any) -> TrialContext:
    fields = {"home", "workspace", "cli", "python", "readable_roots", "tool_environment"}
    if not isinstance(value, dict) or set(value) not in (
        fields,
        fields | {"signin"},
        fields | {"signin", "native_catalog"},
    ):
        raise ValueError("launch must record the complete declared trial context")
    home, workspace, cli, python = (_path(value[name]) for name in ("home", "workspace", "cli", "python"))
    roots = value["readable_roots"]
    if not isinstance(roots, list) or not roots:
        raise ValueError("launch runtime read roots are missing")
    grants = tuple(_path(root) for root in roots)
    signin = None
    if "signin" in value:
        record = value["signin"]
        if (
            not isinstance(record, dict)
            or set(record) != {"home", "credential_store", "mode", "status_process"}
            or record["mode"] != "chatgpt"
            or not isinstance(record["credential_store"], str)
            or record["credential_store"] not in STORES
            or not status_completed(record["status_process"])
        ):
            raise ValueError("launch native sign-in admission is incomplete or invalid")
        auth_home = _path(record["home"])
        if auth_home == PureWindowsPath(auth_home.anchor) or any(
            auth_home.is_relative_to(root) or root.is_relative_to(auth_home) for root in (home, workspace, *grants)
        ):
            raise ValueError("launch native sign-in storage overlaps subject, controller or runtime grants")
        signin = NativeSignin(Path(str(auth_home)), record["credential_store"], record["status_process"])
    if len(set(grants)) != len(grants):
        raise ValueError("launch repeats runtime read roots")
    if home.is_relative_to(workspace) or workspace.is_relative_to(home):
        raise ValueError("controller and subject state overlap")
    for root in grants:
        if root == PureWindowsPath(root.anchor) or any(
            root.is_relative_to(private) or private.is_relative_to(root) for private in (home, workspace)
        ):
            raise ValueError("runtime read grants expose private state")
    if any(not any(executable.is_relative_to(root) for root in grants) for executable in (cli, python)):
        raise ValueError("launch runtime grants do not cover its executables")
    environment = value["tool_environment"]
    profile = workspace / ".trial-profile"
    profiles = {
        "HOME": str(profile / "profile"),
        "USERPROFILE": str(profile / "profile"),
        "APPDATA": str(profile / "profile/AppData/Roaming"),
        "LOCALAPPDATA": str(profile / "profile/AppData/Local"),
        "TEMP": str(profile / "temporary"),
        "TMP": str(profile / "temporary"),
        "PYTHONNOUSERSITE": "1",
        "PYTHONUTF8": "1",
    }
    if (
        not isinstance(environment, dict)
        or set(environment) != set(SYSTEM_VARIABLES) | {"PATH"} | set(profiles)
        or any(not isinstance(text, str) or not text or "\0" in text for text in environment.values())
        or any(environment[name] != text for name, text in profiles.items())
    ):
        raise ValueError("launch shell environment contains undeclared or private context")
    system = _path(environment["SYSTEMROOT"])
    if (
        _path(environment["WINDIR"]) != system
        or _path(environment["COMSPEC"]) != system / "System32/cmd.exe"
        or environment["SYSTEMDRIVE"].casefold() != system.drive.casefold()
        or re.fullmatch(r"\.[A-Za-z0-9]+(?:;\.[A-Za-z0-9]+)*", environment["PATHEXT"]) is None
    ):
        raise ValueError("launch system environment is inconsistent")
    entries = [_path(entry) for entry in environment["PATH"].split(";")]
    optional = [root / "codex-path" for root in grants]
    middle = entries[2:-2]
    if (
        entries[:2] != [python.parent, cli.parent]
        or entries[-2:] != [system / "System32", system / "System32/WindowsPowerShell/v1.0"]
        or middle != [entry for entry in optional if entry in middle]
    ):
        raise ValueError("launch PATH includes undeclared tool directories")
    return TrialContext(
        Path(str(home)),
        Path(str(workspace)),
        Path(str(cli)),
        Path(str(python)),
        tuple(Path(str(root)) for root in grants),
        {"CODEX_HOME": str(signin.home)} if signin is not None else {},
        environment,
        signin,
        decode_record(value["native_catalog"], Path(str(cli))) if "native_catalog" in value else None,
    )


def verify_launch(launch: Any, protocol: dict[str, Any]) -> None:
    """Reconstruct the full declared command; flags alone cannot establish isolation."""
    sources = protocol.get("execution_source_sha256")
    if (
        not isinstance(sources, dict)
        or not sources
        or not isinstance(launch, dict)
        or launch.get("execution_source_sha256") != sources
    ):
        raise ValueError("launch execution sources differ from the frozen protocol")
    context = _context(launch.get("context"))
    if context.native_catalog is not None and context.native_catalog.source_sha256 != sources.get(PIN_SOURCE):
        raise ValueError("Native model catalog evidence differs from the frozen execution source pin")
    if launch.get("command") != command(
        context, protocol["model"], protocol["reasoning_effort"], provider=protocol.get("provider")
    ):
        raise ValueError("recorded launch differs from its declared model, context or permissions")


def verify_process(process: Any, result: dict[str, Any], output_bytes: int, timeout: int) -> None:
    """Keep missing cleanup, incorrect bounds and interrupted processes out of scored results."""
    if not isinstance(process, dict) or process.get("exit_code") != result.get("process_exit_code"):
        raise ValueError("process exit record contradicts the trial result")
    reason = process.get("termination_reason")
    if reason == "launch_error":
        if result["status"] != "harness_error" or process.get("exit_code") is not None:
            raise ValueError("launch failure cannot be scored or assigned an invented exit code")
        return
    expected = {
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "job_active_processes_after_cleanup": 0,
        "job_memory_limit_bytes": 2 * 1024**3,
        "active_process_limit": 32,
        "explicit_environment": True,
        "output_bytes": output_bytes,
        "output_limit_bytes": 8 * 1024**2,
        "wall_time_limit_seconds": float(timeout),
    }
    if any(type(process.get(key)) is not type(value) or process[key] != value for key, value in expected.items()):
        raise ValueError("process bounds, cleanup or native output counts disagree")
    if (
        type(process.get("exit_code")) is not int
        or output_bytes < 0
        or output_bytes > 8 * 1024**2 + (reason == "output_limit")
        or (reason == "output_limit" and output_bytes != 8 * 1024**2 + 1)
    ):
        raise ValueError("process exit or output limit is invalid")
    if (result["status"] == "timed_out") != (reason == "timeout"):
        raise ValueError("trial timeout label contradicts its process record")
    if reason is not None and result["status"] not in {"harness_error", "timed_out"}:
        raise ValueError("an interrupted process cannot become a task score")

"""Run source collection in a separate bounded, profile-free controller process."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from _lib_b.io_utils import write_json
from _trial_collection_contract import BOOTSTRAP as BOOTSTRAP
from _trial_collection_contract import collector_command, process_complete
from _trial_collection_manifest import validate_manifest
from _trial_collection_policy import collection_policy
from _trial_transcript import strict_json
from _windows_appcontainer import checked_path
from _windows_submission_reader import read_workspace_file
from _windows_trial_process import run_owned

ROOT = Path(__file__).resolve().parents[1]


def capture_owned(
    workspace: Path, output: Path, observations: Path, python: Path, declared: dict[str, Any]
) -> dict[str, Any]:
    """Accept only a complete, source-bound receipt from a terminated owned job."""
    policy = collection_policy(declared)
    workspace, output, observations, python = (checked_path(path) for path in (workspace, output, observations, python))
    if (
        observations.is_relative_to(workspace)
        or workspace.is_relative_to(observations)
        or output.is_relative_to(observations)
        or observations.is_relative_to(output)
        or (ROOT / "tools").is_relative_to(workspace)
        or python.is_relative_to(workspace)
    ):
        raise ValueError("collector observations, output and subject state must be disjoint")
    observations.mkdir(parents=True, exist_ok=False)
    command = collector_command(ROOT, python, workspace, output, policy, bootstrap=BOOTSTRAP)
    write_json(
        observations / "launch.json",
        {
            "command": command,
            "policy": policy,
            "source_root": str(ROOT),
            "python": str(python),
            "workspace": str(workspace),
            "output": str(output),
            "observations": str(observations),
        },
    )
    (observations / "input.native").touch(exist_ok=False)
    inherited = {key.upper(): value for key, value in os.environ.items()}
    system_keys = ("SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "SYSTEMDRIVE")
    try:
        if any(not inherited.get(key) for key in system_keys):
            raise ValueError("collector requires the native Windows system environment")
        environment = {key: inherited[key] for key in system_keys}
        environment["PATH"] = os.pathsep.join((str(python.parent), str(Path(environment["SYSTEMROOT"]) / "System32")))
        with (
            (observations / "input.native").open("rb") as stdin,
            (observations / "stdout.native").open("xb") as stdout,
            (observations / "stderr.native").open("xb") as stderr,
        ):
            process = run_owned(
                command,
                cwd=ROOT,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                timeout=policy["timeout_seconds"],
                output_limit=64 * 1024**2,
                memory_limit=1024**3,
                process_limit=4,
                environment=environment,
            )
    except (OSError, ValueError, RuntimeError) as exc:
        process = {
            "exit_code": None,
            "termination_reason": "launch_error",
            "error_type": type(exc).__name__,
            **{key: getattr(exc, key, None) for key in ("errno", "winerror")},
        }
    write_json(observations / "process.json", process)
    record: dict[str, Any]
    stdout_path, stderr_path = observations / "stdout.native", observations / "stderr.native"
    raw = stdout_path.read_bytes() if stdout_path.exists() else b""
    stderr_bytes = stderr_path.read_bytes() if stderr_path.exists() else b""
    if not process_complete(process, policy, len(raw) + len(stderr_bytes)):
        record = {"collection_version": 1, "status": "collection_error", "error_type": "incomplete_process"}
    else:
        try:
            record = validate_manifest(strict_json(raw.decode("utf-8")), policy)
            for name, identity in record["files"].items():
                content = read_workspace_file(output, name, max_bytes=policy["max_file_bytes"])
                if len(content) != identity["bytes"] or hashlib.sha256(content).hexdigest() != identity["sha256"]:
                    raise ValueError("collected file bytes differ from the native source receipt")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            record = {"collection_version": 1, "status": "collection_error", "error_type": type(exc).__name__}
    write_json(observations / "result.json", record)
    return record

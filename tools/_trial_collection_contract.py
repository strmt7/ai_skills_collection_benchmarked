"""Portable consistency checks for native collection launch and process records."""

from __future__ import annotations

import json
from pathlib import PurePath, PureWindowsPath
from typing import Any

from _trial_collection_policy import collection_policy

BOOTSTRAP = (
    "import runpy,sys;sys.path.insert(0,sys.argv[1]);del sys.argv[:2];runpy.run_path(sys.argv[0],run_name='__main__')"
)


def collector_command(
    source: PurePath,
    python: PurePath,
    workspace: PurePath,
    output: PurePath,
    policy: dict[str, Any],
    *,
    bootstrap: str = BOOTSTRAP,
) -> list[str]:
    return [
        str(python),
        "-I",
        "-S",
        "-B",
        "-c",
        bootstrap,
        str(source / "tools"),
        str(source / "tools/collect_agent_workspace.py"),
        "--workspace",
        str(workspace),
        "--output",
        str(output),
        "--policy-json",
        json.dumps(policy, sort_keys=True),
    ]


def process_complete(process: Any, policy: dict[str, Any], output_bytes: int) -> bool:
    expected = {
        "exit_code": 0,
        "termination_reason": None,
        "job_active_processes_after_cleanup": 0,
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "explicit_environment": True,
        "job_memory_limit_bytes": 1024**3,
        "active_process_limit": 4,
        "output_limit_bytes": 64 * 1024**2,
        "wall_time_limit_seconds": float(policy["timeout_seconds"]),
        "output_bytes": output_bytes,
    }
    return isinstance(process, dict) and all(
        type(process.get(key)) is type(value) and process[key] == value for key, value in expected.items()
    )


def verify_collector_launch(record: Any, declared: dict[str, Any], workspace: str) -> None:
    policy = collection_policy(declared)
    paths = {"source_root", "python", "workspace", "output", "observations"}
    if not isinstance(record, dict) or set(record) != paths | {"command", "policy"}:
        raise ValueError("collector launch declaration is incomplete")
    if collection_policy(record["policy"]) != policy:
        raise ValueError("collector launch used a different resource policy")
    parsed = {}
    for key in paths:
        value = record[key]
        if not isinstance(value, str) or "\0" in value:
            raise ValueError("collector paths must be canonical absolute local Windows paths")
        path = PureWindowsPath(value)
        if not path.is_absolute() or len(path.drive) != 2 or str(path) != value or ".." in path.parts:
            raise ValueError("collector paths must be canonical absolute local Windows paths")
        parsed[key] = path
    subject = parsed["workspace"]
    if str(subject) != workspace:
        raise ValueError("collector used a different task workspace")
    output, observations = parsed["output"], parsed["observations"]
    if (
        output.name != "submission"
        or observations.name != "collection"
        or output.parent != observations.parent
        or output.is_relative_to(subject)
        or subject.is_relative_to(output)
        or observations.is_relative_to(subject)
        or subject.is_relative_to(observations)
        or (parsed["source_root"] / "tools").is_relative_to(subject)
        or parsed["python"].is_relative_to(subject)
    ):
        raise ValueError("collector roles overlap or differ from the attempt layout")
    expected = collector_command(parsed["source_root"], parsed["python"], subject, output, policy)
    if record["command"] != expected:
        raise ValueError("collector command differs from its declared source and runtime roles")

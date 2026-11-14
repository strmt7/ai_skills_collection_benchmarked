"""Resource limits and native evidence for the grading driver."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from _trial_context import SYSTEM_VARIABLES

DRIVER_SOURCE = "tools/_trial_grading_process.py"
DRIVER_STDOUT = "grading.driver.stdout.native"
DRIVER_STDERR = "grading.driver.stderr.native"
DRIVER_PROCESS = "grading.driver.process.json"
DRIVER_TIMEOUT = 240.0
DRIVER_OUTPUT_LIMIT = 8 * 1024**2
DRIVER_MEMORY_LIMIT = 2 * 1024**3
DRIVER_PROCESS_LIMIT = 16
DRIVER_EXIT_CODES = {"task_passed": 0, "task_failed": 1, "harness_error": 2}


def driver_environment(python: Path, temporary: Path) -> dict[str, str]:
    """Keep the trusted grader's environment separate from provider credentials."""
    inherited = {key.upper(): value for key, value in os.environ.items()}
    git = shutil.which("git")
    if not git or any(not inherited.get(key) for key in SYSTEM_VARIABLES):
        raise ValueError("Grading requires the native Windows environment and a Git executable")
    environment = {key: inherited[key] for key in SYSTEM_VARIABLES}
    system = Path(environment["SYSTEMROOT"]) / "System32"
    environment["PATH"] = os.pathsep.join((str(python.parent), str(Path(git).resolve().parent), str(system)))
    environment["TEMP"] = environment["TMP"] = str(temporary)
    return environment


def driver_completed(process: Any, output_bytes: int) -> bool:
    """Bind a scored outcome to the bounded process and its captured bytes."""
    expected = {
        "termination_reason": None,
        "job_active_processes_after_cleanup": 0,
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "explicit_environment": True,
        "job_memory_limit_bytes": DRIVER_MEMORY_LIMIT,
        "active_process_limit": DRIVER_PROCESS_LIMIT,
        "output_limit_bytes": DRIVER_OUTPUT_LIMIT,
        "wall_time_limit_seconds": DRIVER_TIMEOUT,
        "output_bytes": output_bytes,
    }
    return (
        isinstance(process, dict)
        and type(process.get("exit_code")) is int
        and process["exit_code"] in DRIVER_EXIT_CODES.values()
        and 0 < output_bytes <= DRIVER_OUTPUT_LIMIT
        and all(type(process.get(key)) is type(value) and process[key] == value for key, value in expected.items())
    )

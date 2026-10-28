"""Confined behavioral grader; the submitted module never loads in this process."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from grade_agent_submission import evaluate as confined_evaluate


def evaluate(
    workspace: Path,
    *,
    fixture: Path | None = None,
    revision: str | None = None,
    runtime_home: Path | None = None,
    dependency_home: Path | None = None,
    output: Path | None = None,
) -> dict[str, Any]:
    return confined_evaluate(
        Path(__file__),
        workspace,
        fixture=fixture,
        revision=revision,
        runtime_home=runtime_home,
        dependency_home=dependency_home,
        output=output,
    )

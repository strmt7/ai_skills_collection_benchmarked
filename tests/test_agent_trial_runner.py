from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
import run_agent_trial as trials


def test_workspace_paths_cannot_escape(tmp_path):
    for path in ("../outside", ".", str(tmp_path.parent / "outside")):
        with pytest.raises(ValueError):
            trials.checked_path(tmp_path, path)


def test_unfinished_jsonl_never_invents_usage_or_completion(tmp_path):
    path = tmp_path / "transcript.jsonl"
    path.write_text('{"type":"turn.started"}\n{"type":', encoding="utf-8")
    assert trials.read_events(path) == [{"type": "turn.started"}]


def test_launch_keeps_sandbox_and_disables_development_context(tmp_path, monkeypatch):
    monkeypatch.setattr(trials.platform, "system", lambda: "Windows")
    args = trials.command({"model": "gpt-6.1-sol", "reasoning_effort": "high"}, tmp_path / "codex.exe", tmp_path)
    assert "--ignore-user-config" in args
    assert "--ephemeral" in args
    assert args[args.index("--sandbox") + 1] == "workspace-write"
    assert 'windows.sandbox="elevated"' in args
    assert "sandbox_workspace_write.network_access=false" in args
    for feature in ("memories", "plugins", "apps", "multi_agent", "browser_use", "computer_use"):
        assert args[args.index(feature) - 1] == "--disable"
    assert not any("bypass" in arg or "ignore-rules" in arg for arg in args)


@pytest.mark.parametrize("changed", ["input", "grader", "skill"])
def test_protocol_freeze_rejects_changed_inputs(tmp_path, monkeypatch, changed):
    grader = tmp_path / "grader.py"
    grader.write_text("grader", encoding="utf-8")
    skill = tmp_path / "skill.md"
    skill.write_text("skill", encoding="utf-8")
    monkeypatch.setattr(trials, "ROOT", tmp_path)
    monkeypatch.setattr(trials, "pinned_file", lambda *args: b"input")
    protocol: dict[str, Any] = {
        "task": {"source_commit": "a" * 40, "files": ["code.py"], "grader": "grader.py", "brief": "brief"},
        "input_sha256": {"code.py": trials.sha256(b"input")},
        "grader_sha256": trials.sha256(b"grader"),
        "conditions": {"improved": {"skills": [{"path": "skill.md", "sha256": trials.sha256(b"skill")}]}},
        "prompt_template": "<TASK_BRIEF> <PYTHON_RUNTIME>",
    }
    if changed == "input":
        protocol["input_sha256"]["code.py"] = "0" * 64
    elif changed == "grader":
        grader.write_text("changed", encoding="utf-8")
    else:
        skill.write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="changed|differ"):
        trials.prepare(protocol, "improved", tmp_path / "python.exe")


def test_grading_timeout_counts_as_failed_submission(tmp_path, monkeypatch):
    def run(*args, **kwargs):
        assert kwargs["timeout"] == 60
        raise subprocess.TimeoutExpired(args[0], 60)

    monkeypatch.setattr(trials.subprocess, "run", run)
    result = trials.external_grade(
        {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py"}, tmp_path, Path("python")
    )
    assert result["status"] == "task_failed"
    assert "grading limit" in result["error"]


def test_existing_attempt_is_never_overwritten(tmp_path):
    protocol = tmp_path / "protocol.json"
    protocol.write_text(json.dumps({}), encoding="utf-8")
    output = tmp_path / "attempt"
    output.mkdir()
    with pytest.raises(ValueError, match="overwrite"):
        trials.run(protocol, "default", output, Path("codex"), Path("python"))

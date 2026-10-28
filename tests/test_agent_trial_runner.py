from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import _trial_transcript
import pytest
import run_agent_trial as trials
import summarize_agent_trials as summary


def test_workspace_paths_cannot_escape(tmp_path):
    for path in ("../outside", ".", str(tmp_path.parent / "outside")):
        with pytest.raises(ValueError):
            trials.checked_path(tmp_path, path)


def test_unfinished_jsonl_never_invents_usage_or_completion(tmp_path):
    path = tmp_path / "transcript.jsonl"
    path.write_text('{"type":"turn.started"}\n{"type":', encoding="utf-8")
    with pytest.raises(ValueError, match="transcript"):
        trials.read_events(path)
    assert trials.read_events(path, allow_truncated_final=True) == [{"type": "turn.started"}]


@pytest.mark.parametrize(
    "transcript",
    [
        '{"type":"turn.started"}\nnot-json\n{"type":"turn.completed"}\n',
        '{"type":"turn.started","type":"turn.completed"}\n',
        '{"type":"turn.completed","usage":{"input_tokens":NaN}}\n',
        '{"type":"turn.completed","usage":{"input_tokens":{"nested":1},"output_tokens":0}}\n',
        '{"type":"turn.completed","usage":{"input_tokens":1,"cached_input_tokens":2,"output_tokens":0}}\n',
        '{"type":"turn.completed","usage":{"input_tokens":1}}\n',
        "[]\n",
        '{"type":"turn.completed"}\n{"type":"turn.completed"}\n',
    ],
)
def test_malformed_transcript_never_becomes_a_completed_trial(tmp_path, transcript):
    path = tmp_path / "transcript.jsonl"
    path.write_text(transcript, encoding="utf-8")
    with pytest.raises(ValueError, match="transcript"):
        trials.read_events(path)


def test_parser_nesting_limit_becomes_a_transcript_error(tmp_path, monkeypatch):
    path = tmp_path / "transcript.jsonl"
    path.write_text('{"type":"turn.started"}\n', encoding="utf-8")

    def too_deep(*args, **kwargs):
        raise RecursionError("fixture nesting limit")

    monkeypatch.setattr(_trial_transcript.json, "loads", too_deep)
    with pytest.raises(ValueError, match="transcript contains an invalid event"):
        trials.read_events(path)


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


def test_grading_timeout_does_not_claim_a_submission_failure(tmp_path, monkeypatch):
    def run(*args, **kwargs):
        assert kwargs["timeout"] == 60
        raise subprocess.TimeoutExpired(args[0], 60)

    monkeypatch.setattr(trials.subprocess, "run", run)
    result = trials.external_grade(
        {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py"}, tmp_path, Path("python")
    )
    assert result["status"] == "harness_error"
    assert "grading limit" in result["error"]


@pytest.mark.parametrize(
    "returncode,stdout",
    [
        (2, '{"status":"harness_error","errors":["sandbox unavailable"]}'),
        (1, "invalid JSON"),
        (0, '{"status":"task_failed"}'),
        (1, '{"status":"task_passed"}'),
        (1, '{"status":[]}'),
        (2, '{"status":"task_failed"}'),
        (127, '{"status":"task_failed"}'),
        (-1, '{"status":"task_failed"}'),
        (0, '{"status":"task_failed","status":"task_passed"}'),
        (0, '{"status":"task_passed","checks_total":NaN}'),
    ],
)
def test_grading_infrastructure_failures_are_not_scored_as_agent_failures(tmp_path, monkeypatch, returncode, stdout):
    monkeypatch.setattr(
        trials.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode, stdout, "")
    )
    result = trials.external_grade(
        {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py"}, tmp_path, Path("python")
    )
    assert result["status"] == "harness_error"


@pytest.mark.parametrize("status,returncode", [("task_passed", 0), ("task_failed", 1), ("harness_error", 2)])
def test_matching_grader_exit_codes_keep_the_reported_status(tmp_path, monkeypatch, status, returncode):
    monkeypatch.setattr(
        trials.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode, json.dumps({"status": status}), ""),
    )
    result = trials.external_grade(
        {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py"}, tmp_path, Path("python")
    )
    assert result["status"] == status


def test_unavailable_grading_driver_is_a_harness_error(tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise FileNotFoundError("fixture runtime unavailable")

    monkeypatch.setattr(trials.subprocess, "run", unavailable)
    result = trials.external_grade(
        {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py"}, tmp_path, Path("python")
    )
    assert result["status"] == "harness_error"


def test_invalid_trial_stream_is_recorded_without_grading(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    protocol = {
        "runner_sha256": trials.sha256((trials.ROOT / "tools/run_agent_trial.py").read_bytes()),
        "grading_driver_sha256": trials.sha256((trials.ROOT / "tools/grade_agent_submission.py").read_bytes()),
        "transcript_parser_sha256": trials.sha256((trials.ROOT / "tools/_trial_transcript.py").read_bytes()),
        "task": {"id": "fixture", "partition": "development", "allowed_changes": []},
        "model": "fixture-model",
        "reasoning_effort": "high",
        "time_limit_seconds": 10,
        "limitations": [],
    }
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
    monkeypatch.setattr(trials, "prepare", lambda *args: (workspace, "fixture", {}))
    monkeypatch.setattr(trials, "command", lambda *args: ["fixture"])

    def unexpected_grade(*args):
        raise AssertionError("invalid transcript must not be graded")

    monkeypatch.setattr(trials, "external_grade", unexpected_grade)

    class FakeProcess:
        returncode = 0

        def __init__(self, *args, stdout, **kwargs):
            stdout.write('{"type":"turn.started"}\nnot-json\n{"type":"turn.completed"}\n')
            stdout.flush()

        def communicate(self, *args, **kwargs):
            return None

    monkeypatch.setattr(trials.subprocess, "Popen", FakeProcess)
    output = tmp_path / "attempt"
    result = trials.run(protocol_path, "default", output, Path("fixture"), Path("python"))
    assert result["status"] == "harness_error"
    assert result["transcript_error"] == "transcript contains an invalid event on line 2"
    assert result["usage"] is None and result["commands_completed"] is None
    assert result["grader"]["status"] == "harness_error"
    summary.verify_transcript(output, result)


def test_changed_transcript_parser_is_rejected_before_launch(tmp_path, monkeypatch):
    protocol = {
        "runner_sha256": trials.sha256((trials.ROOT / "tools/run_agent_trial.py").read_bytes()),
        "grading_driver_sha256": trials.sha256((trials.ROOT / "tools/grade_agent_submission.py").read_bytes()),
        "transcript_parser_sha256": "0" * 64,
    }
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
    monkeypatch.setattr(trials.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("unexpected process"))
    with pytest.raises(ValueError, match="execution tooling changed"):
        trials.run(protocol_path, "default", tmp_path / "attempt", Path("fixture"), Path("python"))
    assert not (tmp_path / "attempt").exists()


def test_frozen_legacy_protocol_refuses_changed_grading_before_launch(tmp_path, monkeypatch):
    def no_launch(*args, **kwargs):
        raise AssertionError("a frozen legacy protocol must not launch a model")

    monkeypatch.setattr(trials.subprocess, "Popen", no_launch)
    protocol = trials.ROOT / "benchmarks/agent-effectiveness/development/protocol-v2.json"
    with pytest.raises(ValueError, match="execution tooling changed"):
        trials.run(protocol, "default", tmp_path / "attempt", tmp_path / "cli", tmp_path / "python")
    assert not (tmp_path / "attempt").exists()


def test_existing_attempt_is_never_overwritten(tmp_path):
    protocol = tmp_path / "protocol.json"
    protocol.write_text(json.dumps({}), encoding="utf-8")
    output = tmp_path / "attempt"
    output.mkdir()
    with pytest.raises(ValueError, match="overwrite"):
        trials.run(protocol, "default", output, Path("codex"), Path("python"))

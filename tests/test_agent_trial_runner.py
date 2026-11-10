from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import _trial_manifest
import _trial_transcript
import pytest
import run_agent_trial as trials
import summarize_agent_trials as summary
from _trial_collection_policy import default_collection_policy
from _trial_context import TrialContext


def declared_fixture() -> dict[str, Any]:
    return {
        "collection_policy": default_collection_policy(),
        "task": {
            "id": "fixture",
            "partition": "development",
            "allowed_changes": [],
            "source_commit": "a" * 40,
            "grader": "tools/grade.py",
            "brief": "Owned control",
            "files": ["code.py"],
        },
        "input_sha256": {"code.py": "b" * 64},
        "prompt_template": "<TASK_BRIEF> <PYTHON_RUNTIME>",
        "conditions": {"default": {"skills": []}},
        "planned_order": [{"repetition": 1, "conditions": ["default"]}],
        "model": "fixture-model",
        "reasoning_effort": "high",
        "time_limit_seconds": 10,
        "limitations": [],
    }


@pytest.mark.parametrize(
    ("exit_code", "timed_out", "violations", "expected"),
    [
        (0, False, [], "task_passed"),
        (None, False, [], "harness_error"),
        (True, False, [], "harness_error"),
        (1, False, [], "harness_error"),
        (0, False, ["outside scope"], "invalid_scope"),
        (1, True, ["outside scope"], "timed_out"),
        (1, False, ["outside scope"], "harness_error"),
    ],
)
def test_trial_status_requires_a_successful_process_and_preserves_failure_precedence(
    exit_code, timed_out, violations, expected
):
    """Incomplete processes cannot become task passes, even when grading succeeds."""
    assert (
        trials.trial_status(
            timed_out=timed_out,
            exit_code=exit_code,
            completed=True,
            collection_errors=[],
            transcript_error=None,
            blocked=False,
            violations=violations,
            grade={"status": "task_passed"},
        )
        == expected
    )


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
    context = TrialContext(
        tmp_path / "controller", tmp_path, tmp_path / "codex.exe", tmp_path / "python.exe", (), {}, {}
    )
    args = trials.command({"model": "gpt-6.1-sol", "reasoning_effort": "high"}, context)
    assert "--ignore-user-config" in args
    assert "--ephemeral" in args
    assert "--sandbox" not in args
    assert 'windows.sandbox="mxc"' in args
    assert "permissions.trial.network.enabled=false" in args
    for feature in ("memories", "plugins", "apps", "multi_agent", "browser_use", "computer_use"):
        assert f"features.{feature}=false" in args
    assert not any("bypass" in arg or "ignore-rules" in arg for arg in args)


def test_execution_uses_a_bounded_job_and_retains_native_process_evidence(tmp_path, monkeypatch):
    context = TrialContext(
        tmp_path / "controller", tmp_path, Path("codex"), Path("python"), (), {"CONTROL": "private"}, {}
    )

    def execute(invocation, **options):
        assert invocation == ["owned fixture"]
        assert options["stdin"].read() == b"task input"
        assert options["environment"] == context.controller_environment
        assert options["cwd"] == context.workspace
        assert options["memory_limit"] == 2 * 1024**3
        assert options["process_limit"] == 32
        assert options["output_limit"] == 8 * 1024**2
        options["stdout"].write(b'{"type":"turn.started"}\n')
        options["stderr"].write(b"native diagnostic\n")
        assert (tmp_path / "transcript.jsonl").read_bytes() == b'{"type":"turn.started"}\n'
        assert (tmp_path / "stderr.txt").read_bytes() == b"native diagnostic\n"
        return {"exit_code": 124, "termination_reason": "timeout", "job_active_processes_after_cleanup": 0}

    monkeypatch.setattr(trials, "run_owned", execute)
    code, timed_out, elapsed = trials.execute_agent(["owned fixture"], "task input", tmp_path, 1, context=context)
    assert code == 124 and timed_out and elapsed >= 0
    assert (tmp_path / "stderr.txt").read_bytes() == b"native diagnostic\n"
    assert json.loads((tmp_path / "process.json").read_bytes())["job_active_processes_after_cleanup"] == 0


def test_launch_failure_is_retained_without_inventing_an_exit_or_cleanup_success(tmp_path, monkeypatch):
    context = TrialContext(tmp_path / "controller", tmp_path, Path("codex"), Path("python"), (), {}, {})

    def fail(*args, **kwargs):
        raise OSError(5, "owned launch control")

    monkeypatch.setattr(trials, "run_owned", fail)
    code, timed_out, _ = trials.execute_agent(["fixture"], "input", tmp_path, 1, context=context)
    assert code is None and timed_out is False
    recorded = json.loads((tmp_path / "process.json").read_bytes())
    assert recorded["termination_reason"] == "launch_error"
    assert recorded["error_type"] == "OSError"
    assert recorded["errno"] == 5 and recorded["winerror"] is None
    assert "job_active_processes_after_cleanup" not in recorded


def test_evidence_collection_reads_only_declared_files_without_walking_scratch(tmp_path, monkeypatch):
    (tmp_path / "observed.txt").write_bytes(b"recorded")
    scratch = tmp_path / "grading/scratch"
    scratch.mkdir(parents=True)
    (scratch / "untrusted.txt").write_bytes(b"not a controller output")
    observed = []

    def read(root, name, *, max_bytes):
        observed.append(name)
        return (root / name).read_bytes()

    monkeypatch.setattr(trials, "read_workspace_file", read)
    hashes, errors = trials.collect_evidence(tmp_path, ["observed.txt"])
    assert observed == ["observed.txt"]
    assert hashes == {"observed.txt": trials.sha256(b"recorded")} and errors == []


def test_missing_evidence_remains_an_explicit_collection_failure(tmp_path, monkeypatch):
    def reject(*args, **kwargs):
        raise ValueError("linked capture")

    monkeypatch.setattr(trials, "read_workspace_file", reject)
    hashes, errors = trials.collect_evidence(tmp_path, ["transcript.jsonl"])
    assert hashes == {} and errors == ["evidence transcript.jsonl: ValueError"]


@pytest.mark.parametrize("directory", ["../outside", "case-abc/observations", "case-" + "a" * 32 + "/scratch"])
def test_grader_cannot_redirect_evidence_reads_to_arbitrary_paths(directory):
    with pytest.raises(ValueError, match="invalid observation directory"):
        trials.grading_evidence({"status": "task_passed", "checks": [{"observation_directory": directory}]})


def test_frozen_execution_sources_include_grader_and_context_helpers():
    hashes = trials.execution_source_hashes()
    assert {
        "tools/_trial_context.py",
        "tools/_windows_trial_process.py",
        "tools/_windows_submission_reader.py",
        "tools/_validator_cases.py",
        "tools/grade_validator_appcontainer_modern.py",
        "toolchains/appcontainer-modern/source.json",
    } <= hashes.keys()
    assert all(len(value) == 64 for value in hashes.values())


@pytest.mark.parametrize("change", ["missing", "added", "changed"])
def test_execution_source_commitment_rejects_changed_or_incomplete_closures(tmp_path, monkeypatch, change):
    sources = trials.execution_source_hashes()
    if change == "missing":
        sources.pop("tools/_trial_context.py")
    elif change == "added":
        sources["unexpected.py"] = "a" * 64
    else:
        sources["tools/_validator_cases.py"] = "b" * 64
    protocol = {
        "protocol_version": 4,
        "execution_source_sha256": sources,
        "runner_sha256": trials.sha256((trials.ROOT / "tools/run_agent_trial.py").read_bytes()),
        "grading_driver_sha256": trials.sha256((trials.ROOT / "tools/grade_agent_submission.py").read_bytes()),
        "transcript_parser_sha256": trials.sha256((trials.ROOT / "tools/_trial_transcript.py").read_bytes()),
        "trial_manifest_sha256": trials.sha256((trials.ROOT / "tools/_trial_manifest.py").read_bytes()),
        "grader_sha256": "a" * 64,
        "grading_cases_sha256": _trial_manifest.case_digest(["case"]),
    }
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(protocol), encoding="utf-8")
    path.with_name("protocol.grading.json").write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "protocol_sha256": trials.sha256(path.read_bytes()),
                "grader_sha256": protocol["grader_sha256"],
                "cases": ["case"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(trials, "run_owned", lambda *args, **kwargs: pytest.fail("unexpected process"))
    with pytest.raises(ValueError, match="execution sources changed"):
        trials.run(path, "default", tmp_path / "attempt", Path("codex"), Path("python"))
    assert not (tmp_path / "attempt").exists()


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
        assert kwargs["timeout"] == 240
        raise subprocess.TimeoutExpired(args[0], 240)

    monkeypatch.setattr(trials.subprocess, "run", run)
    result = trials.external_grade(
        {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py", "source_commit": "a" * 40},
        tmp_path,
        Path("python"),
        frozenset({"case"}),
        runtime_home=tmp_path / "runtime",
        dependency_home=tmp_path / "dependencies",
        output=tmp_path / "grading",
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
        trials.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode, stdout.encode(), b""),
    )
    result = trials.external_grade(
        {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py", "source_commit": "a" * 40},
        tmp_path,
        Path("python"),
        frozenset({"case"}),
        runtime_home=tmp_path / "runtime",
        dependency_home=tmp_path / "dependencies",
        output=tmp_path / "grading",
    )
    assert result["status"] == "harness_error"


@pytest.mark.parametrize("status,returncode", [("task_passed", 0), ("task_failed", 1), ("harness_error", 2)])
def test_matching_grader_exit_codes_keep_the_reported_status(tmp_path, monkeypatch, status, returncode):
    passed = status == "task_passed"
    grade = {"status": status}
    if status != "harness_error":
        grade.update(checks=[{"case": "case", "passed": passed}], checks_total=1, checks_passed=int(passed))
    monkeypatch.setattr(
        trials.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], returncode, json.dumps(grade).encode(), b""),
    )
    result = trials.external_grade(
        {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py", "source_commit": "a" * 40},
        tmp_path,
        Path("python"),
        frozenset({"case"}),
        runtime_home=tmp_path / "runtime",
        dependency_home=tmp_path / "dependencies",
        output=tmp_path / "grading",
    )
    assert result["status"] == status


@pytest.mark.parametrize(
    "grade",
    [
        {"status": "task_passed"},
        {"status": "task_passed", "checks": [], "checks_total": 0, "checks_passed": 0},
        {"status": "task_passed", "checks": [{"case": "other", "passed": True}], "checks_total": 1, "checks_passed": 1},
        {
            "status": "task_passed",
            "checks": [{"case": "case", "passed": True}] * 2,
            "checks_total": 2,
            "checks_passed": 2,
        },
        {
            "status": "task_passed",
            "checks": [{"case": "case", "passed": True}],
            "checks_total": True,
            "checks_passed": 1,
        },
        {"status": "task_passed", "checks": [{"case": "case", "passed": 1}], "checks_total": 1, "checks_passed": 1},
        {"status": "task_passed", "checks": [{"case": "case", "passed": False}], "checks_total": 1, "checks_passed": 0},
        {"status": "task_failed", "checks": [{"case": "case", "passed": True}], "checks_total": 1, "checks_passed": 1},
    ],
)
def test_incomplete_or_contradictory_grading_is_a_harness_error(tmp_path, monkeypatch, grade):
    """A valid exit code alone never authorizes a scored outcome."""
    code = 0 if grade["status"] == "task_passed" else 1
    monkeypatch.setattr(
        trials.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], code, json.dumps(grade).encode(), b""),
    )
    result = trials.external_grade(
        {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py", "source_commit": "a" * 40},
        tmp_path,
        Path("python"),
        frozenset({"case"}),
        runtime_home=tmp_path / "runtime",
        dependency_home=tmp_path / "dependencies",
        output=tmp_path / "grading",
    )
    assert result["status"] == "harness_error"


def test_unavailable_grading_driver_is_a_harness_error(tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise FileNotFoundError("fixture runtime unavailable")

    monkeypatch.setattr(trials.subprocess, "run", unavailable)
    result = trials.external_grade(
        {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py", "source_commit": "a" * 40},
        tmp_path,
        Path("python"),
        frozenset({"case"}),
        runtime_home=tmp_path / "runtime",
        dependency_home=tmp_path / "dependencies",
        output=tmp_path / "grading",
    )
    assert result["status"] == "harness_error"


def test_confined_grading_receives_the_frozen_fixture_and_explicit_homes(tmp_path, monkeypatch):
    observed = []

    def invoke(args, **kwargs):
        observed.append(args)
        return subprocess.CompletedProcess(args, 2, b'{"status":"harness_error","errors":["control"]}', b"")

    monkeypatch.setattr(trials.subprocess, "run", invoke)
    task = {"grader": "benchmarks/agent-effectiveness/graders/artifact_validator.py", "source_commit": "b" * 40}
    result = trials.external_grade(
        task,
        tmp_path / "submission",
        tmp_path / "python",
        frozenset({"case"}),
        runtime_home=tmp_path / "runtime",
        dependency_home=tmp_path / "dependencies",
        output=tmp_path / "grading",
    )
    assert result["status"] == "harness_error"
    args = observed[0]
    for option, expected in {
        "--fixture": str(trials.ROOT.resolve()),
        "--revision": "b" * 40,
        "--runtime-home": str((tmp_path / "runtime").resolve()),
        "--dependency-home": str((tmp_path / "dependencies").resolve()),
        "--output": str((tmp_path / "grading").resolve()),
    }.items():
        assert args[args.index(option) + 1] == expected


@pytest.mark.parametrize("missing", ["runtime_home", "dependency_home", "output"])
def test_missing_confined_inputs_never_fall_back_to_host_grading(tmp_path, monkeypatch, missing):
    monkeypatch.setattr(trials.subprocess, "run", lambda *args, **kwargs: pytest.fail("unexpected grading process"))
    options = {name: tmp_path / name for name in ("runtime_home", "dependency_home", "output")}
    options[missing] = None
    result = trials.external_grade({}, tmp_path, Path("python"), frozenset({"case"}), **options)
    assert result["status"] == "harness_error"
    assert "Explicit confined" in result["error"]


def test_grading_transport_is_never_overwritten(tmp_path, monkeypatch):
    captured = tmp_path / "grading.driver.stdout.native"
    captured.write_bytes(b"previous attempt")
    monkeypatch.setattr(trials.subprocess, "run", lambda *args, **kwargs: pytest.fail("unexpected process"))
    result = trials.external_grade({}, tmp_path, Path("python"), frozenset({"case"}), output=tmp_path / "grading")
    assert result["status"] == "harness_error" and "refusing to overwrite" in result["error"]
    assert captured.read_bytes() == b"previous attempt"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows native collection integration")
def test_collection_captures_new_files_and_checks_protected_inputs(tmp_path):
    contents = {"code.py": b"after\n", "protected.json": b"{}\n", "tests/control.py": b"test\n"}
    workspace = tmp_path / "workspace"
    for name, content in contents.items():
        target = workspace / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    inputs = {"code.py": b"before\n", "protected.json": b"old\n"}
    output = tmp_path / "output"
    output.mkdir()
    submission, changes, violations, errors = trials.collect_submission(
        workspace,
        output,
        inputs,
        {
            "task": {"files": list(inputs), "allowed_changes": ["code.py", "tests/"]},
            "input_sha256": {name: trials.sha256(data) for name, data in inputs.items()},
            "collection_policy": default_collection_policy(),
        },
    )
    assert changes == ["code.py", "protected.json"]
    assert violations == ["protected source input changed: protected.json"]
    assert errors == []
    assert {name: (submission / name).read_bytes() for name in contents} == contents
    assert "-before\n+after\n" in (output / "patch.diff").read_text(encoding="utf-8")


@pytest.mark.parametrize("error_type", ["ValueError", "OSError"])
def test_collection_failures_are_recorded_without_copying_rejected_files(tmp_path, monkeypatch, error_type):
    def reject(*args, **kwargs):
        return {"collection_version": 1, "status": "collection_error", "error_type": error_type}

    monkeypatch.setattr(trials, "capture_owned", reject)
    output = tmp_path / "output"
    output.mkdir()
    submission, _, _, errors = trials.collect_submission(
        tmp_path, output, {"code.py": b"before"}, {"collection_policy": default_collection_policy()}
    )
    assert errors == ["source collection did not complete"]
    assert not submission.exists()
    assert json.loads((output / "workspace-changes.json").read_bytes()) == {
        "complete": False,
        "changes": [],
        "diagnostic_patch": None,
    }


@pytest.mark.parametrize("writable", [True, False])
@pytest.mark.skipif(sys.platform != "win32", reason="Windows native collection integration")
def test_scaffolding_permissions_are_checked_against_the_declared_original(tmp_path, writable):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "helper.txt").write_bytes(b"modified\n")
    output = tmp_path / "output"
    output.mkdir()
    _, changes, violations, errors = trials.collect_submission(
        workspace,
        output,
        {},
        {
            "task": {"files": [], "allowed_changes": ["helper.txt"] if writable else []},
            "input_sha256": {},
            "collection_policy": default_collection_policy(),
            "workspace_scaffold": {"helper.txt": "original\n"},
        },
    )
    assert changes == [] and errors == []
    assert violations == ([] if writable else ["protected scaffold changed: helper.txt"])


def test_scaffolding_keeps_declared_utf8_bytes_without_host_newline_conversion(tmp_path, monkeypatch):
    monkeypatch.setattr(trials, "ROOT", tmp_path)
    monkeypatch.setattr(trials, "pinned_file", lambda *args: b"source")
    (tmp_path / "grader.py").write_bytes(b"grader")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    protocol = {
        "task": {"files": ["code.py"], "source_commit": "a" * 40, "grader": "grader.py", "brief": "owned"},
        "input_sha256": {"code.py": trials.sha256(b"source")},
        "grader_sha256": trials.sha256(b"grader"),
        "conditions": {"default": {"skills": []}},
        "workspace_scaffold": {"helper.txt": "first\nsecond\n"},
        "prompt_template": "<TASK_BRIEF> <PYTHON_RUNTIME>",
    }
    trials.prepare(protocol, "default", tmp_path / "python", workspace=workspace)
    assert (workspace / "helper.txt").read_bytes() == b"first\nsecond\n"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows native collection integration")
def test_native_collection_rejects_a_hardlink_before_copying_any_source(tmp_path):
    import os

    workspace, output = tmp_path / "workspace", tmp_path / "output"
    workspace.mkdir()
    output.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"private control\n")
    os.link(outside, workspace / "code.py")
    (workspace / "action-log.json").write_bytes(b"{}\n")
    submission, _, _, errors = trials.collect_submission(
        workspace,
        output,
        {"code.py": b"original\n"},
        {
            "task": {"allowed_changes": ["code.py"]},
            "workspace_scaffold": {"action-log.json": ""},
            "collection_policy": default_collection_policy(),
        },
    )
    assert errors == ["source collection did not complete"]
    assert not submission.exists()
    assert outside.read_bytes() == b"private control\n"


def test_invalid_trial_stream_is_recorded_without_grading(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    protocol = {
        **declared_fixture(),
        "protocol_version": 4,
        "execution_source_sha256": trials.execution_source_hashes(),
        "runner_sha256": trials.sha256((trials.ROOT / "tools/run_agent_trial.py").read_bytes()),
        "grading_driver_sha256": trials.sha256((trials.ROOT / "tools/grade_agent_submission.py").read_bytes()),
        "transcript_parser_sha256": trials.sha256((trials.ROOT / "tools/_trial_transcript.py").read_bytes()),
        "trial_manifest_sha256": trials.sha256((trials.ROOT / "tools/_trial_manifest.py").read_bytes()),
        "grader_sha256": "a" * 64,
        "grading_cases_sha256": _trial_manifest.case_digest(["independent"]),
        "model": "fixture-model",
        "reasoning_effort": "high",
        "time_limit_seconds": 10,
        "limitations": [],
    }
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
    protocol_path.with_name("protocol.grading.json").write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "protocol_sha256": trials.sha256(protocol_path.read_bytes()),
                "grader_sha256": protocol["grader_sha256"],
                "cases": ["independent"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(trials, "prepare", lambda *args, **kwargs: (workspace, "fixture", {}))
    monkeypatch.setattr(trials, "command", lambda *args: ["fixture"])
    monkeypatch.setattr(trials, "require_qualified_trial_execution", lambda: None)

    def unexpected_grade(*args):
        raise AssertionError("invalid transcript must not be graded")

    monkeypatch.setattr(trials, "external_grade", unexpected_grade)

    context = TrialContext(tmp_path / "controller", workspace, Path("fixture"), Path("python"), (), {}, {})
    monkeypatch.setattr(trials, "temporary_home", lambda: tmp_path / "private-cache/private")

    def isolated_context(home, *args):
        assert home.is_relative_to(tmp_path / "private-cache")
        assert not home.is_relative_to(tmp_path / "attempt")
        return context

    monkeypatch.setattr(trials, "create_context", isolated_context)
    monkeypatch.setattr(trials, "read_workspace_file", lambda root, name, **kwargs: (root / name).read_bytes())

    def invalid_stream(*args, stdout, **kwargs):
        stdout.write(b'{"type":"turn.started"}\nnot-json\n{"type":"turn.completed"}\n')
        return {"exit_code": 0, "termination_reason": None, "job_active_processes_after_cleanup": 0}

    monkeypatch.setattr(trials, "run_owned", invalid_stream)
    output = tmp_path / "attempt"
    result = trials.run(protocol_path, "default", output, Path("fixture"), Path("python"))
    assert result["status"] == "harness_error"
    assert result["transcript_error"] == "transcript contains an invalid event on line 2"
    assert result["usage"] is None and result["commands_completed"] is None
    assert result["grader"]["status"] == "harness_error"
    summary.verify_transcript(output, result)


def test_unqualified_execution_stops_before_workspace_or_process_creation(tmp_path, monkeypatch):
    """An unqualified trial must stop before creating a workspace or agent process."""
    protocol = {
        **declared_fixture(),
        "protocol_version": 4,
        "execution_source_sha256": trials.execution_source_hashes(),
        "runner_sha256": trials.sha256((trials.ROOT / "tools/run_agent_trial.py").read_bytes()),
        "grading_driver_sha256": trials.sha256((trials.ROOT / "tools/grade_agent_submission.py").read_bytes()),
        "transcript_parser_sha256": trials.sha256((trials.ROOT / "tools/_trial_transcript.py").read_bytes()),
        "trial_manifest_sha256": trials.sha256((trials.ROOT / "tools/_trial_manifest.py").read_bytes()),
        "grader_sha256": "a" * 64,
        "grading_cases_sha256": _trial_manifest.case_digest(["case"]),
    }
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
    protocol_path.with_name("protocol.grading.json").write_text(
        json.dumps(
            {
                "manifest_version": 1,
                "protocol_sha256": trials.sha256(protocol_path.read_bytes()),
                "grader_sha256": protocol["grader_sha256"],
                "cases": ["case"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(trials, "prepare", lambda *args: pytest.fail("unexpected workspace creation"))
    monkeypatch.setattr(trials, "_run_controller", lambda *args, **kwargs: pytest.fail("unexpected lifecycle entry"))
    monkeypatch.setattr(trials.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("unexpected process"))
    output = tmp_path / "attempt"
    with pytest.raises(RuntimeError, match="integrated runner.*not been independently qualified"):
        trials.run(protocol_path, "default", output, Path("fixture"), Path("python"))
    assert not output.exists()


@pytest.mark.parametrize("problem", ["missing", "changed", "legacy"])
def test_uncommitted_grading_cases_stop_before_a_trial_launch(tmp_path, monkeypatch, problem):
    """Reject missing or changed case commitments without starting a process."""
    protocol = {
        "protocol_version": 2 if problem == "legacy" else 4,
        "execution_source_sha256": trials.execution_source_hashes(),
        "runner_sha256": trials.sha256((trials.ROOT / "tools/run_agent_trial.py").read_bytes()),
        "grading_driver_sha256": trials.sha256((trials.ROOT / "tools/grade_agent_submission.py").read_bytes()),
        "transcript_parser_sha256": trials.sha256((trials.ROOT / "tools/_trial_transcript.py").read_bytes()),
        "trial_manifest_sha256": trials.sha256((trials.ROOT / "tools/_trial_manifest.py").read_bytes()),
        "grader_sha256": "a" * 64,
        "grading_cases_sha256": _trial_manifest.case_digest(["expected"]),
    }
    protocol_path = tmp_path / "protocol.json"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
    if problem == "changed":
        protocol_path.with_name("protocol.grading.json").write_text(
            json.dumps(
                {
                    "manifest_version": 1,
                    "protocol_sha256": trials.sha256(protocol_path.read_bytes()),
                    "grader_sha256": protocol["grader_sha256"],
                    "cases": ["different"],
                }
            ),
            encoding="utf-8",
        )
    monkeypatch.setattr(trials.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("unexpected process"))
    with pytest.raises(ValueError, match="grading manifest|committed"):
        trials.run(protocol_path, "default", tmp_path / "attempt", Path("fixture"), Path("python"))
    assert not (tmp_path / "attempt").exists()


def test_ambiguous_protocol_is_rejected_before_trial_launch(tmp_path, monkeypatch):
    """Duplicate protocol keys are rejected before any agent process starts."""
    path = tmp_path / "protocol.json"
    path.write_text('{"protocol_version": 3, "protocol_version": 3}', encoding="utf-8")
    monkeypatch.setattr(trials.subprocess, "Popen", lambda *args, **kwargs: pytest.fail("unexpected process"))
    with pytest.raises(ValueError, match="duplicate JSON key"):
        trials.run(path, "default", tmp_path / "attempt", Path("fixture"), Path("python"))
    assert not (tmp_path / "attempt").exists()


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

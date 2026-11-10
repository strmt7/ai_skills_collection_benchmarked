"""Setup failure records are counted without executing a model or inventing its usage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import run_agent_trial as trials
import summarize_agent_trials as summary
from _trial_collection_policy import default_collection_policy
from _trial_context import TrialContext
from _trial_manifest import case_digest


@pytest.fixture
def frozen(tmp_path, monkeypatch):
    protocol: dict[str, Any] = {
        "collection_policy": default_collection_policy(),
        "protocol_version": 4,
        "task": {
            "id": "owned-setup-control",
            "partition": "development",
            "brief": "Independent fixture.",
            "files": ["code.py"],
            "allowed_changes": [],
            "source_commit": "a" * 40,
            "grader": "tools/grade.py",
        },
        "input_sha256": {"code.py": "b" * 64},
        "prompt_template": "<TASK_BRIEF> Use <PYTHON_RUNTIME>.",
        "conditions": {"default": {"skills": []}},
        "planned_order": [{"repetition": 1, "conditions": ["default"]}],
        "model": "fixture-model",
        "reasoning_effort": "high",
        "time_limit_seconds": 10,
        "limitations": [],
        "execution_source_sha256": trials.execution_source_hashes(),
        "grader_sha256": "c" * 64,
        "grading_cases_sha256": case_digest(["independent-case"]),
        **{
            key: trials.sha256((trials.ROOT / "tools" / name).read_bytes())
            for key, name in (
                ("runner_sha256", "run_agent_trial.py"),
                ("grading_driver_sha256", "grade_agent_submission.py"),
                ("transcript_parser_sha256", "_trial_transcript.py"),
                ("trial_manifest_sha256", "_trial_manifest.py"),
            )
        },
    }
    path = tmp_path / "protocol.json"
    path.write_text(json.dumps(protocol), encoding="utf-8")
    digest = trials.sha256(path.read_bytes())
    path.with_name("protocol.grading.json").write_text(
        json.dumps(
            {"manifest_version": 1, "protocol_sha256": digest, "grader_sha256": "c" * 64, "cases": ["independent-case"]}
        ),
        encoding="utf-8",
    )
    # Qualification refusal is replaced only for synthetic controller-unit tests.
    # Any actual model process remains a test failure.
    monkeypatch.setattr(trials, "require_qualified_trial_execution", lambda: None)
    monkeypatch.setattr(trials, "run_owned", lambda *args, **kwargs: pytest.fail("unexpected model process"))
    monkeypatch.setattr(trials, "external_grade", lambda *args, **kwargs: pytest.fail("unexpected grading"))
    monkeypatch.setattr(
        trials,
        "native_path",
        lambda selected: tmp_path / "cache" if selected == trials.ROOT / ".venv/agent-trial-contexts" else selected,
    )
    monkeypatch.setattr(trials, "read_workspace_file", lambda root, name, **kwargs: (root / name).read_bytes())
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.setattr(trials.tempfile, "mkdtemp", lambda **kwargs: str(workspace))
    monkeypatch.setattr(trials, "prepare", lambda *args, **kwargs: (kwargs["workspace"], "owned fixture", {}))
    monkeypatch.setattr(
        trials,
        "create_context",
        lambda home, work, *args: TrialContext(home, work, Path("fixture"), Path("python"), (), {}, {}),
    )
    monkeypatch.setattr(trials, "command", lambda *args: ["fixture"])
    output = tmp_path / "trials/repetition-1/default"
    return path, protocol, digest, output


def test_explicit_empty_credentials_cannot_fall_back_to_the_parent_environment(frozen, monkeypatch):
    path, protocol, _, output = frozen
    protocol["provider"] = {"base_url": "http://127.0.0.1:8041/v1", "credential_env": "TRIAL_CREDENTIAL"}
    path.write_text(json.dumps(protocol), encoding="utf-8")
    digest = trials.sha256(path.read_bytes())
    path.with_name("protocol.grading.json").write_text(
        json.dumps(
            {"manifest_version": 1, "protocol_sha256": digest, "grader_sha256": "c" * 64, "cases": ["independent-case"]}
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("TRIAL_CREDENTIAL", "parent-only fixture value")
    result = trials._run_controller(path, "default", output, Path("fixture"), Path("python"), credential_source={})
    assert result["attempt_phase"] == "setup_failed" and result["status"] == "harness_error"
    assert result["usage"] is None and result["process_exit_code"] is None
    error = json.loads((output / "setup-error.json").read_bytes())
    assert error["stage"] == "context" and error["error_type"] == "ValueError"
    assert "parent-only fixture value" not in json.dumps(result)
    summary.verify_result(output, protocol, digest, "default", frozenset({"independent-case"}))


@pytest.mark.parametrize("stage", ["workspace", "prepare", "context", "prompt", "command", "launch_record"])
def test_prelaunch_errors_leave_verifiable_unscored_results(frozen, monkeypatch, stage):
    path, protocol, digest, output = frozen
    original_write = trials.write_json

    def fail(*args, **kwargs):
        raise OSError(5, "SYNTHETIC_PRIVATE_MARKER must not enter published diagnostics")

    if stage == "workspace":
        monkeypatch.setattr(trials.tempfile, "mkdtemp", fail)
    elif stage == "launch_record":

        def write(target, value):
            return fail() if target.name == "launch.json" else original_write(target, value)

        monkeypatch.setattr(trials, "write_json", write)
    elif stage == "prompt":
        original_text = Path.write_text

        def write_text(target, *args, **kwargs):
            return fail() if target.name == "prompt.txt" else original_text(target, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", write_text)
    else:
        monkeypatch.setattr(trials, "create_context" if stage == "context" else stage, fail)
    result = trials.run(path, "default", output, Path("fixture"), Path("python"))
    assert result["status"] == "harness_error" and result["attempt_phase"] == "setup_failed"
    assert result["usage"] is None and result["process_exit_code"] is None
    error = json.loads((output / "setup-error.json").read_bytes())
    assert error == {"stage": stage, "error_type": "OSError", "errno": 5, "winerror": None}
    assert "SYNTHETIC_PRIVATE_MARKER" not in (output / "setup-error.json").read_text()
    verified, runtime = summary.verify_result(output, protocol, digest, "default", frozenset({"independent-case"}))
    assert verified == result and runtime == ("unavailable", None)
    report = summary.summarize(path, output.parents[1])
    assert report["completed_attempts"] == 1
    assert report["conditions"]["default"]["status_counts"]["harness_error"] == 1
    assert report["prompt_runtime_evidence"]["unavailable_attempts"] == 1
    assert "Executed prompt evidence is unavailable for 1 infrastructure-failed attempt." in summary.render(report)


def test_setup_failure_cannot_be_relabelled_after_a_launch_capture(frozen, monkeypatch):
    path, protocol, digest, output = frozen

    def fail(*args, **kwargs):
        raise RuntimeError("owned setup control")

    monkeypatch.setattr(trials, "create_context", fail)
    trials.run(path, "default", output, Path("fixture"), Path("python"))
    (output / "transcript.jsonl").write_bytes(b"")
    with pytest.raises(ValueError, match="model launch attempt"):
        summary.verify_result(output, protocol, digest, "default", frozenset({"independent-case"}))


def test_setup_failure_cannot_invent_zero_usage(frozen, monkeypatch):
    path, protocol, digest, output = frozen

    def fail(*args, **kwargs):
        raise RuntimeError("owned setup control")

    monkeypatch.setattr(trials, "create_context", fail)
    result = trials.run(path, "default", output, Path("fixture"), Path("python"))
    result["usage"] = {"input_tokens": 0, "output_tokens": 0}
    (output / "result.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError, match="invented usage"):
        summary.verify_result(output, protocol, digest, "default", frozenset({"independent-case"}))


@pytest.mark.parametrize("change", ["phase", "condition", "stage", "errno", "grader"])
def test_rehashing_failure_metadata_cannot_hide_contradictions(frozen, monkeypatch, change):
    path, protocol, digest, output = frozen

    def fail(*args, **kwargs):
        raise RuntimeError("owned setup control")

    monkeypatch.setattr(trials, "create_context", fail)
    result = trials.run(path, "default", output, Path("fixture"), Path("python"))
    if change == "grader":
        result["grader"]["checks_passed"] = 1
    else:
        filename = "setup-error.json" if change in {"errno", "stage"} else "attempt.json"
        value = json.loads((output / filename).read_bytes())
        value[change] = True if change == "errno" else "different"
        (output / filename).write_text(json.dumps(value), encoding="utf-8")
        result["evidence_sha256"][filename] = summary.sha256(output / filename)
    (output / "result.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError):
        summary.verify_result(output, protocol, digest, "default", frozenset({"independent-case"}))


def test_cancellation_leaves_unresolved_state_without_a_fabricated_result(frozen, monkeypatch):
    path, _, _, output = frozen

    def cancel(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(trials, "create_context", cancel)
    with pytest.raises(KeyboardInterrupt):
        trials.run(path, "default", output, Path("fixture"), Path("python"))
    state = json.loads((output / "attempt.json").read_bytes())
    assert state["phase"] == "setup" and state["stage"] == "context"
    assert state["model_launch_attempted"] is False and not (output / "result.json").exists()
    with pytest.raises(ValueError, match="planned attempt has not completed"):
        summary.summarize(path, output.parents[1])
    with pytest.raises(ValueError, match="refusing to overwrite"):
        trials.run(path, "default", output, Path("fixture"), Path("python"))


def test_failed_terminal_storage_is_not_reported_as_successful_accounting(frozen, monkeypatch):
    path, _, _, output = frozen
    original = trials.write_json

    def fail(*args, **kwargs):
        raise RuntimeError("owned setup control")

    def write(target, value):
        if target.name == "setup-error.json":
            raise OSError("owned storage failure")
        return original(target, value)

    monkeypatch.setattr(trials, "create_context", fail)
    monkeypatch.setattr(trials, "write_json", write)
    with pytest.raises(OSError, match="storage failure"):
        trials.run(path, "default", output, Path("fixture"), Path("python"))
    assert not (output / "result.json").exists()
    with pytest.raises(ValueError, match="planned attempt has not completed"):
        summary.summarize(path, output.parents[1])


@pytest.fixture
def controller_run(frozen, monkeypatch):
    """Synthetic controller only: model and grading launchers remain forbidden."""
    path, protocol, digest, output = frozen

    def executed(invocation, prompt, destination, *args, **kwargs):
        (destination / "input.native").write_bytes(prompt.encode())
        (destination / "transcript.jsonl").write_bytes(
            b'{"type":"turn.completed","usage":{"input_tokens":4,"cached_input_tokens":0,"output_tokens":2}}\n'
        )
        (destination / "stderr.txt").write_bytes(b"")
        trials.write_json(destination / "process.json", {"synthetic_unit_control": True})
        return 0, False, 0.1

    def collected(workspace, destination, *args, **kwargs):
        (destination / "patch.diff").write_bytes(b"")
        (destination / "collection").mkdir()
        trials.write_json(destination / "collection/result.json", {"status": "collection_error"})
        return destination / "submission", [], [], []

    def graded(*args, **kwargs):
        for stream in ("stdout", "stderr"):
            (output / f"grading.driver.{stream}.native").write_bytes(b"")
        return {"status": "harness_error", "error": "synthetic unit control"}

    monkeypatch.setattr(trials, "execute_agent", executed)
    monkeypatch.setattr(trials, "collect_submission", collected)
    monkeypatch.setattr(trials, "external_grade", graded)
    return path, protocol, digest, output


@pytest.mark.parametrize("stage", ["agent", "transcript", "submission", "grader", "evidence", "result"])
def test_postsetup_controller_failures_remain_counted_without_invented_measurements(controller_run, monkeypatch, stage):
    path, protocol, digest, output = controller_run
    original_write = trials.write_json
    failed_once = False

    def fail(*args, **kwargs):
        raise OSError(5, "PRIVATE_CONTROLLER_MESSAGE must not be published")

    if stage == "result":

        def write(target, value):
            nonlocal failed_once
            if target.name == "result.json" and target.parent == output and not failed_once:
                failed_once = True
                return fail()
            return original_write(target, value)

        monkeypatch.setattr(trials, "write_json", write)
    else:
        monkeypatch.setattr(
            trials,
            {
                "agent": "execute_agent",
                "transcript": "read_events",
                "submission": "collect_submission",
                "grader": "external_grade",
                "evidence": "grading_evidence",
            }[stage],
            fail,
        )
    result = trials.run(path, "default", output, Path("fixture"), Path("python"))
    assert result["status"] == "harness_error" and result["attempt_phase"] == "controller_failed"
    expected_usage = None if stage == "agent" else {"input_tokens": 4, "cached_input_tokens": 0, "output_tokens": 2}
    assert result["usage"] == expected_usage and result["process_exit_code"] is None
    assert result["commands_completed"] == (None if stage == "agent" else 0)
    error = json.loads((output / "controller-error.json").read_bytes())
    assert error == {"stage": stage, "error_type": "OSError", "errno": 5, "winerror": None}
    assert "PRIVATE_CONTROLLER_MESSAGE" not in (output / "controller-error.json").read_text()
    verified, runtime = summary.verify_result(output, protocol, digest, "default", frozenset({"independent-case"}))
    assert verified == result and runtime == ("unavailable", None)
    report = summary.summarize(path, output.parents[1])
    assert report["completed_attempts"] == 1
    assert report["conditions"]["default"]["status_counts"]["harness_error"] == 1
    assert report["conditions"]["default"]["usage_unavailable_attempts"] == (1 if stage == "agent" else 0)


@pytest.fixture
def failed_controller(controller_run, monkeypatch):
    path, protocol, digest, output = controller_run

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic controller failure")

    monkeypatch.setattr(trials, "external_grade", fail)
    result = trials.run(path, "default", output, Path("fixture"), Path("python"))
    return protocol, digest, output, result


@pytest.mark.parametrize(
    "change", ["usage", "exit", "commands", "error", "stage", "phase", "workspace", "launch", "errno", "score"]
)
def test_controller_failure_cannot_invent_measurements_or_hide_lifecycle_contradictions(failed_controller, change):
    protocol, digest, output, result = failed_controller
    if change == "usage":
        result["usage"] = None
    elif change == "exit":
        result["process_exit_code"] = 0
    elif change == "commands":
        result["commands_completed"] = False
    elif change == "error":
        result["transcript_error"] = "invented parser error"
    elif change == "score":
        result["grader"]["checks_passed"] = 1
    else:
        name = "controller-error.json" if change in {"stage", "errno"} else "attempt.json"
        data = json.loads((output / name).read_bytes())
        key, value = {
            "stage": ("stage", "unknown"),
            "phase": ("phase", "setup_failed"),
            "workspace": ("workspace", None),
            "launch": ("model_launch_attempted", False),
            "errno": ("errno", True),
        }[change]
        data[key] = value
        (output / name).write_text(json.dumps(data), encoding="utf-8")
        result["evidence_sha256"][name] = summary.sha256(output / name)
    (output / "result.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError):
        summary.verify_result(output, protocol, digest, "default", frozenset({"independent-case"}))


def test_failure_rejects_grader_scratch_inventory_before_opening_it(failed_controller, monkeypatch):
    protocol, digest, output, result = failed_controller
    result["evidence_sha256"]["grading/scratch/private.txt"] = "a" * 64
    (output / "result.json").write_text(json.dumps(result), encoding="utf-8")
    monkeypatch.setattr(
        summary, "evidence_bytes", lambda *args: pytest.fail("no evidence read before inventory admission")
    )
    with pytest.raises(ValueError, match="inventory"):
        summary.verify_result(output, protocol, digest, "default", frozenset({"independent-case"}))


def test_controller_cancellation_remains_unresolved_without_a_fabricated_result(controller_run, monkeypatch):
    path, _, _, output = controller_run

    def cancel(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(trials, "external_grade", cancel)
    with pytest.raises(KeyboardInterrupt):
        trials.run(path, "default", output, Path("fixture"), Path("python"))
    state = json.loads((output / "attempt.json").read_bytes())
    assert state["phase"] == "grading" and state["model_launch_attempted"] is True
    assert not (output / "result.json").exists()
    with pytest.raises(ValueError, match="planned attempt has not completed"):
        summary.summarize(path, output.parents[1])


def test_failed_controller_error_storage_is_not_counted_as_terminal_success(controller_run, monkeypatch):
    path, _, _, output = controller_run
    original = trials.write_json

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic grader controller failure")

    def write(target, value):
        if target.name == "controller-error.json":
            raise OSError("synthetic recording failure")
        return original(target, value)

    monkeypatch.setattr(trials, "external_grade", fail)
    monkeypatch.setattr(trials, "write_json", write)
    with pytest.raises(OSError, match="recording failure"):
        trials.run(path, "default", output, Path("fixture"), Path("python"))
    assert not (output / "result.json").exists()
    with pytest.raises(ValueError, match="planned attempt has not completed"):
        summary.summarize(path, output.parents[1])

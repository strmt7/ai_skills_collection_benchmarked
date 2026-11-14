"""Synthetic unit controls forbid native processes while testing attempt accounting."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import run_swe_skills_trial as trials
from _native_benchmark_runtime import sha256
from _subject_toolchains import load_toolchains
from _trial_context import TrialContext
from prepare_subject_dependencies import inventory


@pytest.fixture
def attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(trials, "ROOT", tmp_path)
    plan_path = tmp_path / "plan.json"
    plan_path.write_bytes(b"frozen native attempt")
    plan = {
        "schema_version": 1,
        "id": "independent-unit",
        "condition": "default",
        "partition": "development",
        "model": "local-unit-fixture",
        "reasoning_effort": "high",
        "time_limit_seconds": 1,
        "provider": {"base_url": "http://127.0.0.1:8041/v1", "credential_env": "NATIVE_FIXTURE"},
        "execution_source_sha256": {"unit": "frozen"},
        "subject_runtime": {},
        "grader_runtime": {},
    }
    task = {"id": "original-author-task", "image_reference": "frozen-image", "collection_policy": {}}
    parent = tmp_path / "subject"
    parent.mkdir()
    state: dict[str, Any] = {
        "grade_calls": 0,
        "collection_calls": 0,
        "exit_code": 0,
        "termination_reason": None,
        "stopped": 0,
        "completed": True,
        "cancel": False,
    }
    admitted = {
        "plan": plan,
        "plan_raw": plan_path.read_bytes(),
        "plan_sha256": sha256(plan_path.read_bytes()),
        "task": task,
        "runtime": {"cli": Path("fixture-cli"), "python": Path("fixture-python"), "roots": ()},
        "before": b"manifest",
        "tree": tmp_path / "baseline-tree",
        "baseline": tmp_path / "baseline",
        "prompt": "independent task",
        "grader_runtime": tmp_path / "grader.json",
    }
    monkeypatch.setattr(trials, "load_plan", lambda path: admitted)
    monkeypatch.setattr(trials, "execution_sources", lambda: {"unit": "frozen"})
    monkeypatch.setattr(trials, "subject_runtime", lambda entry: None)
    monkeypatch.setattr(trials, "archive_sources", lambda *args: None)
    monkeypatch.setattr(trials, "DockerClient", lambda *args: SimpleNamespace(reference="frozen-image"))
    monkeypatch.setattr(trials, "plan_handoff", lambda *args: None)
    monkeypatch.setattr(trials, "seal", lambda *args: {"archive_sha256": "a" * 64})
    monkeypatch.setattr(trials, "restore", lambda *args: {})
    monkeypatch.setattr(trials, "verify_initial_workspace", lambda *args: None)
    monkeypatch.setattr(trials.tempfile, "mkdtemp", lambda **kwargs: str(parent))
    monkeypatch.setattr(
        trials,
        "create_context",
        lambda home, workspace, cli, python, roots: TrialContext(home, workspace, cli, python, roots, {}, {}),
    )
    monkeypatch.setattr(trials, "command", lambda *args, **kwargs: ["forbidden-process-fixture"])
    monkeypatch.setattr(trials, "asset", lambda entry: b"frozen")
    monkeypatch.setattr(trials, "input_assets", lambda plan, runtime=None: {"fixture.json": {}})

    def execute(invocation, prompt, output, timeout, *, context, **resource_options):
        state["prompt"] = prompt
        state["context"] = context
        state["resource_options"] = resource_options
        assert context.controller_environment["NATIVE_FIXTURE"] == "owned fixture credential"
        if state["cancel"]:
            raise KeyboardInterrupt
        if "space_budget" in resource_options:
            resource_options["space_budget"].require_available()
        trials.write_json(
            output / "process.json",
            {
                "windows_job": True,
                "assigned_before_resume": True,
                "kill_on_close": True,
                "job_active_processes_after_cleanup": state["stopped"],
                "termination_reason": state["termination_reason"],
                **(
                    {"space_budget": resource_options["space_budget"].record()}
                    if "space_budget" in resource_options
                    else {}
                ),
                **(
                    {
                        "write_io_limit_bytes": resource_options["write_io_limit"],
                        "job_write_io_bytes": 100,
                        "write_io_overshoot_bytes": 0,
                        "write_io_observation_error": None,
                        "write_io_enforcement": "polled_job_transfer_accounting",
                        "hard_storage_quota": False,
                    }
                    if "write_io_limit" in resource_options
                    else {}
                ),
            },
        )
        (output / "transcript.jsonl").write_text(
            '{"type":"turn.completed","usage":{"input_tokens":2,"output_tokens":1}}\n'
            if state["completed"]
            else '{"type":',
            encoding="utf-8",
        )
        (output / "stderr.txt").write_bytes(b"")
        return state["exit_code"], state["termination_reason"] == "timeout", 0.1

    def capture(workspace, submission, observations, python, policy):
        assert "NATIVE_FIXTURE" not in state["context"].controller_environment
        state["collection_calls"] += 1
        observations.mkdir()
        trials.write_json(observations / "result.json", {"status": "collected"})
        return {"status": "collected"}

    def grade(task, runtime, baseline, collection, output):
        state["grade_calls"] += 1
        output.mkdir()
        result = {
            "status": "task_failed",
            "score": 0.5,
            "native_counts": {"passed": 2, "total": 4},
            "stage": "complete",
        }
        trials.write_json(output / "result.json", result)
        return result

    monkeypatch.setattr(trials, "execute_agent", execute)
    monkeypatch.setattr(trials, "capture_owned", capture)
    monkeypatch.setattr(trials, "grade", grade)
    return plan_path, tmp_path / ".venv/attempt", state


def invoke(attempt):
    path, output, _ = attempt
    return trials._run_controller(path, output, credential_source={"NATIVE_FIXTURE": "owned fixture credential"})


def test_native_fraction_and_denominator_are_preserved(attempt):
    result = invoke(attempt)
    assert result["status"] == "task_failed" and result["score"] == 0.5
    assert result["native_counts"] == {"passed": 2, "total": 4}
    assert attempt[2]["grade_calls"] == 1
    assert "NATIVE_FIXTURE" not in attempt[2]["context"].controller_environment
    assert "owned fixture credential" not in json.dumps(result)


@pytest.mark.parametrize("drift", [False, True])
def test_native_toolchains_need_no_python_dependencies_and_drift_forbids_grading(attempt, tmp_path, monkeypatch, drift):
    root = tmp_path / "native tools"
    root.mkdir()
    binary = root / "node.exe"
    binary.write_bytes(b"frozen native tool fixture")
    raw = json.dumps(
        {
            "schema_version": 1,
            "toolchains": [
                {
                    "name": "node",
                    "version": "26.13.1",
                    "root": str(root),
                    "files": {"node.exe": {"bytes": binary.stat().st_size, "sha256": sha256(binary.read_bytes())}},
                    "directories": [],
                    "commands": {"node": ["node.exe"]},
                }
            ],
        }
    ).encode()
    manifest = tmp_path / "toolchains.json"
    manifest.write_bytes(raw)
    admitted = load_toolchains({"path": str(manifest), "sha256": sha256(raw)})
    load = trials.load_plan

    def with_tools(path):
        value = load(path)
        value["runtime"].update(toolchains=admitted, roots=admitted.roots())
        return value

    execute = trials.execute_agent

    def subject(*args, **kwargs):
        assert root in kwargs["context"].readable_roots
        result = execute(*args, **kwargs)
        if drift:
            binary.write_bytes(b"changed native tool fixture")
        return result

    monkeypatch.setattr(trials, "load_plan", with_tools)
    monkeypatch.setattr(trials, "execute_agent", subject)
    result = invoke(attempt)
    assert json.dumps(str(binary)) in attempt[2]["prompt"]
    assert result["status"] == ("harness_error" if drift else "task_failed")
    assert result["score"] == (None if drift else 0.5)
    assert attempt[2]["grade_calls"] == (0 if drift else 1)


@pytest.mark.parametrize("stopped", [1, False, None])
def test_unproven_subject_stop_forbids_collection_and_grading(attempt, stopped):
    attempt[2]["stopped"] = stopped
    result = invoke(attempt)
    assert result["status"] == "harness_error" and result["score"] is None
    assert attempt[2]["collection_calls"] == attempt[2]["grade_calls"] == 0


@pytest.mark.parametrize("failure", ["incomplete", "resource_limit"])
def test_stopped_but_incomplete_execution_is_collected_without_a_score(attempt, failure):
    state = attempt[2]
    if failure == "incomplete":
        state.update(exit_code=1, completed=False)
    else:
        state["termination_reason"] = "output_limit"
    result = invoke(attempt)
    assert result["status"] == "harness_error" and result["score"] is None
    assert state["collection_calls"] == 1 and state["grade_calls"] == 0


def test_cancellation_releases_credentials_without_a_completed_result(attempt):
    attempt[2]["cancel"] = True
    with pytest.raises(KeyboardInterrupt):
        invoke(attempt)
    assert "NATIVE_FIXTURE" not in attempt[2]["context"].controller_environment
    assert not (attempt[1] / "result.json").exists()
    assert json.loads((attempt[1] / "attempt.json").read_bytes())["stage"] == "agent"


def test_public_native_runner_keeps_the_model_gate_closed(tmp_path):
    with pytest.raises(RuntimeError, match="Model trials are unavailable"):
        trials.run(tmp_path / "missing-plan", tmp_path / "untouched")
    assert not (tmp_path / "untouched").exists()


@pytest.fixture
def storage_attempt(attempt, monkeypatch):
    import _windows_storage_budget as storage

    load = trials.load_plan

    def budgeted(path):
        admitted = load(path)
        admitted["plan"].update(
            schema_version=3,
            write_io_limit_bytes=65536,
            storage_limits={"min_free_bytes": 10, "max_workspace_bytes": 1024, "max_workspace_entries": 100},
        )
        return admitted

    monkeypatch.setattr(trials, "load_plan", budgeted)
    monkeypatch.setattr(storage, "checked_path", lambda path: path)
    monkeypatch.setattr(
        storage,
        "available_space",
        lambda _path: {"available_bytes": 1000, "total_bytes": 2000, "volume_free_bytes": 1000},
    )
    attempt[2]["storage_calls"] = []

    def measured(workspace, _limits):
        attempt[2]["storage_calls"].append(workspace)
        return {
            "complete": True,
            "logical_bytes": 0,
            "entries": 0,
            "files": 0,
            "directories": 0,
            "streams": 0,
            "measurement": "stopped_workspace_data_stream_lengths",
        }

    monkeypatch.setattr(trials, "measure_workspace", measured)
    return attempt


def test_storage_plan_checks_initial_and_stopped_workspaces_and_records_monitors(storage_attempt):
    result = invoke(storage_attempt)
    assert result["status"] == "task_failed" and result["score"] == 0.5
    assert len(storage_attempt[2]["storage_calls"]) == 2
    assert set(storage_attempt[2]["resource_options"]) == {"write_io_limit", "space_budget"}
    for name in ("initial-storage.json", "final-storage.json", "setup-space.json"):
        assert name in result["evidence_sha256"] and (storage_attempt[1] / name).is_file()


def test_insufficient_storage_preflight_prevents_subject_and_grader(storage_attempt, monkeypatch):
    import _windows_storage_budget as storage

    monkeypatch.setattr(
        storage, "available_space", lambda _path: {"available_bytes": 5, "total_bytes": 1000, "volume_free_bytes": 1000}
    )
    result = invoke(storage_attempt)
    assert result["status"] == "harness_error" and result["score"] is None
    assert result["stage"] == "storage_preflight" and "context" not in storage_attempt[2]
    assert storage_attempt[2]["grade_calls"] == 0 and not storage_attempt[2]["storage_calls"]
    retained = json.loads((storage_attempt[1] / "setup-space.json").read_bytes())
    assert retained["termination_reason"] == "free_space_limit"


def test_capacity_lost_during_collection_prevents_grader_start(storage_attempt, monkeypatch):
    import _windows_storage_budget as storage

    monkeypatch.setattr(
        storage,
        "available_space",
        lambda _path: {
            "available_bytes": 5 if storage_attempt[2]["collection_calls"] else 1000,
            "total_bytes": 2000,
            "volume_free_bytes": 1000,
        },
    )
    result = invoke(storage_attempt)
    assert result["status"] == "harness_error" and result["score"] is None
    assert result["stage"] == "grading" and storage_attempt[2]["grade_calls"] == 0


def test_post_subject_logical_limit_failure_is_retained_without_grading(storage_attempt, monkeypatch):
    from _windows_storage_budget import WorkspaceStorageExceeded

    measure = trials.measure_workspace

    def oversized(workspace, limits):
        observation = measure(workspace, limits)
        if len(storage_attempt[2]["storage_calls"]) == 2:
            observation.update(complete=False, logical_bytes=1025)
            raise WorkspaceStorageExceeded("workspace_logical_bytes_limit", observation)
        return observation

    monkeypatch.setattr(trials, "measure_workspace", oversized)
    result = invoke(storage_attempt)
    assert result["status"] == "harness_error" and result["score"] is None
    assert result["stage"] == "final_storage" and storage_attempt[2]["grade_calls"] == 0
    retained = json.loads((storage_attempt[1] / "final-storage.json").read_bytes())
    assert retained["complete"] is False and retained["logical_bytes"] == 1025


def test_incomplete_initial_storage_measurement_cannot_become_a_score(storage_attempt, monkeypatch):
    monkeypatch.setattr(trials, "measure_workspace", lambda *_args: {"complete": False})
    result = invoke(storage_attempt)
    assert result["status"] == "harness_error" and result["score"] is None
    assert result["stage"] == "initial_storage" and "context" not in storage_attempt[2]


@pytest.mark.parametrize("alteration", ["record", "termination"])
def test_inconsistent_process_storage_evidence_prevents_collection(storage_attempt, monkeypatch, alteration):
    execute = trials.execute_agent

    def inconsistent(*args, **kwargs):
        result = execute(*args, **kwargs)
        path = args[2] / "process.json"
        process = json.loads(path.read_bytes())
        if alteration == "record":
            del process["space_budget"]
        else:
            kwargs["space_budget"].reason = "free_space_limit"
            process["space_budget"] = kwargs["space_budget"].record()
        path.write_text(json.dumps(process), encoding="utf-8")
        return result

    monkeypatch.setattr(trials, "execute_agent", inconsistent)
    result = invoke(storage_attempt)
    assert result["status"] == "harness_error" and result["score"] is None
    assert storage_attempt[2]["collection_calls"] == 0 and storage_attempt[2]["grade_calls"] == 0


def test_public_admission_rejects_write_only_plan_before_subject(attempt, monkeypatch):
    load = trials.load_plan

    def write_only(path):
        admitted = load(path)
        admitted["plan"].update(schema_version=2, write_io_limit_bytes=65536)
        return admitted

    monkeypatch.setattr(trials, "load_plan", write_only)
    monkeypatch.setattr(trials, "require_qualified_trial_execution", lambda: None)
    result = trials.run(attempt[0], attempt[1])
    assert result["status"] == "harness_error" and result["score"] is None
    assert result["stage"] == "admission" and "context" not in attempt[2]


def test_changed_input_after_native_grading_withholds_its_score(attempt, monkeypatch):
    def asset(entry):
        if attempt[2]["grade_calls"]:
            raise ValueError("frozen asset changed")
        return b"frozen"

    monkeypatch.setattr(trials, "asset", asset)
    result = invoke(attempt)
    assert attempt[2]["grade_calls"] == 1
    assert result["status"] == "harness_error" and result["score"] is None
    assert (attempt[1] / "grading/result.json").is_file()


def test_initial_recapture_failure_prevents_subject_execution(attempt, monkeypatch):
    def fail(*args):
        raise ValueError("initial collector unavailable")

    monkeypatch.setattr(trials, "verify_initial_workspace", fail)
    result = invoke(attempt)
    assert result["status"] == "harness_error" and result["score"] is None
    assert result["stage"] == "baseline_verification"
    assert "context" not in attempt[2] and attempt[2]["grade_calls"] == 0


def test_budgeted_native_plan_passes_its_exact_limit_to_execution(attempt, monkeypatch):
    load = trials.load_plan

    def budgeted(path):
        admitted = load(path)
        admitted["plan"].update(schema_version=2, write_io_limit_bytes=65536)
        return admitted

    monkeypatch.setattr(trials, "load_plan", budgeted)
    result = invoke(attempt)
    assert result["status"] == "task_failed" and result["score"] == 0.5
    assert attempt[2]["resource_options"] == {"write_io_limit": 65536}


def test_public_admission_rejects_legacy_plan_before_subject_launch(attempt, monkeypatch):
    monkeypatch.setattr(trials, "require_qualified_trial_execution", lambda: None)
    result = trials.run(attempt[0], attempt[1])
    assert result["status"] == "harness_error" and result["score"] is None
    assert result["stage"] == "admission" and "context" not in attempt[2]


def test_inconsistent_budget_evidence_prevents_collection_and_grading(attempt, monkeypatch):
    load, execute = trials.load_plan, trials.execute_agent

    def budgeted(path):
        admitted = load(path)
        admitted["plan"].update(schema_version=2, write_io_limit_bytes=65536)
        return admitted

    def inconsistent(*args, **kwargs):
        result = execute(*args, **kwargs)
        path = args[2] / "process.json"
        process = json.loads(path.read_bytes())
        process["write_io_limit_bytes"] += 1
        trials.write_json(path, process)
        return result

    monkeypatch.setattr(trials, "load_plan", budgeted)
    monkeypatch.setattr(trials, "execute_agent", inconsistent)
    result = invoke(attempt)
    assert result["status"] == "harness_error" and result["score"] is None
    assert attempt[2]["collection_calls"] == attempt[2]["grade_calls"] == 0


@pytest.mark.parametrize("drift", [False, True])
def test_dependency_bundle_is_scoped_and_reverified_before_grading(attempt, tmp_path, monkeypatch, drift):
    load = trials.load_plan
    packages = tmp_path / "packages"
    packages.mkdir()
    module = packages / "fixture.py"
    module.write_bytes(b"original dependency")
    receipt = {"packages": str(packages), "inventory": inventory(packages)}

    def with_dependencies(path):
        admitted = load(path)
        admitted["runtime"]["dependencies"] = {
            "raw": b"frozen specification",
            "installer": Path("fixture-installer"),
            "archive_dir": None,
            "import_paths": [],
            "asset": {},
        }
        return admitted

    execute = trials.execute_agent

    def subject(*args, **kwargs):
        context = kwargs["context"]
        assert context.tool_environment["PYTHONPATH"] == str(packages)
        assert "PYTHONPATH" not in context.controller_environment
        assert packages in context.readable_roots
        result = execute(*args, **kwargs)
        if drift:
            module.write_bytes(b"changed dependency")
        return result

    monkeypatch.setattr(trials, "load_plan", with_dependencies)
    monkeypatch.setattr(trials, "prepare_dependencies", lambda *args, **kwargs: receipt)
    monkeypatch.setattr(trials, "execute_agent", subject)
    result = invoke(attempt)
    assert result["status"] == ("harness_error" if drift else "task_failed")
    assert result["score"] == (None if drift else 0.5)
    assert attempt[2]["grade_calls"] == (0 if drift else 1)


def test_plan_changed_after_qualification_cannot_launch(attempt, monkeypatch):
    monkeypatch.setattr(trials, "verify_binding", lambda qualification: None)
    qualification = trials.QualifiedNativeTrial(
        "different-plan", "receipt", "unit-profile", Path("receipt"), (), "source"
    )
    result = trials._run_controller(attempt[0], attempt[1], qualification=qualification)
    assert result["status"] == "harness_error" and result["score"] is None
    assert result["stage"] == "admission" and "context" not in attempt[2]


def test_changed_qualification_after_grading_withholds_score(attempt, monkeypatch):
    observations = []

    def observed(qualification):
        observations.append(qualification)
        if len(observations) == 2:
            raise ValueError("Boundary evidence changed")

    monkeypatch.setattr(trials, "verify_binding", observed)
    qualification = trials.QualifiedNativeTrial(
        sha256(attempt[0].read_bytes()), "receipt", "unit-profile", Path("receipt"), (), "source"
    )
    result = trials._run_controller(
        attempt[0],
        attempt[1],
        qualification=qualification,
        credential_source={"NATIVE_FIXTURE": "owned fixture credential"},
    )
    assert len(observations) == 2 and attempt[2]["grade_calls"] == 1
    assert result["status"] == "harness_error" and result["score"] is None
    assert result["execution_boundary_qualification"] == {"profile": "unit-profile", "receipt_sha256": "receipt"}


def test_public_route_requires_scoped_admission_and_exact_resource_budgets(tmp_path, monkeypatch):
    plan, receipt = tmp_path / "plan", tmp_path / "receipt"
    qualification = trials.QualifiedNativeTrial("frozen-plan", "receipt", "unit-profile", receipt, (), "source")
    calls = []

    def admitted(path, evidence):
        assert path == plan and evidence == receipt
        return qualification

    def controller(path, output, **kwargs):
        calls.append(kwargs)
        return {"status": "harness_error", "score": None}

    monkeypatch.setattr(trials, "admit", admitted)
    monkeypatch.setattr(trials, "_run_controller", controller)
    trials.run(plan, tmp_path / "output", qualification=receipt)
    assert calls == [{"require_resource_budgets": True, "qualification": qualification}]

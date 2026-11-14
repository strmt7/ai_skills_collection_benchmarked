"""Synthetic receipt tests exercise admission and misleading-evidence rejection without native execution."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
import qualify_native_trial_boundary as boundary
from _native_benchmark_runtime import sha256, write_json


@pytest.fixture
def matrix(tmp_path, monkeypatch):
    root = tmp_path / "project"
    state = root / ".venv"
    state.mkdir(parents=True)
    monkeypatch.setattr(boundary, "ROOT", root)
    monkeypatch.setattr(boundary, "execution_sources", lambda: {"runner": "frozen"})
    monkeypatch.setattr(boundary, "source_hashes", lambda: {"grader": "frozen"})
    monkeypatch.setattr(boundary, "CONTEXT_EVIDENCE_NAMES", ("source-binding.json",))
    monkeypatch.setattr(boundary, "check_context", lambda path: {"ok": True})
    context = state / "context"
    context.mkdir()
    runtime = {"cli": state / "cli", "python": state / "python"}
    write_json(
        context / "qualification.json",
        {**{key: str(value) for key, value in runtime.items()}, "checks": {"unit": True}},
    )
    write_json(context / "source-binding.json", {})
    assets = {}
    for key in ("task", "subject_runtime", "grader_runtime", "prompt"):
        path = state / (key + ".txt")
        path.write_text("independent " + key, encoding="utf-8")
        assets[key] = {"path": str(path), "sha256": sha256(path.read_bytes())}
    directories = {}
    for name, (stage, status, score) in boundary.CASES.items():
        directory = state / name
        attempt = directory / "attempt"
        attempt.mkdir(parents=True)
        directories[name] = str(directory)
        plan: dict[str, Any] = {
            "schema_version": 3,
            "id": name,
            "partition": "development",
            "condition": "default",
            "model": "owned-local-model",
            "reasoning_effort": "high",
            "interventions": [],
            "baseline_collection": str(state / "baseline"),
            "execution_source_sha256": {"runner": "frozen"},
            "provider": {"base_url": "http://127.0.0.1:8041/v1", "authentication": "none"},
            "time_limit_seconds": 5 if name == "timeout" else 90,
            "write_io_limit_bytes": 1 if name == "budget" else 1024**3,
            "storage_limits": {"min_free_bytes": 1024**3, "max_workspace_bytes": 1024, "max_workspace_entries": 100},
            **assets,
        }
        write_json(directory / "plan.json", plan)
        write_json(attempt / "plan.json", plan)
        summary: dict[str, Any] = {
            "passed": True,
            "model_requests": 0,
            "authentication": "none",
            "credential_binding_released": True,
            "space_injections": int(name in {"space", "spaceerror", "preflight-space"}),
            "timeout_tool_marker_observed": True,
            "native_integrated_isolation_observed": True,
            "native_tool_process_stopped": True,
            "native_tool_process_observations": [
                {"pid": 12345, "creation_filetime": 123456789, "seen_running": True, "stopped": True}
            ],
        }
        write_json(directory / "summary.json", summary)
        write_json(
            directory / "space-injections.json", [{"real_disk_pressure_created": False}] * summary["space_injections"]
        )
        write_json(
            directory / "transport.json",
            {
                "model_requests": 0,
                "listener_stopped": True,
                "errors": [],
                "fallback_requests": 0,
                "posts": 0 if name == "preflight-space" else 1,
                "requests": [{"authentication": "none", "authorization_present": False}],
            },
        )
        (directory / "implementation.py.txt").write_text("owned unit producer, never executed", encoding="utf-8")
        evidence = {}
        if name != "preflight-space":
            reason = {
                "budget": "write_io_limit",
                "accounting": "resource_observation_error",
                "space": "free_space_limit",
                "spaceerror": "storage_observation_error",
                "timeout": "timeout",
            }.get(name)
            process = {
                "windows_job": True,
                "assigned_before_resume": True,
                "kill_on_close": True,
                "job_active_processes_after_cleanup": 0,
                "job_memory_limit_bytes": 2 * 1024**3,
                "active_process_limit": 32,
                "output_limit_bytes": 8 * 1024**2,
                "explicit_environment": True,
                "wall_time_limit_seconds": plan["time_limit_seconds"],
                "exit_code": int(name == "truncated"),
                "termination_reason": reason,
                "write_io_limit_bytes": plan["write_io_limit_bytes"],
                "job_write_io_bytes": None if name == "accounting" else 2,
                "write_io_overshoot_bytes": None if name == "accounting" else int(name == "budget"),
                "write_io_observation_error": {
                    "api": "QueryInformationJobObject",
                    "information_class": 8,
                    "winerror": 5,
                }
                if name == "accounting"
                else None,
                "write_io_enforcement": "polled_job_transfer_accounting",
                "hard_storage_quota": False,
                "space_budget": {"termination_reason": reason, "observation_error": {"winerror": 5}},
            }
            write_json(attempt / "process.json", process)
            events = (
                [{"type": "turn.failed", "error": "stream closed before response.completed"}]
                if name == "truncated"
                else [{"type": "turn.completed"}]
            )
            (attempt / "transcript.jsonl").write_text(
                "\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8"
            )
            evidence.update({key: sha256((attempt / key).read_bytes()) for key in ("process.json", "transcript.jsonl")})
        if name in {"edited", "unchanged", "isolation"}:
            counts = (
                {"passed": 0, "failed": 10, "skipped": 1, "errors": 0, "total": 11}
                if name == "unchanged"
                else {"passed": 11, "failed": 0, "skipped": 0, "errors": 0, "total": 11}
            )
            (attempt / "grading").mkdir()
            write_json(
                attempt / "grading/result.json",
                {
                    "native_counts": counts,
                    "score": score,
                    "task_id": boundary.TASK,
                    "execution_source_sha256": {"grader": "frozen"},
                    "model_requests": 0,
                },
            )
            output = "Process exited with code 0\nSUBJECT_DEPENDENCY_IMPORTS_VERIFIED\nNATIVE_SUBJECT_EDIT_COMPLETED\nNATIVE_INTEGRATED_ISOLATION_VERIFIED"
            write_json(
                directory / "request-2.native.json",
                {
                    "input": [
                        {"type": "function_call", "arguments": output},
                        {"type": "function_call_output", "call_id": "call_owned_control", "output": output},
                    ]
                },
            )
        if name == "logical":
            write_json(
                attempt / "final-storage.json",
                {"termination_reason": "workspace_logical_bytes_limit", "logical_bytes": 1025},
            )
        if name == "preflight-space":
            write_json(attempt / "setup-space.json", {"termination_reason": "free_space_limit"})
        if name == "truncated":
            (directory / "response-1.native.sse").write_bytes(b"event: response.created\n")
        required = (
            {"plan.json", "setup-space.json"}
            if name == "preflight-space"
            else boundary.ATTEMPT_EVIDENCE - {"collection/result.json", "grading/result.json"}
        )
        if name in {"edited", "unchanged", "isolation"}:
            required = boundary.ATTEMPT_EVIDENCE
        for relative in required:
            target = attempt / relative
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"{}")
            evidence[relative] = sha256(target.read_bytes())
        result: dict[str, Any] = {
            "stage": stage,
            "status": status,
            "score": score,
            "execution_source_sha256": {"runner": "frozen"},
            "plan_sha256": sha256((directory / "plan.json").read_bytes()),
            "evidence_sha256": evidence,
            "timed_out": name == "timeout",
        }
        if name in {"edited", "unchanged", "isolation"}:
            result["native_counts"] = counts
        write_json(attempt / "result.json", result)
        write_json(attempt / "attempt.json", result)

    def load(path):
        plan = json.loads(path.read_bytes())
        return {
            "plan": plan,
            "plan_sha256": sha256(path.read_bytes()),
            "task": {"id": boundary.TASK},
            "runtime": runtime,
        }

    monkeypatch.setattr(boundary, "load_plan", load)
    spec = {
        "schema_version": 1,
        "profile": boundary.PROFILE,
        "context_directory": str(context),
        "controls": directories,
        "execution_source_sha256": {"runner": "frozen"},
    }
    return state, spec


def mutate(matrix, case, relative, update):
    path = Path(matrix[1]["controls"][case]) / relative
    value = json.loads(path.read_bytes())
    update(value)
    write_json(path, value)


def test_complete_matrix_roundtrip_and_scoped_admission(matrix):
    state, spec = matrix
    specification = state / "specification.json"
    write_json(specification, spec)
    output = state / "qualified"
    boundary.qualify(specification, output)
    checked = boundary.check(output)
    assert checked["execution_boundary_qualified"] is True and checked["model_transport_qualified"] is False
    assert len(checked["controls"]) == 11
    admitted = boundary.admit(Path(spec["controls"]["edited"]) / "plan.json", output)
    boundary.verify_binding(admitted)
    (state / "task.txt").write_bytes(b"changed frozen asset")
    with pytest.raises(ValueError, match="evidence changed"):
        boundary.verify_binding(admitted)


@pytest.mark.parametrize("fault", ["missing", "duplicate", "old-sources", "outside"])
def test_invalid_matrix_cannot_qualify(matrix, fault):
    state, spec = matrix
    if fault == "missing":
        del spec["controls"]["timeout"]
    elif fault == "duplicate":
        spec["controls"]["timeout"] = spec["controls"]["edited"]
    elif fault == "old-sources":
        spec["execution_source_sha256"] = {}
    else:
        spec["controls"]["timeout"] = str(state.parent / "unowned")
    with pytest.raises(ValueError):
        boundary.verify(spec)


@pytest.mark.parametrize(
    "case,relative,key,value",
    [
        ("edited", "summary.json", "model_requests", 1),
        ("edited", "summary.json", "model_requests", False),
        ("timeout", "summary.json", "timeout_tool_marker_observed", False),
        ("preflight-space", "attempt/setup-space.json", "termination_reason", None),
        ("logical", "attempt/final-storage.json", "logical_bytes", 1),
        ("edited", "transport.json", "fallback_requests", 1),
        ("edited", "transport.json", "listener_stopped", False),
    ],
)
def test_misleading_control_observation_is_rejected(matrix, case, relative, key, value):
    mutate(matrix, case, relative, lambda record: record.update({key: value}))
    with pytest.raises(ValueError):
        boundary.verify(matrix[1])


@pytest.mark.parametrize(
    "case,field,value",
    [
        ("budget", "termination_reason", "timeout"),
        (
            "accounting",
            "write_io_observation_error",
            {"api": "QueryInformationJobObject", "information_class": 7, "winerror": 5},
        ),
        ("space", "termination_reason", "timeout"),
        ("edited", "job_active_processes_after_cleanup", 1),
        ("edited", "job_active_processes_after_cleanup", False),
    ],
)
def test_wrong_native_mechanism_fails_even_with_consistent_digests(matrix, case, field, value):
    mutate(matrix, case, "attempt/process.json", lambda record: record.update({field: value}))
    directory = Path(matrix[1]["controls"][case])
    result = json.loads((directory / "attempt/result.json").read_bytes())
    result["evidence_sha256"]["process.json"] = sha256((directory / "attempt/process.json").read_bytes())
    write_json(directory / "attempt/result.json", result)
    write_json(directory / "attempt/attempt.json", result)
    with pytest.raises(ValueError):
        boundary.verify(matrix[1])


def test_command_marker_without_matched_output_is_rejected(matrix):
    def remove(record):
        record["input"][1]["output"] = "Process exited with code 0\nNo probe output"

    mutate(matrix, "isolation", "request-2.native.json", remove)
    with pytest.raises(ValueError, match="imports or edits"):
        boundary.verify(matrix[1])


@pytest.mark.parametrize("change", ["model", "holdout", "credentials", "ipv6", "route", "task", "runtime", "storage"])
def test_qualification_cannot_authorize_another_profile(matrix, change):
    state, spec = matrix
    write_json(state / "specification.json", spec)
    boundary.qualify(state / "specification.json", state / "qualified")
    plan = copy.deepcopy(json.loads((Path(spec["controls"]["edited"]) / "plan.json").read_bytes()))
    if change == "model":
        plan["model"] = "another-model"
    elif change == "holdout":
        plan["partition"] = "holdout"
    elif change == "credentials":
        plan["provider"] = {"base_url": "http://127.0.0.1:8041/v1", "credential_env": "UNSELECTED"}
    elif change in {"ipv6", "route"}:
        plan["provider"]["base_url"] = "http://[::1]:8041/v1" if change == "ipv6" else "http://127.0.0.1:8041/other"
    elif change in {"task", "runtime"}:
        plan["task" if change == "task" else "subject_runtime"]["sha256"] = "0" * 64
    else:
        plan["storage_limits"]["max_workspace_bytes"] += 1
    path = state / "different-plan.json"
    write_json(path, plan)
    with pytest.raises(ValueError):
        boundary.admit(path, state / "qualified")


def test_changed_archived_specification_is_rejected(matrix):
    state, spec = matrix
    write_json(state / "specification.json", spec)
    boundary.qualify(state / "specification.json", state / "qualified")
    (state / "qualified/specification.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="specification digest"):
        boundary.check(state / "qualified")


def test_output_cannot_be_created_inside_a_control(matrix):
    state, spec = matrix
    write_json(state / "specification.json", spec)
    with pytest.raises(ValueError, match="overlaps"):
        boundary.qualify(state / "specification.json", Path(spec["controls"]["edited"]) / "new-output")


def test_failed_context_controls_prevent_qualification(matrix, monkeypatch):
    monkeypatch.setattr(boundary, "check_context", lambda path: {"ok": False})
    with pytest.raises(ValueError, match="context qualification failed"):
        boundary.verify(matrix[1])


def test_source_change_during_verification_is_rejected(matrix, monkeypatch):
    original = boundary.control
    changed = []

    def observed(name, *args):
        result = original(name, *args)
        if name == "isolation":
            changed.append(True)
        return result

    monkeypatch.setattr(boundary, "control", observed)
    monkeypatch.setattr(boundary, "execution_sources", lambda: {"runner": "changed" if changed else "frozen"})
    with pytest.raises(ValueError, match="changed during qualification"):
        boundary.verify(matrix[1])


@pytest.mark.parametrize("evidence", [{}, {"unexpected.json": "0" * 64}])
def test_missing_or_unexpected_evidence_cannot_be_qualified(matrix, evidence):
    mutate(matrix, "edited", "attempt/result.json", lambda record: record.update(evidence_sha256=evidence))
    mutate(matrix, "edited", "attempt/attempt.json", lambda record: record.update(evidence_sha256=evidence))
    with pytest.raises(ValueError, match="evidence set"):
        boundary.verify(matrix[1])


def test_changed_admission_implementation_invalidates_live_binding(matrix, monkeypatch):
    state, spec = matrix
    write_json(state / "specification.json", spec)
    boundary.qualify(state / "specification.json", state / "qualified")
    admitted = boundary.admit(Path(spec["controls"]["edited"]) / "plan.json", state / "qualified")
    original = boundary.raw
    monkeypatch.setattr(
        boundary, "raw", lambda path: b"changed admission source" if path == Path(boundary.__file__) else original(path)
    )
    with pytest.raises(ValueError, match="admission source changed"):
        boundary.verify_binding(admitted)


def test_json_cli_checks_a_complete_receipt(matrix, capsys):
    state, spec = matrix
    write_json(state / "specification.json", spec)
    assert (
        boundary.main(
            ["--specification", str(state / "specification.json"), "--output", str(state / "qualified"), "--json"]
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is True and result["validation"]["model_transport_qualified"] is False
    assert result["validation"]["admission_source_sha256"] == sha256(Path(boundary.__file__).read_bytes())


@pytest.mark.parametrize(
    "observations", [[], [{"pid": 12345, "creation_filetime": 123456789, "seen_running": False, "stopped": True}]]
)
def test_timeout_must_observe_the_actual_tool_identity_and_termination(matrix, observations):
    mutate(
        matrix, "timeout", "summary.json", lambda record: record.update(native_tool_process_observations=observations)
    )
    with pytest.raises(ValueError, match="tool"):
        boundary.verify(matrix[1])

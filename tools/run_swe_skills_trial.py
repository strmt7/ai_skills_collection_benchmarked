#!/usr/bin/env python3
"""Run a frozen subject, collect its stopped workspace and preserve the native benchmark score."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections.abc import Mapping
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from typing import Any

from _native_benchmark_runtime import DockerClient, sha256, write_json
from _native_trial_plan import ROOT, archive_sources, execution_sources, input_assets, load_plan, subject_runtime
from _trial_catalog import catalog_lease
from _trial_collection import capture_owned
from _trial_context import command, create_context, temporary_home
from _trial_execution_evidence import context_record
from _trial_provider import credential_lease
from _trial_transcript import parse_events, strict_json
from _windows_appcontainer import checked_path
from _windows_storage_budget import (
    SpaceBudget,
    StorageLimits,
    WorkspaceStorageExceeded,
    measure_workspace,
    verify_workspace_measurement,
)
from _windows_trial_process import ProcessBudgetOptions, verify_write_io_budget
from grade_swe_skills_submission import asset, grade
from prepare_subject_dependencies import prepare as prepare_dependencies
from prepare_subject_dependencies import verify as verify_dependencies
from qualify_native_trial_boundary import QualifiedNativeTrial, admit, verify_binding
from run_agent_trial import exception_metadata, execute_agent, require_qualified_trial_execution
from transfer_benchmark_submission import plan_handoff, restore, seal


def run(plan: Path, output: Path, *, qualification: Path | None = None) -> dict[str, Any]:
    """Require current, scoped boundary evidence before a native development trial."""
    if qualification is None:
        require_qualified_trial_execution()
    admitted = admit(plan, qualification) if qualification is not None else None
    return _run_controller(plan, output, require_resource_budgets=True, qualification=admitted)


def verify_initial_workspace(workspace: Path, output: Path, python: Path, task: dict[str, Any], before: bytes) -> None:
    """Prove the selected collector runtime can recapture the exact starting namespace."""
    captured = capture_owned(
        workspace, output / "initial-submission", output / "initial-collection", python, task["collection_policy"]
    )
    if captured["status"] != "collected":
        raise ValueError("Initial subject source collection did not complete")
    current = (output / "initial-collection/stdout.native").read_bytes()
    handoff = plan_handoff(before, current)
    if (
        handoff.delta["writes"]
        or handoff.delta["deletes"]
        or handoff.baseline["directories"] != handoff.submission["directories"]
    ):
        raise ValueError("Reconstructed subject workspace differs from the frozen baseline")


def record_workspace_storage(workspace: Path, output: Path, limits: StorageLimits) -> None:
    """Retain complete, partial and failed stopped-workspace observations distinctly."""
    try:
        observation = measure_workspace(workspace, limits)
    except WorkspaceStorageExceeded as error:
        write_json(output, {**error.observation, "termination_reason": error.reason})
        raise
    except (OSError, ValueError) as error:
        write_json(output, {"complete": False, "status": "observation_failed", **exception_metadata(error)})
        raise
    write_json(output, observation)
    verify_workspace_measurement(observation, limits)


def _run_controller(
    plan_path: Path,
    output: Path,
    *,
    credential_source: Mapping[str, str] | None = None,
    require_resource_budgets: bool = False,
    qualification: QualifiedNativeTrial | None = None,
) -> dict[str, Any]:
    """Shared lifecycle; live callers must enter through the qualified public route."""
    output = checked_path(output)
    if not output.is_relative_to(ROOT / ".venv") or output == ROOT / ".venv":
        raise ValueError("Native attempt evidence requires a new owned directory")
    output.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {"schema_version": 1, "status": "harness_error", "score": None, "stage": "admission"}
    write_json(output / "attempt.json", report)
    setup_space: SpaceBudget | None = None
    try:
        admitted = load_plan(plan_path)
        if qualification is not None:
            verify_binding(qualification)
            if admitted["plan_sha256"] != qualification.plan_sha256:
                raise ValueError("Native plan changed after boundary qualification")
            report["execution_boundary_qualification"] = {
                "profile": qualification.profile,
                "receipt_sha256": qualification.receipt_sha256,
            }
        (output / "plan.json").write_bytes(admitted["plan_raw"])
        plan, task, runtime = (admitted[name] for name in ("plan", "task", "runtime"))
        if require_resource_budgets and plan.get("schema_version") != 3:
            raise ValueError("Public model execution requires schema-3 explicit write and storage budgets")
        storage_limits = StorageLimits.from_record(plan["storage_limits"]) if plan.get("schema_version") == 3 else None
        if storage_limits is not None:
            setup_space = SpaceBudget(storage_limits, (output, Path(tempfile.gettempdir())))
            report["stage"] = "storage_preflight"
            write_json(output / "attempt.json", report)
            setup_space.require_available()
        archive_sources(output / "sources", plan["execution_source_sha256"])
        for name, entry in input_assets(plan, runtime).items():
            target = output / "inputs" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(asset(entry))
        dependency_receipt = None
        if "dependencies" in runtime:
            setup = runtime["dependencies"]
            (output / "inputs/subject-dependencies.json").write_bytes(setup["raw"])
            report["stage"] = "dependencies"
            write_json(output / "attempt.json", report)
            dependency_receipt = prepare_dependencies(
                setup["raw"],
                runtime["python"],
                setup["installer"],
                output / "dependencies",
                archive_dir=setup["archive_dir"],
                **({"space_budget": setup_space} if setup_space is not None else {}),
            )
            runtime["roots"] = (*runtime["roots"], verify_dependencies(dependency_receipt))
        report.update(
            plan_sha256=admitted["plan_sha256"],
            task_id=task["id"],
            condition=plan["condition"],
            partition=plan["partition"],
            model_requested=plan["model"],
            provider_model_snapshot=None,
            latency_claim_eligible=False,
            usage_source="cli_transcript",
            reasoning_effort_requested=plan["reasoning_effort"],
            usage=None,
            write_io_limit_bytes=plan.get("write_io_limit_bytes"),
            subject_platform="Windows",
            grader_platform="Linux",
            execution_source_sha256=execution_sources(),
        )
        for path in (admitted["baseline"], admitted["tree"], plan_path.resolve()):
            if output.is_relative_to(path) or path.is_relative_to(output):
                raise ValueError("Native attempt inputs and output must be disjoint")
        report["stage"] = "preflight"
        write_json(output / "attempt.json", report)
        client = DockerClient(ROOT, output / "preflight", admitted["grader_runtime"])
        if client.reference != task["image_reference"]:
            raise ValueError("Native task and runtime image differ")
        report["stage"] = "workspace"
        write_json(output / "attempt.json", report)
        parent = Path(tempfile.mkdtemp(prefix="native-skill-subject-"))
        workspace = parent / "workspace"
        initial = plan_handoff(admitted["before"], admitted["before"])
        sealed = seal(initial, admitted["tree"], output / "initial.tar")
        rebuilt = restore(initial, admitted["tree"], output / "initial.tar", sealed["archive_sha256"], workspace)
        write_json(output / "initial-source.json", rebuilt)
        if storage_limits is not None:
            report["stage"] = "initial_storage"
            write_json(output / "attempt.json", report)
            record_workspace_storage(workspace, output / "initial-storage.json", storage_limits)
            if setup_space is not None:
                setup_space.require_available()
        report["stage"] = "baseline_verification"
        write_json(output / "attempt.json", report)
        verify_initial_workspace(workspace, output, runtime["python"], task, admitted["before"])
        subject_runtime(plan["subject_runtime"])
        context = create_context(temporary_home(), workspace, runtime["cli"], runtime["python"], runtime["roots"])
        if dependency_receipt is not None:
            paths = [checked_path(workspace / name) for name in runtime["dependencies"]["import_paths"]]
            if any(not path.is_relative_to(workspace) or not path.is_dir() for path in paths):
                raise ValueError("Subject source import directories are missing or outside the workspace")
            paths.append(verify_dependencies(dependency_receipt))
            context = replace(
                context,
                tool_environment={
                    **context.tool_environment,
                    "PYTHONPATH": os.pathsep.join(str(path) for path in paths),
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )
        report.update(stage="agent", workspace=str(workspace))
        write_json(output / "attempt.json", report)
        agent_space = (
            SpaceBudget(storage_limits, (output, workspace, context.home, Path(tempfile.gettempdir())))
            if storage_limits is not None
            else None
        )
        resources: ProcessBudgetOptions = {}
        if plan.get("schema_version") in (2, 3):
            resources["write_io_limit"] = plan["write_io_limit_bytes"]
        if agent_space is not None:
            resources["space_budget"] = agent_space
        prompt = admitted["prompt"] + "\n\nPython executable for this attempt: " + str(runtime["python"]) + "\n"
        if "toolchains" in runtime:
            prompt += runtime["toolchains"].instructions()
        with ExitStack() as credentials:
            selected = credentials.enter_context(
                credential_lease(
                    context, plan["provider"], os.environ if credential_source is None else credential_source
                )
            )
            selected = credentials.enter_context(
                catalog_lease(selected, plan["provider"], local=runtime.get("local_catalog"))
            )
            invocation = command(selected, plan["model"], plan["reasoning_effort"], provider=plan["provider"])
            write_json(
                output / "launch.json",
                {"command": invocation, "context": context_record(selected), "plan_sha256": admitted["plan_sha256"]},
            )
            exit_code, timed_out, elapsed = execute_agent(
                invocation,
                prompt,
                output,
                plan["time_limit_seconds"],
                context=selected,
                **resources,
            )
        report.update(process_exit_code=exit_code, elapsed_seconds=elapsed, timed_out=timed_out)
        process = strict_json((output / "process.json").read_text(encoding="utf-8"))
        if (
            process.get("windows_job") is not True
            or process.get("assigned_before_resume") is not True
            or process.get("kill_on_close") is not True
            or type(process.get("job_active_processes_after_cleanup")) is not int
            or process["job_active_processes_after_cleanup"] != 0
        ):
            raise ValueError("Subject termination is not established; collection is forbidden")
        if plan.get("schema_version") in (2, 3):
            verify_write_io_budget(process, plan["write_io_limit_bytes"])
        if agent_space is not None:
            if process.get("space_budget") != agent_space.record() or (
                agent_space.reason is not None and process.get("termination_reason") is None
            ):
                raise ValueError("Subject space observations differ from the actual budget monitor")
            report["stage"] = "final_storage"
            write_json(output / "attempt.json", report)
            record_workspace_storage(workspace, output / "final-storage.json", agent_space.limits)
        report["stage"] = "collection"
        write_json(output / "attempt.json", report)
        if setup_space is not None:
            setup_space.require_available()
        captured = capture_owned(
            workspace, output / "submission", output / "collection", runtime["python"], task["collection_policy"]
        )
        if captured["status"] != "collected":
            raise ValueError("Subject collection did not complete")
        report["collection_result_sha256"] = sha256((output / "collection/result.json").read_bytes())
        events = parse_events(
            (output / "transcript.jsonl").read_bytes(),
            allow_truncated_final=exit_code != 0 or timed_out or process.get("termination_reason") is not None,
        )
        report["usage"] = next(
            (event.get("usage") for event in reversed(events) if event["type"] == "turn.completed"), None
        )
        if (
            exit_code != 0
            or timed_out
            or process.get("termination_reason") is not None
            or not any(event["type"] == "turn.completed" for event in events)
        ):
            raise ValueError("Subject execution did not produce a completed turn")
        report["stage"] = "grading"
        write_json(output / "attempt.json", report)
        if dependency_receipt is not None:
            verify_dependencies(dependency_receipt)
            asset(runtime["dependencies"]["asset"])
        if "toolchains" in runtime:
            runtime["toolchains"].verify()
        asset(plan["grader_runtime"])
        if setup_space is not None:
            setup_space.require_available()
        graded = grade(
            task, admitted["grader_runtime"], admitted["baseline"], output / "collection", output / "grading"
        )
        if setup_space is not None:
            setup_space.require_available()
        for entry in input_assets(plan, runtime).values():
            asset(entry)
        subject_runtime(plan["subject_runtime"])
        if dependency_receipt is not None:
            verify_dependencies(dependency_receipt)
            asset(runtime["dependencies"]["asset"])
        if (
            sha256(plan_path.read_bytes()) != admitted["plan_sha256"]
            or plan["execution_source_sha256"] != execution_sources()
        ):
            raise ValueError("Frozen native attempt inputs changed during execution")
        if qualification is not None:
            verify_binding(qualification)
        report.update(
            status=graded["status"],
            score=graded["score"],
            native_counts=graded.get("native_counts"),
            native_stage=graded.get("stage"),
            stage="complete",
        )
        report["grading_result_sha256"] = sha256((output / "grading/result.json").read_bytes())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        report.update(status="harness_error", score=None, **exception_metadata(error))
    finally:
        if setup_space is not None:
            write_json(output / "setup-space.json", setup_space.record())
    names = [
        "plan.json",
        "launch.json",
        "input.native",
        "process.json",
        "transcript.jsonl",
        "stderr.txt",
        "collection/result.json",
        "initial-collection/result.json",
        "grading/result.json",
        "initial-storage.json",
        "final-storage.json",
        "setup-space.json",
    ]
    report["evidence_sha256"] = {
        name: sha256((output / name).read_bytes()) for name in names if (output / name).is_file()
    }
    write_json(output / "attempt.json", report)
    write_json(output / "result.json", report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, help="Current scoped native boundary qualification directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run(args.plan, args.output, qualification=args.qualification)
    print(json.dumps(result, sort_keys=True))
    return {"task_passed": 0, "task_failed": 1, "harness_error": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())

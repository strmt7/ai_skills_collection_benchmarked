"""Bind a stopped native subject to the sealed TestEval grader inputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _native_benchmark_runtime import write_json
from _trial_collection import capture_owned
from _trial_transcript import parse_events
from _windows_appcontainer import checked_path
from collect_testeval_submission import ROOT, object_from, read_asset
from grade_testeval_submission import TEST_SUBMISSION, load_test_snippets, sha256, validate_task_plan
from transfer_benchmark_submission import plan_handoff, restore, seal
from validate_testeval_calibration import read_evidence


@dataclass(frozen=True, slots=True)
class TestEvalSubject:
    """Controller-owned copies of a public task and its starting workspace."""

    output: Path
    workspace: Path
    python: Path
    task_bytes: bytes
    baseline_bytes: bytes

    @property
    def handoff(self) -> Path:
        return self.output / "handoff"

    @property
    def task_plan(self) -> Path:
        return self.output / "task-plan.json"


def prepare_subject(
    task_plan: Path, baseline_dir: Path, workspace: Path, output: Path, python: Path
) -> TestEvalSubject:
    """Reconstruct and verify the exact baseline before any tool runs."""
    task_plan, baseline_dir, workspace, output, python = map(
        checked_path, (task_plan, baseline_dir, workspace, output, python)
    )
    owned = ROOT / ".venv"
    if (
        output == owned
        or not output.is_relative_to(owned)
        or workspace.is_relative_to(ROOT)
        or any(
            a.is_relative_to(b) or b.is_relative_to(a) for a in (workspace, output) for b in (baseline_dir, task_plan)
        )
        or workspace.is_relative_to(output)
        or output.is_relative_to(workspace)
        or workspace.exists()
    ):
        raise ValueError("Use new disjoint controller evidence and a subject workspace outside the checkout")
    task_bytes = read_evidence(task_plan)
    task = object_from(task_bytes)
    validate_task_plan(task)
    before = read_asset(baseline_dir / "baseline.collection.json", task["baseline_manifest_sha256"])
    initial = plan_handoff(before, before)
    if (
        set(initial.baseline["files"]) != {"task.txt"}
        or initial.baseline["directories"]
        or initial.baseline["excluded"]
    ):
        raise ValueError("The public TestEval subject baseline must contain only the task prompt")
    output.mkdir(exist_ok=False)
    prepared = TestEvalSubject(output, workspace, python, task_bytes, before)
    prepared.task_plan.write_bytes(task_bytes)
    prepared.handoff.mkdir()
    (prepared.handoff / "baseline.collection.json").write_bytes(before)
    archive = output / "baseline.tar"
    baseline_tree = baseline_dir / "baseline"
    receipt = seal(initial, baseline_tree, archive)
    restore(initial, baseline_tree, archive, receipt["archive_sha256"], prepared.handoff / "baseline")
    restore(initial, prepared.handoff / "baseline", archive, receipt["archive_sha256"], workspace)

    observed = output / "initial-collection"
    result = capture_owned(workspace, output / "initial-submission", observed, python, initial.baseline["policy"])
    if result["status"] != "collected":
        raise ValueError("The native collector could not attest the starting TestEval workspace")
    actual = plan_handoff(before, read_asset(observed / "stdout.native"))
    if actual.delta["writes"] or actual.delta["deletes"] or actual.submission["directories"]:
        raise ValueError("The reconstructed TestEval workspace differs from the frozen baseline")
    write_json(output / "baseline-receipt.json", receipt)
    return prepared


def stopped_execution(process: dict[str, Any]) -> bool:
    """Require a successful owned Windows job and a terminated process tree."""
    return (
        all(process.get(key) is True for key in ("windows_job", "assigned_before_resume", "kill_on_close"))
        and "termination_reason" in process
        and process["termination_reason"] is None
        and type(process.get("exit_code")) is int
        and process["exit_code"] == 0
        and type(process.get("job_active_processes_after_cleanup")) is int
        and process["job_active_processes_after_cleanup"] == 0
    )


def finish_subject(subject: TestEvalSubject) -> dict[str, Any]:
    """Seal a submitted test file only after native job and turn completion."""
    execution = subject.output / "execution"
    outcome: dict[str, Any] = {
        "schema_version": 1,
        "status": "execution_incomplete",
        "archive_sha256": None,
        "task_plan_sha256": sha256(subject.task_bytes),
    }
    result_path = subject.output / "subject-result.json"
    if result_path.exists():
        raise FileExistsError("TestEval subject evidence already exists")

    try:
        native = read_evidence(execution / "process.json")
        outcome["process_sha256"] = sha256(native)
        if stopped_execution(object_from(native)):
            with (execution / "transcript.jsonl").open("rb") as stream:
                raw = stream.read(8 * 1024**2 + 1)
            if len(raw) > 8 * 1024**2:
                raise ValueError("Native TestEval transcript exceeds the recorded limit")
            outcome["transcript_sha256"] = sha256(raw)
            events = parse_events(raw)
            turns = [event["type"] for event in events if event["type"] in {"turn.completed", "turn.failed"}]
            if turns == ["turn.completed"] and events[-1]["type"] == "turn.completed":
                outcome["status"] = "capture_incomplete"
                _capture_completed(subject, outcome)
    except (OSError, RuntimeError, TypeError, ValueError, KeyError) as error:
        outcome["error_type"] = type(error).__name__
    write_json(result_path, outcome)
    return outcome


def _capture_completed(subject: TestEvalSubject, outcome: dict[str, Any]) -> None:
    read_asset(subject.task_plan, sha256(subject.task_bytes))
    read_asset(subject.handoff / "baseline.collection.json", sha256(subject.baseline_bytes))
    initial = plan_handoff(subject.baseline_bytes, subject.baseline_bytes)
    captured = subject.output / "submission"
    observations = subject.output / "collection"
    result = capture_owned(subject.workspace, captured, observations, subject.python, initial.baseline["policy"])
    if result["status"] != "collected":
        return
    raw = read_asset(observations / "stdout.native")
    outcome["collection_manifest_sha256"] = sha256(raw)
    delivery = plan_handoff(subject.baseline_bytes, raw)
    if (
        delivery.delta["deletes"]
        or delivery.submission["directories"]
        or delivery.delta["writes"].keys() - {TEST_SUBMISSION}
    ):
        outcome["status"] = "submission_scope_changed"
        return
    if TEST_SUBMISSION not in delivery.delta["writes"]:
        outcome["status"] = "missing_submission"
        return
    outcome["status"] = "submission_invalid"
    submitted = read_evidence(captured / TEST_SUBMISSION)
    load_test_snippets(submitted)
    (subject.handoff / "submission.collection.json").write_bytes(raw)
    outcome["status"] = "seal_incomplete"
    receipt = seal(delivery, captured, subject.handoff / "submission.tar")
    outcome.update(status="sealed", archive_sha256=receipt["archive_sha256"], suite_sha256=sha256(submitted))

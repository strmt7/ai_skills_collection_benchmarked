"""Qualify a scoped anonymous native execution boundary from independent development controls."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from _native_benchmark_runtime import ProcessIdentity, sha256, write_json
from _native_trial_plan import ROOT, execution_sources, input_assets, load_plan
from _trial_provider import validate_provider
from _trial_transcript import parse_events, strict_json
from _windows_appcontainer import checked_path
from _windows_trial_process import verify_write_io_budget
from grade_swe_skills_submission import asset, source_hashes
from qualify_trial_context import EVIDENCE_NAMES as CONTEXT_EVIDENCE_NAMES
from qualify_trial_context import check as check_context

PROFILE = "windows-native-packaging-anonymous-v1"
TASK = "swe-skills-bench/batch1/python-packaging"
ATTEMPT_EVIDENCE = frozenset(
    {
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
    }
)
CASES = {
    "edited": ("complete", "task_passed", 1.0),
    "unchanged": ("complete", "task_failed", 0.0),
    "truncated": ("collection", "harness_error", None),
    "budget": ("collection", "harness_error", None),
    "accounting": ("collection", "harness_error", None),
    "logical": ("final_storage", "harness_error", None),
    "space": ("collection", "harness_error", None),
    "spaceerror": ("collection", "harness_error", None),
    "preflight-space": ("storage_preflight", "harness_error", None),
    "timeout": ("collection", "harness_error", None),
    "isolation": ("complete", "task_passed", 1.0),
}


def require(value: bool, reason: str) -> None:
    if not value:
        raise ValueError(reason)


def anonymous(provider: Any) -> bool:
    selected = validate_provider(provider)
    if selected.get("authentication") != "none":
        return False
    endpoint = urlsplit(selected["base_url"])
    return (
        endpoint.scheme == "http"
        and endpoint.hostname == "127.0.0.1"
        and endpoint.port is not None
        and endpoint.path.rstrip("/") == "/v1"
    )


def owned(path: str | Path) -> Path:
    path = checked_path(Path(path))
    require(path.is_relative_to(ROOT / ".venv") and path != ROOT / ".venv", "Use owned qualification paths")
    return path


def raw(path: Path) -> bytes:
    path = checked_path(path)
    require(path.is_file() and path.stat().st_size <= 16 * 1024**2, "Invalid or oversized qualification evidence")
    return path.read_bytes()


def document(path: Path) -> dict[str, Any]:
    value = strict_json(raw(path).decode("utf-8"))
    require(isinstance(value, dict), "Qualification evidence must be a JSON object")
    return value


def remember(path: Path, inventory: dict[str, str]) -> None:
    path = owned(path)
    inventory[str(path)] = sha256(raw(path))


def tool_output(directory: Path, inventory: dict[str, str]) -> str:
    path = directory / "request-2.native.json"
    reply = document(path)
    outputs = [
        row
        for row in reply["input"]
        if row.get("type") == "function_call_output" and row.get("call_id") == "call_owned_control"
    ]
    require(len(outputs) == 1 and isinstance(outputs[0].get("output"), str), "Missing matched tool return")
    output = outputs[0]["output"]
    require("Process exited with code 0" in output, "Native control tool did not exit successfully")
    remember(path, inventory)
    return str(output)


def control(name: str, directory: Path, positive: dict[str, Any], inventory: dict[str, str]) -> dict[str, Any]:
    attempt = directory / "attempt"
    summary, plan, result, transport = (
        document(path)
        for path in (
            directory / "summary.json",
            directory / "plan.json",
            attempt / "result.json",
            directory / "transport.json",
        )
    )
    require(summary["passed"] is True, "The control producer reported failure: " + name)
    require((result["stage"], result["status"], result["score"]) == CASES[name], "Wrong control outcome: " + name)
    require(
        all(type(value) is int and value == 0 for value in (summary["model_requests"], transport["model_requests"])),
        "Model results are not scripted controls",
    )
    require(result["score"] is None or type(result["score"]) is float, "Control score must be a native numeric score")
    require(
        summary["authentication"] == "none" and summary["credential_binding_released"] is True, "Wrong credential path"
    )
    require(
        transport["listener_stopped"] is True and not transport["errors"], "Control transport did not close cleanly"
    )
    require(transport["fallback_requests"] == 0, "Unexpected fallback route")
    require(
        all(
            row.get("authorization_present") is False and row.get("authentication") == "none"
            for row in transport["requests"]
        ),
        "Control sent an authorization header",
    )
    require(set(plan) == set(positive) and plan["schema_version"] == 3, "Control plan schema differs")
    require(plan["execution_source_sha256"] == execution_sources(), "Control execution sources changed")
    require(anonymous(plan["provider"]), "Control is not the qualified anonymous IPv4 route")
    stable = (
        "partition",
        "condition",
        "model",
        "reasoning_effort",
        "storage_limits",
        "interventions",
        "baseline_collection",
    )
    require(all(plan[key] == positive[key] for key in stable), "Controls do not share one frozen profile")
    require(plan["time_limit_seconds"] == (5 if name == "timeout" else 90), "Control deadline differs")
    require(plan["write_io_limit_bytes"] == (1 if name == "budget" else 1024**3), "Control write budget differs")
    for key, entry in input_assets(plan).items():
        asset(entry)
        require(entry["sha256"] == input_assets(positive)[key]["sha256"], "Control assets differ: " + key)
        remember(Path(entry["path"]), inventory)
    require(sha256(raw(attempt / "plan.json")) == sha256(raw(directory / "plan.json")), "Archived control plan differs")
    require(raw(attempt / "attempt.json") == raw(attempt / "result.json"), "Control lifecycle and result disagree")
    if name != "preflight-space":
        require(result["execution_source_sha256"] == execution_sources(), "Attempt sources differ")
        require(result["plan_sha256"] == sha256(raw(directory / "plan.json")), "Attempt plan digest differs")
    required = (
        {"plan.json", "setup-space.json"}
        if name == "preflight-space"
        else ATTEMPT_EVIDENCE - {"collection/result.json", "grading/result.json"}
    )
    if name in {"edited", "unchanged", "isolation"}:
        required = ATTEMPT_EVIDENCE
    require(
        isinstance(result["evidence_sha256"], dict)
        and required <= result["evidence_sha256"].keys() <= ATTEMPT_EVIDENCE,
        "Native evidence set is incomplete or unexpected",
    )
    for relative, expected in result["evidence_sha256"].items():
        path = checked_path(attempt / relative)
        require(
            path.is_relative_to(attempt) and sha256(raw(path)) == expected,
            "Native evidence digest differs: " + relative,
        )
        remember(path, inventory)
    for relative in (
        "summary.json",
        "implementation.py.txt",
        "plan.json",
        "transport.json",
        "space-injections.json",
        "attempt/result.json",
        "attempt/attempt.json",
    ):
        remember(directory / relative, inventory)
    injections_path = directory / "space-injections.json"
    injections = strict_json(raw(injections_path).decode("utf-8"))
    require(
        isinstance(injections, list)
        and len(injections) == summary["space_injections"]
        and all(row["real_disk_pressure_created"] is False for row in injections),
        "Space injections differ",
    )
    if name == "preflight-space":
        require(not (attempt / "process.json").exists() and transport["posts"] == 0, "Preflight launched a subject")
        require(
            document(attempt / "setup-space.json")["termination_reason"] == "free_space_limit" and injections,
            "Wrong preflight fault",
        )
        return {"case": name, "stage": result["stage"], "status": result["status"], "score": None}
    process = document(attempt / "process.json")
    require(
        process["windows_job"] is True
        and process["assigned_before_resume"] is True
        and process["kill_on_close"] is True
        and type(process["job_active_processes_after_cleanup"]) is int
        and process["job_active_processes_after_cleanup"] == 0,
        "Owned subject cleanup is not established",
    )
    require(
        process["job_memory_limit_bytes"] == 2 * 1024**3
        and process["active_process_limit"] == 32
        and process["output_limit_bytes"] == 8 * 1024**2
        and process["explicit_environment"] is True
        and process["wall_time_limit_seconds"] == plan["time_limit_seconds"],
        "Native resource profile differs",
    )
    verify_write_io_budget(process, plan["write_io_limit_bytes"])
    events = parse_events(raw(attempt / "transcript.jsonl"), allow_truncated_final=result["status"] == "harness_error")
    if name in {"edited", "unchanged", "isolation"}:
        require(
            process["exit_code"] == 0
            and process["termination_reason"] is None
            and any(event["type"] == "turn.completed" for event in events),
            "Native turn did not complete",
        )
        counts = (
            {"passed": 0, "failed": 10, "skipped": 1, "errors": 0, "total": 11}
            if name == "unchanged"
            else {"passed": 11, "failed": 0, "skipped": 0, "errors": 0, "total": 11}
        )
        graded = document(attempt / "grading/result.json")
        require(type(graded["score"]) is float, "Native grader score must be numeric")
        require(
            all(type(value) is int for value in graded["native_counts"].values())
            and all(type(value) is int for value in result["native_counts"].values()),
            "Native counts must be integers",
        )
        require(
            graded["native_counts"] == result["native_counts"] == counts and graded["score"] == result["score"],
            "Original native scorer counts differ",
        )
        require(
            graded["task_id"] == TASK
            and graded["execution_source_sha256"] == source_hashes()
            and graded["model_requests"] == 0,
            "Native grader profile differs",
        )
        remember(attempt / "grading/result.json", inventory)
        if name != "unchanged":
            output = tool_output(directory, inventory)
            require(
                "SUBJECT_DEPENDENCY_IMPORTS_VERIFIED" in output and "NATIVE_SUBJECT_EDIT_COMPLETED" in output,
                "Prepared imports or edits did not execute",
            )
            if name == "isolation":
                require(
                    summary["native_integrated_isolation_observed"] is True
                    and "NATIVE_INTEGRATED_ISOLATION_VERIFIED" in output,
                    "Integrated isolation probe did not execute",
                )
    else:
        require(not (attempt / "grading").exists(), "Interrupted control reached grading")
        if name == "truncated":
            require(
                process["exit_code"] != 0
                and process["termination_reason"] is None
                and any(
                    event["type"] == "turn.failed" and "stream closed before response.completed" in json.dumps(event)
                    for event in events
                ),
                "Native incomplete-stream fault not observed",
            )
            path = directory / "response-1.native.sse"
            require(b"event: response.completed" not in raw(path), "Control stream was not truncated")
            remember(path, inventory)
        elif name == "budget":
            require(
                process["termination_reason"] == "write_io_limit" and process["job_write_io_bytes"] > 1,
                "Native write limit did not trip",
            )
        elif name == "accounting":
            require(
                process["termination_reason"] == "resource_observation_error"
                and process["write_io_observation_error"]
                == {"api": "QueryInformationJobObject", "information_class": 8, "winerror": 5},
                "Wrong accounting fault",
            )
        elif name == "logical":
            observation = document(attempt / "final-storage.json")
            require(
                observation["termination_reason"] == "workspace_logical_bytes_limit"
                and observation["logical_bytes"] > plan["storage_limits"]["max_workspace_bytes"],
                "Wrong logical-size fault",
            )
        elif name in {"space", "spaceerror"}:
            reason = "free_space_limit" if name == "space" else "storage_observation_error"
            require(
                process["termination_reason"] == process["space_budget"]["termination_reason"] == reason and injections,
                "Wrong active-space fault",
            )
            if name == "spaceerror":
                require(process["space_budget"]["observation_error"]["winerror"] == 5, "Wrong native space error")
        elif name == "timeout":
            require(
                process["termination_reason"] == "timeout"
                and result["timed_out"] is True
                and summary["timeout_tool_marker_observed"] is True,
                "Timeout did not interrupt a running tool",
            )
            observations = summary["native_tool_process_observations"]
            require(
                summary["native_tool_process_stopped"] is True
                and isinstance(observations, list)
                and len(observations) == 1,
                "Actual timed-out tool termination is not established",
            )
            observed = observations[0]
            ProcessIdentity(observed["pid"], observed["creation_filetime"])
            require(
                observed.get("seen_running") is True and observed.get("stopped") is True and "error" not in observed,
                "Timed-out tool identity or cleanup countercontrol failed",
            )
    return {"case": name, "stage": result["stage"], "status": result["status"], "score": result["score"]}


def verify(specification: dict[str, Any]) -> dict[str, Any]:
    require(
        set(specification) == {"schema_version", "profile", "context_directory", "controls", "execution_source_sha256"}
        and type(specification["schema_version"]) is int
        and specification["schema_version"] == 1
        and specification["profile"] == PROFILE,
        "Invalid boundary qualification specification",
    )
    sources = execution_sources()
    require(specification["execution_source_sha256"] == sources, "Boundary specification sources changed")
    directories = specification["controls"]
    require(isinstance(directories, dict) and set(directories) == set(CASES), "The complete control matrix is required")
    paths = {name: owned(path) for name, path in directories.items()}
    require(len(set(paths.values())) == len(CASES), "Control directories must be distinct")
    positive_path = paths["edited"] / "plan.json"
    admitted = load_plan(positive_path)
    positive = admitted["plan"]
    require(
        admitted["task"]["id"] == TASK
        and positive["schema_version"] == 3
        and positive["partition"] == "development"
        and positive["condition"] == "default"
        and positive["interventions"] == [],
        "Unsupported calibration task",
    )
    context = owned(specification["context_directory"])
    context_report = check_context(context)
    require(context_report["ok"] is True, "Current native context qualification failed")
    record = document(context / "qualification.json")
    require(
        checked_path(Path(record["cli"])) == admitted["runtime"]["cli"]
        and checked_path(Path(record["python"])) == admitted["runtime"]["python"],
        "Context and control runtimes differ",
    )
    inventory: dict[str, str] = {}
    for name in (*CONTEXT_EVIDENCE_NAMES, "qualification.json"):
        remember(context / name, inventory)
    results = [control(name, paths[name], positive, inventory) for name in CASES]
    require(execution_sources() == sources, "Boundary sources changed during qualification")
    return {
        "profile": PROFILE,
        "execution_boundary_qualified": True,
        "model_transport_qualified": False,
        "model_efficacy_established": False,
        "model_inferences": 0,
        "counted_model_trials": 0,
        "execution_source_sha256": sources,
        "admission_source_sha256": sha256(raw(Path(__file__))),
        "controls": results,
        "context_checks": len(record["checks"]),
        "positive_plan": positive,
        "input_sha256": inventory,
        "scope": "Serial Windows anonymous-Responses development calibration for the frozen packaging task and qualified runtime; no other task, account, model-backend identity, efficacy or commercial-readiness claim.",
    }


def qualify(specification: Path, output: Path) -> dict[str, Any]:
    specification, output = owned(specification), owned(output)
    require(not output.exists(), "Qualification output must be new")
    frozen = raw(specification)
    validation = verify(document(specification))
    require(raw(specification) == frozen, "Boundary specification changed during qualification")
    declared = document(specification)
    protected = [owned(declared["context_directory"]), *(owned(path) for path in declared["controls"].values())]
    require(
        not any(Path(path).is_relative_to(output) for path in validation["input_sha256"])
        and not any(output.is_relative_to(path) for path in protected),
        "Qualification output overlaps control evidence",
    )
    output.mkdir(parents=True)
    (output / "specification.json").write_bytes(frozen)
    report = {"schema_version": 1, "specification_sha256": sha256(frozen), "validation": validation}
    write_json(output / "qualification.json", report)
    return report


def check(output: Path) -> dict[str, Any]:
    output = owned(output)
    record = document(output / "qualification.json")
    require(
        set(record) == {"schema_version", "specification_sha256", "validation"}
        and type(record["schema_version"]) is int
        and record["schema_version"] == 1,
        "Invalid boundary receipt",
    )
    require(
        sha256(raw(output / "specification.json")) == record["specification_sha256"],
        "Boundary specification digest differs",
    )
    current = verify(document(output / "specification.json"))
    require(current == record["validation"], "Boundary qualification evidence changed")
    return current


@dataclass(frozen=True)
class QualifiedNativeTrial:
    plan_sha256: str
    receipt_sha256: str
    profile: str
    receipt_path: Path
    input_sha256: tuple[tuple[str, str], ...]
    admission_source_sha256: str


def verify_binding(qualification: QualifiedNativeTrial) -> None:
    require(sha256(raw(Path(__file__))) == qualification.admission_source_sha256, "Boundary admission source changed")
    require(sha256(raw(qualification.receipt_path)) == qualification.receipt_sha256, "Boundary receipt changed")
    for path, expected in qualification.input_sha256:
        require(sha256(raw(owned(path))) == expected, "Boundary evidence changed: " + path)


def admit(plan_path: Path, qualification: Path) -> QualifiedNativeTrial:
    receipt = owned(qualification) / "qualification.json"
    frozen = raw(receipt)
    validation = check(qualification)
    admitted = load_plan(plan_path)
    plan, positive = admitted["plan"], validation["positive_plan"]
    require(
        plan["schema_version"] == 3 and plan["partition"] == "development" and anonymous(plan["provider"]),
        "Profile permits anonymous development only",
    )
    for key in ("model", "reasoning_effort", "storage_limits", "write_io_limit_bytes", "baseline_collection"):
        require(plan[key] == positive[key], "Trial differs from the qualified profile: " + key)
    for key in ("task", "subject_runtime", "grader_runtime"):
        require(plan[key]["sha256"] == positive[key]["sha256"], "Trial uses an unqualified asset: " + key)
    require(raw(receipt) == frozen, "Boundary receipt changed during admission")
    return QualifiedNativeTrial(
        admitted["plan_sha256"],
        sha256(frozen),
        PROFILE,
        receipt,
        tuple(sorted(validation["input_sha256"].items())),
        validation["admission_source_sha256"],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--specification", type=Path)
    mode.add_argument("--check", type=Path, metavar="QUALIFICATION_DIRECTORY")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", help="Include the full qualification validation envelope")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.check:
            require(args.output is None, "Check mode does not write output")
            validation = check(args.check)
        else:
            require(args.output is not None, "Qualification requires --output")
            validation = qualify(args.specification, args.output)["validation"]
        report = {
            "ok": True,
            **{
                key: validation[key]
                for key in (
                    "profile",
                    "execution_boundary_qualified",
                    "model_transport_qualified",
                    "model_inferences",
                    "counted_model_trials",
                )
            },
            "controls": len(validation["controls"]),
            "context_checks": validation["context_checks"],
        }
        if args.json:
            report["validation"] = validation
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        report = {"ok": False, "errors": [str(error)], "model_inferences": 0}
    print(json.dumps(report, sort_keys=True))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

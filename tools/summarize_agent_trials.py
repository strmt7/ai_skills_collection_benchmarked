#!/usr/bin/env python3
"""Verify every planned matched attempt and publish descriptive coding-agent results."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import tempfile
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from _lib_b.io_utils import dumps_deterministic, write_json, write_text
from _trial_collection_contract import process_complete, verify_collector_launch
from _trial_collection_manifest import validate_manifest
from _trial_comparisons import STATUSES, compare_blocks
from _trial_comparisons import verify_usage as _verify_usage
from _trial_execution_evidence import (
    FAILURE_OBSERVATIONS,
    failure_measurements,
    verify_attempt,
    verify_launch,
    verify_process,
)
from _trial_grading_process import (
    DRIVER_EXIT_CODES,
    DRIVER_PROCESS,
    DRIVER_SOURCE,
    DRIVER_STDERR,
    DRIVER_STDOUT,
    driver_completed,
)
from _trial_manifest import read_grading_manifest, validate_grade_checks
from _trial_prompt import verify_prompt
from _trial_protocol import validate_declaration
from _trial_transcript import parse_events, strict_json
from _trial_workspace_changes import workspace_changes

LIMITATIONS = [
    "Quality is checked externally; agent-written regression tests are not a coverage or mutation score.",
    "Token statistics are descriptive actual CLI usage, not priced cost, significance, or general efficiency claims.",
    "Input tokens include cached input; reasoning usage is retained separately, not added again to output tokens.",
    "Elapsed time is diagnostic only unless host and workload conditions are controlled.",
    "A requested model name does not verify its provider-resolved snapshot; availability is recorded per attempt.",
    "This report includes only attempts declared in its frozen protocol; other experiments are not pooled.",
    "The grading process executes submitted Python on the host; it is not a hardened service for arbitrary untrusted submissions.",
    "A case manifest checks the reported denominator but cannot independently prove that the grader ran "
    "or that observations are authentic.",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    """Reject ambiguous or non-finite JSON in recorded trial metadata."""
    return strict_json(path.read_text(encoding="utf-8"))


def evidence_path(directory: Path, relative: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError("evidence names must be strings")
    name = PurePosixPath(relative)
    if name.is_absolute() or ".." in name.parts or "\\" in relative or ":" in relative or name.as_posix() != relative:
        raise ValueError("evidence names must be safe relative POSIX paths")
    path = directory / relative
    if not path.resolve().is_relative_to(directory.resolve()) or path.is_symlink():
        raise ValueError(f"external evidence: {relative}")
    return path


def evidence_bytes(directory: Path, relative: str) -> bytes:
    path = evidence_path(directory, relative)
    if path.is_file():
        return path.read_bytes()
    if path.exists():
        raise ValueError(f"evidence must be a file: {relative}")
    # The frozen runner recorded grader-created bytecode. Git rightly ignores
    # loose cache files; preserve their exact bytes in a nonexecuted transport.
    archive = directory / "bytecode-evidence.zip"
    if (
        "__pycache__" not in PurePosixPath(relative).parts
        or not relative.endswith(".pyc")
        or not archive.is_file()
        or archive.is_symlink()
    ):
        raise ValueError(f"missing evidence: {relative}")
    with zipfile.ZipFile(archive) as zipped:
        if sum(info.file_size for info in zipped.infolist()) > 16 * 1024 * 1024 or len(zipped.namelist()) != len(
            set(zipped.namelist())
        ):
            raise ValueError("bytecode evidence archive is oversized or ambiguous")
        try:
            return zipped.read(relative)
        except KeyError as exc:
            raise ValueError(f"missing bytecode evidence: {relative}") from exc


def package_bytecode(directory: Path, evidence: dict[str, str]) -> None:
    names = sorted(name for name in evidence if "__pycache__" in PurePosixPath(name).parts and name.endswith(".pyc"))
    if not names:
        return
    archive = directory / "bytecode-evidence.zip"
    if archive.exists():
        with zipfile.ZipFile(archive) as zipped:
            if zipped.namelist() != names or any(
                hashlib.sha256(zipped.read(name)).hexdigest() != evidence[name] for name in names
            ):
                raise ValueError("existing bytecode transport differs from the frozen evidence")
        return
    contents = {name: evidence_bytes(directory, name) for name in names}
    if any(hashlib.sha256(contents[name]).hexdigest() != evidence[name] for name in names):
        raise ValueError("cannot package changed bytecode evidence")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_STORED) as zipped:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o100644 << 16
            zipped.writestr(info, contents[name])


def verify_transcript(directory: Path, result: dict[str, Any]) -> None:
    """Cross-check recorded completion, usage and command counts with the native event stream."""
    allow_truncated = result["status"] in {"harness_error", "timed_out"} and (
        result["status"] == "timed_out" or result.get("process_exit_code") != 0
    )
    raw = evidence_bytes(directory, "transcript.jsonl")
    try:
        events = parse_events(raw, allow_truncated_final=allow_truncated)
    except ValueError as exc:
        if (
            result["status"] in {"harness_error", "timed_out"}
            and result.get("transcript_error") == str(exc)
            and result.get("usage") is None
            and result.get("commands_completed") is None
        ):
            return
        raise
    if result.get("transcript_error") is not None:
        raise ValueError("transcript error is not supported by the recorded events")
    completed = [event for event in events if event["type"] == "turn.completed"]
    if len(completed) > 1 or (result["status"] in {"task_passed", "task_failed", "invalid_scope"} and not completed):
        raise ValueError("transcript does not establish a single completed turn")
    usage = completed[0].get("usage") if completed else None
    commands = sum(
        event["type"] == "item.completed" and event["item"].get("type") == "command_execution" for event in events
    )
    if (
        json.dumps(result.get("usage"), sort_keys=True) != json.dumps(usage, sort_keys=True)
        or type(result.get("commands_completed")) is not int
        or result["commands_completed"] != commands
    ):
        raise ValueError("transcript disagrees with recorded usage or command count")


def _verify_identity(result: dict[str, Any], protocol: dict[str, Any], protocol_hash: str, condition: str) -> None:
    """Check the attempt's protocol, condition, status and exit-code identity."""
    expected = {
        "protocol_sha256": protocol_hash,
        "task_id": protocol["task"]["id"],
        "partition": protocol["task"]["partition"],
        "condition": condition,
        "model_requested": protocol["model"],
        "reasoning_effort_requested": protocol["reasoning_effort"],
    }
    if any(result.get(key) != value for key, value in expected.items()):
        raise ValueError("attempt differs from its frozen protocol or assigned condition")
    if result.get("status") not in STATUSES:
        raise ValueError("unknown attempt outcome")
    if "process_exit_code" not in result or (
        result["process_exit_code"] is not None and type(result["process_exit_code"]) is not int
    ):
        raise ValueError("process exit code must be an integer or unavailable")


def _verify_evidence(directory: Path, result: dict[str, Any], protocol_hash: str) -> bytes:
    """Validate the retained files, transcript and launch protocol binding."""
    evidence = result.get("evidence_sha256")
    if not isinstance(evidence, dict) or not {
        "launch.json",
        "transcript.jsonl",
        "prompt.txt",
        "stderr.txt",
        "patch.diff",
    }.issubset(evidence):
        raise ValueError("attempt evidence manifest is incomplete")
    prompt = b""
    for relative, digest in evidence.items():
        content = evidence_bytes(directory, relative)
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError(f"evidence hash changed: {relative}")
        if relative == "prompt.txt":
            prompt = content
    verify_transcript(directory, result)
    launch = read_json(directory / "launch.json")
    if not isinstance(launch, dict) or launch.get("protocol_sha256") != protocol_hash:
        raise ValueError("launch used a different frozen protocol")
    return prompt


def _verify_v4_inventory(directory: Path, result: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    """Reject undeclared paths before opening any file from the evidence inventory."""
    if not isinstance(result.get("evidence_sha256"), dict):
        raise ValueError("trial evidence inventory must be a digest mapping")
    if result.get("attempt_phase") != "finished":
        raise ValueError("executed trial requires a finished attempt lifecycle record")
    if result.get("provider_model_snapshot") is not None:
        raise ValueError("provider-resolved model identity has no qualified evidence source")
    if result.get("latency_claim_eligible") is not False:
        raise ValueError("modern trial elapsed time remains diagnostic only")
    evidence = set(result["evidence_sha256"])
    required = {
        "attempt.json",
        "launch.json",
        "process.json",
        "input.native",
        "prompt.txt",
        "transcript.jsonl",
        "stderr.txt",
        "patch.diff",
        "workspace-changes.json",
        "collection/launch.json",
        "collection/input.native",
        "collection/process.json",
        "collection/result.json",
    }
    allowed = required | {
        "collection/stdout.native",
        "collection/stderr.native",
        DRIVER_STDOUT,
        DRIVER_STDERR,
        DRIVER_PROCESS,
    }
    streams = {DRIVER_STDOUT, DRIVER_STDERR}
    if DRIVER_SOURCE in protocol["execution_source_sha256"] and streams & evidence:
        required |= streams | {DRIVER_PROCESS}
    grade = result["grader"]
    if grade.get("status") in {"task_passed", "task_failed"}:
        grading = {
            "grading/result.json",
            "grading/checks.json",
            *streams,
        }
        for check in grade["checks"]:
            relative = check.get("observation_directory")
            if not isinstance(relative, str) or re.fullmatch(r"case-[0-9a-f]{32}/observations", relative) is None:
                raise ValueError("grading stream directory is not a declared confined observation")
            grading.update(f"grading/{relative}/{stream}.native" for stream in ("stdout", "stderr"))
        required |= grading
        allowed |= grading
    if not required.issubset(evidence) or any(
        name not in allowed and not name.startswith("submission/") for name in evidence
    ):
        raise ValueError("trial evidence inventory contains missing or undeclared outputs")
    raw = evidence_bytes(directory, "collection/result.json")
    if hashlib.sha256(raw).hexdigest() != result["evidence_sha256"]["collection/result.json"]:
        raise ValueError("source capture metadata hash changed")
    manifest = strict_json(raw.decode("utf-8"))
    if not isinstance(manifest, dict) or manifest.get("status") not in {"collected", "collection_error"}:
        raise ValueError("source capture outcome is unavailable")
    if manifest["status"] == "collected":
        validate_manifest(manifest, protocol["collection_policy"])
        submission = {"submission/" + name for name in manifest["files"]}
        required |= submission | {"collection/stdout.native", "collection/stderr.native"}
        allowed |= submission
    elif result["status"] in {"task_passed", "task_failed", "invalid_scope"}:
        raise ValueError("incomplete source collection cannot be scored")
    if not required.issubset(evidence) or not evidence.issubset(allowed):
        raise ValueError("trial evidence inventory contains missing or undeclared outputs")
    return manifest


def _verify_v4_execution(
    directory: Path, result: dict[str, Any], protocol: dict[str, Any], prompt: bytes, manifest: dict[str, Any]
) -> None:
    """Cross-check native launch, prompt, process bounds and grading transport records."""
    grade = result["grader"]
    if grade.get("status") in {"task_passed", "task_failed"}:
        stdout = evidence_bytes(directory, DRIVER_STDOUT)
        if strict_json(stdout.decode("utf-8")) != grade:
            raise ValueError("recorded grader differs from its native driver response")
        if DRIVER_SOURCE in protocol["execution_source_sha256"] or DRIVER_PROCESS in result["evidence_sha256"]:
            process = strict_json(evidence_bytes(directory, DRIVER_PROCESS).decode("utf-8"))
            stderr = evidence_bytes(directory, DRIVER_STDERR)
            if (
                not driver_completed(process, len(stdout) + len(stderr))
                or process["exit_code"] != DRIVER_EXIT_CODES[grade["status"]]
            ):
                raise ValueError("scored grading result lacks a matching completed native process")
    raw_input = evidence_bytes(directory, "input.native")
    if raw_input not in (prompt, prompt.replace(b"\r\n", b"\n")):
        raise ValueError("native model input differs from the captured prompt")
    if evidence_bytes(directory, "collection/input.native") != b"":
        raise ValueError("source collector requires an empty native input stream")
    changes_record = read_json(directory / "workspace-changes.json")
    if not isinstance(changes_record, dict):
        raise ValueError("source namespace change record is unavailable")
    if manifest["status"] == "collected":
        changes, source_changes, violations = workspace_changes(protocol, manifest)
        if (
            result.get("changed_source_files") != source_changes
            or result.get("scope_violations") != violations
            or changes_record.get("complete") is not True
            or changes_record.get("changes") != changes
        ):
            raise ValueError("reported source changes or scope violations disagree with collected input digests")
        raw = evidence_bytes(directory, "collection/stdout.native")
        if strict_json(raw.decode("utf-8")) != manifest:
            raise ValueError("source capture receipt differs from its native worker response")
        if any(
            result["evidence_sha256"]["submission/" + name] != data["sha256"]
            or len(evidence_bytes(directory, "submission/" + name)) != data["bytes"]
            for name, data in manifest["files"].items()
        ):
            raise ValueError("collected source bytes differ from the source capture receipt")
        process = read_json(directory / "collection/process.json")
        if not process_complete(
            process,
            protocol["collection_policy"],
            len(raw) + len(evidence_bytes(directory, "collection/stderr.native")),
        ):
            raise ValueError("source capture process did not complete within its declared bounds")
    elif (
        result.get("evidence_collection_errors") == []
        or changes_record.get("complete") is not False
        or changes_record.get("changes") != []
        or result.get("changed_source_files") != []
        or result.get("scope_violations") != []
    ):
        raise ValueError("source capture failure must retain unavailable scope and collection errors")
    attempt = read_json(directory / "attempt.json")
    verify_attempt(attempt, result["protocol_sha256"], result["condition"], "finished")
    launch = read_json(directory / "launch.json")
    verify_launch(launch, protocol)
    if attempt["workspace"] != launch["context"]["workspace"]:
        raise ValueError("attempt workspace differs from its recorded launch")
    verify_collector_launch(
        read_json(directory / "collection/launch.json"), protocol["collection_policy"], attempt["workspace"]
    )
    verify_process(
        read_json(directory / "process.json"),
        result,
        sum(len(evidence_bytes(directory, name)) for name in ("transcript.jsonl", "stderr.txt")),
        protocol["time_limit_seconds"],
    )


def _verify_failed_attempt(directory: Path, result: dict[str, Any]) -> None:
    """Retain terminal infrastructure failures without claiming observed execution."""
    phase = result["attempt_phase"]
    error_name = "setup-error.json" if phase == "setup_failed" else "controller-error.json"
    nulls = {"provider_model_snapshot"}
    if phase == "setup_failed":
        nulls |= {"usage", "process_exit_code", "commands_completed", "transcript_error"}
    if (
        result["status"] != "harness_error"
        or not nulls.issubset(result)
        or any(result[key] is not None for key in nulls)
        or result.get("latency_claim_eligible") is not False
        or any(result.get(key) != [] for key in ("changed_source_files", "scope_violations"))
        or not isinstance(result.get("evidence_collection_errors"), list)
        or any(not isinstance(value, str) or not value for value in result["evidence_collection_errors"])
        or result["grader"].get("status") != "harness_error"
        or set(result["grader"]) != {"status", "error"}
        or not isinstance(result["grader"]["error"], str)
        or not result["grader"]["error"]
        or type(result.get("elapsed_seconds")) not in (int, float)
        or not math.isfinite(result["elapsed_seconds"])
        or result["elapsed_seconds"] < 0
    ):
        raise ValueError("infrastructure failure cannot contain task scores, execution counts or invented usage")
    evidence = result.get("evidence_sha256")
    required, allowed = (
        {"attempt.json", error_name},
        FAILURE_OBSERVATIONS[phase],
    )
    if not isinstance(evidence, dict) or not required.issubset(evidence) or not set(evidence).issubset(allowed):
        raise ValueError("infrastructure failure has an invalid evidence inventory")
    if phase == "setup_failed" and any(
        (directory / name).exists() or (directory / name).is_symlink()
        for name in (
            "input.native",
            "process.json",
            "transcript.jsonl",
            "stderr.txt",
            "grading",
            DRIVER_STDOUT,
            DRIVER_STDERR,
            DRIVER_PROCESS,
        )
    ):
        raise ValueError("setup failure contains evidence of a model launch attempt")
    for name, digest in evidence.items():
        if hashlib.sha256(evidence_bytes(directory, name)).hexdigest() != digest:
            raise ValueError(f"failure evidence hash changed: {name}")
    if phase == "controller_failed":
        measured = failure_measurements(
            *(
                evidence_bytes(directory, name) if name in evidence else None
                for name in ("transcript.jsonl", "process.json")
            )
        )
        if not set(measured).issubset(result) or any(
            json.dumps(result[key], sort_keys=True) != json.dumps(value, sort_keys=True)
            for key, value in measured.items()
        ):
            raise ValueError("failure measurements disagree with retained native observations")
    attempt = read_json(directory / "attempt.json")
    verify_attempt(attempt, result["protocol_sha256"], result["condition"], phase)
    error = read_json(directory / error_name)
    if (
        not isinstance(error, dict)
        or set(error) != {"stage", "error_type", "errno", "winerror"}
        or error["stage"] != attempt["stage"]
        or not isinstance(error["error_type"], str)
        or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", error["error_type"]) is None
        or any(error[name] is not None and type(error[name]) is not int for name in ("errno", "winerror"))
    ):
        raise ValueError("failure metadata disagrees with its lifecycle record")


def _verify_checks(
    result: dict[str, Any], expected_cases: frozenset[str]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Validate the external grader's cases and complete scored denominator."""
    grade = result.get("grader")
    if not isinstance(grade, dict):
        raise ValueError("external grader result is unavailable")
    if not isinstance(grade.get("status"), str) or grade["status"] not in {
        "task_passed",
        "task_failed",
        "harness_error",
    }:
        raise ValueError("external grader result has an unknown status")
    checks = validate_grade_checks(grade, expected_cases, scored=result["status"] in {"task_passed", "task_failed"})
    return grade, checks


def _verify_scored_outcome(
    result: dict[str, Any], grade: dict[str, Any], checks: list[dict[str, Any]], clean_execution: bool
) -> None:
    """Require scored outcomes to agree with grading and scope evidence."""
    status = result["status"]
    if status not in {"task_passed", "task_failed"}:
        return
    if (
        not checks
        or all(check["passed"] for check in checks) != (status == "task_passed")
        or grade.get("status") != status
        or not clean_execution
        or result.get("scope_violations") != []
    ):
        label = "pass" if status == "task_passed" else "task failure"
        raise ValueError(f"reported {label} is contradicted by grading, execution, or collection evidence")


def _verify_scope_outcome(result: dict[str, Any], clean_execution: bool) -> None:
    """Require an invalid-scope outcome to contain actual scope violations."""
    if result["status"] != "invalid_scope":
        return
    violations = result.get("scope_violations")
    if (
        not clean_execution
        or not isinstance(violations, list)
        or not violations
        or any(not isinstance(violation, str) or not violation for violation in violations)
    ):
        raise ValueError("reported scope violation is not supported by execution and scope evidence")


def _verify_outcome(result: dict[str, Any], grade: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    """Reject pass, failure or scope labels contradicted by execution evidence."""
    clean_execution = (
        type(result.get("process_exit_code")) is int
        and result["process_exit_code"] == 0
        and result.get("evidence_collection_errors") == []
    )
    _verify_scored_outcome(result, grade, checks, clean_execution)
    _verify_scope_outcome(result, clean_execution)


def verify_result(
    directory: Path, protocol: dict[str, Any], protocol_hash: str, condition: str, expected_cases: frozenset[str]
) -> tuple[dict[str, Any], tuple[str, bytes | None]]:
    """Verify an attempt's identity, evidence, grading outcome and usage."""
    result = read_json(directory / "result.json")
    if not isinstance(result, dict):
        raise ValueError("trial result must be an object")
    _verify_identity(result, protocol, protocol_hash, condition)
    grade, checks = _verify_checks(result, expected_cases)
    if protocol.get("protocol_version") == 4:
        validate_declaration(protocol, condition)
        if isinstance(result.get("attempt_phase"), str) and result["attempt_phase"] in FAILURE_OBSERVATIONS:
            _verify_failed_attempt(directory, result)
            _verify_usage(result)
            return result, ("unavailable", None)
        manifest = _verify_v4_inventory(directory, result, protocol)
    prompt = _verify_evidence(directory, result, protocol_hash)
    runtime = verify_prompt(prompt, protocol, condition)
    if protocol.get("protocol_version") == 4:
        _verify_v4_execution(directory, result, protocol, prompt, manifest)
    _verify_outcome(result, grade, checks)
    _verify_usage(result)
    return result, runtime


def prompt_runtime_evidence(
    runtimes: dict[tuple[int, str], tuple[str, bytes | None]], conditions: set[str]
) -> dict[str, Any]:
    """Compare recorded prompt path text within each block without publishing paths."""
    repetitions = {repetition for repetition, _ in runtimes}
    if (
        not repetitions
        or any(type(repetition) is not int or repetition < 1 for repetition in repetitions)
        or set(runtimes) != {(repetition, condition) for repetition in repetitions for condition in conditions}
        or any(
            status not in {"recorded", "not_requested", "ambiguous", "unavailable"}
            or (status == "recorded" and (not isinstance(path, bytes) or not path))
            or (status != "recorded" and path is not None)
            for status, path in runtimes.values()
        )
    ):
        raise ValueError("invalid prompt runtime evidence")
    counts = Counter(status for status, _ in runtimes.values())
    comparisons = {}
    if "default" in conditions:
        for condition in sorted(conditions - {"default"}):
            pairs: Counter[str] = Counter()
            for repetition in sorted(repetitions):
                baseline, candidate = runtimes[repetition, "default"], runtimes[repetition, condition]
                if baseline[0] != "recorded" or candidate[0] != "recorded":
                    pairs["unavailable_pairs"] += 1
                elif baseline[1] == candidate[1]:
                    pairs["same_recorded_path"] += 1
                else:
                    pairs["different_recorded_path"] += 1
            comparisons[condition] = {
                "planned_pairs": len(repetitions),
                "same_recorded_path": pairs["same_recorded_path"],
                "different_recorded_path": pairs["different_recorded_path"],
                "unavailable_pairs": pairs["unavailable_pairs"],
            }
    return {
        **({"unavailable_attempts": counts["unavailable"]} if counts["unavailable"] else {}),
        "recorded_attempts": counts["recorded"],
        "not_requested_attempts": counts["not_requested"],
        "ambiguous_attempts": counts["ambiguous"],
        "comparisons": comparisons,
    }


def summarize(protocol_path: Path, trials: Path, *, package_caches: bool = False) -> dict[str, Any]:
    protocol_bytes = protocol_path.read_bytes()
    protocol = strict_json(protocol_bytes.decode("utf-8"))
    if not isinstance(protocol, dict):
        raise ValueError("trial protocol must be an object")
    if protocol.get("protocol_version") == 4:
        validate_declaration(protocol)
    protocol_hash = hashlib.sha256(protocol_bytes).hexdigest()
    expected_cases, manifest_hash = read_grading_manifest(protocol_path, protocol, protocol_hash)
    rows, planned_paths = [], set()
    runtimes: dict[tuple[int, str], tuple[str, bytes | None]] = {}
    repetitions = set()
    conditions = set(protocol["conditions"])
    for block in protocol["planned_order"]:
        repetition = block["repetition"]
        if (
            type(repetition) is not int
            or repetition < 1
            or repetition in repetitions
            or len(block["conditions"]) != len(conditions)
            or set(block["conditions"]) != conditions
        ):
            raise ValueError("every repetition must assign every condition exactly once")
        repetitions.add(repetition)
        for condition in block["conditions"]:
            if not condition.replace("-", "").replace("_", "").isalnum():
                raise ValueError("unsafe condition name")
            relative = f"repetition-{repetition}/{condition}"
            planned_paths.add(relative + "/result.json")
            directory = trials / relative
            if not (directory / "result.json").is_file():
                raise ValueError(f"planned attempt has not completed: {relative}")
            result, runtime = verify_result(directory, protocol, protocol_hash, condition, expected_cases)
            runtimes[repetition, condition] = runtime
            if package_caches:
                package_bytecode(directory, result["evidence_sha256"])
            rows.append(
                {
                    "repetition": repetition,
                    "condition": condition,
                    "status": result["status"],
                    "checks_passed": result["grader"].get("checks_passed"),
                    "checks_total": result["grader"].get("checks_total"),
                    "usage": result.get("usage"),
                    "elapsed_seconds_diagnostic_only": result.get("elapsed_seconds"),
                    "provider_model_snapshot": result.get("provider_model_snapshot"),
                    "result_path": relative + "/result.json",
                    "result_sha256": sha256(directory / "result.json"),
                    "bytecode_transport_sha256": sha256(directory / "bytecode-evidence.zip")
                    if (directory / "bytecode-evidence.zip").is_file()
                    else None,
                }
            )
    if not rows:
        raise ValueError("protocol contains no planned attempts")
    observed_results = (
        trials.glob("*/*/result.json") if protocol.get("protocol_version") == 4 else trials.rglob("result.json")
    )
    observed_paths = {path.relative_to(trials).as_posix() for path in observed_results}
    if observed_paths != planned_paths:
        raise ValueError("trial directory includes unplanned results; refusing selective or duplicate accounting")
    manifest_path = protocol_path.with_name(protocol_path.stem + ".grading.json")
    if manifest_path.is_symlink() or sha256(protocol_path) != protocol_hash or sha256(manifest_path) != manifest_hash:
        raise ValueError("trial protocol or grading manifest changed during verification")
    summaries = {}
    for condition in sorted(conditions):
        matched = [row for row in rows if row["condition"] == condition]
        usage = [row["usage"] for row in matched if row["usage"] is not None]
        summaries[condition] = {
            "planned_attempts": len(matched),
            "status_counts": dict(sorted(Counter(row["status"] for row in matched).items())),
            "task_passes": sum(row["status"] == "task_passed" for row in matched),
            "usage_observed_attempts": len(usage),
            "usage_unavailable_attempts": len(matched) - len(usage),
            "token_statistics": {
                key: {
                    "sum": sum(record[key] for record in usage),
                    "median": statistics.median(record[key] for record in usage),
                    "min": min(record[key] for record in usage),
                    "max": max(record[key] for record in usage),
                }
                for key in ("input_tokens", "output_tokens")
            }
            if usage
            else None,
        }
    return {
        "report_version": 2,
        "protocol_sha256": protocol_hash,
        "grading_manifest_sha256": manifest_hash,
        "expected_grading_cases": len(expected_cases),
        "task_id": protocol["task"]["id"],
        "partition": protocol["task"]["partition"],
        "model_requested": protocol["model"],
        "reasoning_effort_requested": protocol["reasoning_effort"],
        "task_count": 1,
        "planned_attempts": len(rows),
        "completed_attempts": len(rows),
        "conditions": summaries,
        "attempts": rows,
        "block_comparison": compare_blocks(rows, conditions),
        "prompt_runtime_evidence": prompt_runtime_evidence(runtimes, conditions),
        "quality_superiority_established": False,
        "limitations": [
            f"One task and {len(repetitions)} matched {'attempt' if len(repetitions) == 1 else 'attempts'} "
            "per condition do not establish collection-wide effectiveness.",
            *[
                "Grading uses the declared confined Windows runtime; consistency checks do not authenticate "
                "execution or qualify a service for arbitrary untrusted submissions."
                if protocol.get("protocol_version") == 4 and item.startswith("The grading process executes")
                else item
                for item in LIMITATIONS
            ],
            *protocol.get("limitations", []),
        ],
    }


def _format_token_interval(deltas: dict[str, Any] | None, key: str) -> str:
    """Format an observed interval without inventing a value for missing usage."""
    if deltas is None:
        return "unavailable"
    stats = deltas[key]
    return f"{stats['median']:,} [{stats['min']:,}, {stats['max']:,}]"


def _render_block_comparison(comparison: dict[str, Any]) -> list[str]:
    """Show every planned outcome and the observed success-conditional token deltas."""
    if comparison["baseline"] is None:
        return ["", "No block comparison is available because the protocol has no default condition."]
    if not comparison["comparisons"]:
        return []
    lines = [
        "",
        "## Repetition-block comparison with default",
        "",
        "Blocks follow the protocol's planned repetitions; a shared random seed or causal effect is not implied. "
        "Unscored includes harness errors, invalid scope and timeouts.",
        "",
        "| Condition | Planned blocks | Both pass | Only condition passes | Only default passes | Neither passes | Unscored |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, value in comparison["comparisons"].items():
        outcomes = value["outcomes"]
        lines.append(
            f"| {name} | {value['planned_blocks']} | {outcomes['both_passed']} | "
            f"{outcomes['candidate_only_passed']} | {outcomes['baseline_only_passed']} | "
            f"{outcomes['neither_passed']} | {outcomes['unscored']} |"
        )
    lines += [
        "",
        "Token differences are condition minus default, only where both passed and both usages are available. "
        "They are descriptive, success-conditional observations; they do not establish a causal or efficiency advantage.",
        "",
        "| Condition | Comparable / both-pass blocks | Input token difference, median [min, max] | Output token difference, median [min, max] |",
        "| --- | --- | --- | --- |",
    ]
    for name, value in comparison["comparisons"].items():
        deltas = value["token_deltas"]

        lines.append(
            f"| {name} | {value['token_comparable_blocks']}/{value['outcomes']['both_passed']} | "
            f"{_format_token_interval(deltas, 'input_tokens')} | {_format_token_interval(deltas, 'output_tokens')} |"
        )
    return lines


def render(report: dict[str, Any]) -> str:
    lines = [
        f"# Matched {report['partition']} trials",
        "",
        f"Task: `{report['task_id']}`. Requested model: `{report['model_requested']}` with `{report['reasoning_effort_requested']}` reasoning.",
        "",
        f"All {report['planned_attempts']} planned attempts are recorded. No quality superiority is established.",
        f"Each scored attempt must report all {report['expected_grading_cases']} cases in the grading manifest "
        f"(`{report['grading_manifest_sha256']}`).",
        "",
        "| Condition | Task passes / planned | Observed usage | Input tokens, median [min–max] | Output tokens, median [min–max] |",
        "| --- | --- | --- | --- | --- |",
    ]
    for condition, values in report["conditions"].items():
        stats = values["token_statistics"]

        def token_range(key: str, stats: dict[str, Any] | None = stats) -> str:
            return (
                "unavailable"
                if stats is None
                else f"{stats[key]['median']:,} [{stats[key]['min']:,}–{stats[key]['max']:,}]"
            )

        lines.append(
            f"| {condition} | {values['task_passes']}/{values['planned_attempts']} | {values['usage_observed_attempts']}/{values['planned_attempts']} | {token_range('input_tokens')} | {token_range('output_tokens')} |"
        )
    lines += _render_block_comparison(report["block_comparison"])
    runtime = report["prompt_runtime_evidence"]
    lines += [
        "",
        "## Runtime paths recorded in prompts",
        "",
        f"Path text is available for {runtime['recorded_attempts']} attempts; "
        f"{runtime['not_requested_attempts']} did not request a path and {runtime['ambiguous_attempts']} were ambiguous.",
    ]
    if runtime.get("unavailable_attempts", 0):
        missing = runtime["unavailable_attempts"]
        lines.append(
            f"Executed prompt evidence is unavailable for {missing} infrastructure-failed {'attempt' if missing == 1 else 'attempts'}."
        )
    if runtime["comparisons"]:
        lines += [
            "",
            "| Condition | Same path text | Different path text | Unavailable pairs |",
            "| --- | ---: | ---: | ---: |",
        ]
        for condition, evidence in runtime["comparisons"].items():
            lines.append(
                f"| {condition} | {evidence['same_recorded_path']} | {evidence['different_recorded_path']} | {evidence['unavailable_pairs']} |"
            )
    lines += [
        "",
        "Path text is not published here. Equal text does not prove the same runtime was used; "
        "different text may identify the same runtime.",
    ]
    lines += [
        "",
        "Input counts include cached input. Output counts are reported as returned by the CLI. These are descriptive tokens, not priced costs or statistically demonstrated efficiency gains.",
        "",
        "Condition definitions and run order are recorded in the associated protocol. Other experiments are not pooled into this report.",
        "",
        "## Limits",
        "",
    ]
    lines += [f"- {limitation}" for limitation in report["limitations"]]
    return "\n".join(lines) + "\n"


def plots(report: dict[str, Any], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"svg.hashsalt": report["protocol_sha256"], "svg.fonttype": "none", "font.size": 10})
    conditions = sorted(report["conditions"])
    colors = ["#2563eb", "#059669", "#d97706"]
    figure, axis = plt.subplots(figsize=(7.6, 4.6), layout="constrained")
    values = [report["conditions"][condition] for condition in conditions]
    passed = [value["status_counts"].get("task_passed", 0) for value in values]
    failed = [value["status_counts"].get("task_failed", 0) for value in values]
    unscored = [
        sum(count for status, count in value["status_counts"].items() if status not in {"task_passed", "task_failed"})
        for value in values
    ]
    planned = [value["planned_attempts"] for value in values]
    passed_fraction = [count / total for count, total in zip(passed, planned, strict=True)]
    failed_fraction = [count / total for count, total in zip(failed, planned, strict=True)]
    unscored_fraction = [count / total for count, total in zip(unscored, planned, strict=True)]
    axis.bar(conditions, passed_fraction, label="Passed", color="#059669")
    axis.bar(conditions, failed_fraction, bottom=passed_fraction, label="Failed", color="#b91c1c")
    bottom = [left + right for left, right in zip(passed_fraction, failed_fraction, strict=True)]
    axis.bar(conditions, unscored_fraction, bottom=bottom, label="Unscored", color="#6b7280")
    for index, (passed_count, failed_count, unscored_count) in enumerate(zip(passed, failed, unscored, strict=True)):
        axis.text(
            index,
            1.02,
            f"{passed_count} pass / {failed_count} fail / {unscored_count} unscored",
            ha="center",
            fontsize=8,
        )
    axis.set(
        ylim=(0, 1.16),
        ylabel="Fraction of planned attempts",
        title=f"One {report['partition']} task; no demonstrated quality advantage",
    )
    axis.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=3, frameon=False)
    figure.savefig(output / "quality.svg", metadata={"Date": None, "Creator": "summarize_agent_trials.py"})
    figure.savefig(output / "quality.png", dpi=150, metadata={"Software": "summarize_agent_trials.py"})
    plt.close(figure)
    figure, axes = plt.subplots(1, 2, figsize=(10, 4.2), layout="constrained")
    for axis, key, title in zip(
        axes,
        ("input_tokens", "output_tokens"),
        ("Input tokens, including cached input", "Output tokens, as reported by CLI"),
        strict=True,
    ):
        for index, condition in enumerate(conditions):
            rows = [row for row in report["attempts"] if row["condition"] == condition and row["usage"] is not None]
            axis.scatter(
                [index + (i - (len(rows) - 1) / 2) * 0.1 for i in range(len(rows))],
                [row["usage"][key] for row in rows],
                color=colors[index % len(colors)],
                label=condition,
            )
        axis.set_xticks(range(len(conditions)), conditions)
        axis.set(ylabel="Tokens per attempt", title=title)
        axis.set_ylim(bottom=0)
    figure.suptitle("Every observed attempt; descriptive usage, no cost or significance claim")
    figure.savefig(output / "tokens.svg", metadata={"Date": None, "Creator": "summarize_agent_trials.py"})
    figure.savefig(output / "tokens.png", dpi=150, metadata={"Software": "summarize_agent_trials.py"})
    plt.close(figure)


def verify_plots(report: dict[str, Any], output: Path) -> None:
    """Compare rendered SVG content and PNG pixels without changing published files."""
    from PIL import Image

    with tempfile.TemporaryDirectory() as directory:
        rendered = Path(directory)
        plots(report, rendered)
        for name in ("quality.svg", "tokens.svg"):
            expected_svg = (rendered / name).read_bytes().replace(b"\r\n", b"\n")
            actual_svg = (output / name).read_bytes().replace(b"\r\n", b"\n")
            if actual_svg != expected_svg:
                raise ValueError(f"published {name} differs from the verified trial report")
        for name in ("quality.png", "tokens.png"):
            with Image.open(rendered / name) as expected_image, Image.open(output / name) as actual_image:
                if (
                    expected_image.size != actual_image.size
                    or expected_image.convert("RGBA").tobytes() != actual_image.convert("RGBA").tobytes()
                ):
                    raise ValueError(f"published {name} pixels differ from the verified trial report")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--trials", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--check", action="store_true", help="Reverify all attempts and compare existing JSON/Markdown without writing"
    )
    parser.add_argument(
        "--plots", action="store_true", help="Generate standalone SVG charts; requires the reports extra"
    )
    parser.add_argument(
        "--check-plots", action="store_true", help="With --check, verify published charts; requires the reports extra"
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--package-bytecode",
        action="store_true",
        help="Preserve frozen cache-byte evidence in portable archives; never change result records",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.check and (args.plots or args.package_bytecode):
            raise ValueError("--check does not write charts or bytecode transports")
        if args.check_plots and not args.check:
            raise ValueError("--check-plots requires --check")
        report = summarize(args.protocol, args.trials, package_caches=args.package_bytecode)
        if args.check:
            if (args.output_dir / "summary.json").read_text(encoding="utf-8") != dumps_deterministic(report) or (
                args.output_dir / "README.md"
            ).read_text(encoding="utf-8") != render(report):
                raise ValueError("published trial report differs from verified recorded attempts")
            if args.check_plots:
                verify_plots(report, args.output_dir)
        else:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            write_json(args.output_dir / "summary.json", report)
            write_text(args.output_dir / "README.md", render(report))
            if args.plots:
                plots(report, args.output_dir)
        print(
            json.dumps(
                {
                    "valid": True,
                    "completed_attempts": report["completed_attempts"],
                    "quality_superiority_established": False,
                }
            )
        )
        return 0
    except (OSError, ValueError, KeyError, TypeError, ImportError, zipfile.BadZipFile) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Grade a collected validator patch with sealed oracles and native confinement."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import appcontainer_runtime
from _validator_cases import accepted, cases
from _windows_appcontainer import checked_path, checked_tree, run_appcontainer

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "tools/appcontainer_validator_worker.py"
TASK_FILES = (
    "data/skills_catalog.json",
    "data/benchmark_scenarios.json",
    "evaluators/benchmark_run_artifact.schema.json",
)
TRUSTED_FILES = (
    "tools/grade_validator_appcontainer.py",
    "tools/_validator_cases.py",
    "tools/appcontainer_validator_worker.py",
    "tools/appcontainer_runtime.py",
    "tools/_windows_appcontainer.py",
    "tools/_windows_owned_python.py",
    "toolchains/appcontainer/source.json",
)


def snapshot(directory: Path) -> dict[str, str]:
    return {p.relative_to(directory).as_posix(): appcontainer_runtime.digest(p) for p in checked_tree(directory)}


def collect_candidate(submission: Path, fixture: Path, revision: str, destination: Path) -> dict[str, str]:
    source = checked_path(submission / "tools/check_benchmark_artifact.py")
    if not source.is_file() or source.stat().st_size > 1024 * 1024:
        raise ValueError("The submitted validator must be a regular source file of at most 1 MiB")
    if not re.fullmatch("[0-9a-f]{40}", revision):
        raise ValueError("An exact lowercase 40-character fixture commit is required")
    checked_path(fixture)
    git = ["git", "-c", "core.longpaths=true", "-C", str(fixture)]
    root = subprocess.run([*git, "rev-parse", "--show-toplevel"], capture_output=True, check=True, timeout=10)
    if Path(root.stdout.decode("utf-8").strip()).resolve() != fixture.resolve():
        raise ValueError("Fixture must identify its exact Git root")
    destination.mkdir(parents=True, exist_ok=False)
    target = destination / "tools/check_benchmark_artifact.py"
    target.parent.mkdir()
    shutil.copyfile(source, target)
    for name in TASK_FILES:
        result = subprocess.run([*git, "show", revision + ":" + name], capture_output=True, check=True, timeout=15)
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result.stdout)
    return snapshot(destination)


def grade(submission: Path, fixture: Path, runtime_home: Path, output: Path, revision: str) -> dict[str, Any]:
    if sys.platform != "win32":
        raise ValueError("The confined evaluator requires Windows x64")
    workspace = common_workspace(runtime_home, output)
    trusted = {name: appcontainer_runtime.digest(ROOT / name) for name in TRUSTED_FILES}
    specification = json.loads(appcontainer_runtime.SOURCE.read_bytes())
    errors = appcontainer_runtime.verify(runtime_home, specification)
    if errors:
        raise ValueError("; ".join(errors))
    output.mkdir(parents=True, exist_ok=False)
    # Oracle data is loaded before any submitted code is executed. Only the
    # copied API inputs and the small worker adapter are ever mounted.
    candidate = output / "candidate"
    collected = collect_candidate(submission, fixture, revision, candidate)
    source = json.loads((candidate / "data/skills_catalog.json").read_bytes())[0]
    bootstrap = output / "bootstrap"
    bootstrap.mkdir()
    shutil.copyfile(WORKER, bootstrap / WORKER.name)
    worker_hash = appcontainer_runtime.digest(bootstrap / WORKER.name)
    observations: list[dict[str, Any]] = []
    deadline = time.monotonic() + 180
    for name, record, expected, missing_schema in cases(source, revision):
        if time.monotonic() > deadline:
            raise TimeoutError("The grading campaign exceeded its total deadline")
        observation = evaluate_case(
            output, runtime_home, candidate, bootstrap, workspace, record, missing_schema, deadline
        )
        process = observation["process"]
        observation.update(
            case=name,
            passed=process["exit_code"] == 0
            and process["termination_reason"] is None
            and accepted(observation["response"], expected),
        )
        observations.append(observation)
        if snapshot(candidate) != collected or appcontainer_runtime.digest(bootstrap / WORKER.name) != worker_hash:
            raise ValueError("Read-only grader inputs changed during candidate execution")
        (output / "checks.json").write_text(json.dumps(observations, indent=2) + "\n", encoding="utf-8")
    if appcontainer_runtime.verify(runtime_home, specification):
        raise ValueError("Runtime source graph changed during grading")
    if trusted != {name: appcontainer_runtime.digest(ROOT / name) for name in TRUSTED_FILES}:
        raise ValueError("Trusted evaluator source changed during grading")
    count = sum(row["passed"] for row in observations)
    result = {
        "measurement_kind": "confined_validator_contract_evaluation",
        "status": "task_passed" if count == len(observations) else "task_failed",
        "checks_passed": count,
        "checks_total": len(observations),
        "checks": observations,
        "runtime_version": specification["version"],
        "candidate_file_sha256": collected,
        "worker_sha256": worker_hash,
        "trusted_source_sha256": trusted,
        "fixture_commit": revision,
        "oracle_process_separate": True,
        "independent_model_trials": 0,
        "agent_performance_claim": False,
        "scope": "Windows x64 stdlib-only validator API fixture; no coding-agent superiority or collection-wide score",
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def evaluate_case(
    output: Path,
    runtime_home: Path,
    candidate: Path,
    bootstrap: Path,
    workspace: Path,
    record: dict[str, Any],
    missing_schema: bool,
    deadline: float,
) -> dict[str, Any]:
    # Candidate-visible paths carry no oracle label or case ordinal.
    current = output / ("case-" + uuid.uuid4().hex)
    inputs, scratch = current / "inputs", current / "scratch"
    inputs.mkdir(parents=True)
    scratch.mkdir()
    (inputs / "transcript.txt").write_text("Recorded commands\n", encoding="utf-8")
    (inputs / "result.json").write_text("{}\n", encoding="utf-8")
    (inputs / "directory").mkdir()
    artifact = inputs / "artifact.json"
    artifact.write_text(json.dumps(record, allow_nan=False), encoding="utf-8")
    request = {"module": str(candidate / "tools/check_benchmark_artifact.py"), "artifact": str(artifact)}
    if missing_schema:
        request["schema_override"] = str(inputs / "unavailable.schema.json")
    request_file = inputs / "request.json"
    request_file.write_text(json.dumps(request), encoding="utf-8")
    wire_hashes = snapshot(inputs)
    process = run_appcontainer(
        runtime_home / "runtime/python.exe",
        ["-I", "-S", "-B", "-X", "utf8", str(bootstrap / WORKER.name), str(request_file)],
        workspace=workspace,
        readable=[runtime_home / "runtime", candidate, bootstrap, inputs],
        scratch=scratch,
        output=current / "observations",
        timeout=min(10, max(0.01, deadline - time.monotonic())),
    )
    response = parse_response(current / "observations/stdout.native")
    if snapshot(inputs) != wire_hashes:
        raise ValueError("Read-only wire inputs changed during candidate execution")
    return {
        "response": response,
        "process": process,
        "observation_directory": current.name + "/observations",
        "stdout_sha256": appcontainer_runtime.digest(current / "observations/stdout.native"),
        "stderr_sha256": appcontainer_runtime.digest(current / "observations/stderr.native"),
    }


def common_workspace(runtime_home: Path, output: Path) -> Path:
    cache = (ROOT / ".venv").resolve()
    checked_path(runtime_home)
    checked_path(output)
    if not runtime_home.resolve().is_relative_to(cache) or not output.resolve().is_relative_to(cache):
        raise ValueError("Runtime and output must use dedicated directories inside this clone's .venv")
    if runtime_home.resolve() == cache or output.resolve() == cache:
        raise ValueError("Use dedicated runtime and observation directories")
    if output.is_relative_to(runtime_home) or runtime_home.is_relative_to(output):
        raise ValueError("Runtime and observations must not overlap")
    return cache


def parse_response(path: Path) -> Any:
    try:
        return json.loads(path.read_bytes(), parse_constant=reject_constant, object_pairs_hook=unique_keys)
    except (UnicodeError, ValueError, RecursionError):
        return {"kind": "invalid_response"}


def reject_constant(value: str) -> None:
    raise ValueError(f"Non-finite JSON constant: {value}")


def unique_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Repeated JSON key")
        result[key] = value
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--runtime-home", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = grade(
            checked_path(args.submission),
            checked_path(args.fixture),
            checked_path(args.runtime_home),
            checked_path(args.output),
            args.revision,
        )
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "harness_error", "errors": [str(error)], "agent_performance_claim": False}))
        return 2
    print(
        json.dumps({key: result[key] for key in ["status", "checks_passed", "checks_total", "agent_performance_claim"]})
    )
    return int(result["status"] != "task_passed")


if __name__ == "__main__":
    raise SystemExit(main())

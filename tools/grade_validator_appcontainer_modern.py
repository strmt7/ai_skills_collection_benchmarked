"""Grade validator submissions in a source-bound AppContainer with pinned dependencies."""

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

import appcontainer_dependencies as dependencies
import appcontainer_runtime as runtime
import grade_validator_appcontainer as legacy
from _validator_cases import accepted, cases
from _windows_appcontainer import Native, checked_path, run_appcontainer
from _windows_submission_reader import read_submission

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "tools/appcontainer_validator_worker_modern.py"
SUPPORT_FILES = (
    "tools/_source_history.py",
    "tools/_catalog_publication.py",
    "tools/build_catalog.py",
    "tools/update_readme_badges.py",
    "tools/_source_admission.py",
    "tools/check_no_secret_patterns.py",
    *(
        f"tools/_lib_b/{name}.py"
        for name in (
            "__init__",
            "credential_neutralizations",
            "credential_patterns",
            "dependency_graphs",
            "determinism",
            "frontmatter_utils",
            "hashing",
            "io_utils",
            "logging_utils",
        )
    ),
)
EVALUATOR_FILES = (
    *legacy.EVALUATOR_FILES,
    "tools/grade_validator_appcontainer_modern.py",
    "tools/grade_agent_submission.py",
    "benchmarks/agent-effectiveness/graders/artifact_validator.py",
    "tools/appcontainer_validator_worker_modern.py",
    "tools/appcontainer_dependencies.py",
    "toolchains/appcontainer-modern/source.json",
)


def collect_support(fixture: Path, revision: str, candidate: Path) -> None:
    """Copy helper code from the trusted fixture, never from the submission."""
    fixture, candidate = checked_path(fixture), checked_path(candidate)
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("An exact lowercase 40-character fixture commit is required")
    git = ["git", "-c", "core.longpaths=true", "-C", str(fixture)]
    root = subprocess.run([*git, "rev-parse", "--show-toplevel"], capture_output=True, check=True, timeout=10)
    if Path(root.stdout.decode("utf-8").strip()).resolve() != fixture.resolve():
        raise ValueError("Fixture must identify its exact Git root")
    for name in SUPPORT_FILES:
        result = subprocess.run([*git, "show", f"{revision}:{name}"], capture_output=True, check=True, timeout=15)
        target = checked_path(candidate / name)
        if target.exists():
            raise ValueError("trusted helper collides with a candidate file")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result.stdout)


def collect_candidate(payload: bytes, fixture: Path, revision: str, candidate: Path) -> None:
    """Stage only the opened submission and fixture files from an exact Git commit."""
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("An exact lowercase 40-character fixture commit is required")
    git = ["git", "-c", "core.longpaths=true", "-C", str(fixture)]
    root = subprocess.run([*git, "rev-parse", "--show-toplevel"], capture_output=True, check=True, timeout=10)
    if Path(root.stdout.decode("utf-8").strip()).resolve() != fixture.resolve():
        raise ValueError("Fixture must identify its exact Git root")
    candidate.mkdir(parents=True, exist_ok=False)
    target = candidate / "tools/check_benchmark_artifact.py"
    target.parent.mkdir()
    target.write_bytes(payload)
    for name in legacy.TASK_FILES:
        result = subprocess.run([*git, "show", f"{revision}:{name}"], capture_output=True, check=True, timeout=15)
        target = candidate / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result.stdout)


def checked_homes(runtime_home: Path, dependency_home: Path, output: Path) -> Path:
    workspace = legacy.common_workspace(runtime_home, output)
    if dependency_home == workspace or not dependency_home.is_relative_to(workspace):
        raise ValueError("Dependency home must be a dedicated directory inside this clone's .venv")
    for left, right in ((dependency_home, runtime_home), (dependency_home, output)):
        if left.is_relative_to(right) or right.is_relative_to(left):
            raise ValueError("Dependency, runtime and output directories must not overlap")
    return workspace


def grade(
    submission: Path,
    fixture: Path,
    runtime_home: Path,
    dependency_home: Path,
    output: Path,
    revision: str,
) -> dict[str, Any]:
    if sys.platform != "win32":
        raise ValueError("The confined evaluator requires Windows x64")
    submission, fixture, runtime_home, dependency_home, output = (
        checked_path(path) for path in (submission, fixture, runtime_home, dependency_home, output)
    )
    workspace = checked_homes(runtime_home, dependency_home, output)
    interpreter_spec = json.loads(runtime.SOURCE.read_bytes())
    dependency_spec = dependencies.load_specification()
    if dependency_spec["python_version"] != interpreter_spec["version"]:
        raise ValueError("Dependency graph does not match the pinned interpreter")
    with runtime.lease(runtime_home, interpreter_spec), runtime.lease(dependency_home, dependency_spec):
        return grade_with_leases(
            submission,
            fixture,
            runtime_home,
            dependency_home,
            output,
            revision,
            workspace,
            interpreter_spec,
            dependency_spec,
        )


def grade_with_leases(
    submission: Path,
    fixture: Path,
    runtime_home: Path,
    dependency_home: Path,
    output: Path,
    revision: str,
    workspace: Path,
    interpreter_spec: dict[str, Any],
    dependency_spec: dict[str, Any],
) -> dict[str, Any]:
    evaluator_files = [{"path": name, "sha256": runtime.digest(ROOT / name)} for name in EVALUATOR_FILES]
    if errors := runtime.verify(runtime_home, interpreter_spec) + runtime.verify(dependency_home, dependency_spec):
        raise ValueError("; ".join(errors))
    legacy.check_unlinked_files(runtime_home)
    legacy.check_unlinked_files(dependency_home)
    payload = read_submission(submission)
    output.mkdir(parents=True, exist_ok=False)
    native = Native()
    native.grant(output, native.owner_sid(), None)
    (output / "controller-sentinel.txt").write_text("controller-owned sentinel\n", encoding="utf-8")
    candidate = output / "candidate"
    collect_candidate(payload, fixture, revision, candidate)
    collect_support(fixture, revision, candidate)
    collected = legacy.snapshot(candidate)
    source = json.loads((candidate / "data/skills_catalog.json").read_bytes())[0]
    bootstrap = output / "bootstrap"
    bootstrap.mkdir()
    shutil.copyfile(WORKER, bootstrap / WORKER.name)
    worker_hash = runtime.digest(bootstrap / WORKER.name)
    observations: list[dict[str, Any]] = []
    deadline = time.monotonic() + 180
    for name, record, expected, missing in cases(source, revision):
        if time.monotonic() > deadline:
            raise TimeoutError("The grading campaign exceeded its total deadline")
        observation = evaluate_case(
            output, runtime_home, dependency_home, candidate, bootstrap, workspace, record, missing, deadline
        )
        process = observation["process"]
        observation.update(
            case=name,
            passed=process["exit_code"] == 0
            and process["termination_reason"] is None
            and accepted(observation["response"], expected),
        )
        observations.append(observation)
        if legacy.snapshot(candidate) != collected or runtime.digest(bootstrap / WORKER.name) != worker_hash:
            raise ValueError("Read-only grader inputs changed during candidate execution")
        (output / "checks.json").write_text(json.dumps(observations, indent=2) + "\n", encoding="utf-8")
    if runtime.verify(runtime_home, interpreter_spec) or runtime.verify(dependency_home, dependency_spec):
        raise ValueError("Pinned runtime or dependency graph changed during grading")
    if evaluator_files != [{"path": name, "sha256": runtime.digest(ROOT / name)} for name in EVALUATOR_FILES]:
        raise ValueError("Trusted evaluator source changed during grading")
    count = sum(row["passed"] for row in observations)
    result = {
        "measurement_kind": "confined_validator_contract_evaluation",
        "status": "task_passed" if count == len(observations) else "task_failed",
        "checks_passed": count,
        "checks_total": len(observations),
        "checks": observations,
        "runtime_version": interpreter_spec["version"],
        "dependency_bundle_sha256": dependency_spec["archive_sha256"],
        "candidate_file_sha256": collected,
        "worker_sha256": worker_hash,
        "evaluator_files": evaluator_files,
        "controller_output_sealed": True,
        "fixture_commit": revision,
        "oracle_process_separate": True,
        "independent_model_trials": 0,
        "agent_performance_claim": False,
        "scope": "Windows x64 validator API fixture with pinned dependencies; not an agent performance score",
    }
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def evaluate_case(
    output: Path,
    runtime_home: Path,
    dependency_home: Path,
    candidate: Path,
    bootstrap: Path,
    workspace: Path,
    record: dict[str, Any],
    missing_schema: bool,
    deadline: float,
) -> dict[str, Any]:
    current = output / ("case-" + uuid.uuid4().hex)
    inputs, scratch = current / "inputs", current / "scratch"
    inputs.mkdir(parents=True)
    scratch.mkdir()
    (inputs / "transcript.txt").write_text("Recorded commands\n", encoding="utf-8")
    (inputs / "result.json").write_text("{}\n", encoding="utf-8")
    (inputs / "directory").mkdir()
    artifact = inputs / "artifact.json"
    artifact.write_text(json.dumps(record, allow_nan=False), encoding="utf-8")
    request = {
        "module": str(candidate / "tools/check_benchmark_artifact.py"),
        "artifact": str(artifact),
        "dependencies": str(dependency_home / "runtime"),
    }
    if missing_schema:
        request["schema_override"] = str(inputs / "unavailable.schema.json")
    request_file = inputs / "request.json"
    request_file.write_text(json.dumps(request), encoding="utf-8")
    wire_hashes = legacy.snapshot(inputs)
    process = run_appcontainer(
        runtime_home / "runtime/python.exe",
        ["-I", "-S", "-B", "-X", "utf8", str(bootstrap / WORKER.name), str(request_file)],
        workspace=workspace,
        readable=[runtime_home / "runtime", dependency_home / "runtime", candidate, bootstrap, inputs],
        scratch=scratch,
        output=current / "observations",
        timeout=min(10, max(0.01, deadline - time.monotonic())),
    )
    response = legacy.parse_response(current / "observations/stdout.native")
    if legacy.snapshot(inputs) != wire_hashes:
        raise ValueError("Read-only wire inputs changed during candidate execution")
    return {
        "response": response,
        "process": process,
        "observation_directory": current.name + "/observations",
        "stdout_sha256": runtime.digest(current / "observations/stdout.native"),
        "stderr_sha256": runtime.digest(current / "observations/stderr.native"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--runtime-home", type=Path, required=True)
    parser.add_argument("--dependency-home", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = grade(
            args.submission, args.fixture, args.runtime_home, args.dependency_home, args.output, args.revision
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

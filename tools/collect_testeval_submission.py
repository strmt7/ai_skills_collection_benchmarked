"""Capture native TestEval and independent pytest evidence for the public pilot."""

from __future__ import annotations

import argparse
import json
import sys
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from _native_benchmark_runtime import ContainerLease, DockerClient, LeaseResources, stage_inputs, write_json
from _native_grader_dependencies import PYTHON, environment_packet, validate_environment
from _trial_transcript import strict_json
from grade_testeval_submission import (
    ASSIGNMENT_FIELDS,
    CAPTURE_EVIDENCE,
    TEST_SUBMISSION,
    grade,
    is_digest,
    load_test_snippets,
    sha256,
    validate_plan,
    validate_task_plan,
)
from transfer_benchmark_submission import plan_handoff, restore
from validate_testeval_calibration import read_evidence

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "benchmarks/agent-effectiveness/development/testeval-pilot-v2"
INPUT = "/tmp/benchmark-inputs"
WORKSPACE = "/tmp/testeval"
TIMEOUT = 30
PUBLISHER_TIMEOUT = 150
ASSET_LIMIT = 16 * 1024**2
PREPARE = f"""
import json,sys
sys.path.insert(0,{INPUT!r}+"/tools")
from _native_grader_dependencies import prepare
print(json.dumps(prepare()))
"""
EXECUTE = f"""
import os,shutil,sys
from pathlib import Path
source=Path({INPUT!r})/"stage"
work=Path({WORKSPACE!r})
shutil.copytree(source,work)
os.chdir(work)
env={{"PATH":str(Path(sys.executable).parent)+":"+os.defpath,"HOME":str(work),
      "LANG":"C.UTF-8","PYTHONNOUSERSITE":"1","PYTHONDONTWRITEBYTECODE":"1",
      "PYTEST_DISABLE_PLUGIN_AUTOLOAD":"1"}}
if sys.argv[1]=="publisher":
    env["PYTEST_PLUGINS"]="pytest_cov.plugin"
    args=["eval_overall.py","--path","subject.jsonl","--ks","1"]
else:
    tests=sorted(p.name for p in work.glob("test_subject*.py"))
    if not tests:
        raise ValueError("Independent pytest stage requires generated test files")
    args=["-m","pytest","-q","-c","/dev/null","-p","no:cacheprovider",
          "--junitxml=report.xml",*tests]
os.execve(sys.executable,[sys.executable,"-B","-X","utf8",*args],env)
"""


def read_asset(path: Path, digest: str | None = None) -> bytes:
    with path.open("rb") as stream:
        content = stream.read(ASSET_LIMIT + 1)
    if len(content) > ASSET_LIMIT or (digest is not None and sha256(content) != digest):
        raise ValueError(f"Missing frozen identity or exceeded asset budget for {path.name}")
    return content


def object_from(content: bytes) -> dict[str, Any]:
    value = strict_json(content.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def load_profile() -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    raw = read_asset(PILOT / "native-profile.json")
    profile = object_from(raw)
    if type(profile.get("schema_version")) is not int or profile["schema_version"] != 1:
        raise ValueError("Expected a version 1 TestEval collector profile")
    selection = object_from(read_asset(PILOT / "selection.json", profile["selection_sha256"]))
    return raw, profile, selection


def publisher_inputs(
    profile: dict[str, Any], selection: dict[str, Any], plan: dict[str, Any], assets: Path
) -> tuple[dict, dict[str, bytes]]:
    selected = {row["task_num"] for row in selection["selected"]}
    source = selection["publisher"]
    if (
        selection["partition"] != "public_development"
        or plan["task_id"] not in selected
        or plan["publisher"]
        != {
            "commit_sha": source["commit"],
            "dataset_sha256": source["dataset_sha256"],
            "evaluator_sha256": source["evaluator_sha256"],
        }
    ):
        raise ValueError("Plan is outside the frozen public TestEval pilot")
    files = {name: read_asset(assets / name, digest) for name, digest in profile["publisher_inputs"].items()}
    projection = [object_from(row) for row in files.pop("selected.jsonl").splitlines()]
    if len(projection) != len(selected) or {row["task_num"] for row in projection} != selected:
        raise ValueError("The publisher projection differs from the public task selection")
    task = next(row for row in projection if row["task_num"] == plan["task_id"])
    if sha256(files["eval_overall.py"]) != source["evaluator_sha256"]:
        raise ValueError("Publisher evaluator differs from the selected commit")
    if sha256(task["code"].encode("utf-8")) != plan["programs"]["reference"]:
        raise ValueError("Reference program differs from the publisher projection")
    return task, files


def report_file(output: Path, name: str, content: bytes) -> dict[str, str] | None:
    if not content:
        return None
    with (output / name).open("xb") as stream:
        stream.write(content)
    return {"file": name, "sha256": sha256(content)}


def run_stage(
    client: DockerClient,
    output: Path,
    name: str,
    payload: dict[str, bytes],
    dependencies: dict[str, bytes],
    environment: dict[str, Any],
    *,
    timeout: int = TIMEOUT,
) -> tuple[str, int | None, bytes]:
    mode = "publisher" if name == "publisher" else "pytest"
    setup_timeout = environment["setup_timeout_seconds"]
    lease = ContainerLease(
        client,
        output / (name + ".lease.json"),
        seconds=setup_timeout + timeout + 90,
        resources=LeaseResources(**environment["resources"], executable_workspace=True),
    )
    stage = "setup_failed"
    try:
        identity = lease.create()
        lease.start()
        stage_inputs(
            lease,
            output / (name + "-input"),
            {**dependencies, **payload},
            retain_packet=False,
        )
        client.run(
            name + "-dependencies",
            ["container", "exec", "--user=0:0", identity, "python", "-I", "-B", "-c", PREPARE],
            timeout=setup_timeout,
        )
        stage = "interrupted"
        argv = ["container", "exec", "--user=65534:65534", identity]
        result = client.capture(name, [*argv, PYTHON, "-I", "-B", "-c", EXECUTE, mode], timeout=timeout)
        process = result.process
        if process["job_active_processes_after_cleanup"] or process["termination_reason"]:
            termination = "timed_out" if process["termination_reason"] == "timeout" else "interrupted"
            return termination, None, b""
        if mode == "publisher":
            return "completed", process["exit_code"], result.stdout.read_bytes()
        report = client.run(
            name + "-junit",
            [
                *argv,
                "python",
                "-I",
                "-B",
                "-c",
                f"from pathlib import Path;import sys;p=Path({WORKSPACE!r})/'report.xml';"
                "sys.stdout.buffer.write(p.read_bytes()) if p.is_file() else None",
            ],
        )
        return "completed", process["exit_code"], report
    except (OSError, RuntimeError, ValueError) as error:
        write_json(output / (name + ".error.json"), {"stage": stage, "error": str(error)})
        return stage, None, b""
    finally:
        lease.close()


def capture_directory(output: Path) -> Path:
    directory = output.resolve()
    ignored = (ROOT / ".venv").resolve()
    if directory == ignored or not directory.is_relative_to(ignored) or directory.exists():
        raise ValueError("Use a new TestEval capture directory in this checkout's ignored state")
    return directory


def collect(plan_path: Path, suite: Path, defects: Path, assets: Path, runtime: Path, output: Path) -> dict[str, Any]:
    """Execute a reviewed development suite with an authored pytest inventory."""
    raw = read_asset(plan_path)
    plan = object_from(raw)
    validate_plan(plan)
    if plan["schema_version"] != 1:
        raise ValueError("A version 2 grade plan must come from a sealed handoff")
    content = read_asset(suite, plan["subject_suite_sha256"]).decode("utf-8")
    return _collect_admitted(raw, [content], defects, assets, runtime, output)


def collect_handoff(
    task_path: Path, handoff_dir: Path, archive_sha256: str, defects: Path, assets: Path, runtime: Path, output: Path
) -> dict[str, Any]:
    """Grade only exact tests reconstructed from a controller-owned handoff."""
    task_bytes = read_evidence(task_path)
    task = object_from(task_bytes)
    validate_task_plan(task)
    directory = handoff_dir.resolve(strict=True)
    if not directory.is_relative_to((ROOT / ".venv").resolve()) or not is_digest(archive_sha256):
        raise ValueError("TestEval handoff requires controller-owned paths and the sealed archive digest")
    output = capture_directory(output)
    if output.is_relative_to(directory) or directory.is_relative_to(output):
        raise ValueError("TestEval handoff and capture directories must be disjoint")
    baseline = read_asset(directory / "baseline.collection.json", task["baseline_manifest_sha256"])
    submission = read_evidence(directory / "submission.collection.json")
    handoff = plan_handoff(baseline, submission)
    if (
        set(handoff.delta["writes"]) != {TEST_SUBMISSION}
        or handoff.delta["deletes"]
        or handoff.submission["directories"] != handoff.baseline["directories"]
    ):
        raise ValueError(f"TestEval handoff must change only {TEST_SUBMISSION}")
    with TemporaryDirectory(prefix="testeval-restore-", dir=output.parent) as scratch:
        rebuilt = Path(scratch) / "workspace"
        receipt = restore(handoff, directory / "baseline", directory / "submission.tar", archive_sha256, rebuilt)
        tests = read_evidence(rebuilt / TEST_SUBMISSION)
    snippets = load_test_snippets(tests)
    admitted = {
        CAPTURE_EVIDENCE["task_plan"]: task_bytes,
        CAPTURE_EVIDENCE["handoff"]: json.dumps(receipt, sort_keys=True).encode("utf-8") + b"\n",
        TEST_SUBMISSION: tests,
    }
    plan = {
        "schema_version": 2,
        **{key: task[key] for key in ASSIGNMENT_FIELDS},
        "subject_suite_sha256": sha256(tests),
        **{key: {"file": name, "sha256": sha256(admitted[name])} for key, name in CAPTURE_EVIDENCE.items()},
    }
    raw = json.dumps(plan, sort_keys=True).encode("utf-8") + b"\n"
    return _collect_admitted(raw, snippets, defects, assets, runtime, output, admitted=admitted)


def _collect_admitted(
    plan_bytes: bytes,
    snippets: list[str],
    defects: Path,
    assets: Path,
    runtime: Path,
    output: Path,
    *,
    admitted: dict[str, bytes] | None = None,
) -> dict[str, Any]:
    plan = object_from(plan_bytes)
    validate_plan(plan)
    version = plan["schema_version"]
    if (version == 2) != (admitted is not None):
        raise ValueError("Version 2 TestEval grading requires admitted submission evidence")
    profile_bytes, profile, selection = load_profile()
    task, publisher = publisher_inputs(profile, selection, plan, assets)
    suite_digest = plan["subject_suite_sha256"]
    prediction = json.dumps({**task, "tests": snippets}, sort_keys=True).encode("utf-8") + b"\n"
    publisher["predictions/subject.jsonl"] = prediction
    subject_files = {}
    for index, snippet in enumerate(snippets, 1):
        name = "test_subject.py" if version == 1 else f"test_subject_{index:02}.py"
        subject_files["stage/" + name] = b"from under_test import Solution\n\n" + snippet.encode("utf-8")
    programs = {"reference": task["code"].encode("utf-8")}
    for name, digest in plan["programs"].items():
        if name != "reference":
            try:
                programs[name] = read_asset(defects / (name + ".py"), digest)
            except FileNotFoundError:
                continue

    def wheel(row: dict[str, str]) -> bytes:
        return read_asset(assets / row["path"], row["sha256"])

    environment = validate_environment(profile["python_environment"], wheel)
    dependencies = environment_packet(environment, wheel)
    dependencies["task.json"] = json.dumps({"python_environment": environment}, sort_keys=True).encode()
    if object_from(read_asset(runtime)).get("image_reference") != profile["image_reference"]:
        raise ValueError("Runtime differs from the frozen public TestEval pilot image")
    output = capture_directory(output)
    output.mkdir()
    (output / "plan.json").write_bytes(plan_bytes)
    (output / "native-profile.json").write_bytes(profile_bytes)
    (output / "collector.py.txt").write_bytes(Path(__file__).read_bytes())
    for name, content in (admitted or {}).items():
        with (output / name).open("xb") as stream:
            stream.write(content)
    publisher_stage: dict[str, Any] = {
        "source": plan["publisher"],
        "subject_suite_sha256": suite_digest,
        "termination": "interrupted",
        "exit_code": None,
        "stdout": None,
    }
    variants: dict[str, dict[str, Any]] = {
        name: {
            "program_sha256": digest if name in programs else None,
            "subject_suite_sha256": suite_digest,
            "termination": "interrupted" if name in programs else "fixture_unavailable",
            "exit_code": None,
            "junit": None,
        }
        for name, digest in plan["programs"].items()
    }
    capture = {
        "schema_version": version,
        "plan_sha256": sha256(plan_bytes),
        "publisher": publisher_stage,
        "variants": variants,
    }
    capture_path = output / "capture.json"
    write_json(capture_path, capture)
    client = DockerClient(ROOT, output / "client", runtime)
    termination, code, content = run_stage(
        client,
        output,
        "publisher",
        {"stage/" + name: data for name, data in publisher.items()},
        dependencies,
        environment,
        **({"timeout": PUBLISHER_TIMEOUT} if version == 2 else {}),
    )
    publisher_stage.update(
        termination=termination, exit_code=code, stdout=report_file(output, "publisher.stdout", content)
    )
    write_json(capture_path, capture)
    for name, program in programs.items():
        stage_name = "pytest-" + name
        termination, code, content = run_stage(
            client,
            output,
            stage_name,
            {"stage/under_test.py": program, **subject_files},
            dependencies,
            environment,
        )
        variants[name].update(
            termination=termination, exit_code=code, junit=report_file(output, stage_name + ".xml", content)
        )
        write_json(capture_path, capture)
    result = grade(plan_bytes, capture_path)
    write_json(output / "grade.json", {"ok": True, "result": result})
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("plan", "defects", "assets", "runtime", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    submission = parser.add_mutually_exclusive_group(required=True)
    submission.add_argument("--suite", type=Path, help="Reviewed suite with a version 1 grade plan")
    submission.add_argument("--handoff", type=Path, help="Sealed submission directory with a version 2 task plan")
    parser.add_argument("--archive-sha256", help="Controller's digest for the sealed submission.tar")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if (args.handoff is None) != (args.archive_sha256 is None):
        parser.error("--handoff and --archive-sha256 must be supplied together")
    try:
        inputs = (args.defects, args.assets, args.runtime, args.output)
        if args.handoff is None:
            result = collect(args.plan, args.suite, *inputs)
        else:
            result = collect_handoff(args.plan, args.handoff, args.archive_sha256, *inputs)
    except (KeyError, OSError, RuntimeError, TypeError, ValueError, tarfile.TarError) as error:
        print(f"TestEval collection failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "result": result}, indent=2))
    complete = {"measured", "passed", "test_failed"}
    statuses = [result["native_test_eval"], result["reference"], *result["defects"].values()]
    return 0 if all(row["status"] in complete for row in statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())

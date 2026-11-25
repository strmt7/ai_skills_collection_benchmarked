"""Capture native TestEval and independent pytest evidence for the public pilot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from _native_benchmark_runtime import ContainerLease, DockerClient, LeaseResources, stage_inputs, write_json
from _native_grader_dependencies import PYTHON, environment_packet, validate_environment
from _trial_transcript import strict_json
from grade_testeval_submission import grade, sha256, validate_plan

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "benchmarks/agent-effectiveness/development/testeval-pilot-v2"
INPUT = "/tmp/benchmark-inputs"
WORKSPACE = "/tmp/testeval"
TIMEOUT = 30
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
    args=["-m","pytest","-q","-c","/dev/null","-p","no:cacheprovider",
          "--junitxml=report.xml","test_subject.py"]
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
) -> tuple[str, int | None, bytes]:
    mode = "publisher" if name == "publisher" else "pytest"
    setup_timeout = environment["setup_timeout_seconds"]
    lease = ContainerLease(
        client,
        output / (name + ".lease.json"),
        seconds=setup_timeout + TIMEOUT + 90,
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
        result = client.capture(name, [*argv, PYTHON, "-I", "-B", "-c", EXECUTE, mode], timeout=TIMEOUT)
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


def collect(plan_path: Path, suite: Path, defects: Path, assets: Path, runtime: Path, output: Path) -> dict[str, Any]:
    """Execute a trusted, reviewed development suite and account for all planned stages."""
    plan_bytes = read_asset(plan_path)
    plan = object_from(plan_bytes)
    validate_plan(plan)
    profile_bytes, profile, selection = load_profile()
    task, publisher = publisher_inputs(profile, selection, plan, assets)
    suite_digest = plan["subject_suite_sha256"]
    suite_bytes = read_asset(suite, suite_digest)
    prediction = json.dumps({**task, "tests": [suite_bytes.decode("utf-8")]}, sort_keys=True).encode() + b"\n"
    publisher["predictions/subject.jsonl"] = prediction
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
    output = output.resolve()
    if not output.is_relative_to(ROOT / ".venv"):
        raise ValueError("Use a new TestEval capture directory in this checkout's ignored state")
    output.mkdir()
    (output / "plan.json").write_bytes(plan_bytes)
    (output / "native-profile.json").write_bytes(profile_bytes)
    (output / "collector.py.txt").write_bytes(Path(__file__).read_bytes())
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
        "schema_version": 1,
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
            {
                "stage/under_test.py": program,
                "stage/test_subject.py": b"from under_test import Solution\n\n" + suite_bytes,
            },
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
    for option in ("plan", "suite", "defects", "assets", "runtime", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = collect(args.plan, args.suite, args.defects, args.assets, args.runtime, args.output)
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(f"TestEval collection failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "result": result}, indent=2))
    complete = {"measured", "passed", "test_failed"}
    statuses = [result["native_test_eval"], result["reference"], *result["defects"].values()]
    return 0 if all(row["status"] in complete for row in statuses) else 1


if __name__ == "__main__":
    raise SystemExit(main())

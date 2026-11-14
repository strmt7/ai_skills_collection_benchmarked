#!/usr/bin/env python3
"""Grade a completed source capture with pinned SWE-Skills-Bench code in owned containers."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from _native_benchmark_runtime import ContainerLease, DockerClient, LeaseResources, sha256, stage_inputs, write_json
from _native_grader_dependencies import PREFIX as DEPENDENCY_PREFIX
from _native_grader_dependencies import PYTHON as DEPENDENCY_PYTHON
from _native_grader_dependencies import environment_packet, validate_environment
from _trial_collection_contract import process_complete, verify_collector_launch
from _trial_collection_manifest import validate_manifest
from _trial_collection_policy import collection_policy
from _trial_protocol import relative_path
from _trial_transcript import strict_json
from run_agent_trial import execution_source_hashes
from transfer_benchmark_submission import plan_handoff, seal
from verify_swe_skills_bench_pytest_result import _inventory, verify_result

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ["python", "-I", "-B", "-X", "utf8"]
DEPENDENCY_SETUP = "import sys,json;sys.path.insert(0,'/tmp/benchmark-inputs/tools');from _native_grader_dependencies import prepare;print(json.dumps(prepare()))"
DEPENDENCY_VERIFY = "import sys,json;sys.path.insert(0,'/tmp/benchmark-inputs/tools');from _native_grader_dependencies import inventory;print(json.dumps(inventory()))"
SUPPORT = (
    "transfer_benchmark_submission.py",
    "_trial_collection_manifest.py",
    "_trial_collection_policy.py",
    "_trial_protocol.py",
    "_trial_declarations.py",
    "_trial_provider.py",
    "_trial_signin.py",
    "_trial_transcript.py",
)
REBUILD = r"""
import json,sys
from pathlib import Path
root=Path("/tmp/benchmark-inputs")
sys.path.insert(0,str(root/"tools"))
from transfer_benchmark_submission import plan_handoff,restore
task=json.loads((root/"task.json").read_bytes())
before=(root/"baseline.json").read_bytes()
after=(root/"submission.json").read_bytes()
base=root/"baseline"
base.mkdir(exist_ok=True)
for path in json.loads(before)["directories"]:(base/path).mkdir(exist_ok=True)
result=restore(plan_handoff(before,after),base,root/"delta.tar",sys.argv[1],Path("/workspace")/task["source_directory"])
if "python_environment" in task:
    repo=Path("/workspace")/task["source_directory"]
    for path in [repo,*repo.rglob("*")]:path.chmod(path.stat().st_mode|0o222)
tests=Path("/workspace/tests")
tests.mkdir()
verifier=tests/task["verifier"]["target"]
verifier.write_bytes((root/"verifier.py").read_bytes())
verifier.chmod(0o444)
print(json.dumps(result))
"""
EVALUATE = r"""
import json,os,subprocess,sys,tempfile,time
from pathlib import Path
root=Path("/tmp/benchmark-inputs")
task=json.loads((root/"task.json").read_bytes())
repo=Path("/workspace")/task["source_directory"]
if os.getuid()==0:raise ValueError("Verifier execution must be unprivileged")
env={**os.environ,"PYTHONPYCACHEPREFIX":"/tmp/python-cache","PYTEST_ADDOPTS":"-o cache_dir=/tmp/pytest-cache","SWE_REPO_DIR":str(repo)}
if "python_environment" in task:
    home=Path("/tmp/grader-task-home")
    home.mkdir(mode=0o700)
    env.update(HOME=str(home),XDG_CACHE_HOME=str(home/"cache"),XDG_CONFIG_HOME=str(home/"config"),XDG_DATA_HOME=str(home/"data"),TMPDIR="/tmp",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1")
    with tempfile.TemporaryFile(dir=repo):pass
env["PYTHONPATH"]=os.pathsep.join(str(repo/path) for path in task["import_paths"])
if task["python_safe_path"]:env["PYTHONSAFEPATH"]="1"
else:env.pop("PYTHONSAFEPATH",None)
started=time.monotonic()
probe="import hashlib,importlib.util,json,sys; result={}\nfor name in sys.argv[1:]:\n spec=importlib.util.find_spec(name)\n path=spec.origin if spec is not None else None\n result[name]={'path':path,'sha256':hashlib.sha256(open(path,'rb').read()).hexdigest() if path else None}\nprint(json.dumps(result))"
checked=subprocess.run([sys.executable,"-B","-c",probe,*task["expected_imports"]],cwd=repo,env=env,capture_output=True,check=True,timeout=10)
origins=json.loads(checked.stdout)
if checked.stderr or origins!=task["expected_imports"]:
    print(json.dumps({"import_error":True,"imports":origins,"expected_imports":task["expected_imports"]}))
    sys.exit(0)
with open("/tmp/pytest.stdout","xb") as stdout,open("/tmp/pytest.stderr","xb") as stderr:
    try:
        run=subprocess.run([sys.executable,"-m","pytest","/workspace/tests/"+task["verifier"]["target"],"-v","--tb=short","-rs",
                            "--junitxml=/tmp/pytest.xml"],cwd=repo,env=env,stdout=stdout,stderr=stderr,
                           timeout=task["test_timeout_seconds"],check=False)
        result={"exit_code":run.returncode,"timed_out":False}
    except subprocess.TimeoutExpired:
        result={"exit_code":124,"timed_out":True}
print(json.dumps({**result,"duration":time.monotonic()-started,"uid":os.getuid(),"imports":origins,"python_safe_path":task["python_safe_path"]}))
"""
SCORE = r"""
import asyncio,importlib.metadata,json,os,sys,tempfile
from pathlib import Path
root=Path("/tmp/benchmark-inputs")
sys.path[:0]=[str(root/"scorer"),"/tmp/scorer-dependencies"]
if os.getuid()==0:raise ValueError("Publisher scoring must be unprivileged")
from src.evaluator.unit_test_runner import UnitTestRunner
from src.orchestrator.docker_manager import ExecutionResult
task=json.loads((root/"task.json").read_bytes())
execution=json.loads((root/"execution.json").read_bytes())
path="/workspace/tests/"+task["verifier"]["target"]
repo="/workspace/"+task["source_directory"]
command="python -m pytest "+path+" -v --tb=short"
params={"test_command":command,"working_dir":repo,"timeout":task["test_timeout_seconds"],"min_pass_rate":task["min_pass_rate"]}
expected=[("ls -la "+path+" 2>&1",10),("cd "+repo+" && SWE_REPO_DIR="+repo+" "+command+" -rs",params["timeout"])]
temp=Path("/tmp/publisher-output")
temp.mkdir()
tempfile.tempdir=str(temp)
class RecordedTransport:
    def __init__(self):self.calls=[]
    def execute_command(self,command,timeout):
        if len(self.calls)>=len(expected) or (command,timeout)!=expected[len(self.calls)]:
            raise ValueError("Publisher command contract differs from the qualified profile")
        self.calls.append((command,timeout))
        if len(self.calls)==1:
            return ExecutionResult(exit_code=0,stdout=path+"\n",stderr="",duration=0.0)
        return ExecutionResult(stdout=(root/"console").read_text(),stderr=(root/"stderr").read_text(),**execution)
transport=RecordedTransport()
result=asyncio.run(UnitTestRunner(transport,params).evaluate())
if transport.calls!=expected:raise ValueError("Publisher did not complete its command contract")
versions={name:importlib.metadata.version(name) for name in task["scorer"]["versions"]}
if versions!=task["scorer"]["versions"]:raise ValueError("Scorer runtime differs from the frozen dependency versions")
print(json.dumps({"verdict":result.to_dict(),"versions":versions,"uid":os.getuid()}))
"""


def source_hashes() -> dict[str, str]:
    names = {
        "grade_swe_skills_submission.py",
        "_native_grader_dependencies.py",
        "_native_benchmark_runtime.py",
        "_native_image_archive.py",
        "transfer_benchmark_submission.py",
        "verify_swe_skills_bench_pytest_result.py",
    }
    return {
        **execution_source_hashes(),
        **{"tools/" + name: sha256((ROOT / "tools" / name).read_bytes()) for name in sorted(names)},
    }


def asset(entry: Any) -> bytes:
    if (
        not isinstance(entry, dict)
        or not isinstance(entry.get("path"), str)
        or not Path(entry["path"]).is_absolute()
        or not isinstance(entry.get("sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) is None
    ):
        raise ValueError("Task asset requires an explicit path and SHA-256")
    path = Path(entry["path"])
    if not path.is_file() or path.stat().st_size > 16 * 1024**2:
        raise ValueError("Task asset is missing or exceeds the input budget")
    data = path.read_bytes()
    if sha256(data) != entry["sha256"]:
        raise ValueError("Task asset differs from its frozen identity")
    return data


def validate_task(task: Any) -> dict[str, Any]:
    fields = {
        "schema_version",
        "id",
        "source",
        "collection_policy",
        "baseline_manifest_sha256",
        "image_reference",
        "verifier",
        "inventory",
        "source_directory",
        "import_paths",
        "test_timeout_seconds",
        "min_pass_rate",
        "grader_user",
        "scorer",
        "execution_source_sha256",
        "import_origins",
        "python_safe_path",
    }
    if (
        not isinstance(task, dict)
        or type(task.get("schema_version")) is not int
        or task.get("schema_version") not in (2, 3)
        or set(task) != fields | ({"python_environment"} if task["schema_version"] == 3 else set())
    ):
        raise ValueError("Expected a complete frozen native grading task")
    if task["execution_source_sha256"] != source_hashes():
        raise ValueError("Native controller sources differ from the frozen task")
    collection_policy(task["collection_policy"])
    if task["schema_version"] == 3:
        environment = validate_environment(task["python_environment"], asset)
        LeaseResources(**environment["resources"], executable_workspace=True, repository_workspace=True)
    source = task["source"]
    if (
        not isinstance(source, dict)
        or set(source) != {"repository", "commit"}
        or not isinstance(source["repository"], str)
        or re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", source["repository"]) is None
        or not isinstance(source["commit"], str)
        or re.fullmatch(r"[0-9a-f]{40}", source["commit"]) is None
    ):
        raise ValueError("Native task source provenance is malformed")
    if (
        not isinstance(task["id"], str)
        or not task["id"]
        or re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", task["source_directory"]) is None
        or re.fullmatch(r"test_[a-z0-9_]+\.py", task["verifier"]["target"]) is None
        or type(task["test_timeout_seconds"]) is not int
        or not 1 <= task["test_timeout_seconds"] <= 900
        or type(task["min_pass_rate"]) not in (int, float)
        or not 0 <= task["min_pass_rate"] <= 1
        or not isinstance(task["grader_user"], str)
        or re.fullmatch(r"[a-z][a-z0-9_-]*", task["grader_user"]) is None
        or task["grader_user"] == "root"
        or not isinstance(task["import_paths"], list)
        or not task["import_paths"]
    ):
        raise ValueError("Native task command or runtime profile is invalid")
    for path in task["import_paths"]:
        if path != ".":
            relative_path(path)
    if type(task["python_safe_path"]) is not bool:
        raise ValueError("Native task must declare its Python path behavior")
    origins = task["import_origins"]
    if not isinstance(origins, dict) or not origins or "pytest" not in origins:
        raise ValueError("Native task must pin its framework and project import origins")
    source_modules = 0
    for name, origin in origins.items():
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None
            or not isinstance(origin, dict)
        ):
            raise ValueError("Native import origin declaration is malformed")
        if set(origin) == {"source_path"}:
            relative_path(origin["source_path"], workspace=True)
            if name == "pytest":
                raise ValueError("The test framework must resolve from the pinned image")
            source_modules += 1
        elif set(origin) == {"image_path", "sha256"}:
            if (
                not isinstance(origin["image_path"], str)
                or not origin["image_path"].startswith("/usr/")
                or not isinstance(origin["sha256"], str)
                or re.fullmatch(r"[0-9a-f]{64}", origin["sha256"]) is None
            ):
                raise ValueError("Pinned image import identity is malformed")
            if name == "pytest" and task["schema_version"] == 3:
                raise ValueError("The test framework must resolve from the frozen environment")
        elif set(origin) == {"environment_path", "sha256"} and task["schema_version"] == 3:
            relative_path(origin["environment_path"])
            if not isinstance(origin["sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", origin["sha256"]) is None:
                raise ValueError("Frozen environment import identity is malformed")
        else:
            raise ValueError("An import origin must declare source bytes or a pinned image module")
    if not source_modules:
        raise ValueError("Native task must declare the project code being evaluated")
    scorer = task["scorer"]
    if not isinstance(scorer, dict) or set(scorer) != {"files", "wheels", "versions"}:
        raise ValueError("Publisher scorer must declare sources and dependencies")
    if not isinstance(scorer["files"], list) or not 1 <= len(scorer["files"]) <= 64:
        raise ValueError("Publisher scorer source inventory is invalid")
    targets = set()
    for entry in scorer["files"]:
        name = relative_path(entry["target"])
        if not name.startswith("src/") or name.casefold() in targets:
            raise ValueError("Publisher source has a duplicate or out-of-scope destination")
        targets.add(name.casefold())
        asset(entry)
    wheels = scorer["wheels"]
    if not isinstance(wheels, list) or not 1 <= len(wheels) <= 64 or not isinstance(scorer["versions"], dict):
        raise ValueError("Publisher dependency inventory is invalid")
    projects = set()
    wheel_files = set()
    for wheel in wheels:
        name = wheel["project"]
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name) is None
            or name.casefold() in projects
            or not isinstance(wheel["version"], str)
            or re.fullmatch(r"[0-9]+(?:\.[0-9]+)+(?:\.post[0-9]+)?", wheel["version"]) is None
            or scorer["versions"].get(name) != wheel["version"]
            or re.fullmatch(r"[A-Za-z0-9._-]+\.whl", Path(wheel["path"]).name) is None
            or Path(wheel["path"]).name in wheel_files
        ):
            raise ValueError("Publisher wheel declaration is invalid")
        projects.add(name.casefold())
        wheel_files.add(Path(wheel["path"]).name)
        asset(wheel)
    asset(task["verifier"])
    profile = _inventory(asset(task["inventory"]))
    if task["schema_version"] == 3:
        pytest_wheel = next(row for row in task["python_environment"]["wheels"] if row["project"] == "pytest")
        if pytest_wheel["version"] != profile.pytest_version:
            raise ValueError("Frozen environment and evaluator inventory disagree on pytest version")
    if profile.min_pass_rate != task["min_pass_rate"] or (
        profile.collection_policy is not None and profile.collection_policy != task["collection_policy"]
    ):
        raise ValueError("Native inventory and task disagree on scoring or collection policy")
    return task


def completed_capture(directory: Path, policy: dict[str, Any]) -> tuple[bytes, Path]:
    launch = strict_json((directory / "launch.json").read_text(encoding="utf-8"))
    verify_collector_launch(launch, policy, launch["workspace"])
    if Path(launch["source_root"]).resolve() != ROOT or Path(launch["observations"]).resolve() != directory.resolve():
        raise ValueError("Source collection belongs to another controller or attempt")
    stdout = (directory / "stdout.native").read_bytes()
    stderr = (directory / "stderr.native").read_bytes()
    process = strict_json((directory / "process.json").read_text(encoding="utf-8"))
    if not process_complete(process, policy, len(stdout) + len(stderr)):
        raise ValueError("Source collection process did not complete")
    native = validate_manifest(strict_json(stdout.decode("utf-8")), policy)
    record = (directory / "result.json").read_bytes()
    if strict_json(record.decode("utf-8")) != native:
        raise ValueError("Source collection result differs from its native process output")
    return record, Path(launch["output"])


def _run(
    lease: ContainerLease,
    label: str,
    program: str,
    *arguments: str,
    user: str = "0:0",
    timeout: int = 30,
    python: str = "python",
) -> bytes:
    if lease.identity is None or lease.owned(lease.identity) is None:
        raise ValueError("Native operation requires an owned container")
    return lease.client.run(
        label,
        [
            "container",
            "exec",
            "--user=" + user,
            "--env=PYTHONDONTWRITEBYTECODE=1",
            lease.identity,
            python,
            *PYTHON[1:],
            "-c",
            program,
            *arguments,
        ],
        timeout=timeout,
    )


def grade(task: dict[str, Any], runtime: Path, baseline: Path, collection: Path, output: Path) -> dict[str, Any]:
    """Grade a stopped subject's complete capture and retain every phase's evidence."""
    if output.exists() or not output.resolve().is_relative_to(ROOT / ".venv"):
        raise ValueError("Native grade output must be a new directory in owned ignored state")
    output.mkdir()
    report: dict[str, Any] = {"status": "harness_error", "score": None, "model_requests": 0, "stage": "validate"}
    try:
        task = validate_task(task)
        before, base = completed_capture(baseline, task["collection_policy"])
        after, submitted = completed_capture(collection, task["collection_policy"])
        if sha256(before) != task["baseline_manifest_sha256"]:
            raise ValueError("Baseline capture differs from the frozen task")
        plan = plan_handoff(before, after)
        expected_imports = {}
        for name, origin in task["import_origins"].items():
            if "source_path" in origin:
                path = origin["source_path"]
                identity = plan.submission["files"].get(path)
                expected_imports[name] = {
                    "path": "/workspace/" + task["source_directory"] + "/" + path,
                    "sha256": identity["sha256"] if identity else None,
                }
            else:
                path = (
                    str(DEPENDENCY_PREFIX / origin["environment_path"])
                    if "environment_path" in origin
                    else origin["image_path"]
                )
                expected_imports[name] = {"path": path, "sha256": origin["sha256"]}
        runtime_task = {**task, "expected_imports": expected_imports}
        report.update(task_id=task["id"], stage="handoff")
        sealed = seal(plan, submitted, output / "delta.tar")
        write_json(output / "handoff.json", sealed)
        client = DockerClient(ROOT, output / "client", runtime)
        if client.reference != task["image_reference"]:
            raise ValueError("Native runtime image differs from the frozen task")
        packet = {
            "baseline.json": before,
            "submission.json": after,
            "delta.tar": (output / "delta.tar").read_bytes(),
            "task.json": (json.dumps(runtime_task, sort_keys=True) + "\n").encode(),
            "verifier.py": asset(task["verifier"]),
            **{"tools/" + name: (ROOT / "tools" / name).read_bytes() for name in SUPPORT},
        }
        for name, identity in plan.baseline["files"].items():
            raw = (base / name).read_bytes()
            if len(raw) != identity["bytes"] or sha256(raw) != identity["sha256"]:
                raise ValueError("Pinned baseline bytes changed after collection")
            packet["baseline/" + name] = raw
        environment = task.get("python_environment")
        if environment is not None:
            packet.update(environment_packet(environment, asset))
        report["stage"] = "native-grader"
        write_json(output / "progress.json", report)
        lease = ContainerLease(
            client,
            output / "grader.lease.json",
            seconds=task["test_timeout_seconds"] + 60 + (environment["setup_timeout_seconds"] if environment else 0),
            resources=LeaseResources(
                **(
                    environment["resources"]
                    if environment
                    else {"memory_bytes": 768 * 1024**2, "tmpfs_bytes": 64 * 1024**2}
                ),
                pids_limit=64,
                executable_workspace=environment is not None,
                repository_workspace=True,
            ),
        )
        try:
            grader_id = lease.create()
            lease.start()
            stage_inputs(lease, output / "grader-inputs", packet)
            if environment is not None:
                prepared = strict_json(
                    _run(
                        lease, "prepare-dependencies", DEPENDENCY_SETUP, timeout=environment["setup_timeout_seconds"]
                    ).decode("utf-8")
                )
                write_json(output / "dependencies.native.json", prepared)
            rebuilt_raw = _run(lease, "restore", REBUILD, sealed["archive_sha256"])
            (output / "reconstruction.native.json").write_bytes(rebuilt_raw)
            rebuilt = strict_json(rebuilt_raw.decode("utf-8"))
            expected = {
                "status": "grader_tree_rebuilt",
                "archive_sha256": sealed["archive_sha256"],
                "baseline_manifest_sha256": sha256(before),
                "submission_manifest_sha256": sha256(after),
            }
            if not isinstance(rebuilt, dict) or any(rebuilt.get(key) != value for key, value in expected.items()):
                raise ValueError("Native reconstruction differs from the sealed captures")
            native = strict_json(
                _run(
                    lease,
                    "pytest",
                    EVALUATE,
                    user=task["grader_user"],
                    timeout=task["test_timeout_seconds"] + 10,
                    python=DEPENDENCY_PYTHON if environment is not None else "python",
                ).decode("utf-8")
            )
            write_json(output / "execution.json", native)
            if native.get("import_error"):
                raise ValueError("Native framework or project imports differ from the declared source")
            for suffix in ("stdout", "stderr"):
                data = client.run(
                    "collect-" + suffix,
                    [
                        "container",
                        "exec",
                        "--user=" + task["grader_user"],
                        grader_id,
                        "cat",
                        "/tmp/pytest." + suffix,
                    ],
                )
                (output / ("pytest." + suffix + ".native")).write_bytes(data)
            if native["timed_out"]:
                raise ValueError("Native verifier exceeded its declared time budget")
            xml = client.run(
                "collect-junit",
                ["container", "exec", "--user=" + task["grader_user"], grader_id, "cat", "/tmp/pytest.xml"],
            )
            (output / "pytest.xml.native").write_bytes(xml)
            if environment is not None:
                final_inventory = strict_json(
                    _run(lease, "verify-dependencies", DEPENDENCY_VERIFY, user=task["grader_user"]).decode("utf-8")
                )
                write_json(output / "dependencies-after.native.json", final_inventory)
                if final_inventory != prepared["inventory"]:
                    raise ValueError("Frozen grader environment changed during evaluator execution")
        finally:
            lease.close()

        report["stage"] = "publisher-score"
        write_json(output / "progress.json", report)
        scorer = task["scorer"]
        scorer_packet = {
            "task.json": packet["task.json"],
            "execution.json": (
                json.dumps({k: native[k] for k in ("exit_code", "timed_out", "duration")}) + "\n"
            ).encode(),
            "console": (output / "pytest.stdout.native").read_bytes(),
            "stderr": (output / "pytest.stderr.native").read_bytes(),
            **{"scorer/" + row["target"]: asset(row) for row in scorer["files"]},
            **{"wheels/" + Path(row["path"]).name: asset(row) for row in scorer["wheels"]},
        }
        lock = "".join(
            f"{row['project']}=={row['version']} --hash=sha256:{row['sha256']}\n" for row in scorer["wheels"]
        )
        scorer_packet["requirements.lock"] = lock.encode()
        score_lease = ContainerLease(
            client,
            output / "scorer.lease.json",
            seconds=90,
            resources=LeaseResources(tmpfs_bytes=48 * 1024**2),
        )
        try:
            scorer_id = score_lease.create()
            score_lease.start()
            stage_inputs(score_lease, output / "scorer-inputs", scorer_packet)
            client.run(
                "install-scorer",
                [
                    "container",
                    "exec",
                    "--user=" + task["grader_user"],
                    "--env=PIP_CONFIG_FILE=/dev/null",
                    scorer_id,
                    *PYTHON,
                    "-m",
                    "pip",
                    "--disable-pip-version-check",
                    "install",
                    "--no-index",
                    "--no-deps",
                    "--no-cache-dir",
                    "--require-hashes",
                    "--find-links=/tmp/benchmark-inputs/wheels",
                    "--target=/tmp/scorer-dependencies",
                    "-r",
                    "/tmp/benchmark-inputs/requirements.lock",
                ],
                timeout=45,
            )
            scored = strict_json(_run(score_lease, "publisher-score", SCORE, user=task["grader_user"]).decode("utf-8"))
            write_json(output / "publisher.json", scored)
        finally:
            score_lease.close()
        report["stage"] = "admission"
        publisher = (json.dumps(scored["verdict"], sort_keys=True) + "\n").encode()
        (output / "publisher-result.json").write_bytes(publisher)
        inventory = asset(task["inventory"])
        profile = strict_json(inventory.decode("utf-8"))
        bound = {"submission_manifest": after, "handoff_result": rebuilt_raw} if profile["schema_version"] == 2 else {}
        result = verify_result(
            inventory=inventory,
            console=(output / "pytest.stdout.native").read_bytes(),
            junit=xml,
            publisher=publisher,
            exit_code=native["exit_code"],
            timed_out=native["timed_out"],
            **bound,
        )
        write_json(output / "admission.json", result)
        report.update(
            status="task_passed" if result["score"] >= task["min_pass_rate"] else "task_failed",
            score=result["score"],
            stage="complete",
            native_counts={key: result[key] for key in ("passed", "failed", "skipped", "errors", "total")},
            task_sha256=sha256((json.dumps(task, sort_keys=True) + "\n").encode()),
            baseline_manifest_sha256=sha256(before),
            submission_manifest_sha256=sha256(after),
            archive_sha256=sealed["archive_sha256"],
            execution_source_sha256=source_hashes(),
        )
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        report.update(error_type=type(error).__name__, error=str(error))
    write_json(output / "result.json", report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--baseline-collection", required=True, type=Path)
    parser.add_argument("--submission-collection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        task = strict_json(args.task.read_text(encoding="utf-8"))
        result = grade(task, args.runtime, args.baseline_collection, args.submission_collection, args.output)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {"status": "harness_error", "score": None, "error": str(error), "model_requests": 0}
    print(json.dumps(result, sort_keys=True))
    return {"task_passed": 0, "task_failed": 1, "harness_error": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())

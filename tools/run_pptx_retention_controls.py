#!/usr/bin/env python3
"""Compare pinned native PPTX converters on an owned, deterministic fixture."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import _pptx_retention as evaluator
import _windows_owned_python as owned_python

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "skills/ppt-master"
MAX_SOURCE_FILES = 20000
MAX_SOURCE_BYTES = 256 * 1024 * 1024
FROZEN_NAMES = {
    "retention.pptx",
    "task-before-execution.json",
    "controller-before-execution.py",
    "evaluator-before-execution.py",
    "requirements.txt",
    "old-source-manifest.json",
    "new-source-manifest.json",
    "process-control-before-execution.py",
}
BOOTSTRAP = r"""
import os,runpy,sys
from pathlib import Path
script=Path(sys.argv[1]).resolve()
owned=Path(sys.argv[2]).resolve()
arguments=sys.argv[3:]
def check_path(path):
    if not isinstance(path,int) and not Path(os.fsdecode(path)).resolve().is_relative_to(owned):
        raise RuntimeError('Write outside owned consumer workspace denied')
def audit(event,args):
    if event in ('socket.connect','socket.bind','socket.getaddrinfo','subprocess.Popen','os.system'):
        raise RuntimeError('Network or subprocess execution denied in converter controls')
    if event=='open' and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
        check_path(args[0])
    if event in ('os.remove','os.rmdir','os.mkdir'):check_path(args[0])
    if event in ('os.rename','os.replace'):
        check_path(args[0]);check_path(args[1])
sys.addaudithook(audit)
sys.path.insert(0,str(script.parent))
sys.argv=[str(script),*arguments]
runpy.run_path(str(script),run_name='__main__')
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular_file(root: Path, name: str, checked_directories: set[Path] | None = None) -> Path:
    """Check canonical paths and reject links; reuse parent checks within one scan."""
    relative = PurePosixPath(name)
    if (
        not relative.parts
        or relative.as_posix() != name
        or relative.is_absolute()
        or "\\" in name
        or ":" in name
        or ".." in relative.parts
    ):
        raise ValueError(f"noncanonical component resource: {name}")
    path = root.joinpath(*relative.parts)
    directories = checked_directories if checked_directories is not None else set()
    for parent in path.parents:
        if parent == root or parent in directories:
            break
        info = parent.lstat()
        if not stat.S_ISDIR(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"linked or non-directory resource parent: {name}")
    else:
        raise ValueError(f"resource escapes component root: {name}")
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ValueError(f"linked or nonregular component resource: {name}")
    for parent in path.parents:
        if parent == root or parent in directories:
            break
        directories.add(parent)
    return path


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git(root: Path, *args: str) -> bytes:
    command = [
        "git",
        "-c",
        "core.longpaths=true",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "core.hooksPath=NUL",
        "-C",
        str(root),
        *args,
    ]
    result = subprocess.run(command, capture_output=True, timeout=60)
    if result.returncode:
        raise ValueError("source Git metadata is unavailable")
    return result.stdout


def verify_source(root: Path, commit: str) -> dict[str, Any]:
    """Verify all selected working files against an exact committed Git tree."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("source commit must be an immutable 40-character Git SHA")
    root = root.resolve()
    if Path(_git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve() != root:
        raise ValueError("source must be the exact Git checkout root")
    if _git(root, "rev-parse", "HEAD").decode().strip() != commit:
        raise ValueError("source HEAD does not match the requested commit")
    # Omitting --exclude-standard deliberately includes ignored bytecode and .env files.
    if _git(root, "ls-files", "--others", "-z", "--", PACKAGE).strip(b"\0"):
        raise ValueError("source package contains untracked or ignored files")
    entries = [row for row in _git(root, "ls-tree", "-r", "-z", commit, "--", PACKAGE).split(b"\0") if row]
    if not 1 <= len(entries) <= MAX_SOURCE_FILES:
        raise ValueError("source package is absent or exceeds the file budget")
    files, errors = [], []
    checked_directories: set[Path] = set()
    size = 0
    for row in entries:
        metadata, encoded_name = row.split(b"\t", 1)
        mode, kind, blob = metadata.decode().split()
        name = encoded_name.decode("utf-8")
        if kind != "blob" or mode not in {"100644", "100755"}:
            errors.append(f"{name}: nonregular source object")
            continue
        try:
            path = regular_file(root, name, checked_directories)
            with path.open("rb") as stream:
                expected_size = os.fstat(stream.fileno()).st_size
                if expected_size > MAX_SOURCE_BYTES - size:
                    errors.append("source package exceeds the byte budget")
                    break
                raw = stream.read(expected_size + 1)
            if len(raw) != expected_size:
                raise ValueError("source file changed while reading")
            size += len(raw)
            if size > MAX_SOURCE_BYTES:
                errors.append("source package exceeds the byte budget")
                break
            actual = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False).hexdigest()
            if actual != blob:
                errors.append(f"{name}: working bytes differ from the pinned Git blob")
            files.append(
                {"path": name, "mode": mode, "blob": blob, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            )
        except (OSError, ValueError) as error:
            errors.append(f"{name}: {error}")
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "commit": commit,
        "package": PACKAGE,
        "tree": _git(root, "rev-parse", f"{commit}:{PACKAGE}").decode().strip(),
        "file_count": len(files),
        "bytes": size,
        "files": files,
    }


def environment_versions(lock: Path) -> dict[str, str]:
    packages = {}
    for line in lock.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        match = re.fullmatch(r"([a-z0-9-]+)==([^ ]+) --hash=sha256:[a-f0-9]{64}", line)
        if match is None:
            raise ValueError("consumer lock requires one exact, hashed wheel record per package")
        name, version = match.groups()
        if name in packages or importlib.metadata.version(name) != version:
            raise ValueError(f"consumer dependency differs from its lock: {name}")
        packages[name] = version
    if set(packages) != {"defusedxml", "python-pptx", "lxml", "pillow", "typing-extensions", "xlsxwriter"}:
        raise ValueError("consumer lock does not describe the complete six-package cohort")
    return packages


def invoke(command: list[str], workspace: Path, prefix: str, environment: dict[str, str]) -> tuple[int, dict[str, Any]]:
    """Retain native output, including unsuccessful and timed-out invocations."""
    with (
        (workspace / f"{prefix}.stdout.log").open("xb") as stdout,
        (workspace / f"{prefix}.stderr.log").open("xb") as stderr,
    ):
        if command[1:4] != ["-I", "-B", "-c"]:
            raise ValueError("native invocation must use the reviewed isolated bootstrap")
        return owned_python.run_python(
            command[0], command[4], command[5:], cwd=workspace, environment=environment, stdout=stdout, stderr=stderr
        )


def run_controls(args: argparse.Namespace) -> dict[str, Any]:
    sources = [
        ("old", args.baseline_source.resolve(), args.baseline_commit),
        ("new", args.candidate_source.resolve(), args.candidate_commit),
    ]
    output = args.output.resolve()
    if any(output.is_relative_to(source) for _, source, _ in sources):
        raise ValueError("output must be outside both source checkouts")
    snapshots = {label: verify_source(source, commit) for label, source, commit in sources}
    versions = environment_versions(args.requirements)
    fixture, task = evaluator.create_fixture(output)
    write_json(output / "task-before-execution.json", task)
    (output / "controller-before-execution.py").write_bytes(Path(__file__).read_bytes())
    (output / "evaluator-before-execution.py").write_bytes(Path(evaluator.__file__).read_bytes())
    (output / "process-control-before-execution.py").write_bytes(Path(owned_python.__file__).read_bytes())
    (output / "requirements.txt").write_bytes(args.requirements.read_bytes())
    for label, snapshot in snapshots.items():
        write_json(output / f"{label}-source-manifest.json", snapshot)
    frozen = {name: sha256(output / name) for name in sorted(FROZEN_NAMES)}
    results = []
    for label, source, _ in sources:
        workspace = output / label
        workspace.mkdir()
        (workspace / "validation").mkdir()
        (workspace / "validation/workflow.log").write_text("", encoding="utf-8")
        script = source / PACKAGE / "scripts/source_to_md/ppt_to_md.py"
        environment = {
            key: value
            for key, value in os.environ.items()
            if key.upper() in {"SYSTEMROOT", "WINDIR", "PATH", "COMSPEC", "PATHEXT", "TEMP", "TMP"}
        }
        environment.update(PYTHONUTF8="1", PPT_MASTER_PROJECT_PATH=str(workspace))
        guard_exit, guard_process = invoke(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                BOOTSTRAP,
                str(script.parents[1] / "attribution_guard.py"),
                str(workspace),
            ],
            workspace,
            "integrity-guard",
            environment,
        )
        cli_exit = None
        cli_process = None
        markdown = workspace / "retention.md"
        if guard_exit == 0:
            cli_exit, cli_process = invoke(
                [
                    sys.executable,
                    "-I",
                    "-B",
                    "-c",
                    BOOTSTRAP,
                    str(script),
                    str(workspace),
                    str(fixture),
                    "-o",
                    str(markdown),
                ],
                workspace,
                "converter",
                environment,
            )
        text = read_markdown(output, label)
        checks = {
            "cli_completes": cli_exit == 0 and guard_exit == 0,
            **evaluator.evaluate_markdown(text),
            "input_bytes_unchanged": sha256(fixture) == frozen["retention.pptx"],
        }
        if verify_source(source, snapshots[label]["commit"]) != snapshots[label]:
            raise ValueError(f"{label} source changed during conversion")
        results.append(
            {
                "version": label,
                "source_commit": snapshots[label]["commit"],
                "guard_exit_code": guard_exit,
                "exit_code": cli_exit,
                "owned_processes": {"guard": guard_process, "converter": cli_process},
                "checks": checks,
                "passed": sum(checks.values()),
                "total": len(checks),
                "markdown_sha256": sha256(markdown) if markdown.is_file() else None,
                "native_logs": {path.name: sha256(path) for path in sorted(workspace.glob("*.log"))},
            }
        )
    if any(sha256(output / name) != digest for name, digest in frozen.items()):
        raise ValueError("a frozen control input changed during execution")
    return {
        "schema_version": 1,
        "evidence_class": "native-component-content-retention-controls",
        "frozen_inputs": frozen,
        "results": results,
        "python_version": sys.version.split()[0],
        "consumer_versions": versions,
        "same_interpreter_and_dependencies": True,
        "guards_bypassed": False,
        "process_controls": "Windows kill-on-close jobs gate the real interpreter before site initialization; deadlines and output bounds include descendants. Python isolated mode; inherited provider credentials absent; audit denial of sockets, subprocesses and writes outside owned output. This is not an OS sandbox.",
        "coding_agents_or_external_llms_executed": 0,
        "paid_jobs_executed": 0,
        "benchmark_scope": "One synthetic three-slide fixture and eleven component controls; no rendering, Office certification, performance or coding-agent score.",
    }


def read_markdown(output: Path, label: str) -> str:
    path = output / label / "retention.md"
    if not path.exists():
        return ""
    path = regular_file(output, f"{label}/retention.md")
    if path.stat().st_size > evaluator.MAX_MARKDOWN_BYTES:
        raise ValueError("retention Markdown exceeds the one MiB evaluation budget")
    return path.read_text(encoding="utf-8")


def check_result(output: Path) -> dict[str, Any]:
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    if (
        not isinstance(result, dict)
        or result.get("schema_version") != 1
        or result.get("evidence_class") != "native-component-content-retention-controls"
    ):
        raise ValueError("unsupported component result")
    if not isinstance(result.get("frozen_inputs"), dict) or set(result["frozen_inputs"]) != FROZEN_NAMES:
        raise ValueError("component result omits required frozen inputs")
    for name, digest in result["frozen_inputs"].items():
        if sha256(regular_file(output, name)) != digest:
            raise ValueError("frozen component input hash mismatch")
    for name, path in (
        ("evaluator-before-execution.py", Path(evaluator.__file__)),
        ("controller-before-execution.py", Path(__file__)),
        ("process-control-before-execution.py", Path(owned_python.__file__)),
    ):
        if sha256(output / name) != sha256(path):
            raise ValueError("result was produced by a different controller or evaluator version")
    task = json.loads((output / "task-before-execution.json").read_text(encoding="utf-8"))
    if task["fixture_sha256"] != result["frozen_inputs"]["retention.pptx"]:
        raise ValueError("task and frozen fixture hashes differ")
    if (
        not isinstance(result.get("results"), list)
        or any(not isinstance(row, dict) for row in result["results"])
        or [row["version"] for row in result["results"]] != ["old", "new"]
    ):
        raise ValueError("component result must preserve both source versions")
    for row in result["results"]:
        manifest = json.loads((output / f"{row['version']}-source-manifest.json").read_text(encoding="utf-8"))
        if row["source_commit"] != manifest["commit"] or not re.fullmatch(r"[0-9a-f]{40}", row["source_commit"]):
            raise ValueError("result source commit differs from the frozen source manifest")
        if type(row["guard_exit_code"]) is not int or (
            row["exit_code"] is not None and type(row["exit_code"]) is not int
        ):
            raise ValueError("native exit codes must be integers")
        for phase, code in (("guard", row["guard_exit_code"]), ("converter", row["exit_code"])):
            process = row["owned_processes"][phase]
            if code is None and process is None:
                continue
            if (
                not isinstance(process, dict)
                or any(
                    process.get(key) is not True
                    for key in ("windows_job", "real_interpreter_gated_before_site", "kill_on_close")
                )
                or type(process.get("active_processes_after_cleanup")) is not int
                or process["active_processes_after_cleanup"] != 0
            ):
                raise ValueError("owned process cleanup evidence is incomplete")
            reason = process.get("termination_reason")
            if (reason is None and code in {124, 125}) or (
                reason is not None and (reason, code) not in {("timeout", 124), ("output_limit", 125)}
            ):
                raise ValueError("owned process termination reason differs from its native status")
        required_logs = {"integrity-guard.stdout.log", "integrity-guard.stderr.log"}
        if row["exit_code"] is not None:
            required_logs.update({"converter.stdout.log", "converter.stderr.log"})
        if not isinstance(row.get("native_logs"), dict) or set(row["native_logs"]) != required_logs:
            raise ValueError("native execution logs are incomplete")
        for name, digest in row["native_logs"].items():
            if sha256(regular_file(output, f"{row['version']}/{name}")) != digest:
                raise ValueError("native execution log hash mismatch")
        markdown = output / row["version"] / "retention.md"
        if (sha256(markdown) if markdown.is_file() else None) != row["markdown_sha256"]:
            raise ValueError("native Markdown output hash mismatch")
        text = read_markdown(output, row["version"])
        expected = {
            "cli_completes": row["exit_code"] == 0 and row["guard_exit_code"] == 0,
            **evaluator.evaluate_markdown(text),
            "input_bytes_unchanged": True,
        }
        if (
            not isinstance(row.get("checks"), dict)
            or any(type(value) is not bool for value in row["checks"].values())
            or type(row["passed"]) is not int
            or type(row["total"]) is not int
            or expected != row["checks"]
            or row["passed"] != sum(expected.values())
            or row["total"] != len(expected)
        ):
            raise ValueError("component result differs from its retained native output")
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-source", type=Path)
    parser.add_argument("--baseline-commit")
    parser.add_argument("--candidate-source", type=Path)
    parser.add_argument("--candidate-commit")
    parser.add_argument("--requirements", type=Path, default=ROOT / "toolchains/pptx-native/requirements.txt")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate retained inputs and recompute semantic checks without rerunning converters",
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.check:
            result = check_result(args.output.resolve())
        else:
            if any(
                value is None
                for value in (args.baseline_source, args.baseline_commit, args.candidate_source, args.candidate_commit)
            ):
                raise ValueError("execution requires both explicit source roots and immutable commits")
            result = run_controls(args)
            write_json(args.output.resolve() / "result.json", result)
            result = check_result(args.output.resolve())
        complete = all(
            row["checks"]["cli_completes"] and row["checks"]["input_bytes_unchanged"] for row in result["results"]
        )
        candidate_passed = all(result["results"][1]["checks"].values())
        summary = {
            "errors": [],
            "protocol_complete": complete,
            "candidate_controls_passed": candidate_passed,
            "results": [
                {key: row[key] for key in ("version", "source_commit", "passed", "total")} for row in result["results"]
            ],
            "coding_agent_efficacy_scored": False,
        }
        print(json.dumps(summary, indent=2) if args.json else str(summary))
        return 0 if complete and candidate_passed else 1
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        importlib.metadata.PackageNotFoundError,
        subprocess.SubprocessError,
    ) as error:
        print(json.dumps({"errors": [str(error)], "protocol_complete": False, "coding_agent_efficacy_scored": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run a fresh CLI coding trial against a frozen, externally graded protocol."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from _lib_b.io_utils import read_json, write_json

ROOT = Path(__file__).resolve().parents[1]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def checked_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError(f"path escapes its workspace: {relative}")
    return path


def pinned_file(commit: str, path: str) -> bytes:
    checked_path(ROOT, path)
    if len(commit) != 40 or any(character not in "0123456789abcdef" for character in commit):
        raise ValueError("source commit must be an immutable SHA")
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{path}"])


def prepare(protocol: dict[str, Any], condition: str, python: Path) -> tuple[Path, str, dict[str, bytes]]:
    task = protocol["task"]
    inputs = {name: pinned_file(task["source_commit"], name) for name in task["files"]}
    if {name: sha256(data) for name, data in inputs.items()} != protocol["input_sha256"]:
        raise ValueError("frozen task source hashes differ")
    grader = checked_path(ROOT, task["grader"])
    if sha256(grader.read_bytes()) != protocol["grader_sha256"]:
        raise ValueError("external grader changed after protocol freeze")
    instructions = []
    for skill in protocol["conditions"][condition]["skills"]:
        path = checked_path(ROOT, skill["path"])
        data = path.read_bytes()
        if sha256(data) != skill["sha256"]:
            raise ValueError("condition instructions changed after protocol freeze")
        instructions.append(data.decode("utf-8"))
    workspace = Path(tempfile.mkdtemp(prefix="skills-agent-trial-"))
    for name, data in inputs.items():
        target = checked_path(workspace, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    for name, text in protocol.get("workspace_scaffold", {}).items():
        if name in inputs:
            raise ValueError("workspace scaffold must not replace pinned source inputs")
        target = checked_path(workspace, name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    prompt = (
        protocol["prompt_template"]
        .replace("<TASK_BRIEF>", task["brief"])
        .replace("<PYTHON_RUNTIME>", str(python.resolve()))
    )
    if instructions:
        prompt += "\n\nAdditional skill instructions for this condition:\n\n" + "\n\n".join(instructions)
    return workspace, prompt, inputs


def command(protocol: dict[str, Any], cli: Path, workspace: Path) -> list[str]:
    result = [
        str(cli.resolve()),
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "-c",
        'approval_policy="never"',
        "-c",
        f'model_reasoning_effort="{protocol["reasoning_effort"]}"',
        "-c",
        "features.skip_host_skill_discovery=true",
        "-c",
        'web_search="disabled"',
        "-c",
        "sandbox_workspace_write.network_access=false",
    ]
    if platform.system() == "Windows":
        result.extend(["-c", 'windows.sandbox="elevated"'])
    for feature in ("memories", "plugins", "apps", "multi_agent", "browser_use", "computer_use"):
        result.extend(["--disable", feature])
    return [*result, "--json", "-m", protocol["model"], "-C", str(workspace), "-"]


def read_events(path: Path) -> list[dict[str, Any]]:
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # A killed process may leave one truncated final event. Retain the
            # raw transcript; do not infer a completed turn or zero usage.
            continue
    return events


def external_grade(task: dict[str, Any], workspace: Path, python: Path) -> dict[str, Any]:
    try:
        result = subprocess.run(
            [
                str(python.resolve()),
                str(ROOT / "tools/grade_agent_submission.py"),
                str(checked_path(ROOT, task["grader"])),
                str(workspace.resolve()),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"status": "task_failed", "error": "submitted code exceeded the 60-second grading limit"}
    if result.returncode:
        return {"status": "task_failed", "error": "submission could not be graded", "diagnostic": result.stderr[-2000:]}
    return json.loads(result.stdout)


def run(protocol_path: Path, condition: str, output: Path, cli: Path, python: Path) -> dict[str, Any]:
    protocol = read_json(protocol_path)
    if output.exists():
        raise ValueError("trial output already exists; refusing to overwrite an attempt")
    for name, key in (("run_agent_trial.py", "runner_sha256"), ("grade_agent_submission.py", "grading_driver_sha256")):
        if sha256((ROOT / "tools" / name).read_bytes()) != protocol[key]:
            raise ValueError("benchmark execution tooling changed after protocol freeze")
    workspace, prompt, inputs = prepare(protocol, condition, python)
    output.mkdir(parents=True, exist_ok=False)
    (output / "prompt.txt").write_text(prompt, encoding="utf-8")
    invocation = command(protocol, cli, workspace)
    write_json(output / "launch.json", {"command": invocation, "protocol_sha256": sha256(protocol_path.read_bytes())})
    started = time.monotonic()
    timed_out = False
    with (
        (output / "transcript.jsonl").open("w", encoding="utf-8") as stdout,
        (output / "stderr.txt").open("w", encoding="utf-8") as stderr,
    ):
        process = subprocess.Popen(
            invocation, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, text=True, encoding="utf-8"
        )
        try:
            process.communicate(prompt, timeout=protocol["time_limit_seconds"])
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.communicate()
    elapsed = time.monotonic() - started
    events = read_events(output / "transcript.jsonl")
    usage = next((event.get("usage") for event in reversed(events) if event["type"] == "turn.completed"), None)
    completed = any(event["type"] == "turn.completed" for event in events)
    commands = [
        event["item"]
        for event in events
        if event["type"] == "item.completed" and event.get("item", {}).get("type") == "command_execution"
    ]
    changes: list[str] = []
    violations: list[str] = []
    patch: list[str] = []
    collection_errors: list[str] = []
    submission = output / "submission"
    for name, before in inputs.items():
        source = checked_path(workspace, name)
        if source.is_file():
            target = checked_path(submission, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        after = source.read_bytes() if source.is_file() else b""
        if after != before:
            changes.append(name)
            if name not in protocol["task"]["allowed_changes"]:
                violations.append(f"protected source input changed: {name}")
            patch.extend(
                difflib.unified_diff(
                    before.decode("utf-8").splitlines(True),
                    after.decode("utf-8").splitlines(True),
                    fromfile=f"a/{name}",
                    tofile=f"b/{name}",
                )
            )
    for name in protocol.get("workspace_scaffold", {}):
        path = checked_path(workspace, name)
        target = checked_path(submission, name)
        try:
            data = path.read_bytes()
        except OSError as exc:
            collection_errors.append(f"{name}: {type(exc).__name__}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    (output / "patch.diff").write_text("".join(patch), encoding="utf-8")
    grade = external_grade(protocol["task"], submission, python)
    # Policy/tool launch errors are harness failures, not evidence that the
    # model failed the coding task. Keep them in accounting with actual usage.
    blocked = "blocked by policy" in (output / "stderr.txt").read_text(encoding="utf-8")
    status = (
        "timed_out"
        if timed_out
        else "harness_error"
        if blocked or process.returncode or not completed or collection_errors
        else "invalid_scope"
        if violations
        else grade["status"]
    )
    result = {
        "trial_version": 1,
        "protocol_sha256": sha256(protocol_path.read_bytes()),
        "task_id": protocol["task"]["id"],
        "partition": protocol["task"]["partition"],
        "condition": condition,
        "status": status,
        "model_requested": protocol["model"],
        "provider_model_snapshot": None,
        "reasoning_effort_requested": protocol["reasoning_effort"],
        "usage": usage,
        "elapsed_seconds": elapsed,
        "latency_claim_eligible": False,
        "process_exit_code": process.returncode,
        "commands_completed": len(commands),
        "changed_source_files": changes,
        "scope_violations": violations,
        "evidence_collection_errors": collection_errors,
        "grader": grade,
        "limitations": protocol["limitations"],
        "evidence_sha256": {
            path.relative_to(output).as_posix(): sha256(path.read_bytes())
            for path in sorted(output.rglob("*"))
            if path.is_file()
        },
    }
    write_json(output / "result.json", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--condition", choices=("default", "karpathy", "improved"), required=True)
    parser.add_argument("--output", type=Path, required=True, help="New attempt directory; never overwritten")
    parser.add_argument("--cli", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run(args.protocol, args.condition, args.output, args.cli, args.python)
    print(
        json.dumps(
            {
                "status": result["status"],
                "usage": result["usage"],
                "checks_passed": result["grader"].get("checks_passed"),
                "checks_total": result["grader"].get("checks_total"),
            }
        )
    )
    return 0 if result["status"] == "task_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())

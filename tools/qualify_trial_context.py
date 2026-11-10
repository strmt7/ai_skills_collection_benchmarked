"""Qualify private prompt and command contexts without invoking a model."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from _lib_b.io_utils import write_json
from _trial_context import TrialContext, create_context, options, temporary_home
from _trial_rpc import command_control
from _trial_transcript import strict_json
from _windows_appcontainer import checked_path
from _windows_trial_process import run_owned

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    "tools/qualify_trial_context.py",
    "tools/_trial_context.py",
    "tools/_trial_provider.py",
    "tools/_trial_rpc.py",
    "tools/_windows_trial_process.py",
    "tools/_windows_appcontainer.py",
    "tools/_windows_owned_python.py",
    "tools/_trial_transcript.py",
    *(
        f"tools/_lib_b/{name}.py"
        for name in ("__init__", "determinism", "frontmatter_utils", "hashing", "io_utils", "logging_utils")
    ),
)
MARKERS = {"global": "CONTEXT_GLOBAL_680ef4", "project": "CONTEXT_PROJECT_e34321", "skill": "CONTEXT_SKILL_a4d36c"}
INTERVENTION = "CONTEXT_INTERVENTION_26f9a1"
PROMPT = "Inspect the owned fixture without changing its files."
EXPECTED_COMMAND = {
    "outside_read": False,
    "outside_write": False,
    "workspace_write": True,
    "loopback_connect": False,
    "child_completed": True,
    "parent_canary": None,
    "controller_home": None,
}
PROBE_PATH = "qualification_probe.py"
EVIDENCE_NAMES = (
    PROBE_PATH,
    "source-binding.json",
    "specification.json",
    *(
        prefix + "/" + name
        for prefix in ("positive-prompt", "baseline-prompt", "intervention-prompt", "host-command")
        for name in ("stdout.native", "stderr.native", "process.json")
    ),
    "native-command/stdout.native",
    "native-command/stderr.native",
    "native-command/requests.json",
    "native-command/observations.json",
    "native-command/probe-after.native",
)
PROBE = """import json,os,socket,subprocess,sys
from pathlib import Path
p=Path(os.environ['CONTROL_SEALED']);r={}
try:p.read_bytes();r['outside_read']=True
except OSError:r['outside_read']=False
try:p.write_text('changed');r['outside_write']=True
except OSError:r['outside_write']=False
p=Path('owned-write');p.write_text('owned');r['workspace_write']=p.read_text()=='owned'
with socket.socket() as s:
 s.settimeout(1);r['loopback_connect']=s.connect_ex(('127.0.0.1',int(os.environ['CONTROL_PORT'])))==0
p=subprocess.run([sys.executable,'-I','-B','-S','-c',"print('child control')"],capture_output=True,timeout=3)
r['child_completed']=p.returncode==0 and b'child control' in p.stdout
r['parent_canary']=os.environ.get('PARENT_CANARY')
r['controller_home']=os.environ.get('CODEX_HOME')
print(json.dumps(r))
"""


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def sources() -> dict[str, str]:
    return {name: digest(ROOT / name) for name in SOURCES}


def capture(context: TrialContext, command: list[str], output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=False)
    (output / "stdin.native").write_bytes(b"")
    with (
        (output / "stdin.native").open("rb") as stdin,
        (output / "stdout.native").open("xb") as stdout,
        (output / "stderr.native").open("xb") as stderr,
    ):
        process = run_owned(
            command,
            cwd=context.workspace,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=40,
            output_limit=8 * 1024**2,
            memory_limit=2 * 1024**3,
            process_limit=32,
            environment=context.controller_environment,
        )
    write_json(output / "process.json", process)
    return process


def semantic_messages(items: list[dict[str, Any]], codex_home: Path) -> list[dict[str, Any]]:
    """Normalize declared metadata and the private native arg0 shim directory.

    Raw input remains retained. Semantic equality does not mean identical wire
    bytes or identical tokenization of the randomized runtime paths. Match the
    exact XML-escaped root without decoding or rewriting other prompt text.
    """
    rendered_root = escape(str(codex_home / "tmp/arg0-windows"), {"'": "&apos;", '"': "&quot;"})
    shim = re.compile(r"<path>" + re.escape(rendered_root) + r"[\\/]codex-arg0[A-Za-z0-9]{6}</path>")
    result = []
    for item in items:
        row = {key: value for key, value in item.items() if key != "id"}
        metadata = row.get("internal_chat_message_metadata_passthrough")
        if isinstance(metadata, dict):
            row["internal_chat_message_metadata_passthrough"] = {
                k: v for k, v in metadata.items() if k != "create_time"
            }
        if row.get("role") == "user" and isinstance(row.get("content"), list):
            row["content"] = [
                {**entry, "text": shim.sub("<path>CODEX_ARG0_EPHEMERAL</path>", entry["text"])}
                if isinstance(entry, dict)
                and isinstance(entry.get("text"), str)
                and entry["text"].startswith("<environment_context>")
                else entry
                for entry in row["content"]
            ]
        result.append(row)
    return result


def exited_cleanly(process: Any) -> bool:
    return (
        isinstance(process, dict)
        and type(process.get("exit_code")) is int
        and process["exit_code"] == 0
        and process.get("termination_reason") is None
        and type(process.get("job_active_processes_after_cleanup")) is int
        and process["job_active_processes_after_cleanup"] == 0
    )


def probe_command(python: Path, shell: Path, script: Path) -> list[str]:
    """Exercise the ordinary Windows shell route with explicit, quoted argv."""

    def quote(path: Path) -> str:
        return "'" + str(path).replace("'", "''") + "'"

    return [
        str(shell),
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "& " + quote(python) + " -I -B -S " + quote(script),
    ]


def observed_checks(output: Path) -> dict[str, bool]:
    """Recompute every context result from the selected native observations."""
    binding = strict_json((output / "source-binding.json").read_text(encoding="utf-8"))
    if not isinstance(binding, dict) or any(
        not isinstance(binding.get(key), str) or not binding[key]
        for key in ("python", "shell", "workspace", "codex_home")
    ):
        raise ValueError("Invalid control source binding")
    checks, inputs = {}, {}
    for condition in ("positive", "baseline", "intervention"):
        destination = output / (condition + "-prompt")
        process = strict_json((destination / "process.json").read_text(encoding="utf-8"))
        raw = (destination / "stdout.native").read_text(encoding="utf-8")
        items = strict_json(raw)
        if not isinstance(items, list) or not items or any(not isinstance(item, dict) for item in items):
            raise ValueError("The prompt inspector returned invalid messages")
        inputs[condition] = items
        checks[condition + "_process"] = exited_cleanly(process)
        checks[condition + "_markers"] = all(
            (marker in raw) == (condition == "positive") for marker in MARKERS.values()
        ) and ((INTERVENTION in raw) == (condition == "intervention"))
    home = Path(binding["codex_home"])
    a, b = semantic_messages(inputs["baseline"], home), semantic_messages(inputs["intervention"], home)
    checks["matched_prefix"] = a[:-1] == b[:-1]
    checks["declared_intervention_only"] = (
        b[-1].get("content") == [{"type": "input_text", "text": PROMPT + "\n" + INTERVENTION}]
        and a[-1].get("content") == [{"type": "input_text", "text": PROMPT}]
        and {k: v for k, v in a[-1].items() if k != "content"} == {k: v for k, v in b[-1].items() if k != "content"}
    )
    host = strict_json((output / "host-command/stdout.native").read_text(encoding="utf-8"))
    if not isinstance(host, dict):
        raise ValueError("Invalid native host countercontrol")
    checks["host_countercontrol"] = (
        exited_cleanly(strict_json((output / "host-command/process.json").read_text(encoding="utf-8")))
        and all(
            host.get(name) is True
            for name in ("outside_read", "outside_write", "workspace_write", "loopback_connect", "child_completed")
        )
        and host.get("parent_canary") == "owned parent-only marker"
    )
    result = strict_json((output / "native-command/observations.json").read_text(encoding="utf-8"))
    if not isinstance(result, dict) or not isinstance(result.get("command"), dict):
        raise ValueError("Missing native command response")
    response = result.get("command", {}).get("result", {})
    if not isinstance(response, dict):
        raise ValueError("Invalid native command result")
    command_succeeded = type(response.get("exitCode")) is int and response["exitCode"] == 0
    actual = strict_json(response.get("stdout", "null")) if command_succeeded else None
    checks["native_command"] = (
        command_succeeded
        and isinstance(actual, dict)
        and set(actual) == set(EXPECTED_COMMAND)
        and all(type(actual[key]) is type(value) and actual[key] == value for key, value in EXPECTED_COMMAND.items())
    )
    checks["native_cleanup"] = result.get("worker_stopped") is True and exited_cleanly(result.get("process"))
    requests = strict_json((output / "native-command/requests.json").read_text(encoding="utf-8"))
    if not isinstance(requests, list) or any(not isinstance(row, dict) for row in requests):
        raise ValueError("Invalid native control request inventory")
    checks["model_free_methods"] = [row.get("method") for row in requests] == [
        "initialize",
        "initialized",
        "command/exec",
    ]
    checks["declared_probe"] = all(
        (output / name).read_bytes() == PROBE.encode("utf-8")
        for name in (PROBE_PATH, "native-command/probe-after.native")
    )
    checks["declared_command_only"] = (
        len(requests) == 3
        and requests[2].get("params", {}).get("command")
        == probe_command(Path(binding["python"]), Path(binding["shell"]), Path(binding["workspace"]) / PROBE_PATH)
        and requests[2]["params"].get("cwd") == binding["workspace"]
        and requests[2]["params"].get("timeoutMs") == 5000
        and requests[2]["params"].get("outputBytesCap") == 16384
    )
    return checks


def qualify(cli: Path, python: Path, roots: tuple[Path, ...], output: Path) -> dict[str, Any]:
    if sys.platform != "win32":
        raise ValueError("Native context controls require Windows")
    cli, python, output = (checked_path(path) for path in (cli, python, output))
    shell = checked_path(Path(os.environ["SYSTEMROOT"]) / "System32/WindowsPowerShell/v1.0/powershell.exe")
    if not shell.is_file():
        raise ValueError("The declared native Windows PowerShell executable is unavailable")
    if not output.is_relative_to(ROOT / ".venv") or output == ROOT / ".venv":
        raise ValueError("Use a dedicated private output directory inside this clone's .venv")
    initial = sources()
    output.mkdir(parents=True, exist_ok=False)
    fixtures = Path(tempfile.mkdtemp(prefix="skills-context-fixtures-"))
    positive_workspace, workspace = fixtures / "positive/task", fixtures / "clean/task"
    positive_home, home = temporary_home(), temporary_home()
    write_json(
        output / "source-binding.json",
        {
            "source_sha256": initial,
            "cli": str(cli),
            "python": str(python),
            "shell": str(shell),
            "workspace": str(workspace),
            "codex_home": str(home / "profile"),
        },
    )
    specification = {
        "scope": "Native context controls only; not complete trial qualification or agent efficacy",
        "model_inferences": 0,
        "positive_markers": MARKERS,
        "positive_permission_profile": ":workspace",
        "tested_permission_profile": "trial",
        "baseline_forbids_markers": True,
        "intervention_suffix": "\n" + INTERVENTION,
        "comparison_nuisances": ["message IDs", "creation times", "private native arg0 shim directory"],
        "expected_command": EXPECTED_COMMAND,
        "execution_path": "native Windows PowerShell -> admitted Python",
        "direct_non_system_image_launch_qualified": False,
    }
    write_json(output / "specification.json", specification)
    for path in (positive_workspace, workspace):
        path.mkdir(parents=True)
        (path / "AGENTS.md").write_text(MARKERS["project"] + "\n", encoding="utf-8")
        subprocess.run(["git", "-c", "core.longpaths=true", "init", "--quiet", str(path)], check=True, timeout=10)
    positive = create_context(positive_home, positive_workspace, cli, python, roots)
    context = create_context(home, workspace, cli, python, roots)
    (output / PROBE_PATH).write_bytes(PROBE.encode("utf-8"))
    probe = workspace / PROBE_PATH
    probe.write_bytes(PROBE.encode("utf-8"))
    profile = Path(positive.controller_environment["CODEX_HOME"])
    (profile / "AGENTS.md").write_text(MARKERS["global"] + "\n", encoding="utf-8")
    skill = profile / "skills/control/SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "---\nname: control\ndescription: " + MARKERS["skill"] + "\n---\nOwned control.\n", encoding="utf-8"
    )
    for condition in ("positive", "baseline", "intervention"):
        current = positive if condition == "positive" else context
        arguments = options(current, "gpt-6.1-sol", "high")
        if condition == "positive":
            arguments.extend(
                [
                    "-c",
                    'default_permissions=":workspace"',
                    "-c",
                    "project_doc_max_bytes=65536",
                    "-c",
                    "skills.include_instructions=true",
                ]
            )
        prompt = PROMPT + ("\n" + INTERVENTION if condition == "intervention" else "")
        destination = output / (condition + "-prompt")
        capture(current, [str(cli), *arguments, "debug", "prompt-input", prompt], destination)
    sealed = output / "sealed.txt"
    sealed.write_text("owned control", encoding="utf-8")
    context.controller_environment["PARENT_CANARY"] = "owned parent-only marker"
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(2)
        listener.settimeout(3)
        wire = {"CONTROL_SEALED": str(sealed), "CONTROL_PORT": str(listener.getsockname()[1])}
        host_environment = dict(context.controller_environment)
        context.controller_environment.update(wire)
        capture(context, [str(python), "-I", "-B", "-S", str(probe)], output / "host-command")
        connection, _ = listener.accept()
        connection.close()
        context.controller_environment.clear()
        context.controller_environment.update(host_environment)
        sealed.write_text("owned control", encoding="utf-8")
        command_control(
            context, probe_command(python, shell, probe), output / "native-command", environment_overrides=wire
        )
    with checked_path(probe).open("rb") as source:
        (output / "native-command/probe-after.native").write_bytes(source.read(len(PROBE.encode("utf-8")) + 1))
    checks = observed_checks(output)
    checks["sources_unchanged"] = sources() == initial
    record = {
        "schema_version": 1,
        "checks": checks,
        "ok": all(checks.values()),
        "complete_trial_boundary_qualified": False,
        "model_inferences": 0,
        "source_sha256": initial,
        "cli": str(cli),
        "cli_sha256": digest(cli),
        "python": str(python),
        "python_sha256": digest(python),
        "shell": str(shell),
        "shell_sha256": digest(shell),
        "workspace": str(workspace),
        "codex_home": context.controller_environment["CODEX_HOME"],
        "evidence_sha256": {name: digest(output / name) for name in EVIDENCE_NAMES},
    }
    write_json(output / "qualification.json", record)
    return record


def check(output: Path) -> dict[str, Any]:
    record = strict_json((output / "qualification.json").read_text(encoding="utf-8"))
    if not isinstance(record, dict) or any(
        not isinstance(record.get(key), dict) for key in ("checks", "evidence_sha256")
    ):
        raise ValueError("Invalid qualification record")
    errors = []
    if (
        type(record.get("schema_version")) is not int
        or record.get("schema_version") != 1
        or record.get("complete_trial_boundary_qualified") is not False
        or type(record.get("model_inferences")) is not int
        or record.get("model_inferences") != 0
    ):
        errors.append("invalid context-only qualification scope")
    if record.get("source_sha256") != sources():
        errors.append("context qualification sources changed")
    binding = strict_json((output / "source-binding.json").read_text(encoding="utf-8"))
    if not isinstance(binding, dict) or any(
        binding.get(key) != record.get(key)
        for key in ("source_sha256", "cli", "python", "shell", "workspace", "codex_home")
    ):
        errors.append("native source binding disagrees with its qualification record")
    for key in ("cli", "python", "shell"):
        if digest(checked_path(Path(record[key]))) != record[key + "_sha256"]:
            errors.append(key + " executable changed")
    if set(record["evidence_sha256"]) != set(EVIDENCE_NAMES):
        errors.append("native evidence set is incomplete or unexpected")
    for name, expected in record["evidence_sha256"].items():
        target = checked_path(output / name)
        if not target.is_relative_to(output.resolve()) or digest(target) != expected:
            errors.append("native evidence changed: " + name)
    recomputed = observed_checks(output)
    recomputed["sources_unchanged"] = record.get("source_sha256") == sources()
    if (
        record.get("ok") is not True
        or record.get("checks") != recomputed
        or any(type(value) is not bool for value in record.get("checks", {}).values())
        or not all(value is True for value in recomputed.values())
    ):
        errors.append("one or more native context controls failed")
    return {"ok": not errors, "errors": errors, "complete_trial_boundary_qualified": False, "model_inferences": 0}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cli", type=Path)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--readable-root", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.check:
            record = check(checked_path(args.output))
        else:
            if args.cli is None or args.python is None:
                raise ValueError("Explicit CLI and Python executables are required")
            record = qualify(args.cli, args.python, tuple(args.readable_root), args.output)
        print(
            json.dumps(
                record
                if args.json
                else {key: record[key] for key in ("ok", "complete_trial_boundary_qualified", "model_inferences")}
            )
        )
        return 0 if record["ok"] else 1
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)], "complete_trial_boundary_qualified": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

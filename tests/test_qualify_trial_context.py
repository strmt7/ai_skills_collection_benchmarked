from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import pytest
import qualify_trial_context as controls


@pytest.fixture
def observation(tmp_path):
    cli, python, shell = tmp_path / "cli.exe", tmp_path / "python.exe", tmp_path / "powershell.exe"
    cli.write_bytes(b"CLI identity fixture")
    python.write_bytes(b"Python identity fixture")
    shell.write_bytes(b"Shell identity fixture")
    git = tmp_path / "git.exe"
    git.write_bytes(b"Git identity fixture")
    workspace, home = tmp_path / "runtime-workspace", tmp_path / "private/profile"

    def put(name, value):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    process = {"exit_code": 0, "termination_reason": None, "job_active_processes_after_cleanup": 0}
    for condition in ("positive", "baseline", "intervention"):
        text = "common coding context"
        if condition == "positive":
            text += " ".join(controls.MARKERS.values())
        prompt = controls.PROMPT + ("\n" + controls.INTERVENTION if condition == "intervention" else "")
        put(
            condition + "-prompt/stdout.native",
            [
                {"role": "developer", "content": [{"type": "input_text", "text": text}]},
                {"role": "user", "content": [{"type": "input_text", "text": prompt}]},
            ],
        )
        put(condition + "-prompt/process.json", process)
    put(
        "host-command/stdout.native",
        {
            **{
                key: True
                for key in ("outside_read", "outside_write", "workspace_write", "loopback_connect", "child_completed")
            },
            "parent_canary": "owned parent-only marker",
        },
    )
    put("host-command/process.json", process)
    put(
        "native-command/observations.json",
        {
            "command": {"result": {"exitCode": 0, "stdout": json.dumps(controls.EXPECTED_COMMAND)}},
            "process": process,
            "worker_stopped": True,
        },
    )
    put(
        "native-command/requests.json",
        [
            {"method": "initialize"},
            {"method": "initialized"},
            {
                "method": "command/exec",
                "params": {
                    "command": controls.probe_command(python, shell, workspace / controls.PROBE_PATH),
                    "cwd": str(workspace),
                    "timeoutMs": 5000,
                    "outputBytesCap": 16384,
                },
            },
        ],
    )
    put(
        "source-binding.json",
        {
            "source_sha256": controls.sources(),
            "cli": str(cli),
            "python": str(python),
            "shell": str(shell),
            "git": str(git),
            "git_sha256": controls.digest(git),
            "workspace": str(workspace),
            "codex_home": str(home),
        },
    )
    probe = tmp_path / controls.PROBE_PATH
    probe.parent.mkdir(parents=True, exist_ok=True)
    probe.write_bytes(controls.PROBE.encode("utf-8"))
    (tmp_path / "native-command/probe-after.native").write_bytes(controls.PROBE.encode("utf-8"))
    for name in controls.EVIDENCE_NAMES:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(b"owned fixture")
    for condition in ("positive", "baseline"):
        put("git-" + condition + "/process.json", process)
        put("git-" + condition + "/command.json", {"command": [str(git), "init", "--quiet"]})
    checks = controls.observed_checks(tmp_path)
    checks["sources_unchanged"] = True
    record = {
        "schema_version": 1,
        "complete_trial_boundary_qualified": False,
        "model_inferences": 0,
        "ok": True,
        "checks": checks,
        "source_sha256": controls.sources(),
        "cli": str(cli),
        "cli_sha256": controls.digest(cli),
        "python": str(python),
        "python_sha256": controls.digest(python),
        "shell": str(shell),
        "shell_sha256": controls.digest(shell),
        "git": str(git),
        "git_sha256": controls.digest(git),
        "workspace": str(workspace),
        "codex_home": str(home),
        "evidence_sha256": {name: controls.digest(tmp_path / name) for name in controls.EVIDENCE_NAMES},
    }
    put("qualification.json", record)
    return tmp_path, record, put


def test_complete_context_record_is_verified_without_claiming_full_trials(observation):
    path, _, _ = observation
    result = controls.check(path)
    assert result["ok"] is True
    assert result["complete_trial_boundary_qualified"] is False and result["model_inferences"] == 0


@pytest.mark.parametrize(
    "change", ["missing_check", "numeric_check", "missing_evidence", "scope", "source", "bytes", "shell", "git"]
)
def test_incomplete_or_changed_records_never_pass(observation, change):
    path, record, put = observation
    if change == "missing_check":
        record["checks"].pop("native_command")
    elif change == "numeric_check":
        record["checks"]["native_command"] = 1
    elif change == "missing_evidence":
        record["evidence_sha256"].pop("native-command/requests.json")
    elif change == "scope":
        record["complete_trial_boundary_qualified"] = True
    elif change == "source":
        record["source_sha256"]["tools/_trial_context.py"] = "a" * 64
    elif change == "shell":
        (path / "powershell.exe").write_bytes(b"changed shell executable")
    elif change == "git":
        (path / "git.exe").write_bytes(b"changed Git executable")
    else:
        (path / "baseline-prompt/stderr.native").write_bytes(b"changed")
    put("qualification.json", record)
    assert controls.check(path)["ok"] is False


def test_rehashed_bare_git_command_cannot_prove_explicit_runtime_use(observation):
    path, record, put = observation
    relative = "git-positive/command.json"
    put(relative, {"command": ["git", "init", "--quiet"]})
    record["evidence_sha256"][relative] = controls.digest(path / relative)
    put("qualification.json", record)
    assert controls.check(path)["ok"] is False


def test_fixture_git_ignores_inherited_configuration_and_uses_owned_bounds(tmp_path, monkeypatch):
    git = tmp_path / "admitted/git.exe"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    for key in controls.SYSTEM_VARIABLES:
        monkeypatch.setenv(key, os.environ.get(key, "owned-system-value"))
    monkeypatch.setenv("GIT_DIR", "unrelated repository")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    observed: dict[str, Any] = {}

    def run(command, **kwargs):
        observed.update(command=command, options=kwargs)
        return {"exit_code": 0, "termination_reason": None, "job_active_processes_after_cleanup": 0}

    monkeypatch.setattr(controls, "run_owned", run)
    output = tmp_path / "owned-evidence"
    controls.initialize_fixture(git, workspace, output)
    assert observed["command"][0] == str(git)
    options = observed["options"]
    assert options["cwd"] == workspace and options["timeout"] == 10
    assert options["memory_limit"] == 512 * 1024**2 and options["process_limit"] == 8
    environment = options["environment"]
    assert "GIT_DIR" not in environment and "GIT_CONFIG_COUNT" not in environment
    assert environment["GIT_CONFIG_NOSYSTEM"] == "1" and environment["GIT_TERMINAL_PROMPT"] == "0"
    assert Path(environment["GIT_CONFIG_GLOBAL"]).read_bytes() == b""
    assert (output / "process.json").is_file()


@pytest.mark.parametrize("change", ["command", "cwd"])
def test_consistently_rehashed_wrong_command_still_fails_behavioral_recheck(observation, change):
    path, record, put = observation
    requests = json.loads((path / "native-command/requests.json").read_bytes())
    if change == "command":
        requests[2]["params"]["command"] = ["owned-python", "-c", "print('fabricated control')"]
    else:
        requests[2]["params"]["cwd"] = str(path / "other-workspace")
    put("native-command/requests.json", requests)
    record["evidence_sha256"]["native-command/requests.json"] = controls.digest(path / "native-command/requests.json")
    put("qualification.json", record)
    assert controls.check(path)["ok"] is False


@pytest.mark.parametrize("stdout", ["", "MXC launch failed", json.dumps(controls.EXPECTED_COMMAND)])
def test_failed_native_command_is_not_parsed_as_a_success(observation, stdout):
    path, _, put = observation
    result = json.loads((path / "native-command/observations.json").read_bytes())
    result["command"]["result"] = {"exitCode": 1, "stdout": stdout, "stderr": "native launch failed"}
    put("native-command/observations.json", result)
    assert controls.observed_checks(path)["native_command"] is False


@pytest.mark.parametrize("name", [controls.PROBE_PATH, "native-command/probe-after.native"])
def test_consistently_rehashed_changed_probe_still_fails_behavioral_recheck(observation, name):
    path, record, put = observation
    probe = path / name
    probe.write_bytes(b"print('different probe')\n")
    record["evidence_sha256"][name] = controls.digest(probe)
    put("qualification.json", record)
    assert controls.check(path)["ok"] is False


@pytest.mark.parametrize(("path_name", "xml_escaped"), [("private", False), ("private ' Ω &", True)])
def test_nuisance_comparison_preserves_meaning_and_other_runtime_paths(tmp_path, path_name, xml_escaped):
    home = tmp_path / path_name

    def item(suffix):
        rendered = str(home / ("tmp/arg0-windows/codex-arg0" + suffix))
        if xml_escaped:
            rendered = escape(rendered, {"'": "&apos;", '"': "&quot;"})
        return [
            {
                "id": suffix,
                "role": "user",
                "internal_chat_message_metadata_passthrough": {
                    "create_time": suffix,
                    "meaning": "preserved",
                },
                "content": [
                    {
                        "type": "input_text",
                        "text": "<environment_context><path>"
                        + rendered
                        + "</path>deny outside writes</environment_context>",
                    }
                ],
            }
        ]

    a, b = item("ABC123"), item("DEF456")
    assert controls.semantic_messages(a, home) == controls.semantic_messages(b, home)
    changed = copy.deepcopy(b)
    changed[0]["content"][0]["text"] = changed[0]["content"][0]["text"].replace("deny", "allow")
    assert controls.semantic_messages(a, home) != controls.semantic_messages(changed, home)
    assert controls.semantic_messages(a, tmp_path / "another-home") != controls.semantic_messages(
        b, tmp_path / "another-home"
    )
    assert a[0]["id"] == "ABC123"

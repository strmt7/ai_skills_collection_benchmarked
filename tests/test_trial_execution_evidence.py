"""Reject consistently rehashed launch, process and scratch-inventory substitutions."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

import pytest
import summarize_agent_trials as summary
from _trial_catalog import PIN_SOURCE, LocalCatalog
from _trial_collection_contract import collector_command
from _trial_collection_policy import default_collection_policy
from _trial_context import TrialContext, command
from _trial_execution_evidence import _context as read_context
from _trial_execution_evidence import context_record, verify_launch, verify_process
from _trial_signin import NativeSignin


@pytest.fixture
def frozen():
    workspace = PureWindowsPath("C:/owned/subject")
    profile = workspace / ".trial-profile"
    environment = {
        "SYSTEMROOT": "C:\\Windows",
        "WINDIR": "C:\\Windows",
        "COMSPEC": "C:\\Windows\\System32\\cmd.exe",
        "SYSTEMDRIVE": "C:",
        "PATHEXT": ".COM;.EXE;.BAT;.CMD",
        "PATH": "C:\\tools\\python;C:\\tools\\cli\\bin;C:\\Windows\\System32;C:\\Windows\\System32\\WindowsPowerShell\\v1.0",
        **{
            key: str(profile / relative)
            for key, relative in {
                "HOME": "profile",
                "USERPROFILE": "profile",
                "APPDATA": "profile/AppData/Roaming",
                "LOCALAPPDATA": "profile/AppData/Local",
                "TEMP": "temporary",
                "TMP": "temporary",
            }.items()
        },
        "PYTHONNOUSERSITE": "1",
        "PYTHONUTF8": "1",
    }
    context = TrialContext(
        Path("C:\\owned\\controller"),
        Path(str(workspace)),
        Path("C:\\tools\\cli\\bin\\codex.exe"),
        Path("C:\\tools\\python\\python.exe"),
        (Path("C:\\tools\\cli"), Path("C:\\tools\\python")),
        {"AUTHENTICATION_CANARY": "not published"},
        environment,
    )
    protocol: dict[str, Any] = {
        "collection_policy": default_collection_policy(),
        "protocol_version": 4,
        "model": "gpt-6.1-sol",
        "reasoning_effort": "high",
        "execution_source_sha256": {"tools/fixture.py": "a" * 64},
        "task": {
            "id": "owned-fixture",
            "partition": "development",
            "source_commit": "b" * 40,
            "grader": "tools/grade.py",
            "files": ["code.py"],
            "allowed_changes": [],
            "brief": "Independent fixture.",
        },
        "input_sha256": {"code.py": hashlib.sha256(b"owned fixture").hexdigest()},
        "prompt_template": "<TASK_BRIEF> Use <PYTHON_RUNTIME>.",
        "conditions": {"default": {"skills": []}},
        "planned_order": [{"repetition": 1, "conditions": ["default"]}],
        "time_limit_seconds": 10,
        "limitations": [],
    }
    launch = {
        "command": command(context, protocol["model"], protocol["reasoning_effort"]),
        "context": context_record(context),
        "execution_source_sha256": protocol["execution_source_sha256"].copy(),
        "protocol_sha256": "d" * 64,
    }
    process = {
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "job_active_processes_after_cleanup": 0,
        "exit_code": 0,
        "termination_reason": None,
        "output_bytes": 100,
        "output_limit_bytes": 8 * 1024**2,
        "wall_time_limit_seconds": 10.0,
        "job_memory_limit_bytes": 2 * 1024**3,
        "active_process_limit": 32,
        "explicit_environment": True,
    }
    return protocol, launch, process


def test_launch_context_excludes_controller_authentication(frozen):
    protocol, launch, _ = frozen
    assert "AUTHENTICATION_CANARY" not in json.dumps(launch)
    verify_launch(launch, protocol)


def test_archived_local_metadata_round_trips_but_cannot_rewrite_a_version_four_protocol(frozen):
    protocol, launch, _ = frozen
    raw = json.dumps(
        {
            "models": [
                {
                    "slug": protocol["model"],
                    "context_window": 65536,
                    "base_instructions": "Owned frozen native instructions.",
                }
            ]
        }
    )
    local = LocalCatalog(r"C:\owned\local-model.json", hashlib.sha256(raw.encode()).hexdigest(), raw)
    context = replace(read_context(launch["context"]), local_catalog=local)
    launch["context"] = context_record(context)
    assert read_context(launch["context"]).local_catalog == local
    protocol["provider"] = {"authentication": "none", "base_url": "http://127.0.0.1:8123/v1"}
    launch["command"] = command(context, protocol["model"], protocol["reasoning_effort"], provider=protocol["provider"])
    with pytest.raises(ValueError, match="Version-4"):
        verify_launch(launch, protocol)


def native_launch(frozen, native_catalog_pin):
    protocol, launch, process = frozen
    home = Path("C:\\native-signin")
    admission = {
        **process,
        "output_limit_bytes": 65536,
        "wall_time_limit_seconds": 20,
        "job_memory_limit_bytes": 1024**3,
        "active_process_limit": 8,
        "write_io_limit_bytes": 1024**2,
        "job_write_io_bytes": 24,
        "write_io_observation_error": None,
        "write_io_enforcement": "polled_job_transfer_accounting",
        "hard_storage_quota": False,
    }
    context = replace(
        read_context(launch["context"]),
        controller_environment={"CODEX_HOME": str(home)},
        signin=NativeSignin(home, "file", admission),
        native_catalog=native_catalog_pin(Path(launch["context"]["cli"])),
    )
    assert context.native_catalog is not None
    protocol["execution_source_sha256"][PIN_SOURCE] = context.native_catalog.source_sha256
    launch["execution_source_sha256"] = protocol["execution_source_sha256"].copy()
    protocol["provider"] = {"authentication": "codex_signin", "codex_home": str(home), "credential_store": "file"}
    launch["context"] = context_record(context)
    launch["command"] = command(context, protocol["model"], protocol["reasoning_effort"], provider=protocol["provider"])
    return protocol, launch


def test_native_signin_context_and_denied_store_round_trip_without_credentials(frozen, native_catalog_pin):
    protocol, launch = native_launch(frozen, native_catalog_pin)
    verify_launch(launch, protocol)
    assert launch["context"]["signin"]["mode"] == "chatgpt"
    assert "access_token" not in json.dumps(launch)


@pytest.mark.parametrize("mutation", ["mode", "unfinished", "boolean", "overlap", "mismatched", "missing", "extra"])
def test_unproven_or_substituted_native_signin_binding_is_rejected(frozen, mutation, native_catalog_pin):
    protocol, launch = native_launch(frozen, native_catalog_pin)
    record = launch["context"]["signin"]
    if mutation == "mode":
        record["mode"] = "apikey"
    elif mutation == "unfinished":
        record["status_process"]["job_active_processes_after_cleanup"] = 1
    elif mutation == "boolean":
        record["status_process"]["exit_code"] = False
    elif mutation == "overlap":
        record["home"] = launch["context"]["workspace"]
    elif mutation == "mismatched":
        protocol["provider"]["codex_home"] = "C:\\another-signin"
    elif mutation == "missing":
        del launch["context"]["signin"]
    else:
        record["credential"] = "private-canary"
    with pytest.raises(ValueError):
        verify_launch(launch, protocol)


@pytest.mark.parametrize("fault", ["missing", "extra", "malformed", "pin-substitution", "command-override"])
def test_native_catalog_evidence_is_bound_to_the_frozen_pin_and_entire_command(frozen, native_catalog_pin, fault):
    protocol, launch = native_launch(frozen, native_catalog_pin)
    record = launch["context"]["native_catalog"]
    if fault == "missing":
        del launch["context"]["native_catalog"]
    elif fault == "extra":
        record["unexpected"] = True
    elif fault == "malformed":
        record["pin"] = "{}"
    elif fault == "pin-substitution":
        pin = json.loads(record["pin"])
        pin["resources"]["models.json"]["sha256"] = "b" * 64
        record["pin"] = json.dumps(pin)
    else:
        index = launch["command"].index("exec")
        launch["command"][index:index] = ["-c", 'model_catalog_json="C:/other/models.json"']
    with pytest.raises(ValueError):
        verify_launch(launch, protocol)


def test_launch_must_match_the_frozen_provider_without_recording_its_credential(frozen):
    from _trial_provider import provider_options

    protocol, launch, _ = frozen
    protocol["provider"] = {"base_url": "https://model.example.test/v1", "credential_env": "TRIAL_TOKEN"}
    with pytest.raises(ValueError, match="recorded launch differs"):
        verify_launch(launch, protocol)
    offset = launch["command"].index("exec")
    launch["command"][offset:offset] = provider_options(protocol["provider"])
    verify_launch(launch, protocol)
    protocol["provider"]["base_url"] = "https://different.example.test/v1"
    with pytest.raises(ValueError, match="recorded launch differs"):
        verify_launch(launch, protocol)


@pytest.mark.parametrize(
    "argument", ["--sandbox", "--dangerously-bypass-approvals-and-sandbox", "--enable=memories", "--model=other"]
)
def test_appending_a_command_override_is_rejected(frozen, argument):
    protocol, launch, _ = frozen
    launch["command"].append(argument)
    with pytest.raises(ValueError, match="recorded launch differs"):
        verify_launch(launch, protocol)


@pytest.mark.parametrize("change", ["controller", "profile", "path", "root", "source", "model", "missing"])
def test_context_and_source_substitutions_are_rejected(frozen, change):
    protocol, launch, _ = frozen
    record = launch["context"]
    if change == "controller":
        record["tool_environment"]["CODEX_HOME"] = record["home"]
    elif change == "profile":
        record["tool_environment"]["HOME"] = record["home"]
    elif change == "path":
        record["tool_environment"]["PATH"] += ";C:\\unrelated"
    elif change == "root":
        record["readable_roots"].append("C:\\owned")
    elif change == "source":
        launch["execution_source_sha256"] = {"tools/different.py": "e" * 64}
    elif change == "model":
        protocol["model"] = "different-model"
    else:
        del record["workspace"]
    with pytest.raises(ValueError):
        verify_launch(launch, protocol)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("kill_on_close", False),
        ("assigned_before_resume", False),
        ("job_active_processes_after_cleanup", 1),
        ("job_active_processes_after_cleanup", False),
        ("active_process_limit", 128),
        ("job_memory_limit_bytes", 8 * 1024**3),
        ("output_limit_bytes", 100),
        ("wall_time_limit_seconds", 11.0),
        ("explicit_environment", False),
        ("output_bytes", 99),
        ("exit_code", True),
        ("termination_reason", "timeout"),
    ],
)
def test_inconsistent_process_records_cannot_support_a_score(frozen, key, value):
    _, _, process = frozen
    process[key] = value
    with pytest.raises(ValueError):
        verify_process(process, {"status": "task_passed", "process_exit_code": 0}, 100, 10)


def test_success_and_real_output_limit_failure_remain_distinct(frozen):
    _, _, process = frozen
    verify_process(process, {"status": "task_passed", "process_exit_code": 0}, 100, 10)
    process.update(termination_reason="output_limit", exit_code=125, output_bytes=8 * 1024**2 + 1)
    result = {"status": "harness_error", "process_exit_code": 125}
    verify_process(process, result, 8 * 1024**2 + 1, 10)
    result["status"] = "task_failed"
    with pytest.raises(ValueError, match="interrupted"):
        verify_process(process, result, 8 * 1024**2 + 1, 10)


def test_launch_error_does_not_require_fabricated_cleanup_or_exit(frozen):
    process = {"termination_reason": "launch_error", "exit_code": None, "error_type": "OSError"}
    verify_process(process, {"status": "harness_error", "process_exit_code": None}, 0, 10)
    with pytest.raises(ValueError, match="launch failure"):
        verify_process(process, {"status": "task_failed", "process_exit_code": None}, 0, 10)


@pytest.fixture
def captured(tmp_path, frozen):
    protocol, launch, process = frozen
    prompt = b"Independent fixture. Use C:\\tools\\python\\python.exe."
    grade = {
        "status": "task_passed",
        "checks": [
            {"case": "independent-case", "passed": True, "observation_directory": "case-" + "a" * 32 + "/observations"}
        ],
        "checks_passed": 1,
        "checks_total": 1,
    }
    events = [{"type": "turn.completed", "usage": {"input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 5}}]
    transcript = (json.dumps(events[0]) + "\n").encode()
    process["output_bytes"] = len(transcript)
    contents = {
        "attempt.json": json.dumps(
            {
                "attempt_version": 1,
                "protocol_sha256": "d" * 64,
                "condition": "default",
                "phase": "finished",
                "stage": "result",
                "model_launch_attempted": True,
                "workspace": launch["context"]["workspace"],
            }
        ).encode(),
        "launch.json": json.dumps(launch).encode(),
        "process.json": json.dumps(process).encode(),
        "input.native": prompt,
        "prompt.txt": prompt,
        "transcript.jsonl": transcript,
        "stderr.txt": b"",
        "patch.diff": b"",
        "submission/code.py": b"owned fixture",
        "grading.driver.stdout.native": json.dumps(grade).encode(),
        "grading.driver.stderr.native": b"",
        "grading/result.json": json.dumps(grade).encode(),
        "grading/checks.json": json.dumps(grade["checks"]).encode(),
        **{f"grading/case-{'a' * 32}/observations/{stream}.native": b"" for stream in ("stdout", "stderr")},
    }
    for name, data in contents.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    result: dict[str, Any] = {
        "protocol_sha256": "d" * 64,
        "task_id": protocol["task"]["id"],
        "partition": "development",
        "condition": "default",
        "model_requested": protocol["model"],
        "reasoning_effort_requested": "high",
        "status": "task_passed",
        "attempt_phase": "finished",
        "process_exit_code": 0,
        "provider_model_snapshot": None,
        "latency_claim_eligible": False,
        "commands_completed": 0,
        "scope_violations": [],
        "changed_source_files": [],
        "evidence_collection_errors": [],
        "usage": events[0]["usage"],
        "grader": grade,
        "evidence_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()},
    }
    refresh_collection(tmp_path, protocol, result)
    return tmp_path, protocol, result


def refresh_collection(directory, protocol, result, changes=None):
    """Create synthetic native records for consistency tests, never execution evidence."""
    files = {
        name.removeprefix("submission/"): (directory / name).read_bytes()
        for name in result["evidence_sha256"]
        if name.startswith("submission/")
    }
    directories = sorted(
        {parent.as_posix() for name in files for parent in PurePosixPath(name).parents if parent.as_posix() != "."}
    )
    policy = protocol["collection_policy"]
    manifest = {
        "collection_version": 1,
        "status": "collected",
        "policy": policy,
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for name, data in files.items()
        },
        "directories": directories,
        "directory_count": len(directories),
        "excluded": [],
        "file_count": len(files),
        "total_bytes": sum(map(len, files.values())),
        "post_inventory_matches": True,
        "atomic_snapshot": False,
        "precondition": "All subject execution must be stopped before capture.",
    }
    raw = json.dumps(manifest).encode()
    workspace = PureWindowsPath("C:/owned/subject")
    source, python = PureWindowsPath("C:/controller/source"), PureWindowsPath("C:/tools/python/python.exe")
    output, observations = (
        PureWindowsPath("C:/owned/attempt/submission"),
        PureWindowsPath("C:/owned/attempt/collection"),
    )
    launch = {
        "source_root": str(source),
        "python": str(python),
        "workspace": str(workspace),
        "output": str(output),
        "observations": str(observations),
        "policy": policy,
        "command": collector_command(source, python, workspace, output, policy),
    }
    process = {
        "exit_code": 0,
        "termination_reason": None,
        "job_active_processes_after_cleanup": 0,
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "explicit_environment": True,
        "job_memory_limit_bytes": 1024**3,
        "active_process_limit": 4,
        "output_limit_bytes": 64 * 1024**2,
        "wall_time_limit_seconds": float(policy["timeout_seconds"]),
        "output_bytes": len(raw),
    }
    records = {
        "collection/launch.json": json.dumps(launch).encode(),
        "collection/process.json": json.dumps(process).encode(),
        "collection/input.native": b"",
        "collection/stdout.native": raw,
        "collection/stderr.native": b"",
        "collection/result.json": raw,
        "workspace-changes.json": json.dumps(
            {"complete": True, "changes": changes or [], "diagnostic_patch": None}
        ).encode(),
    }
    for name, content in records.items():
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    for name in set(result["evidence_sha256"]) | records.keys():
        result["evidence_sha256"][name] = summary.sha256(directory / name)
    (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")


def modified(path, before, after):
    return {
        "path": path,
        "object": "file",
        "kind": "modified",
        "before_sha256": hashlib.sha256(before).hexdigest(),
        "after_sha256": hashlib.sha256(after).hexdigest(),
    }


def test_modern_result_requires_native_transport_and_execution_records(captured):
    directory, protocol, result = captured
    verified, runtime = summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))
    assert verified == result
    assert runtime == ("recorded", b"C:\\tools\\python\\python.exe")


@pytest.mark.parametrize("change", ["concealed-edit", "invented-edit"])
def test_collected_digests_must_support_reported_changes_and_scope(captured, change):
    directory, protocol, result = captured
    if change == "concealed-edit":
        path = directory / "submission/code.py"
        path.write_bytes(b"modified protected input")
        result["evidence_sha256"]["submission/code.py"] = summary.sha256(path)
    else:
        result["changed_source_files"] = ["code.py"]
    refresh_collection(directory, protocol, result)
    with pytest.raises(ValueError, match="source changes or scope"):
        summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))


@pytest.mark.parametrize("allowed", [True, False])
def test_real_edits_preserve_the_declared_task_scope(captured, allowed):
    directory, protocol, result = captured
    path = directory / "submission/code.py"
    path.write_bytes(b"modified input")
    result["evidence_sha256"]["submission/code.py"] = summary.sha256(path)
    result["changed_source_files"] = ["code.py"]
    if allowed:
        protocol["task"]["allowed_changes"] = ["code.py"]
    else:
        result["status"] = "invalid_scope"
        result["scope_violations"] = ["protected source input changed: code.py"]
    refresh_collection(directory, protocol, result, [modified("code.py", b"owned fixture", b"modified input")])
    verified, _ = summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))
    assert verified["status"] == ("task_passed" if allowed else "invalid_scope")


@pytest.mark.parametrize("case", ["allowed", "protected", "concealed"])
def test_scaffold_changes_use_the_same_scope_contract_in_reporting(captured, case):
    directory, protocol, result = captured
    protocol["workspace_scaffold"] = {"helper.txt": "original\n"}
    path = directory / "submission/helper.txt"
    path.write_bytes(b"modified\n")
    result["evidence_sha256"]["submission/helper.txt"] = summary.sha256(path)
    if case == "allowed":
        protocol["task"]["allowed_changes"] = ["helper.txt"]
    elif case == "protected":
        result["status"] = "invalid_scope"
        result["scope_violations"] = ["protected scaffold changed: helper.txt"]
    refresh_collection(directory, protocol, result, [modified("helper.txt", b"original\n", b"modified\n")])
    if case == "concealed":
        with pytest.raises(ValueError, match="source changes or scope"):
            summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))
    else:
        verified, _ = summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))
        assert verified["status"] == ("task_passed" if case == "allowed" else "invalid_scope")


def test_undeclared_scratch_path_is_rejected_before_any_evidence_read(captured, monkeypatch):
    directory, protocol, result = captured
    result["evidence_sha256"]["grading/scratch/private.txt"] = "e" * 64
    (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")
    monkeypatch.setattr(summary, "evidence_bytes", lambda *args: pytest.fail("unexpected evidence read"))
    with pytest.raises(ValueError, match="inventory"):
        summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))


@pytest.mark.parametrize(
    ("field", "value"), [("provider_model_snapshot", "invented-snapshot"), ("latency_claim_eligible", True)]
)
def test_unqualified_identity_and_latency_claims_are_rejected(captured, field, value):
    directory, protocol, result = captured
    result[field] = value
    (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError):
        summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))


@pytest.mark.parametrize("name", ["launch.json", "process.json", "input.native", "grading.driver.stdout.native"])
def test_rehashing_changed_native_records_cannot_make_them_consistent(captured, name):
    directory, protocol, result = captured
    path = directory / name
    if name == "input.native":
        path.write_bytes(b"substituted task")
    else:
        value = json.loads(path.read_bytes())
        if name == "launch.json":
            value["command"].append("--enable=memories")
        elif name == "process.json":
            value["job_active_processes_after_cleanup"] = 2
        else:
            value["checks_passed"] = 0
        path.write_text(json.dumps(value), encoding="utf-8")
    result["evidence_sha256"][name] = summary.sha256(path)
    (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError):
        summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))


@pytest.mark.parametrize(
    "change", ["override", "workspace", "layout", "runtime", "unc", "cleanup", "memory", "bool", "size"]
)
def test_collector_receipt_substitutions_are_rejected_even_after_rehashing(captured, change):
    directory, protocol, result = captured
    summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))
    name = (
        "collection/launch.json"
        if change in {"override", "workspace", "layout", "runtime", "unc"}
        else "collection/process.json"
    )
    value = json.loads((directory / name).read_bytes())
    if change == "override":
        value["command"].append("--unexpected")
    elif change == "workspace":
        value["workspace"] = "C:\\other\\subject"
    elif change == "layout":
        value["output"] = "C:\\owned\\subject\\submission"
    elif change == "runtime":
        value["python"] = "C:\\owned\\subject\\python.exe"
    elif change == "unc":
        value["source_root"] = "\\\\server\\share\\source"
    elif change == "cleanup":
        value["job_active_processes_after_cleanup"] = 1
    elif change == "memory":
        value["job_memory_limit_bytes"] *= 2
    elif change == "bool":
        value["exit_code"] = False
    else:
        manifest = json.loads((directory / "collection/result.json").read_bytes())
        manifest["files"]["code.py"]["bytes"] += 1
        manifest["total_bytes"] += 1
        raw = json.dumps(manifest).encode()
        for relative in ("collection/result.json", "collection/stdout.native"):
            (directory / relative).write_bytes(raw)
            result["evidence_sha256"][relative] = summary.sha256(directory / relative)
        value["output_bytes"] = len(raw)
    (directory / name).write_text(json.dumps(value), encoding="utf-8")
    result["evidence_sha256"][name] = summary.sha256(directory / name)
    (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError):
        summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))


@pytest.mark.parametrize("permitted", [True, False])
def test_deleted_sources_remain_verifiable_and_scope_checked(captured, permitted):
    directory, protocol, result = captured
    (directory / "submission/code.py").unlink()
    del result["evidence_sha256"]["submission/code.py"]
    result["changed_source_files"] = ["code.py"]
    if permitted:
        protocol["task"]["allowed_changes"] = ["code.py"]
    else:
        result["status"] = "invalid_scope"
        result["scope_violations"] = ["protected source input changed: code.py"]
    refresh_collection(
        directory,
        protocol,
        result,
        [
            {
                "path": "code.py",
                "object": "file",
                "kind": "deleted",
                "before_sha256": protocol["input_sha256"]["code.py"],
                "after_sha256": None,
            }
        ],
    )
    verified, _ = summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))
    assert verified["changed_source_files"] == ["code.py"]


def test_failed_collection_is_unscored_and_keeps_native_failure_observations(captured):
    directory, protocol, result = captured
    original_grade = result["grader"]
    grading_hashes = {
        name: digest
        for name, digest in result["evidence_sha256"].items()
        if name.startswith(("grading/", "grading.driver."))
    }
    result.update(
        status="harness_error",
        evidence_collection_errors=["source collection did not complete"],
        grader={"status": "harness_error", "error": "Collection failed"},
    )
    for name in list(result["evidence_sha256"]):
        if name.startswith(("submission/", "grading/", "grading.driver.")):
            del result["evidence_sha256"][name]
    records = {
        "collection/result.json": {
            "collection_version": 1,
            "status": "collection_error",
            "error_type": "incomplete_process",
        },
        "collection/process.json": {
            "exit_code": 124,
            "termination_reason": "timeout",
            "job_active_processes_after_cleanup": 0,
        },
        "workspace-changes.json": {"complete": False, "changes": [], "diagnostic_patch": None},
    }
    for name, value in records.items():
        (directory / name).write_text(json.dumps(value), encoding="utf-8")
        result["evidence_sha256"][name] = summary.sha256(directory / name)
    (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")
    verified, _ = summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))
    assert verified["status"] == "harness_error"
    result["status"] = "task_passed"
    result["grader"] = original_grade
    result["evidence_sha256"].update(grading_hashes)
    (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError, match="incomplete source collection cannot be scored"):
        summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))


def test_collector_cannot_accept_substituted_native_input(captured):
    directory, protocol, result = captured
    path = directory / "collection/input.native"
    path.write_bytes(b"unexpected input")
    result["evidence_sha256"]["collection/input.native"] = summary.sha256(path)
    (directory / "result.json").write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError, match="empty native input"):
        summary.verify_result(directory, protocol, "d" * 64, "default", frozenset({"independent-case"}))

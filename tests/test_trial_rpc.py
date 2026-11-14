from __future__ import annotations

import json

import _trial_rpc as rpc
import pytest
from _trial_context import TrialContext


@pytest.fixture
def context(tmp_path):
    workspace, home, runtime = (tmp_path / name for name in ("workspace", "home", "runtime"))
    for path in (workspace, home, runtime):
        path.mkdir()
    return TrialContext(home, workspace, runtime / "codex.exe", runtime / "python.exe", (runtime,), {}, {})


def test_native_control_negotiates_before_sending_one_model_free_command(tmp_path, monkeypatch, context):
    observed = []

    def server(invocation, **streams):
        assert "app-server" in invocation and "--stdio" in invocation
        assert streams["memory_limit"] == 2 * 1024**3 and streams["process_limit"] == 32
        request = json.loads(streams["stdin"].readline())
        observed.append(request["method"])
        streams["stdout"].write(b'{"id":1,"result":{"initialized":true}}\n')
        for _ in range(2):
            request = json.loads(streams["stdin"].readline())
            observed.append(request["method"])
        assert request["params"]["command"] == ["fixture", "argument"]
        assert request["params"]["timeoutMs"] == 5000
        streams["stdout"].write(b'{"id":2,"result":{"exitCode":0,"stdout":"control","stderr":""}}\n')
        return {"exit_code": 0, "job_active_processes_after_cleanup": 0}

    monkeypatch.setattr(rpc, "run_owned", server)
    output = tmp_path / "observations"
    result = rpc.command_control(context, ["fixture", "argument"], output)
    assert observed == ["initialize", "initialized", "command/exec"]
    assert result["worker_stopped"] is True
    assert result["command"]["result"]["stdout"] == "control"
    assert "process_error" not in result and "client_error" not in result
    assert json.loads((output / "requests.json").read_bytes())[2]["method"] == "command/exec"


def test_protocol_initialization_failure_preserves_the_error_and_stops(tmp_path, monkeypatch, context):
    def server(invocation, **streams):
        assert json.loads(streams["stdin"].readline())["method"] == "initialize"
        streams["stdout"].write(b'{"id":1,"error":{"code":-32600,"message":"owned rejection"}}\n')
        assert streams["stdin"].read() == b""
        return {"exit_code": 0, "job_active_processes_after_cleanup": 0}

    monkeypatch.setattr(rpc, "run_owned", server)
    result = rpc.command_control(context, ["fixture"], tmp_path / "observations")
    assert result["worker_stopped"] is True and "command" not in result
    assert result["initialize"]["error"]["message"] == "owned rejection"
    assert result["client_error"]["type"] == "ValueError"


def test_protocol_process_failure_is_retained_without_fabricating_a_response(tmp_path, monkeypatch, context):
    def unavailable(*args, **kwargs):
        raise OSError("owned launch error")

    monkeypatch.setattr(rpc, "run_owned", unavailable)
    result = rpc.command_control(context, ["fixture"], tmp_path / "observations")
    assert result["worker_stopped"] is True
    assert result["process_error"]["type"] == "OSError"
    assert "command" not in result and "process" not in result


def test_subject_cannot_write_control_observations(tmp_path, monkeypatch, context):
    monkeypatch.setattr(rpc, "run_owned", lambda *args, **kwargs: pytest.fail("unexpected process"))
    output = context.workspace / "observations"
    with pytest.raises(ValueError, match="must be separate"):
        rpc.command_control(context, ["fixture"], output)
    assert not output.exists()


def test_longer_native_control_preserves_nested_deadlines(tmp_path, monkeypatch, context):
    def server(invocation, **streams):
        assert streams["timeout"] == 155
        streams["stdin"].readline()
        streams["stdout"].write(b'{"id":1,"result":{}}\n')
        streams["stdin"].readline()
        request = json.loads(streams["stdin"].readline())
        assert request["params"]["timeoutMs"] == 120000
        assert request["params"]["outputBytesCap"] == 262144
        streams["stdout"].write(b'{"id":2,"result":{"exitCode":0}}\n')
        return {"exit_code": 0, "job_active_processes_after_cleanup": 0}

    monkeypatch.setattr(rpc, "run_owned", server)
    result = rpc.command_control(
        context, ["fixture"], tmp_path / "observations", timeout_seconds=120, output_bytes=262144
    )
    assert result["worker_stopped"] is True
    assert result["command"]["result"]["exitCode"] == 0


@pytest.mark.parametrize(
    "limits",
    [{"timeout_seconds": value} for value in (0, 301, True, 1.5)]
    + [{"output_bytes": value} for value in (0, 1024**2 + 1, True, 1.5)],
)
def test_invalid_control_budgets_do_not_create_output_or_process(tmp_path, monkeypatch, context, limits):
    monkeypatch.setattr(rpc, "run_owned", lambda *args, **kwargs: pytest.fail("unexpected process"))
    output = tmp_path / "observations"
    with pytest.raises(ValueError):
        rpc.command_control(context, ["fixture"], output, **limits)
    assert not output.exists()


def test_cancellation_joins_the_control_worker_and_retains_its_stop_evidence(tmp_path, monkeypatch, context):
    def server(invocation, **streams):
        streams["stdin"].read()
        return {"exit_code": 0, "job_active_processes_after_cleanup": 0}

    def cancel(*args):
        raise KeyboardInterrupt

    monkeypatch.setattr(rpc, "run_owned", server)
    monkeypatch.setattr(rpc, "response", cancel)
    output = tmp_path / "observations"
    with pytest.raises(KeyboardInterrupt):
        rpc.command_control(context, ["fixture"], output)
    result = json.loads((output / "observations.json").read_bytes())
    assert result["worker_stopped"] is True
    assert result["process"]["job_active_processes_after_cleanup"] == 0
    assert "command" not in result

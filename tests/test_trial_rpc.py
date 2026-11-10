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

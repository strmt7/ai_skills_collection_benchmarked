from __future__ import annotations

import json
from typing import Any

import check_native_trial_readiness as command
import pytest


@pytest.fixture
def admitted(tmp_path, monkeypatch):
    root, auth, runtime = (tmp_path / name for name in ("repo", "auth", "runtime"))
    for path in (root, auth, runtime):
        path.mkdir()
    source = {"tools/controller.py": "a" * 64}
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}", encoding="utf-8")
    provider = {"authentication": "codex_signin", "codex_home": str(auth), "credential_store": "file"}
    plan = {
        "provider": provider,
        "model": "gpt-6.1-sol",
        "reasoning_effort": "high",
        "execution_source_sha256": source.copy(),
    }
    state: dict[str, Any] = {"archives": [], "probes": [], "source": source, "status": "eligible"}
    monkeypatch.setattr(command, "ROOT", root)
    monkeypatch.setattr(command, "execution_sources", lambda: state["source"])
    monkeypatch.setattr(
        command,
        "load_plan",
        lambda _: {
            "plan": plan,
            "runtime": {"roots": (runtime,), "cli": runtime / "codex.exe", "python": runtime / "python.exe"},
            "plan_sha256": "b" * 64,
        },
    )
    monkeypatch.setattr(command, "archive_sources", lambda *values: state["archives"].append(values))
    monkeypatch.setattr(command, "create_context", lambda *values: values)

    def probe(*values):
        state["probes"].append(values)
        if state.get("drift"):
            state["source"] = {"tools/controller.py": "c" * 64}
        return {
            "status": state["status"],
            "eligible": state["status"] == "eligible",
            "model_inferences": 0,
            "raw_account_metadata_retained": False,
            "whole_model_trial_boundary_qualified": False,
        }

    monkeypatch.setattr(command, "probe", probe)
    return root, auth, runtime, plan_path, plan, state


@pytest.mark.parametrize("status", ["eligible", "ineligible", "harness_error"])
def test_readiness_publishes_its_metadata_outcome_without_running_a_trial(admitted, status):
    root, _, _, plan_path, _, state = admitted
    state["status"] = status
    output = root / ".venv/readiness"
    report = command.run(plan_path, output)
    assert report["status"] == status
    assert json.loads((output / "readiness.json").read_bytes()) == report
    assert report["model_inferences"] == 0 and report["whole_model_trial_boundary_qualified"] is False
    assert state["probes"][0][2:] == ("gpt-6.1-sol", "high")
    assert len(state["archives"]) == 1


@pytest.mark.parametrize("target", ["auth", "runtime", "tracked", "existing", "ancestor"])
def test_readiness_cannot_modify_authentication_runtime_or_tracked_source(admitted, target):
    root, auth, runtime, plan_path, _, state = admitted
    output = {
        "auth": auth / "new-evidence",
        "runtime": runtime / "new-evidence",
        "tracked": root / "artifacts/new-evidence",
        "existing": root,
        "ancestor": root.parent,
    }[target]
    marker = auth / "owner-data"
    marker.write_text("keep", encoding="utf-8")
    existed = output.exists()
    with pytest.raises(ValueError):
        command.run(plan_path, output)
    assert output.exists() is existed and marker.read_text(encoding="utf-8") == "keep"
    assert not state["archives"] and not state["probes"]


def test_readiness_refuses_a_legacy_provider_before_creating_evidence(admitted):
    root, _, _, plan_path, plan, state = admitted
    plan["provider"] = {"base_url": "http://127.0.0.1:1234", "authentication": "none"}
    output = root / ".venv/readiness"
    with pytest.raises(ValueError, match="official CLI"):
        command.run(plan_path, output)
    assert not output.exists() and not state["probes"]


def test_source_drift_invalidates_an_otherwise_eligible_metadata_check(admitted):
    root, _, _, plan_path, _, state = admitted
    state["drift"] = True
    report = command.run(plan_path, root / ".venv/readiness")
    assert report["status"] == "harness_error" and report["eligible"] is False
    assert report["error_type"] == "SourceChanged"


def test_cli_reports_setup_failure_without_native_error_text(monkeypatch, capsys):
    def fail(*_):
        raise ValueError("private-error-payload-canary")

    monkeypatch.setattr(command, "run", fail)
    assert command.main(["--plan", "input.json", "--output", "new-output"]) == 2
    value = capsys.readouterr().out
    assert "private-error-payload-canary" not in value
    assert json.loads(value)["error_type"] == "ValueError"


@pytest.mark.parametrize(("status", "exit_code"), [("eligible", 0), ("ineligible", 1), ("harness_error", 2)])
def test_cli_exit_distinguishes_metadata_rejection_from_harness_failure(monkeypatch, capsys, status, exit_code):
    monkeypatch.setattr(
        command, "run", lambda *_: {"status": status, "eligible": status == "eligible", "model_inferences": 0}
    )
    assert command.main(["--plan", "input.json", "--output", "new-output"]) == exit_code
    assert json.loads(capsys.readouterr().out)["status"] == status

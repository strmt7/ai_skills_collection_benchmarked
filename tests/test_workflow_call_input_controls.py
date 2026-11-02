"""Check that workflow-type controls do not accept invalid evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "benchmarks/component-controls/workflow-call-inputs/controls.py"
SPEC = importlib.util.spec_from_file_location("workflow_call_input_controls", PATH)
assert SPEC is not None and SPEC.loader is not None
controls = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(controls)


def fake_success(args: list[str], **_: object) -> subprocess.CompletedProcess[str]:
    output = "1.7.12\n" if "-version" in args else ""
    return subprocess.CompletedProcess(args, 0, output, "")


def test_control_rejects_linter_that_accepts_everything(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(controls.subprocess, "run", fake_success)
    with pytest.raises(ValueError, match="workflow_call-choice: unexpected actionlint result"):
        controls.run(tmp_path / "fake-actionlint", tmp_path)


def test_changed_source_template_is_not_admitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    stale = tmp_path / "template.yml"
    stale.write_bytes(controls.TEMPLATE.read_bytes() + b"\n# changed\n")
    monkeypatch.setattr(controls, "TEMPLATE", stale)
    monkeypatch.setattr(controls.subprocess, "run", fake_success)
    with pytest.raises(ValueError, match="source template changed"):
        controls.run(tmp_path / "fake-actionlint", tmp_path)


def test_missing_maintained_example_is_not_admitted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    skill = tmp_path / "SKILL.md"
    skill.write_text("No YAML example.\n", encoding="utf-8")
    monkeypatch.setattr(controls, "SKILL", skill)
    monkeypatch.setattr(controls.subprocess, "run", fake_success)
    with pytest.raises(ValueError, match="one maintained YAML workflow example"):
        controls.run(tmp_path / "fake-actionlint", tmp_path)


def test_recorded_platform_controls_bind_inputs_and_expected_outcomes() -> None:
    record = json.loads((ROOT / "artifacts/research/2026-11-02/workflow-call-inputs/qualification.json").read_bytes())
    assert record["overlay_sha256"] == hashlib.sha256(controls.SKILL.read_bytes()).hexdigest()
    assert record["controls_sha256"] == hashlib.sha256(PATH.read_bytes()).hexdigest()
    assert (
        record["source_template_sha256"]
        == hashlib.sha256(controls.TEMPLATE.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    )
    windows = record["runs"]["windows"]["outcomes"]
    linux = record["runs"]["linux"]["outcomes"]
    assert windows == linux
    assert len(windows) == 16
    assert {case["case"] for case in windows if case["exit_code"] != 0} == {
        "workflow_call-choice",
        "workflow_call-environment",
        "workflow_call-boolean-default-maybe",
        "workflow_call-number-default-abc",
    }

from __future__ import annotations

import importlib.util
import json
from typing import Any

import grade_agent_submission as driver
import pytest
from helpers import ROOT


def grader() -> Any:
    path = ROOT / "benchmarks/agent-effectiveness/graders/artifact_validator.py"
    spec = importlib.util.spec_from_file_location("independent_grader", path)
    assert spec is not None and spec.loader is not None
    module: Any = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_sandbox_configuration_never_imports_submitted_code(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "tools").mkdir(parents=True)
    marker = tmp_path / "controller-marker"
    marker.write_text("unchanged", encoding="utf-8")
    (workspace / "tools/check_benchmark_artifact.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('changed')\n", encoding="utf-8"
    )
    direct = grader().evaluate(workspace)
    via_driver = driver.evaluate(driver.GRADER, workspace)
    assert direct["status"] == via_driver["status"] == "harness_error"
    assert marker.read_text(encoding="utf-8") == "unchanged"


def test_explicit_configuration_routes_to_confined_grader(tmp_path, monkeypatch):
    observed = []

    def confined(workspace, fixture, runtime_home, dependency_home, output, revision):
        observed.append((workspace, fixture, runtime_home, dependency_home, output, revision))
        return {"status": "task_passed", "checks_passed": 17, "checks_total": 17, "agent_performance_claim": False}

    monkeypatch.setattr(driver.confined, "grade", confined)
    workspace, fixture, runtime_home, dependency_home, output = (
        tmp_path / x for x in ("submission", "fixture", "runtime", "dependencies", "output")
    )
    revision = "a" * 40
    result = grader().evaluate(
        workspace,
        fixture=fixture,
        revision=revision,
        runtime_home=runtime_home,
        dependency_home=dependency_home,
        output=output,
    )
    assert result["status"] == "task_passed"
    assert observed == [(workspace, fixture, runtime_home, dependency_home, output, revision)]


def test_unrecognized_grader_is_never_imported(tmp_path):
    grader_path = tmp_path / "untrusted_grader.py"
    marker = tmp_path / "marker"
    grader_path.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported external grader"):
        driver.evaluate(grader_path, tmp_path)
    assert not marker.exists()


def test_grader_sibling_inside_grader_directory_is_not_executed(tmp_path, monkeypatch):
    directory = tmp_path / "benchmarks/agent-effectiveness/graders"
    directory.mkdir(parents=True)
    allowed = directory / "artifact_validator.py"
    sibling = directory / "other.py"
    marker = tmp_path / "marker"
    sibling.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n", encoding="utf-8")
    monkeypatch.setattr(driver, "GRADER", allowed)
    with pytest.raises(ValueError, match="unsupported external grader"):
        driver.evaluate(sibling, tmp_path)
    assert not marker.exists()


def test_confined_runtime_failure_is_reported_as_harness_error(tmp_path, monkeypatch):
    def failed(*args):
        raise RuntimeError("sandbox unavailable")

    monkeypatch.setattr(driver.confined, "grade", failed)
    result = driver.evaluate(
        driver.GRADER,
        tmp_path,
        fixture=tmp_path,
        revision="a" * 40,
        runtime_home=tmp_path,
        dependency_home=tmp_path,
        output=tmp_path / "out",
    )
    assert result["status"] == "harness_error"
    assert "sandbox unavailable" in result["errors"][0]


def test_legacy_cli_fails_closed_without_configuration(tmp_path, capsys):
    assert driver.main([str(driver.GRADER), str(tmp_path)]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == "harness_error"

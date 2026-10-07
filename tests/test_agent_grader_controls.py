from __future__ import annotations

import importlib.util
import json
from typing import Any

import pytest
from helpers import ROOT, load


def grader() -> Any:
    path = ROOT / "benchmarks/agent-effectiveness/graders/artifact_validator.py"
    spec = importlib.util.spec_from_file_location("independent_grader", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_behavioral_grader_accepts_known_correct_implementation():
    result = grader().evaluate(ROOT)
    assert result["status"] == "task_passed"
    assert result["checks_passed"] == result["checks_total"] == 17


@pytest.mark.parametrize("verdict,errors", [("artifact_complete", []), ("artifact_incomplete", ["rejected"])])
def test_behavioral_grader_rejects_always_accept_and_always_reject_implementations(tmp_path, verdict, errors):
    tools = tmp_path / "tools"
    data = tmp_path / "data"
    tools.mkdir()
    data.mkdir()
    (data / "skills_catalog.json").write_text(json.dumps(load("data/skills_catalog.json")[:1]), encoding="utf-8")
    source = (
        "from pathlib import Path\n"
        "SCHEMA_PATH = Path('schema.json')\n"
        "def validate_artifact(path):\n"
        f"    return {{'verdict': {verdict!r}, 'errors': {errors!r}, 'warnings': []}}\n"
    )
    (tools / "check_benchmark_artifact.py").write_text(source, encoding="utf-8")
    result = grader().evaluate(tmp_path)
    assert result["status"] == "task_failed"
    assert 0 < result["checks_passed"] < result["checks_total"]

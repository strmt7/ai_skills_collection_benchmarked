from __future__ import annotations

import copy
import hashlib
import json
import runpy
import shutil
from pathlib import Path

import pytest

METHOD = Path(__file__).resolve().parents[1] / "benchmarks/component-controls/backend"


@pytest.fixture
def evidence(tmp_path):
    namespace = runpy.run_path(str(METHOD / "prepare_backend.py"))
    _, bindings = namespace["modules"]()
    result = json.loads((METHOD / "result.json").read_text(encoding="utf-8"))
    shutil.copytree(METHOD / "native", tmp_path / "native")
    return namespace["validate_result"], copy.deepcopy(result), bindings, tmp_path


def test_backend_evidence_binds_current_source_and_retains_misses(evidence):
    validate, result, bindings, root = evidence
    assert validate(result, bindings, root) == []
    assert sum(result["arms"]["source"]["node"].values()) == 6
    assert sum(result["arms"]["source"]["go"].values()) == 3
    assert result["arms"]["source"]["typecheck_exit_code"] == 2


@pytest.mark.parametrize(
    "field,value", [("agent_performance_claim", True), ("blind_evaluation", True), ("independent_model_trials", 1)]
)
def test_component_evidence_cannot_be_promoted_to_model_efficacy(evidence, field, value):
    validate, result, bindings, root = evidence
    result[field] = value
    assert any("cannot claim" in error for error in validate(result, bindings, root))


def test_backend_source_or_summary_drift_is_rejected(evidence):
    validate, result, bindings, root = evidence
    bindings["benchmarks/component-controls/backend/contract.json"] = "0" * 64
    result["arms"]["source"]["go"]["concatenated-values"] = True
    assert len(validate(result, bindings, root)) >= 2


@pytest.mark.parametrize(
    "change",
    [
        "node-duplicate",
        "node-not-boolean",
        "go-missing",
        "go-duplicate",
        "cleanup",
        "exit",
        "missing-phase",
        "runtime",
        "qualification",
    ],
)
def test_native_evidence_is_checked_even_when_tampered_hash_is_updated(evidence, change):
    validate, result, bindings, root = evidence
    native = root / "native"
    if change.startswith("node-"):
        path = native / "source-node.stdout.log"
        data = json.loads(path.read_text(encoding="utf-8"))
        if change == "node-duplicate":
            data["results"][0] = data["results"][1]
        else:
            data["results"][0]["passed"] = 1
        path.write_text(json.dumps(data), encoding="utf-8")
    elif change.startswith("go-"):
        path = native / "source-go.stdout.log"
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        terminal = next(
            row
            for row in rows
            if row.get("Test", "").startswith("TestJSONBodyContracts/") and row["Action"] in ["pass", "fail"]
        )
        rows = [row for row in rows if row is not terminal] if change == "go-missing" else [*rows, terminal]
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    elif change in ["cleanup", "exit", "missing-phase"]:
        path = native / "processes.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        if change == "cleanup":
            data["source-go"]["active_processes_after_cleanup"] = 1
        elif change == "exit":
            data["source-go"]["exit_code"] = 0
        else:
            data.pop("qualification")
        path.write_text(json.dumps(data), encoding="utf-8")
    elif change == "runtime":
        (native / "go-version.stdout.log").write_text("unqualified runtime", encoding="utf-8")
    else:
        (native / "qualification.stdout.log").write_text('{"passed": false}', encoding="utf-8")
    result["native_sha256"] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in native.iterdir() if path.is_file()
    }
    assert validate(result, bindings, root)


def test_preparation_loads_actual_profile_and_go_reference():
    namespace = runpy.run_path(str(METHOD / "prepare_backend.py"))
    modules, _ = namespace["modules"]()
    assert "return await operation();" in modules["maintained.mts"]
    reference = (METHOD.parents[2] / "included/improved/skills/api-design-current/references/decode-json.go").read_text(
        encoding="utf-8"
    )
    assert modules["maintained-go/decode.go"].replace("package bodycontrols", "package httpjson", 1) == reference

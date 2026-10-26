from __future__ import annotations

import copy
import hashlib
import json
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest

METHOD = Path(__file__).resolve().parents[1] / "benchmarks/component-controls/frontend"


@pytest.fixture
def evidence(tmp_path):
    namespace = runpy.run_path(str(METHOD / "prepare.py"))
    _, bindings = namespace["modules"]()
    result = json.loads((METHOD / "result.json").read_text(encoding="utf-8"))
    shutil.copytree(METHOD / "native", tmp_path / "native")
    shutil.copyfile(METHOD / "contract.json", tmp_path / "contract.json")
    return namespace["validate_result"], copy.deepcopy(result), bindings, tmp_path


def test_recorded_frontend_evidence_is_bound_to_current_sources(evidence):
    validate, result, bindings, root = evidence
    assert validate(result, bindings, root) == []


@pytest.mark.parametrize("change", ["oracle", "summary", "agent_claim", "compiler_exit", "compiler_log"])
def test_stale_or_inflated_frontend_evidence_is_rejected(evidence, change):
    validate, result, bindings, root = evidence
    if change == "oracle":
        bindings["benchmarks/component-controls/frontend/contract.json"] = "0" * 64
    elif change == "summary":
        result["arms"]["locked"]["passed"] = 8
    elif change == "agent_claim":
        result["agent_performance_claim"] = True
    elif change == "compiler_exit":
        result["arms"]["locked"]["typecheck_exit_code"] = 0
    else:
        (root / "native/maintained-compile.log").write_text("unrecorded compiler failure", encoding="utf-8")
    assert validate(result, bindings, root)


def test_repeated_contract_cannot_replace_an_omitted_failure(evidence):
    validate, result, bindings, root = evidence
    path = root / "native/locked-controls.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["results"][0] = data["results"][2]
    path.write_text(json.dumps(data), encoding="utf-8")
    result["arms"]["locked"]["controls_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert any("every declared contract" in error for error in validate(result, bindings, root))


def test_unrecognized_arm_is_rejected_without_reading_outside_evidence(evidence):
    validate, result, bindings, root = evidence
    result["arms"]["../../outside"] = {}
    assert "Exactly three source-bound arms required" in validate(result, bindings, root)


def test_git_transport_preserves_native_npm_capture_bytes(tmp_path):
    repository = METHOD.parents[2]
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    shutil.copyfile(repository / ".gitattributes", tmp_path / ".gitattributes")
    for name in ("package.json", "package-lock.json"):
        relative = "benchmarks/component-controls/frontend/" + name
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        # Reproduce npm's Windows capture even when this test runs on Linux.
        captured = (METHOD / name).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
        target.write_bytes(captured)
        subprocess.run(
            ["git", "-c", "core.longpaths=true", "-c", "core.autocrlf=true", "add", "--", relative],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        committed = subprocess.run(
            ["git", "-c", "core.longpaths=true", "show", ":" + relative],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        ).stdout
        assert committed == captured, f"Git altered the frozen npm capture: {name}"

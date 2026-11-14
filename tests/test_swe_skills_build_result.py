"""Independent admission controls for native build evidence and original metrics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import verify_swe_skills_bench_build_result as verifier


def encoded(value):
    return json.dumps(value).encode()


def fixture(*, code=0, timed_out=False, expected=0, output=b"compiled\n", error=b""):
    inventory = {
        "schema_version": 1,
        "task_id": "independent/build-control",
        "working_dir": "/workspace/project",
        "build_command": "python -m py_compile module.py",
        "expected_exit_code": expected,
        "timeout_seconds": 30,
    }
    native = {
        "schema_version": 1,
        "command": "cd /workspace/project && python -m py_compile module.py",
        "timeout_seconds": 30,
        "exit_code": code,
        "timed_out": timed_out,
        "duration_seconds": 30.25 if timed_out else 0.25,
        "stdout_sha256": hashlib.sha256(output).hexdigest(),
        "stderr_sha256": hashlib.sha256(error).hexdigest(),
        "execution_complete": True,
        "remaining_owned_processes": 0,
    }
    if timed_out:
        verdict = {
            "level": "L1",
            "method": "build_check",
            "status": "failed",
            "score": 0.0,
            "message": "Build timed out",
            "details": {
                "command": inventory["build_command"],
                "timeout": 30,
                "output": output.decode(errors="replace")[:2000],
            },
        }
    elif code == expected:
        verdict = {
            "level": "L1",
            "method": "build_check",
            "status": "passed",
            "score": 1.0,
            "message": "Build succeeded",
            "details": {"command": inventory["build_command"], "exit_code": code, "duration": 0.25},
        }
    else:
        verdict = {
            "level": "L1",
            "method": "build_check",
            "status": "failed",
            "score": 0.0,
            "message": "Build failed",
            "details": {
                "command": inventory["build_command"],
                "exit_code": code,
                "expected_exit_code": expected,
                "error_summary": "independent diagnostic",
                "full_output": (error or output).decode(errors="replace")[:5000],
            },
        }
    return {
        "inventory": encoded(inventory),
        "execution": encoded(native),
        "publisher": encoded(verdict),
        "stdout": output,
        "stderr": error,
    }


@pytest.mark.parametrize(
    ("code", "timed_out", "expected", "score"),
    [(0, False, 0, 1.0), (7, False, 0, 0.0), (7, False, 7, 1.0), (0, True, 0, 0.0), (-9, True, 0, 0.0)],
)
def test_native_outcomes_preserve_publisher_exit_and_timeout_semantics(code, timed_out, expected, score):
    result = verifier.verify_result(**fixture(code=code, timed_out=timed_out, expected=expected))
    assert result["admitted"] and result["score"] == score


def test_error_text_is_not_an_alternative_build_metric():
    result = verifier.verify_result(**fixture(output=b"error: diagnostic-only fixture\n"))
    assert result["admitted"] and result["score"] == 1.0


@pytest.mark.parametrize(
    ("document", "field", "value"),
    [
        ("inventory", "schema_version", True),
        ("inventory", "task_id", ""),
        ("inventory", "working_dir", "/workspace/../foreign"),
        ("inventory", "build_command", "different"),
        ("inventory", "expected_exit_code", True),
        ("inventory", "timeout_seconds", 0),
        ("execution", "schema_version", True),
        ("execution", "command", "different"),
        ("execution", "timeout_seconds", 29),
        ("execution", "exit_code", True),
        ("execution", "timed_out", 0),
        ("execution", "duration_seconds", -1),
        ("execution", "duration_seconds", 10**1000),
        ("execution", "execution_complete", False),
        ("execution", "remaining_owned_processes", 1),
        ("execution", "remaining_owned_processes", False),
        ("execution", "stdout_sha256", "0" * 64),
        ("execution", "stderr_sha256", "0" * 64),
        ("publisher", "method", "unit_test"),
        ("publisher", "level", "L2"),
        ("publisher", "status", "error"),
        ("publisher", "status", "failed"),
        ("publisher", "score", True),
        ("publisher", "score", 0.5),
        ("publisher", "details", []),
    ],
)
def test_inconsistent_or_incomplete_evidence_is_unscored(document, field, value):
    data = fixture()
    record = json.loads(data[document])
    record[field] = value
    data[document] = encoded(record)
    result = verifier.verify_result(**data)
    assert not result["admitted"] and result["status"] == "unscored" and "score" not in result


@pytest.mark.parametrize("kind", ["duration", "exit_code", "timeout", "output"])
def test_original_publisher_details_remain_bound_to_native_evidence(kind):
    data = fixture(timed_out=kind in {"timeout", "output"})
    record = json.loads(data["publisher"])
    record["details"][kind] = "stale"
    data["publisher"] = encoded(record)
    assert not verifier.verify_result(**data)["admitted"]


def test_failure_output_cannot_be_replaced_without_rejection():
    data = fixture(code=1, error=b"fatal: exact native diagnostic\n")
    record = json.loads(data["publisher"])
    record["details"]["full_output"] = "some other failure"
    data["publisher"] = encoded(record)
    assert not verifier.verify_result(**data)["admitted"]


@pytest.mark.parametrize(
    "raw", [b"[]", b"null", b"{", b'{"schema_version":1,"schema_version":1}', b'{"x":NaN}', b"\xff"]
)
def test_invalid_json_is_quarantined(raw):
    data = fixture()
    data["execution"] = raw
    assert not verifier.verify_result(**data)["admitted"]


def test_all_detectable_errors_are_reported_together():
    data = fixture()
    record = json.loads(data["execution"])
    record.update(command="wrong", timeout_seconds=10, remaining_owned_processes=1)
    data["execution"] = encoded(record)
    result = verifier.verify_result(**data)
    assert len(result["errors"]) >= 3


def test_cli_valid_failure_is_admitted_and_bad_evidence_is_not(tmp_path: Path, capsys):
    data = fixture(code=1, error=b"independent failure\n")
    args = []
    for name, raw in data.items():
        path = tmp_path / name
        path.write_bytes(raw)
        args += ["--" + name, str(path)]
    assert verifier.main([*args, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "task_failed"
    (tmp_path / "stdout").write_bytes(b"changed")
    assert verifier.main([*args, "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["status"] == "unscored"


def test_timeout_cannot_precede_its_declared_deadline():
    data = fixture(timed_out=True)
    record = json.loads(data["execution"])
    record["duration_seconds"] = 0.25
    data["execution"] = encoded(record)
    assert not verifier.verify_result(**data)["admitted"]

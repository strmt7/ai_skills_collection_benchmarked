"""Keep publisher observations and independently qualified test outcomes separate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import grade_testeval_submission as grader
import pytest

CASE = "suite::test_observation"
METRICS = b"Syntax Correctness: 1\nExecutable Correctness: 1\nAverage Line Coverage: 1, Average Branch Coverage: 0.8\n"


def write_json(path: Path, payload: dict[str, Any]) -> bytes:
    content = json.dumps(payload, sort_keys=True).encode("utf-8")
    path.write_bytes(content)
    return content


def report(path: Path, content: bytes) -> dict[str, str]:
    path.write_bytes(content)
    return {"file": path.name, "sha256": hashlib.sha256(content).hexdigest()}


def junit(outcome: str = "", *, classname: str = "suite") -> bytes:
    tag = f"<{outcome}/>" if outcome else ""
    return (
        f'<testsuite tests="1" failures="{int(outcome == "failure")}" '
        f'errors="{int(outcome == "error")}" skipped="{int(outcome == "skipped")}">'
        f'<testcase classname="{classname}" name="test_observation">{tag}</testcase></testsuite>'
    ).encode("ascii")


@pytest.fixture
def evidence(tmp_path: Path) -> tuple[bytes, Path, dict[str, Any]]:
    source = {"commit_sha": "a" * 40, "dataset_sha256": "b" * 64, "evaluator_sha256": "c" * 64}
    programs = {"reference": "d" * 64, "constant-result": "e" * 64, "wrong-order": "f" * 64}
    suite = "1" * 64
    plan = write_json(
        tmp_path / "plan.json",
        {
            "schema_version": 1,
            "task_id": 83,
            "publisher": source,
            "programs": programs,
            "subject_suite_sha256": suite,
            "pytest_cases": [CASE],
        },
    )
    capture = {
        "schema_version": 1,
        "plan_sha256": hashlib.sha256(plan).hexdigest(),
        "publisher": {
            "termination": "completed",
            "exit_code": 0,
            "source": source,
            "subject_suite_sha256": suite,
            "stdout": report(tmp_path / "publisher.stdout", METRICS),
        },
        "variants": {
            name: {
                "program_sha256": sha,
                "subject_suite_sha256": suite,
                "termination": "completed",
                "exit_code": int(name == "constant-result"),
                "junit": report(tmp_path / f"{name}.xml", junit("failure" if name == "constant-result" else "")),
            }
            for name, sha in programs.items()
        },
    }
    capture_path = tmp_path / "capture.json"
    write_json(capture_path, capture)
    return plan, capture_path, capture


def test_grade_has_distinct_reach_reference_and_defect_outcomes(
    evidence: tuple[bytes, Path, dict[str, Any]],
) -> None:
    plan, capture, _ = evidence
    result = grader.grade(plan, capture)
    assert result["native_test_eval"] == {
        "status": "measured",
        "exit_code": 0,
        "metrics": {
            "syntax_correctness": 1,
            "executable_correctness": 1,
            "line_coverage": 1,
            "branch_coverage": 0.8,
        },
    }
    assert result["reference"]["status"] == "passed"
    assert result["defects"]["constant-result"]["status"] == "test_failed"
    assert result["defects"]["wrong-order"]["status"] == "passed"
    assert result["sensitivity"] == {"detected": 1, "survived": 1, "inconclusive": 0, "planned": 2}


@pytest.mark.parametrize(
    ("termination", "exit_code", "content", "expected"),
    [
        ("completed", 1, junit("error"), "pytest_case_error"),
        ("completed", 0, junit("skipped"), "pytest_case_skipped"),
        ("completed", 0, junit("failure"), "report_invalid"),
        ("completed", 1, junit("failure", classname="unexpected"), "report_invalid"),
        ("completed", 1, b"<malformed>", "report_invalid"),
        ("completed", 0, None, "report_missing"),
        ("completed", 5, None, "pytest_incomplete"),
        ("fixture_unavailable", None, None, "fixture_unavailable"),
        ("setup_failed", None, None, "setup_failed"),
        ("timed_out", None, junit("failure"), "timed_out"),
        ("interrupted", 2, None, "interrupted"),
    ],
)
def test_inconclusive_cases_are_never_detected_or_silently_dropped(
    evidence: tuple[bytes, Path, dict[str, Any]],
    termination: str,
    exit_code: int | None,
    content: bytes | None,
    expected: str,
) -> None:
    plan, capture_path, capture = evidence
    variant = capture["variants"]["constant-result"]
    variant["termination"], variant["exit_code"] = termination, exit_code
    variant["junit"] = report(capture_path.parent / "new.xml", content) if content is not None else None
    if termination == "fixture_unavailable":
        variant["program_sha256"] = None
    write_json(capture_path, capture)
    result = grader.grade(plan, capture_path)
    assert result["defects"]["constant-result"]["status"] == expected
    assert result["sensitivity"] == {"detected": 0, "survived": 1, "inconclusive": 1, "planned": 2}


def test_reference_failure_keeps_diagnostics_but_prevents_sensitivity_measurement(
    evidence: tuple[bytes, Path, dict[str, Any]],
) -> None:
    plan, capture_path, capture = evidence
    ref = capture["variants"]["reference"]
    ref["junit"] = report(capture_path.parent / "reference.xml", junit("failure"))
    ref["exit_code"] = 1
    write_json(capture_path, capture)
    result = grader.grade(plan, capture_path)
    assert result["reference"]["status"] == "test_failed"
    assert result["native_test_eval"]["status"] == "measured"
    assert result["defects"]["constant-result"]["status"] == "test_failed"
    assert result["sensitivity"] == {"detected": None, "survived": None, "inconclusive": None, "planned": 2}


def test_publisher_failure_preserves_valid_independent_results(
    evidence: tuple[bytes, Path, dict[str, Any]],
) -> None:
    plan, capture_path, capture = evidence
    capture["publisher"]["stdout"] = report(capture_path.parent / "publisher.stdout", b"Unexpected terminal output")
    write_json(capture_path, capture)
    result = grader.grade(plan, capture_path)
    assert result["native_test_eval"] == {"status": "report_invalid", "exit_code": 0, "metrics": None}
    assert result["sensitivity"]["detected"] == 1


@pytest.mark.parametrize("field", ["plan", "suite", "variant", "stream", "source", "program", "exit"])
def test_refuses_evidence_that_has_drifted_from_its_experimental_inputs(
    evidence: tuple[bytes, Path, dict[str, Any]], field: str
) -> None:
    plan, capture_path, capture = evidence
    if field == "plan":
        plan += b" "
    elif field == "suite":
        capture["variants"]["reference"]["subject_suite_sha256"] = "2" * 64
    elif field == "variant":
        del capture["variants"]["constant-result"]
    elif field == "stream":
        (capture_path.parent / "reference.xml").write_bytes(junit("failure"))
    elif field == "source":
        capture["publisher"]["source"]["evaluator_sha256"] = "2" * 64
    elif field == "program":
        capture["variants"]["reference"]["program_sha256"] = "2" * 64
    else:
        capture["variants"]["reference"]["exit_code"] = False
    write_json(capture_path, capture)
    with pytest.raises(ValueError, match="(?i)plan|capture|bytes changed|native exit"):
        grader.grade(plan, capture_path)


def test_check_mode_recomputes_stored_result(
    tmp_path: Path, evidence: tuple[bytes, Path, dict[str, Any]], capsys: pytest.CaptureFixture[str]
) -> None:
    plan, capture, _ = evidence
    expected = tmp_path / "grade.json"
    result = grader.grade(plan, capture)
    argv = ["--plan", str(tmp_path / "plan.json"), "--capture", str(capture)]
    assert grader.main(argv) == 0
    expected.write_text(capsys.readouterr().out, encoding="utf-8")
    argv.extend(["--check", str(expected)])
    assert grader.main(argv) == 0
    assert json.loads(capsys.readouterr().out)["result"] == result
    result["task_id"] = -1
    old = write_json(expected, {"ok": True, "result": result})
    assert grader.main(argv) == 1
    assert "differs" in json.loads(capsys.readouterr().err)["error"]
    assert expected.read_bytes() == old

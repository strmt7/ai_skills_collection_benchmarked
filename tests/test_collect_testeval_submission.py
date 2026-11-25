"""Test prelaunch admission and the collector-to-grader handoff."""

from __future__ import annotations

import json
from pathlib import Path

import collect_testeval_submission as collector
import grade_testeval_submission as grader
import pytest
from _native_benchmark_runtime import DockerCapture

REFERENCE = b"class Solution: pass\n"
DEFECT = b"class Solution: ...\n"
SUITE = b"def test_value(): pass\n"
PUBLISHER = (
    b"Syntax Correctness: 1.0\nExecutable Correctness: 1.0\nAverage Line Coverage: 1.0, Average Branch Coverage: 0.5\n"
)
PASS = (
    b'<testsuite tests="1" errors="0" failures="0" skipped="0">'
    b'<testcase classname="test_subject" name="test_value"/></testsuite>'
)


@pytest.fixture
def pilot(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "ROOT", tmp_path)
    monkeypatch.setattr(collector, "PILOT", tmp_path)
    owned = tmp_path / ".venv"
    owned.mkdir()
    evaluator = b"# evaluator fixture\n"
    publisher = {
        "commit_sha": "1" * 40,
        "dataset_sha256": "2" * 64,
        "evaluator_sha256": collector.sha256(evaluator),
    }
    selection = {
        "partition": "public_development",
        "selected": [{"task_num": 3}],
        "publisher": {**publisher, "commit": publisher["commit_sha"]},
    }
    (tmp_path / "selection.json").write_text(json.dumps(selection), encoding="utf-8")
    assets = {
        "eval_overall.py": evaluator,
        "selected.jsonl": json.dumps({"task_num": 3, "code": REFERENCE.decode()}).encode() + b"\n",
    }
    for name, content in assets.items():
        (tmp_path / name).write_bytes(content)
    profile = {
        "schema_version": 1,
        "selection_sha256": collector.sha256((tmp_path / "selection.json").read_bytes()),
        "image_reference": "fixture",
        "publisher_inputs": {name: collector.sha256(data) for name, data in assets.items()},
        "python_environment": {},
    }
    (tmp_path / "native-profile.json").write_text(json.dumps(profile), encoding="utf-8")
    runtime = tmp_path / "runtime.json"
    runtime.write_text(json.dumps({"image_reference": "fixture"}), encoding="utf-8")
    suite = tmp_path / "suite.py"
    suite.write_bytes(SUITE)
    plan = tmp_path / "plan.json"
    plan.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "task_id": 3,
                "publisher": publisher,
                "programs": {"reference": collector.sha256(REFERENCE), "offset": collector.sha256(DEFECT)},
                "subject_suite_sha256": collector.sha256(SUITE),
                "pytest_cases": ["test_subject::test_value"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(collector, "validate_environment", lambda spec, asset: spec)
    monkeypatch.setattr(collector, "environment_packet", lambda spec, asset: {})
    return plan, suite, tmp_path, tmp_path, runtime, owned / "capture"


def test_missing_defect_remains_in_planned_denominator(pilot, monkeypatch):
    observed = []
    monkeypatch.setattr(collector, "DockerClient", lambda *args: object())

    def execute(client, output, name, payload, dependencies, environment):
        observed.append(name)
        if name == "publisher":
            prediction = json.loads(payload["stage/predictions/subject.jsonl"])
            assert prediction["tests"] == [SUITE.decode()]
            return "completed", 0, PUBLISHER
        assert payload["stage/under_test.py"] == REFERENCE
        assert payload["stage/test_subject.py"] == b"from under_test import Solution\n\n" + SUITE
        return "completed", 0, PASS

    monkeypatch.setattr(collector, "run_stage", execute)
    result = collector.collect(*pilot)
    assert observed == ["publisher", "pytest-reference"]
    assert result["native_test_eval"]["status"] == "measured"
    assert result["reference"]["status"] == "passed"
    assert result["defects"]["offset"]["status"] == "fixture_unavailable"
    assert result["sensitivity"] == {"detected": 0, "survived": 0, "inconclusive": 1, "planned": 1}
    output = pilot[-1]
    assert (
        grader.main(
            [
                "--plan",
                str(output / "plan.json"),
                "--capture",
                str(output / "capture.json"),
                "--check",
                str(output / "grade.json"),
            ]
        )
        == 0
    )
    assert (output / "plan.json").read_bytes() == pilot[0].read_bytes()


@pytest.mark.parametrize("asset", ["suite.py", "offset.py", "eval_overall.py", "selection.json"])
def test_drift_rejected_before_container_creation(pilot, monkeypatch, asset):
    root: Path = pilot[2]
    (root / asset).write_bytes(b"changed\n")

    def unexpected(*args):
        pytest.fail("Unverified assets must be rejected before a Docker client is created")

    monkeypatch.setattr(collector, "DockerClient", unexpected)
    with pytest.raises(ValueError, match="frozen identity"):
        collector.collect(*pilot)
    assert not pilot[-1].exists()


def test_interruption_keeps_the_stage_and_closes_owned_lease(tmp_path, monkeypatch):
    observed = []

    class Lease:
        def __init__(self, *args, **kwargs):
            pass

        def create(self):
            return "fixture"

        def start(self):
            observed.append("started")

        def close(self):
            observed.append("closed")

    def timeout(*args, **kwargs):
        return DockerCapture(
            "fixture",
            tmp_path / "stdout",
            tmp_path / "stderr",
            {"exit_code": 124, "termination_reason": "timeout", "job_active_processes_after_cleanup": 0},
        )

    monkeypatch.setattr(collector, "ContainerLease", Lease)
    monkeypatch.setattr(collector, "stage_inputs", lambda *args, **kwargs: "fixture")
    client = object.__new__(collector.DockerClient)
    monkeypatch.setattr(client, "capture", timeout)
    monkeypatch.setattr(client, "run", lambda *args, **kwargs: b"")
    assert collector.run_stage(
        client,
        tmp_path,
        "pytest-reference",
        {},
        {},
        {
            "setup_timeout_seconds": 30,
            "resources": {},
        },
    ) == ("timed_out", None, b"")
    assert observed == ["started", "closed"]

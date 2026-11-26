"""Test prelaunch admission and the collector-to-grader handoff."""

from __future__ import annotations

import json
from pathlib import Path

import collect_testeval_submission as collector
import grade_testeval_submission as grader
import pytest
from _native_benchmark_runtime import DockerCapture
from _trial_collection_policy import default_collection_policy
from transfer_benchmark_submission import plan_handoff, seal

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


def snapshot(directory: Path, files: dict[str, bytes]) -> bytes:
    directory.mkdir()
    for name, data in files.items():
        (directory / name).write_bytes(data)
    return json.dumps(
        {
            "collection_version": 1,
            "status": "collected",
            "policy": default_collection_policy(),
            "files": {name: {"bytes": len(data), "sha256": grader.sha256(data)} for name, data in files.items()},
            "directories": [],
            "directory_count": 0,
            "excluded": [],
            "file_count": len(files),
            "total_bytes": sum(map(len, files.values())),
            "post_inventory_matches": True,
            "atomic_snapshot": False,
            "precondition": "All subject execution must be stopped before capture.",
        },
        sort_keys=True,
    ).encode("utf-8")


@pytest.fixture
def sealed_submission(pilot):
    plan, _, defects, assets, runtime, output = pilot
    (defects / "offset.py").write_bytes(DEFECT)
    directory = output.with_name("handoff")
    directory.mkdir()
    tests = [SUITE.decode(), "def test_repeat(): pass\n"]
    raw = json.dumps(tests, ensure_ascii=False).encode()
    before = snapshot(directory / "baseline", {"task.txt": b"Exercise current observable behavior"})
    after = snapshot(directory / "captured", {"task.txt": b"Exercise current observable behavior", "tests.json": raw})
    (directory / "baseline.collection.json").write_bytes(before)
    (directory / "submission.collection.json").write_bytes(after)
    receipt = seal(plan_handoff(before, after), directory / "captured", directory / "submission.tar")
    frozen = json.loads(plan.read_bytes())
    task = directory.parent / "task-plan.json"
    task.write_text(
        json.dumps(
            {
                **{key: frozen[key] for key in grader.ASSIGNMENT_FIELDS},
                "schema_version": 2,
                "baseline_manifest_sha256": grader.sha256(before),
            }
        ),
        encoding="utf-8",
    )
    return task, directory, receipt["archive_sha256"], defects, assets, runtime, output, raw, tests


def two_case_report(*, defect: bool = False, alternate: bool = False) -> bytes:
    first = "test_other" if alternate else "test_value"
    tag = "<failure/>" if defect else ""
    return (
        f'<testsuite tests="2" errors="0" failures="{int(defect)}" skipped="0">'
        f'<testcase classname="test_subject_01" name="{first}">{tag}</testcase>'
        '<testcase classname="test_subject_02" name="test_repeat"/></testsuite>'
    ).encode()


@pytest.mark.parametrize(
    ("case", "defect_status", "sensitivity"),
    [
        ("matching", "test_failed", {"detected": 1, "survived": 0, "inconclusive": 0, "planned": 1}),
        ("renamed", "report_invalid", {"detected": 0, "survived": 0, "inconclusive": 1, "planned": 1}),
        (
            "no-reference",
            "reference_inventory_unavailable",
            {"detected": None, "survived": None, "inconclusive": None, "planned": 1},
        ),
    ],
)
def test_sealed_submission_uses_the_reference_inventory(
    sealed_submission, monkeypatch, case, defect_status, sensitivity
):
    task, handoff, archive, defects, assets, runtime, output, raw, snippets = sealed_submission
    observed = []
    monkeypatch.setattr(collector, "DockerClient", lambda *args: object())

    def execute(client, output, name, payload, dependencies, environment, *, timeout=collector.TIMEOUT):
        observed.append(name)
        if name == "publisher":
            assert timeout == collector.PUBLISHER_TIMEOUT
            prediction = json.loads(payload["stage/predictions/subject.jsonl"])
            assert prediction["tests"] == snippets
            return "completed", 0, PUBLISHER
        assert timeout == collector.TIMEOUT
        for index, snippet in enumerate(snippets, 1):
            assert (
                payload[f"stage/test_subject_{index:02}.py"]
                == b"from under_test import Solution\n\n" + snippet.encode()
            )
        if name == "pytest-reference":
            assert payload["stage/under_test.py"] == REFERENCE
            if case == "no-reference":
                return "timed_out", None, b""
            return "completed", 0, two_case_report()
        assert payload["stage/under_test.py"] == DEFECT
        return "completed", 1, two_case_report(defect=True, alternate=case == "renamed")

    monkeypatch.setattr(collector, "run_stage", execute)
    result = collector.collect_handoff(task, handoff, archive, defects, assets, runtime, output)
    assert observed == ["publisher", "pytest-reference", "pytest-offset"]
    assert result["defects"]["offset"]["status"] == defect_status
    assert result["sensitivity"] == sensitivity
    expected = None if case == "no-reference" else ["test_subject_01::test_value", "test_subject_02::test_repeat"]
    assert result["reference_pytest_cases"] == expected
    assert result["submission_snippets"] == 2 and result["archive_sha256"] == archive
    assert (output / "tests.json").read_bytes() == raw
    assert grader.grade((output / "plan.json").read_bytes(), output / "capture.json") == result
    (output / "tests.json").write_bytes(raw + b"\n")
    with pytest.raises(ValueError, match="Evidence bytes changed for tests.json"):
        grader.grade((output / "plan.json").read_bytes(), output / "capture.json")


@pytest.mark.parametrize("drift", ["archive", "baseline", "unrelated-file"])
def test_unadmitted_handoff_never_creates_a_container(sealed_submission, monkeypatch, drift):
    task, directory, archive, defects, assets, runtime, output, _, _ = sealed_submission
    if drift == "archive":
        with (directory / "submission.tar").open("ab") as stream:
            stream.write(b"changed")
    elif drift == "baseline":
        with (directory / "baseline.collection.json").open("ab") as stream:
            stream.write(b" ")
    else:
        other = snapshot(directory / "additional", {"tests.json": b"[]", "other.txt": b"changed"})
        (directory / "submission.collection.json").write_bytes(other)

    def unexpected(*args):
        pytest.fail("Unadmitted handoff must fail before Docker initialization")

    monkeypatch.setattr(collector, "DockerClient", unexpected)
    with pytest.raises(ValueError, match="controller's digest|frozen identity|change only"):
        collector.collect_handoff(task, directory, archive, defects, assets, runtime, output)
    assert not output.exists()

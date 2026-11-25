"""Keep native TestEval and actual pytest outcomes separately verifiable."""

import copy
import json

import pytest
import validate_testeval_calibration as calibration


def test_published_calibration_preserves_the_disagreement() -> None:
    assert calibration.main(["--check"]) == 0
    result = json.loads((calibration.DEFAULT / "result.json").read_bytes())
    assert result["composite_score"] is None
    assert result["model_attempts"] == 0
    correct = result["cases"]["correct_assertion"]
    incorrect = result["cases"]["incorrect_assertion"]
    no_call = result["cases"]["no_call"]
    assert correct["native_metrics"] == incorrect["native_metrics"]
    assert correct["native_metrics"]["line_coverage"] > 0
    assert correct["independent_pytest"]["passed"] == 1
    assert incorrect["independent_pytest"]["failures"] == 1
    assert no_call["independent_pytest"]["passed"] == 1
    assert no_call["native_metrics"]["line_coverage"] == no_call["native_metrics"]["branch_coverage"] == 0


@pytest.mark.parametrize(
    "suffix",
    [
        b"",
        b"Average Line Coverage: nan, Average Branch Coverage: 0.5\n",
        b"Average Line Coverage: 0.5, Average Branch Coverage: 1.2\n",
        b"Average Line Coverage: 0.5, Average Branch Coverage: 0.5\n" * 2,
    ],
)
def test_rejects_incomplete_or_incompatible_metric_reports(suffix: bytes) -> None:
    with pytest.raises(ValueError, match="metric"):
        calibration.publisher_metrics(b"Syntax Correctness: 1.0\nExecutable Correctness: 1.0\n" + suffix)


def test_rejects_disagreeing_exit_and_collected_cases() -> None:
    raw = (
        b'<testsuite tests="1" failures="1" errors="0" skipped="0">'
        b'<testcase classname="generated" name="test_output"><failure/></testcase></testsuite>'
    )
    with pytest.raises(ValueError, match="exit disagrees"):
        calibration.independent_pytest(raw, b"0", ["generated::test_output"])
    with pytest.raises(ValueError, match="different case set"):
        calibration.independent_pytest(raw, b"1", ["generated::test_other"])


def test_rejects_edited_or_replaced_receipt() -> None:
    manifest = json.loads((calibration.DEFAULT / "manifest.json").read_bytes())
    modified = copy.deepcopy(manifest)
    modified["cases"]["correct_assertion"]["publisher_stdout"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Evidence bytes changed"):
        calibration.inspect(calibration.DEFAULT, modified)


def test_rejects_nested_case_absent_from_suite_count() -> None:
    raw = (
        b'<testsuite tests="1" failures="0" errors="0" skipped="0">'
        b'<testcase classname="generated" name="test_output"/>'
        b'<testsuite><testcase classname="x" name="unreported"/></testsuite></testsuite>'
    )
    with pytest.raises(ValueError, match="different case set"):
        calibration.independent_pytest(raw, b"0", ["generated::test_output"])


def test_published_controls_preserve_task_and_runner_disagreements() -> None:
    directory = calibration.DEFAULT.with_name("testeval-public-controls")
    assert calibration.main(["--directory", str(directory), "--check"]) == 0
    result = json.loads((directory / "result.json").read_bytes())
    cases = result["cases"]
    assert result["model_attempts"] == 0
    assert result["composite_score"] is None
    assert len(cases) == 15
    for task in (1805, 2850, 685):
        matching = cases[f"task-{task}-matching"]
        mismatching = cases[f"task-{task}-mismatching"]
        portable = cases[f"task-{task}-matching-portable-shape"]
        no_call = cases[f"task-{task}-no-call"]
        assert matching["native_metrics"] == mismatching["native_metrics"]
        assert matching["native_metrics"]["line_coverage"] > 0
        assert matching["independent_pytest"]["passed"] == portable["independent_pytest"]["passed"] == 1
        assert mismatching["independent_pytest"]["failures"] == 1
        assert portable["native_metrics"] == no_call["native_metrics"]
        assert portable["native_metrics"]["executable_correctness"] == 0


def test_rejects_a_mismatched_native_stream_in_an_intact_archive() -> None:
    directory = calibration.DEFAULT.with_name("testeval-public-controls")
    manifest = json.loads((directory / "manifest.json").read_bytes())
    manifest["cases"]["task-1805-matching"]["publisher_stdout"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Evidence bytes changed"):
        calibration.inspect(directory, manifest)

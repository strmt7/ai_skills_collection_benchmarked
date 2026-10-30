import json

import compare_flink_outputs as target
import pytest


def test_order_and_whitespace_do_not_change_tuples():
    assert target.compare("(1,2)\n(-4,0)\n", "( -4 , 0 )\n(1, 2)\n") == []


@pytest.mark.parametrize("candidate", ["(1,2)\n(1,2)\n", "(1,2)\n(1,3)\n", "(01,2)\n(+1,2)\n"])
def test_duplicate_job_ids_rejected(candidate):
    with pytest.raises(ValueError, match="duplicate jobId"):
        target.compare("(1,2)\n", candidate)


def test_reference_duplicate_also_rejected():
    with pytest.raises(ValueError, match="expected.*duplicate"):
        target.compare("(1,2)\n(1,2)\n", "(1,2)\n")


@pytest.mark.parametrize("candidate", ["", "\n", "(1,-2)", "(1,2.0)", "(1,2,3)", "(1,2) trailing", "(1,2)\n\n"])
def test_invalid_or_empty_records_rejected(candidate):
    with pytest.raises(ValueError):
        target.compare("(1,2)\n", candidate)


def test_missing_extra_and_mismatched_counts_are_reported():
    assert target.compare("(1,2)\n(2,4)\n", "(2,5)\n(3,8)\n") == [
        "missing jobId 1",
        "unexpected jobId 3",
        "jobId 2: expected 4, got 5",
    ]


def test_cli_exit_and_json(tmp_path, capsys):
    expected = tmp_path / "expected.txt"
    actual = tmp_path / "actual.txt"
    expected.write_text("(1,2)\n", encoding="utf-8")
    actual.write_text("(1,2)\n(1,2)\n", encoding="utf-8")
    assert target.main(["--expected", str(expected), "--actual", str(actual), "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["passed"] is False
    assert report["model_scored"] is False
    assert "duplicate" in report["errors"][0]
    actual.write_text("(1,2)\n", encoding="utf-8")
    assert target.main(["--expected", str(expected), "--actual", str(actual), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["passed"] is True

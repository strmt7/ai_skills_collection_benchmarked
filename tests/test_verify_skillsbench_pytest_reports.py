from __future__ import annotations

import hashlib
import json

import pytest
from verify_skillsbench_pytest_reports import MAX_REPORT_BYTES, main, verify_reports

NODE_IDS = (
    "test_metrics.py::test_total[empty - document]",
    "test_metrics.py::test_total[one]",
    "test_metrics.py::test_summary",
)
INVENTORY = hashlib.sha256("\n".join(NODE_IDS).encode()).hexdigest()


@pytest.fixture
def reports():
    pytest_output = (
        "platform linux -- Python 3.12.8, pytest-8.3.4, pluggy-1.7.0 -- /tmp/grader/bin/python\n"
        "rootdir: /verifier\n"
        "plugins: json-ctrf-0.3.6\n"
        "collecting ... collected 3 items\n"
        f"../verifier/{NODE_IDS[0]} FAILED [ 33%]\n"
        f"../verifier/{NODE_IDS[1]} PASSED [ 66%]\n"
        f"../verifier/{NODE_IDS[2]} PASSED [100%]\n"
        "================ short test summary info ================\n"
        f"PASSED ../verifier/{NODE_IDS[1]}\n"
        f"PASSED ../verifier/{NODE_IDS[2]}\n"
        f"FAILED ../verifier/{NODE_IDS[0]} - AssertionError\n"
        "================ 1 failed, 2 passed in 0.10s ================\n"
    )
    ctrf = {
        "results": {
            "tool": {"name": "pytest", "version": "8.3.4"},
            "summary": {"tests": 2, "passed": 2, "failed": 0, "skipped": 0, "pending": 0, "other": 0},
            "tests": [
                {"name": "test_metrics.py::test_total", "status": "passed"},
                {"name": "test_metrics.py::test_summary", "status": "passed"},
            ],
        }
    }
    return {
        "ctrf": json.dumps(ctrf).encode(),
        "pytest_output": pytest_output.encode(),
        "reward": b"1.0\n",
        "expected_node_ids_sha256": INVENTORY,
        "pytest_version": "8.3.4",
    }


def test_retains_official_reward_even_when_parameterized_case_failed(reports):
    result = verify_reports(**reports)
    assert result["official_grouped_reward"] == 1.0
    assert result["ctrf"] == {"tests": 2, "passed": 2, "failed": 0}
    assert result["pytest"] == {"tests": 3, "passed": 2, "failed": 1}
    assert result["ordered_node_ids_sha256"] == INVENTORY
    assert result["report_sha256"]["ctrf"] == hashlib.sha256(reports["ctrf"]).hexdigest()


@pytest.mark.parametrize(
    "key,replacement,message",
    [
        ("expected_node_ids_sha256", "0" * 64, "frozen digest"),
        ("pytest_version", "8.4.0", "declared verifier profile"),
        ("reward", b"0.667\n", "grouped result"),
        ("reward", b"NaN\n", "malformed"),
        ("ctrf", b"", "empty"),
        ("ctrf", b"x" * (MAX_REPORT_BYTES + 1), "size bound"),
    ],
)
def test_unbound_or_invalid_evidence_stays_unscored(reports, key, replacement, message):
    reports[key] = replacement
    with pytest.raises(ValueError, match=message):
        verify_reports(**reports)


@pytest.mark.parametrize(
    "old,replacement,message",
    [
        (b"collected 3", b"collected 4", "inventory is incomplete"),
        (b"1 failed, 2 passed", b"3 passed", "terminal counts disagree"),
        (b"================ short test summary info", b"================ interrupted", "terminal summary"),
        (b"FAILED ../verifier/test_metrics.py", b"PASSED ../verifier/test_metrics.py", "short summary disagree"),
    ],
)
def test_rejects_incomplete_or_contradictory_native_pytest(reports, old, replacement, message):
    reports["pytest_output"] = reports["pytest_output"].replace(old, replacement)
    with pytest.raises(ValueError, match=message):
        verify_reports(**reports)


def test_rejects_consistent_report_using_wrong_group_reducer(reports):
    ctrf = json.loads(reports["ctrf"])
    ctrf["results"]["tests"][0]["status"] = "failed"
    ctrf["results"]["summary"].update(passed=1, failed=1)
    reports.update(ctrf=json.dumps(ctrf).encode(), reward=b"0.5\n")
    with pytest.raises(ValueError, match="last outcome"):
        verify_reports(**reports)


def test_rejects_duplicate_ctrf_names_even_with_matching_count(reports):
    ctrf = json.loads(reports["ctrf"])
    ctrf["results"]["tests"][1]["name"] = ctrf["results"]["tests"][0]["name"]
    reports["ctrf"] = json.dumps(ctrf).encode()
    with pytest.raises(ValueError, match="duplicate"):
        verify_reports(**reports)


def test_exit_zero_and_reward_alone_cannot_be_scored(tmp_path, capsys):
    reward = tmp_path / "reward.txt"
    reward.write_bytes(b"0\n")
    code = main(
        [
            "--reward",
            str(reward),
            "--pytest-output",
            str(tmp_path / "pytest_output.txt"),
            "--ctrf",
            str(tmp_path / "ctrf.json"),
            "--expected-node-ids-sha256",
            INVENTORY,
            "--pytest-version",
            "8.3.4",
        ]
    )
    result = json.loads(capsys.readouterr().out)
    assert code == 2
    assert result["status"] == "unscored"
    assert "official_grouped_reward" not in result

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from _trial_collection_policy import default_collection_policy
from verify_swe_skills_bench_pytest_result import main, verify_result

FIRST = "../tests/test_example.py::TestExample::test_first"
SECOND = "../tests/test_example.py::TestExample::test_second"
XML_FIRST = "tests.test_example.TestExample::test_first"
XML_SECOND = "tests.test_example.TestExample::test_second"


def _bytes(value: object) -> bytes:
    return json.dumps(value).encode("utf-8")


def _inventory() -> bytes:
    return _bytes(
        {
            "schema_version": 1,
            "pytest_version": "9.0.2",
            "rootdir": "/workspace",
            "min_pass_rate": 1.0,
            "cases": {FIRST: XML_FIRST, SECOND: XML_SECOND},
        }
    )


def _console(*, fail: bool = False) -> bytes:
    status = "FAILED" if fail else "PASSED"
    counts = "1 failed, 1 passed" if fail else "2 passed"
    return (
        "platform linux -- Python 3.12.3, pytest-9.0.2, pluggy-1.6.0\n"
        "rootdir: /workspace\n"
        "collecting ... collected 2 items\n\n"
        f"{FIRST} PASSED [ 50%]\n"
        f"{SECOND} {status} [100%]\n"
        f"================ {counts} in 0.05s ================\n"
    ).encode()


def _junit(*, fail: bool = False) -> bytes:
    failure = "<failure>assertion failed</failure>" if fail else ""
    return (
        f'<testsuites><testsuite tests="2" failures="{int(fail)}" skipped="0" errors="0">'
        '<testcase classname="tests.test_example.TestExample" name="test_first"/>'
        f'<testcase classname="tests.test_example.TestExample" name="test_second">{failure}</testcase>'
        "</testsuite></testsuites>"
    ).encode()


def _publisher(*, fail: bool = False) -> bytes:
    return _bytes(
        {
            "level": "L2",
            "method": "unit_test",
            "status": "failed" if fail else "passed",
            "score": 0.5 if fail else 1.0,
            "details": {
                "passed": 1 if fail else 2,
                "failed": int(fail),
                "total": 2,
                "errors": 0,
                "skipped": 0,
                "min_pass_rate": 1.0,
            },
        }
    )


@pytest.mark.parametrize("fail", [False, True])
def test_admits_reconciled_native_fraction(fail: bool) -> None:
    result = verify_result(
        inventory=_inventory(),
        console=_console(fail=fail),
        junit=_junit(fail=fail),
        publisher=_publisher(fail=fail),
        exit_code=int(fail),
    )
    assert result["score"] == (0.5 if fail else 1.0)
    assert result["case_status"] == {XML_FIRST: "passed", XML_SECOND: "failed" if fail else "passed"}
    assert result["total"] == 2


@pytest.mark.parametrize("exit_code,timed_out", [(2, False), (5, False), (124, True), (0, True)])
def test_nonordinary_exit_never_counts(exit_code: int, timed_out: bool) -> None:
    with pytest.raises(ValueError, match="ordinary test verdict"):
        verify_result(
            inventory=_inventory(),
            console=_console(),
            junit=_junit(),
            publisher=_publisher(),
            exit_code=exit_code,
            timed_out=timed_out,
        )


@pytest.mark.parametrize(
    "console,match",
    [
        (_console().splitlines(keepends=True)[0] + b"".join(_console().splitlines(keepends=True)[1:5]), "full frozen"),
        (b"".join(_console().splitlines(keepends=True)[:-1]), "terminal pytest summary"),
        (_console().replace(b"2 passed", b"1 passed"), "terminal counts"),
        (_console().replace(b"test_second", b"test_first"), "repeated case"),
        (_console().replace(b"pytest-9.0.2", b"pytest-9.0.3"), "runtime profile"),
    ],
)
def test_console_must_prove_completeness(console: bytes, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        verify_result(inventory=_inventory(), console=console, junit=_junit(), publisher=_publisher(), exit_code=0)


@pytest.mark.parametrize(
    "junit,match",
    [
        (_junit().replace(b"test_second", b"test_other"), "individual outcomes"),
        (_junit().replace(b"test_second", b"test_first"), "duplicate testcase"),
        (_junit().replace(b"</testcase>", b"<skipped/></testcase>"), "native pytest reason"),
        (_junit().replace(b'failures="0"', b'failures="1"'), "suite counts"),
        (b"<!DOCTYPE testsuites [<!ENTITY unexpected 'x'>]>" + _junit(), "unexpected XML"),
    ],
)
def test_junit_must_confirm_actual_cases(junit: bytes, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        verify_result(inventory=_inventory(), console=_console(), junit=junit, publisher=_publisher(), exit_code=0)


def test_case_outcomes_must_match_even_with_same_totals() -> None:
    swapped = _junit(fail=True).replace(b"test_first", b"temp").replace(b"test_second", b"test_first")
    swapped = swapped.replace(b"temp", b"test_second")
    with pytest.raises(ValueError, match="individual outcomes"):
        verify_result(
            inventory=_inventory(),
            console=_console(fail=True),
            junit=swapped,
            publisher=_publisher(fail=True),
            exit_code=1,
        )


def test_completed_failure_must_match_process_exit() -> None:
    with pytest.raises(ValueError, match="exit code disagrees"):
        verify_result(
            inventory=_inventory(),
            console=_console(fail=True),
            junit=_junit(fail=True),
            publisher=_publisher(fail=True),
            exit_code=0,
        )


@pytest.mark.parametrize(
    "publisher,match",
    [
        (_publisher().replace(b'"score": 1.0', b'"score": 0.5'), "verdict differs"),
        (_publisher().replace(b'"status": "passed"', b'"status": "skipped"'), "verdict differs"),
        (_publisher().replace(b'"total": 2', b'"total": 1'), "counts or threshold"),
        (_publisher().replace(b'"min_pass_rate": 1.0', b'"min_pass_rate": 0.5'), "counts or threshold"),
    ],
)
def test_publisher_fraction_and_counts_must_match(publisher: bytes, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        verify_result(inventory=_inventory(), console=_console(), junit=_junit(), publisher=publisher, exit_code=0)


def test_cli_refuses_truncated_console_with_native_perfect_score(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    evidence = {
        "--inventory": _inventory(),
        "--console": b"".join(_console().splitlines(keepends=True)[:5]),
        "--junit": _junit(),
        "--publisher-result": _publisher(),
    }
    argv = ["--exit-code", "0"]
    for flag, data in evidence.items():
        path = tmp_path / flag.removeprefix("--")
        path.write_bytes(data)
        argv.extend((flag, str(path)))
    assert main(argv) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "native_pytest_result_unverified"
    assert result["score"] is None


MISSING_DEMO = "Demo file absent"


def _candidate_capture(*, has_demo: bool = False) -> tuple[bytes, bytes]:
    files = {"scripts/demo.py": {"sha256": hashlib.sha256(b"x").hexdigest(), "bytes": 1}} if has_demo else {}
    record = {
        "collection_version": 1,
        "status": "collected",
        "policy": default_collection_policy(),
        "files": files,
        "directories": ["scripts"] if has_demo else [],
        "directory_count": int(has_demo),
        "excluded": [],
        "file_count": int(has_demo),
        "total_bytes": int(has_demo),
        "post_inventory_matches": True,
        "atomic_snapshot": False,
        "precondition": "All subject execution must be stopped before capture.",
    }
    raw = _bytes(record)
    receipt = _bytes(
        {
            "status": "grader_tree_rebuilt",
            "submission_manifest_sha256": hashlib.sha256(raw).hexdigest(),
            **{key: record[key] for key in ("file_count", "directory_count", "total_bytes")},
        }
    )
    return raw, receipt


def _skip_arguments(*, has_demo: bool = False) -> dict:
    profile = json.loads(_inventory())
    profile.update(
        {
            "schema_version": 2,
            "collection_policy": default_collection_policy(),
            "candidate_skips": {XML_SECOND: {"missing_file": "scripts/demo.py", "message": MISSING_DEMO}},
        }
    )
    console = (
        _console()
        .replace(f"{SECOND} PASSED".encode(), f"{SECOND} SKIPPED".encode())
        .replace(b"2 passed", b"1 passed, 1 skipped")
    )
    junit = _junit().replace(b'skipped="0"', b'skipped="1"')
    junit = junit.replace(b"</testcase>", f'<skipped type="pytest.skip" message="{MISSING_DEMO}"/></testcase>'.encode())
    publisher = json.loads(_publisher())
    publisher.update(score=0.5, status="failed")
    publisher["details"].update(passed=1, skipped=1)
    manifest, handoff = _candidate_capture(has_demo=has_demo)
    return {
        "inventory": _bytes(profile),
        "console": console,
        "junit": junit,
        "publisher": _bytes(publisher),
        "exit_code": 0,
        "submission_manifest": manifest,
        "handoff_result": handoff,
    }


def test_declared_candidate_skip_stays_in_native_denominator() -> None:
    result = verify_result(**_skip_arguments())
    assert result["score"] == 0.5
    assert result["passed"] == 1 and result["skipped"] == 1 and result["total"] == 2
    assert result["case_status"][XML_SECOND] == "skipped"
    assert result["candidate_skip_evidence"] == {
        XML_SECOND: {"missing_file": "scripts/demo.py", "message": MISSING_DEMO}
    }
    assert {"submission_manifest", "handoff_result"} <= result["sha256"].keys()


@pytest.mark.parametrize("change", ["source_present", "wrong_reason", "unknown_case"])
def test_skip_requires_exact_rule_and_absent_candidate_file(change: str) -> None:
    arguments = _skip_arguments(has_demo=change == "source_present")
    if change == "wrong_reason":
        arguments["junit"] = arguments["junit"].replace(MISSING_DEMO.encode(), b"Missing pytest toolchain")
    if change == "unknown_case":
        profile = json.loads(arguments["inventory"])
        profile["candidate_skips"] = {}
        arguments["inventory"] = _bytes(profile)
    with pytest.raises(ValueError, match="declared candidate evidence"):
        verify_result(**arguments)


@pytest.mark.parametrize("change", ["missing_manifest", "missing_handoff", "wrong_hash", "incomplete_capture"])
def test_skip_evidence_requires_the_reconstructed_complete_capture(change: str) -> None:
    arguments = _skip_arguments()
    if change == "missing_manifest":
        arguments["submission_manifest"] = None
    elif change == "missing_handoff":
        arguments["handoff_result"] = None
    elif change == "wrong_hash":
        handoff = json.loads(arguments["handoff_result"])
        handoff["submission_manifest_sha256"] = "0" * 64
        arguments["handoff_result"] = _bytes(handoff)
    else:
        arguments["submission_manifest"] = _bytes({"status": "collection_error"})
    with pytest.raises(ValueError):
        verify_result(**arguments)


def test_schema_one_still_rejects_a_fully_reported_skip() -> None:
    arguments = _skip_arguments()
    arguments.update(inventory=_inventory(), submission_manifest=None, handoff_result=None)
    with pytest.raises(ValueError, match="declared candidate evidence"):
        verify_result(**arguments)


def test_complete_pass_also_binds_reconstruction_under_schema_two() -> None:
    arguments = _skip_arguments()
    arguments.update(console=_console(), junit=_junit(), publisher=_publisher())
    result = verify_result(**arguments)
    assert result["score"] == 1.0
    assert result["candidate_skip_evidence"] == {}


def test_skipped_count_must_match_publisher_result() -> None:
    arguments = _skip_arguments()
    publisher = json.loads(arguments["publisher"])
    publisher["details"]["skipped"] = 0
    arguments["publisher"] = _bytes(publisher)
    with pytest.raises(ValueError, match="counts or threshold"):
        verify_result(**arguments)


def test_skip_rule_cannot_use_a_file_excluded_from_capture() -> None:
    arguments = _skip_arguments()
    profile = json.loads(arguments["inventory"])
    profile["candidate_skips"][XML_SECOND]["missing_file"] = "cache/__pycache__/demo.py"
    arguments["inventory"] = _bytes(profile)
    with pytest.raises(ValueError, match="outside the capture scope"):
        verify_result(**arguments)

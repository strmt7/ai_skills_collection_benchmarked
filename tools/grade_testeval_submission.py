"""Grade captured TestEval submissions against a frozen independent test plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import ParseError

from _trial_transcript import strict_json
from defusedxml.common import DefusedXmlException
from validate_testeval_calibration import evidence_stream, independent_pytest, publisher_metrics, read_evidence

SHA256 = re.compile(r"[a-f0-9]{64}")
COMMIT = re.compile(r"[a-f0-9]{40}")
VARIANT = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
TERMINATIONS = {"completed", "fixture_unavailable", "setup_failed", "timed_out", "interrupted"}
EVIDENCE_ERRORS = (DefusedXmlException, KeyError, ParseError, UnicodeError, ValueError)
PLAN_FIELDS = {"schema_version", "task_id", "publisher", "programs", "subject_suite_sha256", "pytest_cases"}
CAPTURE_FIELDS = {"schema_version", "plan_sha256", "publisher", "variants"}


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def is_digest(value: object) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def validate_plan(plan: dict[str, Any]) -> None:
    if plan.keys() != PLAN_FIELDS or type(plan["schema_version"]) is not int or plan["schema_version"] != 1:
        raise ValueError("Expected a version 1 TestEval grade plan")
    if type(plan["task_id"]) is not int or plan["task_id"] <= 0:
        raise ValueError("TestEval plan requires a positive publisher task ID")
    source = plan["publisher"]
    if (
        not isinstance(source, dict)
        or source.keys() != {"commit_sha", "dataset_sha256", "evaluator_sha256"}
        or not isinstance(source["commit_sha"], str)
        or COMMIT.fullmatch(source["commit_sha"]) is None
        or not all(is_digest(source[key]) for key in ("dataset_sha256", "evaluator_sha256"))
    ):
        raise ValueError("TestEval plan requires the pinned publisher commit, dataset and evaluator")
    programs = plan["programs"]
    if (
        not isinstance(programs, dict)
        or not 2 <= len(programs) <= 128
        or "reference" not in programs
        or any(VARIANT.fullmatch(name) is None or not is_digest(digest) for name, digest in programs.items())
        or len(set(programs.values())) != len(programs)
    ):
        raise ValueError("TestEval plan requires distinct reference and independently prepared defect programs")
    cases = plan["pytest_cases"]
    if (
        not isinstance(cases, list)
        or not cases
        or any(not isinstance(case, str) or not case.strip() for case in cases)
        or len(set(cases)) != len(cases)
    ):
        raise ValueError("TestEval plan requires distinct, nonempty independent pytest case identities")
    if not is_digest(plan["subject_suite_sha256"]):
        raise ValueError("TestEval plan requires the exact submission suite identity")


def verify_capture(root: Path, capture: dict[str, Any], report_name: str) -> tuple[str, int | None, bytes | None]:
    termination, exit_code, report = capture["termination"], capture["exit_code"], capture[report_name]
    if termination not in TERMINATIONS:
        raise ValueError("Unknown grading process termination")
    if type(exit_code) is not int and not (exit_code is None and termination != "completed"):
        raise ValueError("A completed grading process requires an integer native exit code")
    if report is not None and (not isinstance(report, dict) or report.keys() != {"file", "sha256"}):
        raise ValueError("Native report requires a filename and digest")
    raw = evidence_stream(root, report) if report is not None else None
    return termination, exit_code, raw


def publisher_outcome(root: Path, stage: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    if stage.keys() != {"source", "subject_suite_sha256", "termination", "exit_code", "stdout"}:
        raise ValueError("Publisher capture fields differ from the grading contract")
    if stage["source"] != plan["publisher"] or stage["subject_suite_sha256"] != plan["subject_suite_sha256"]:
        raise ValueError("Publisher capture source or submitted tests differ from the plan")
    termination, exit_code, content = verify_capture(root, stage, "stdout")
    if termination != "completed":
        return {"status": termination, "exit_code": exit_code, "metrics": None}
    if exit_code != 0:
        return {"status": "publisher_failed", "exit_code": exit_code, "metrics": None}
    if content is None:
        return {"status": "report_missing", "exit_code": exit_code, "metrics": None}
    try:
        metrics = publisher_metrics(content)
    except EVIDENCE_ERRORS:
        return {"status": "report_invalid", "exit_code": exit_code, "metrics": None}
    return {"status": "measured", "exit_code": exit_code, "metrics": metrics}


def pytest_outcome(
    root: Path, stage: dict[str, Any], program_sha256: str, suite_sha256: str, cases: list[str]
) -> dict[str, Any]:
    if stage.keys() != {"program_sha256", "subject_suite_sha256", "termination", "exit_code", "junit"}:
        raise ValueError("Variant capture fields differ from the grading contract")
    termination, exit_code, content = verify_capture(root, stage, "junit")
    expected_program = None if termination == "fixture_unavailable" else program_sha256
    if stage["program_sha256"] != expected_program or stage["subject_suite_sha256"] != suite_sha256:
        raise ValueError("Variant program or submitted tests differ from the plan")
    if termination != "completed":
        return {"status": termination, "exit_code": exit_code, "counts": None}
    if exit_code not in (0, 1):
        return {"status": "pytest_incomplete", "exit_code": exit_code, "counts": None}
    if content is None:
        return {"status": "report_missing", "exit_code": exit_code, "counts": None}
    try:
        counts = independent_pytest(content, str(exit_code).encode("ascii"), cases)
    except EVIDENCE_ERRORS:
        return {"status": "report_invalid", "exit_code": exit_code, "counts": None}
    if counts["errors"]:
        status = "pytest_case_error"
    elif counts["skipped"]:
        status = "pytest_case_skipped"
    else:
        status = "test_failed" if counts["failures"] else "passed"
    return {"status": status, "exit_code": exit_code, "counts": counts}


def sensitivity(reference: str, variants: dict[str, str]) -> dict[str, int | None]:
    planned = len(variants)
    if reference != "passed":
        return {"detected": None, "survived": None, "inconclusive": None, "planned": planned}
    detected = sum(outcome == "test_failed" for outcome in variants.values())
    survived = sum(outcome == "passed" for outcome in variants.values())
    return {
        "detected": detected,
        "survived": survived,
        "inconclusive": planned - detected - survived,
        "planned": planned,
    }


def grade(plan_bytes: bytes, capture_file: Path) -> dict[str, Any]:
    plan = strict_json(plan_bytes.decode("utf-8"))
    if not isinstance(plan, dict):
        raise ValueError("TestEval grade plan must be a JSON object")
    validate_plan(plan)
    plan_digest = sha256(plan_bytes)
    capture_path = capture_file.resolve(strict=True)
    capture_bytes = read_evidence(capture_path)
    capture = strict_json(capture_bytes.decode("utf-8"))
    if (
        not isinstance(capture, dict)
        or capture.keys() != CAPTURE_FIELDS
        or type(capture["schema_version"]) is not int
        or capture["schema_version"] != 1
        or capture["plan_sha256"] != plan_digest
    ):
        raise ValueError("Grade capture does not identify the supplied frozen plan")
    variants = capture["variants"]
    if not isinstance(variants, dict) or variants.keys() != plan["programs"].keys():
        raise ValueError("Grade capture must account for every planned program")
    if not isinstance(capture["publisher"], dict) or any(not isinstance(row, dict) for row in variants.values()):
        raise ValueError("Publisher and variant captures must be JSON objects")
    native = publisher_outcome(capture_path.parent, capture["publisher"], plan)
    outcomes = {
        name: pytest_outcome(
            capture_path.parent, row, plan["programs"][name], plan["subject_suite_sha256"], plan["pytest_cases"]
        )
        for name, row in variants.items()
    }
    reference = outcomes.pop("reference")
    return {
        "schema_version": 1,
        "task_id": plan["task_id"],
        "plan_sha256": plan_digest,
        "capture_sha256": sha256(capture_bytes),
        "native_test_eval": native,
        "reference": reference,
        "defects": outcomes,
        "sensitivity": sensitivity(reference["status"], {name: item["status"] for name, item in outcomes.items()}),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--plan", type=Path, required=True, help="Controller-owned frozen task, suite and program identities"
    )
    parser.add_argument(
        "--capture", type=Path, required=True, help="Controller-owned capture alongside its native reports"
    )
    parser.add_argument("--check", type=Path, metavar="RESULT", help="Compare the computed result with this JSON file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = grade(read_evidence(args.plan), args.capture)
        output = {"ok": True, "result": result}
        if args.check and output != strict_json(read_evidence(args.check).decode("utf-8")):
            raise ValueError("Stored TestEval grade differs from the validated observations")
    except (OSError, TypeError, *EVIDENCE_ERRORS) as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(output, allow_nan=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

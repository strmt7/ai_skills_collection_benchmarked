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
from validate_testeval_calibration import evidence_stream, publisher_metrics, pytest_report, read_evidence

SHA256 = re.compile(r"[a-f0-9]{64}")
COMMIT = re.compile(r"[a-f0-9]{40}")
VARIANT = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
TERMINATIONS = {"completed", "fixture_unavailable", "setup_failed", "timed_out", "interrupted"}
EVIDENCE_ERRORS = (DefusedXmlException, KeyError, ParseError, UnicodeError, ValueError)
ASSIGNMENT_FIELDS = {"task_id", "publisher", "programs"}
BASE_PLAN_FIELDS = {"schema_version", "subject_suite_sha256", *ASSIGNMENT_FIELDS}
CAPTURE_EVIDENCE = {"task_plan": "task-plan.json", "handoff": "handoff.json"}
CAPTURE_FIELDS = {"schema_version", "plan_sha256", "publisher", "variants"}
TEST_SUBMISSION = "tests.json"
MAX_SNIPPETS = 20


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def is_digest(value: object) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def validate_assignment(plan: dict[str, Any]) -> None:
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
        or any(
            not isinstance(name, str) or VARIANT.fullmatch(name) is None or not is_digest(digest)
            for name, digest in programs.items()
        )
        or len(set(programs.values())) != len(programs)
    ):
        raise ValueError("TestEval plan requires distinct reference and independently prepared defect programs")


def validate_task_plan(plan: dict[str, Any]) -> None:
    """Validate task inputs frozen before the subject produces tests."""
    if (
        plan.keys() != {"schema_version", "baseline_manifest_sha256", *ASSIGNMENT_FIELDS}
        or type(plan["schema_version"]) is not int
        or plan["schema_version"] != 2
        or not is_digest(plan["baseline_manifest_sha256"])
    ):
        raise ValueError("Expected a version 2 TestEval task plan with a frozen baseline capture")
    validate_assignment(plan)


def load_test_snippets(raw: bytes) -> list[str]:
    """Read the ordered source snippets delivered to the original publisher."""
    value = strict_json(raw.decode("utf-8"))
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_SNIPPETS:
        raise ValueError(f"TestEval submission must be a JSON array of 1 to {MAX_SNIPPETS} source snippets")
    snippets: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError("Each TestEval source snippet must be a string")
        item.encode("utf-8")
        snippets.append(item)
    return snippets


def validate_plan(plan: dict[str, Any]) -> None:
    version = plan.get("schema_version")
    fields = {1: {"pytest_cases"}, 2: CAPTURE_EVIDENCE.keys()}
    if type(version) is not int or version not in fields or plan.keys() != BASE_PLAN_FIELDS | fields[version]:
        raise ValueError("Expected a versioned TestEval grade plan")
    validate_assignment(plan)
    if not is_digest(plan["subject_suite_sha256"]):
        raise ValueError("TestEval plan requires the exact submission suite identity")
    if version == 2:
        for key, filename in CAPTURE_EVIDENCE.items():
            ref = plan[key]
            if (
                not isinstance(ref, dict)
                or ref.keys() != {"file", "sha256"}
                or ref["file"] != filename
                or not is_digest(ref["sha256"])
            ):
                raise ValueError(f"TestEval plan requires a digest-bound {filename}")
        return
    cases = plan["pytest_cases"]
    if (
        not isinstance(cases, list)
        or not cases
        or any(not isinstance(case, str) or not case.strip() for case in cases)
        or len(set(cases)) != len(cases)
    ):
        raise ValueError("TestEval plan requires distinct, nonempty independent pytest case identities")


def submission_evidence(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    task = strict_json(evidence_stream(root, plan["task_plan"]).decode("utf-8"))
    if not isinstance(task, dict):
        raise ValueError("TestEval task plan must be a JSON object")
    validate_task_plan(task)
    if any(plan[key] != task[key] for key in ASSIGNMENT_FIELDS):
        raise ValueError("Grade assignment differs from the frozen TestEval task plan")
    raw = evidence_stream(root, {"file": TEST_SUBMISSION, "sha256": plan["subject_suite_sha256"]})
    handoff = strict_json(evidence_stream(root, plan["handoff"]).decode("utf-8"))
    if (
        not isinstance(handoff, dict)
        or handoff.get("status") != "grader_tree_rebuilt"
        or handoff.get("baseline_manifest_sha256") != task["baseline_manifest_sha256"]
        or not is_digest(handoff.get("submission_manifest_sha256"))
        or not is_digest(handoff.get("archive_sha256"))
        or handoff.get("deletes") != []
        or handoff.get("writes") != {TEST_SUBMISSION: {"bytes": len(raw), "sha256": plan["subject_suite_sha256"]}}
    ):
        raise ValueError("TestEval handoff does not identify the frozen baseline and submission bytes")
    return {
        "task_plan_sha256": plan["task_plan"]["sha256"],
        "archive_sha256": handoff["archive_sha256"],
        "submission_snippets": len(load_test_snippets(raw)),
    }


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
    root: Path,
    stage: dict[str, Any],
    program_sha256: str,
    suite_sha256: str,
    expected: set[str] | None,
    *,
    require_inventory: bool = False,
) -> tuple[dict[str, Any], set[str] | None]:
    if stage.keys() != {"program_sha256", "subject_suite_sha256", "termination", "exit_code", "junit"}:
        raise ValueError("Variant capture fields differ from the grading contract")
    termination, exit_code, content = verify_capture(root, stage, "junit")
    expected_program = None if termination == "fixture_unavailable" else program_sha256
    if stage["program_sha256"] != expected_program or stage["subject_suite_sha256"] != suite_sha256:
        raise ValueError("Variant program or submitted tests differ from the plan")
    if termination != "completed":
        return {"status": termination, "exit_code": exit_code, "counts": None}, None
    if exit_code not in (0, 1):
        return {"status": "pytest_incomplete", "exit_code": exit_code, "counts": None}, None
    if content is None:
        return {"status": "report_missing", "exit_code": exit_code, "counts": None}, None
    try:
        counts, seen = pytest_report(content, str(exit_code).encode("ascii"))
        if expected is not None and seen != expected:
            raise ValueError("Independent pytest collected a different case set")
    except EVIDENCE_ERRORS:
        return {"status": "report_invalid", "exit_code": exit_code, "counts": None}, None
    if require_inventory and expected is None:
        status = "reference_inventory_unavailable"
    elif counts["errors"]:
        status = "pytest_case_error"
    elif counts["skipped"]:
        status = "pytest_case_skipped"
    else:
        status = "test_failed" if counts["failures"] else "passed"
    return {"status": status, "exit_code": exit_code, "counts": counts}, seen


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
    version = plan["schema_version"]
    plan_digest = sha256(plan_bytes)
    capture_path = capture_file.resolve(strict=True)
    capture_bytes = read_evidence(capture_path)
    capture = strict_json(capture_bytes.decode("utf-8"))
    if (
        not isinstance(capture, dict)
        or capture.keys() != CAPTURE_FIELDS
        or type(capture["schema_version"]) is not int
        or capture["schema_version"] != version
        or capture["plan_sha256"] != plan_digest
    ):
        raise ValueError("Grade capture does not identify the supplied frozen plan")
    variants = capture["variants"]
    if not isinstance(variants, dict) or variants.keys() != plan["programs"].keys():
        raise ValueError("Grade capture must account for every planned program")
    if not isinstance(capture["publisher"], dict) or any(not isinstance(row, dict) for row in variants.values()):
        raise ValueError("Publisher and variant captures must be JSON objects")
    root = capture_path.parent
    admission = submission_evidence(root, plan) if version == 2 else {}
    native = publisher_outcome(root, capture["publisher"], plan)
    expected = set(plan["pytest_cases"]) if version == 1 else None
    reference, observed_cases = pytest_outcome(
        root, variants["reference"], plan["programs"]["reference"], plan["subject_suite_sha256"], expected
    )
    if version == 2:
        expected = observed_cases
    outcomes = {
        name: pytest_outcome(
            root, row, plan["programs"][name], plan["subject_suite_sha256"], expected, require_inventory=version == 2
        )[0]
        for name, row in variants.items()
        if name != "reference"
    }
    return {
        "schema_version": version,
        **(
            dict(admission, reference_pytest_cases=sorted(observed_cases) if observed_cases else None)
            if version == 2
            else {}
        ),
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

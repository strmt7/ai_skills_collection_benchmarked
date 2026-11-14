#!/usr/bin/env python3
"""Reconcile a SWE-Skills-Bench pytest verdict with an independent test inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from _trial_collection_manifest import validate_manifest
from _trial_collection_policy import collection_policy, excluded_directory
from _trial_protocol import relative_path
from _trial_transcript import strict_json

MAX_REPORT_BYTES = 512 * 1024
PROGRESS = re.compile(r"(.+?) (PASSED|FAILED|SKIPPED)[ \t]+\[[ \t]*\d+%\]")
TERMINAL = re.compile(r"=+ (.+?) in \d+(?:\.\d+)?s(?: \([0-9:]+\))? =+")


@dataclass(frozen=True, slots=True)
class Inventory:
    pytest_version: str
    rootdir: str
    min_pass_rate: float
    cases: dict[str, str]
    candidate_skips: dict[str, dict[str, str]]
    collection_policy: dict[str, Any] | None


def _text(raw: bytes) -> str:
    if not 0 < len(raw) <= MAX_REPORT_BYTES:
        raise ValueError("Native evidence is empty or exceeds its size bound")
    return raw.decode("utf-8")


def _rate(value: Any) -> bool:
    return type(value) in (float, int) and 0 <= value <= 1


def _inventory(raw: bytes) -> Inventory:
    value = strict_json(_text(raw))
    fields = {
        "schema_version",
        "pytest_version",
        "rootdir",
        "min_pass_rate",
        "cases",
    }
    if isinstance(value, dict) and value.get("schema_version") == 2:
        fields |= {"candidate_skips", "collection_policy"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("Expected a complete native pytest inventory")
    version, rootdir, minimum, cases = (
        value["pytest_version"],
        value["rootdir"],
        value["min_pass_rate"],
        value["cases"],
    )
    if (
        type(value["schema_version"]) is not int
        or value["schema_version"] not in (1, 2)
        or not isinstance(version, str)
        or re.fullmatch(r"\d+\.\d+\.\d+", version) is None
        or not isinstance(rootdir, str)
        or not rootdir.startswith("/")
        or not _rate(minimum)
        or not isinstance(cases, dict)
        or not 1 <= len(cases) <= 20_000
    ):
        raise ValueError("Unsupported pytest inventory profile")
    for console, xml in cases.items():
        if not _case_identity(console) or not _case_identity(xml):
            raise ValueError("Invalid console or JUnit case identity in inventory")
    if len(set(cases.values())) != len(cases):
        raise ValueError("Inventory repeats a JUnit case identity")
    skips = value.get("candidate_skips", {})
    policy = collection_policy(value["collection_policy"]) if value["schema_version"] == 2 else None
    if not isinstance(skips, dict):
        raise ValueError("Candidate skip rules must identify frozen test cases")
    for identity, rule in skips.items():
        if (
            identity not in cases.values()
            or not isinstance(rule, dict)
            or set(rule) != {"missing_file", "message"}
            or not isinstance(rule["message"], str)
            or not 0 < len(rule["message"]) <= 4096
            or not all(char.isprintable() for char in rule["message"])
        ):
            raise ValueError("Candidate skip rule is malformed or names an unknown case")
        path = relative_path(rule["missing_file"], workspace=True)
        if policy is None or any(
            excluded_directory("/".join(path.split("/")[:index]), policy)
            for index in range(1, len(path.split("/")) + 1)
        ):
            raise ValueError("Candidate skip rule refers to a path outside the capture scope")
    return Inventory(version, rootdir, minimum, cases, skips, policy)


def _case_identity(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= 4096
        and value.count("::") >= 1
        and value.strip() == value
        and all(char.isprintable() for char in value)
    )


def _console(raw: bytes, inventory: Inventory) -> dict[str, str]:
    lines = _text(raw).splitlines()
    platform = [line for line in lines if line.startswith("platform ")]
    if (
        [line for line in lines if line.startswith("rootdir: ")] != [f"rootdir: {inventory.rootdir}"]
        or len(platform) != 1
        or re.search(rf"\bpytest-{re.escape(inventory.pytest_version)}(?:,|\s|$)", platform[0]) is None
    ):
        raise ValueError("Pytest runtime profile differs from the frozen inventory")

    outcomes = {}
    for line in lines:
        match = PROGRESS.fullmatch(line)
        if match is None:
            continue
        identity = inventory.cases.get(match[1])
        if identity is None or identity in outcomes:
            raise ValueError("Console has an unexpected or repeated case")
        outcomes[identity] = match[2].lower()
    collected = [
        match[1] for line in lines if (match := re.fullmatch(r"collecting \.\.\. collected (\d+) items?", line))
    ]
    if outcomes.keys() != set(inventory.cases.values()) or collected != [str(len(outcomes))]:
        raise ValueError("Console did not report the full frozen case inventory")

    final = TERMINAL.fullmatch(lines[-1])
    if final is None:
        raise ValueError("Console did not produce a terminal pytest summary")
    counts = {}
    for entry in final[1].split(", "):
        match = re.fullmatch(r"(\d+) (passed|failed|skipped|warnings?)", entry)
        if match is None:
            raise ValueError("Console has an unsupported terminal outcome")
        label = match[2].removesuffix("s")
        if label in counts:
            raise ValueError("Console repeated a terminal outcome")
        counts[label] = int(match[1])
    observed = Counter(outcomes.values())
    if any(counts.get(label, 0) != observed[label] for label in ("passed", "failed", "skipped")):
        raise ValueError("Console terminal counts differ from its case outcomes")
    return outcomes


def _junit(raw: bytes) -> tuple[dict[str, str], dict[str, str]]:
    xml = _text(raw)
    if "<!DOCTYPE" in xml or "<!ENTITY" in xml:
        raise ValueError("JUnit evidence contains an unexpected XML declaration")
    root = ET.fromstring(xml)
    if root.tag != "testsuites" or len(root) != 1 or root[0].tag != "testsuite":
        raise ValueError("Expected one native pytest JUnit suite")
    suite = root[0]
    outcomes = {}
    skips = {}
    for node in suite:
        classname, name = node.get("classname", ""), node.get("name", "")
        identity = f"{classname}::{name}"
        if node.tag != "testcase" or not classname or not name or not _case_identity(identity) or identity in outcomes:
            raise ValueError("JUnit has an invalid or duplicate testcase identity")
        tags = [child.tag for child in node]
        if (
            set(tags) - {"failure", "skipped", "system-out", "system-err"}
            or sum(tags.count(tag) for tag in ("failure", "skipped")) > 1
        ):
            raise ValueError("JUnit testcase did not have an ordinary pass or failure")
        skip = node.find("skipped")
        if skip is not None:
            if skip.get("type") != "pytest.skip" or not skip.get("message"):
                raise ValueError("JUnit skip does not have a native pytest reason")
            outcomes[identity] = "skipped"
            skips[identity] = skip.attrib["message"]
        else:
            outcomes[identity] = "failed" if "failure" in tags else "passed"
    counts = {
        "tests": len(outcomes),
        "failures": sum(status == "failed" for status in outcomes.values()),
        "errors": 0,
        "skipped": len(skips),
    }
    if any(suite.get(label) != str(count) for label, count in counts.items()):
        raise ValueError("JUnit suite counts differ from its testcase outcomes")
    return outcomes, skips


def _submission(profile: Inventory, manifest: bytes | None, handoff: bytes | None) -> dict[str, Any] | None:
    if profile.collection_policy is None:
        if manifest is not None or handoff is not None:
            raise ValueError("Submission evidence requires a frozen collection policy")
        return None
    if manifest is None or handoff is None:
        raise ValueError("This profile requires the complete capture and reconstruction receipt")
    record = validate_manifest(strict_json(_text(manifest)), profile.collection_policy)
    receipt = strict_json(_text(handoff))
    expected = {
        "status": "grader_tree_rebuilt",
        "submission_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        **{key: record[key] for key in ("file_count", "directory_count", "total_bytes")},
    }
    if not isinstance(receipt, dict) or any(
        type(receipt.get(key)) is not type(value) or receipt[key] != value for key, value in expected.items()
    ):
        raise ValueError("Reconstruction receipt differs from the completed submission")
    return record


def verify_result(
    *,
    inventory: bytes,
    console: bytes,
    junit: bytes,
    publisher: bytes,
    exit_code: int,
    timed_out: bool = False,
    submission_manifest: bytes | None = None,
    handoff_result: bytes | None = None,
) -> dict[str, Any]:
    """Require a completed, ordinary pass/fail run before admitting the publisher score."""
    if type(exit_code) is not int or exit_code not in (0, 1) or timed_out:
        raise ValueError("Native pytest did not exit with an ordinary test verdict")
    profile = _inventory(inventory)
    submission = _submission(profile, submission_manifest, handoff_result)
    cases = _console(console, profile)
    xml_cases, skips = _junit(junit)
    if cases != xml_cases:
        raise ValueError("Console and JUnit individual outcomes disagree")
    for identity, message in skips.items():
        rule = profile.candidate_skips.get(identity)
        if (
            rule is None
            or submission is None
            or message != rule["message"]
            or rule["missing_file"].casefold()
            in {name.casefold() for name in [*submission["files"], *submission["directories"]]}
        ):
            raise ValueError("Skipped testcase lacks its declared candidate evidence")
    counts = Counter(cases.values())
    passed, failed, total = counts["passed"], counts["failed"], len(cases)
    if exit_code != int(failed != 0):
        raise ValueError("Native exit code disagrees with completed tests")
    score = passed / total
    verdict = strict_json(_text(publisher))
    if (
        not isinstance(verdict, dict)
        or verdict.get("level") != "L2"
        or verdict.get("method") != "unit_test"
        or not _rate(verdict.get("score"))
        or verdict["score"] != score
        or verdict.get("status") != ("passed" if score >= profile.min_pass_rate else "failed")
    ):
        raise ValueError("Publisher verdict differs from the native test outcomes")
    details = verdict.get("details")
    expected_counts = {"passed": passed, "failed": failed, "total": total, "skipped": len(skips), "errors": 0}
    if (
        not isinstance(details, dict)
        or any(type(details.get(key)) is not int or details[key] != count for key, count in expected_counts.items())
        or not _rate(details.get("min_pass_rate"))
        or details["min_pass_rate"] != profile.min_pass_rate
    ):
        raise ValueError("Publisher test counts or threshold differ from the frozen evidence")
    return {
        "status": "native_pytest_result_verified",
        "score": score,
        **expected_counts,
        "case_status": cases,
        "candidate_skip_evidence": {identity: profile.candidate_skips[identity] for identity in skips},
        "sha256": {
            key: hashlib.sha256(raw).hexdigest()
            for key, raw in (
                ("inventory", inventory),
                ("console", console),
                ("junit", junit),
                ("publisher", publisher),
                ("submission_manifest", submission_manifest),
                ("handoff_result", handoff_result),
            )
            if raw is not None
        },
    }


def _read(path: Path) -> bytes:
    with path.open("rb") as stream:
        return stream.read(MAX_REPORT_BYTES + 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--console", type=Path, required=True)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--publisher-result", type=Path, required=True)
    parser.add_argument("--exit-code", type=int, required=True)
    parser.add_argument("--timed-out", action="store_true")
    parser.add_argument("--submission-manifest", type=Path)
    parser.add_argument("--handoff-result", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = verify_result(
            inventory=_read(args.inventory),
            console=_read(args.console),
            junit=_read(args.junit),
            publisher=_read(args.publisher_result),
            exit_code=args.exit_code,
            timed_out=args.timed_out,
            submission_manifest=_read(args.submission_manifest) if args.submission_manifest else None,
            handoff_result=_read(args.handoff_result) if args.handoff_result else None,
        )
    except (ET.ParseError, OSError, ValueError) as exc:
        print(
            json.dumps({"status": "native_pytest_result_unverified", "score": None, "error": str(exc)}, sort_keys=True)
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

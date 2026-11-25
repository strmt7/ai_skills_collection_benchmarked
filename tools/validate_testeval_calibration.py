"""Validate TestEval calibration evidence and independent pytest outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from _trial_transcript import strict_json
from defusedxml import ElementTree as SafeXML
from defusedxml.common import DefusedXmlException

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "artifacts/research/2026-11-25/testeval-grader-calibration"
LIMIT = 2 * 1024 * 1024
DIGEST = re.compile(r"[a-f0-9]{64}")
COVERAGE = re.compile(r"^Average Line Coverage: ([^,\n]+), Average Branch Coverage: ([^\n]+)$", re.MULTILINE)
OUTCOMES = {"failure": "failures", "error": "errors", "skipped": "skipped"}


def _read(path: Path) -> bytes:
    with path.open("rb") as stream:
        content = stream.read(LIMIT + 1)
    if not content or len(content) > LIMIT:
        raise ValueError(f"Empty or oversized evidence file {path.name}")
    return content


def _evidence(root: Path, spec: dict[str, str], streams: dict[str, str] | None = None) -> bytes:
    name, expected = spec["file"], spec["sha256"]
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]*", name) or DIGEST.fullmatch(expected) is None:
        raise ValueError("Evidence requires a local filename and a SHA-256 digest")
    if streams is None:
        path = root / name
        if path.resolve(strict=True) != path or not path.is_file():
            raise ValueError(f"Evidence file is missing, linked or outside its directory {name}")
        content = _read(path)
    else:
        value = streams.get(name)
        if not isinstance(value, str) or not value:
            raise ValueError(f"Missing or empty archived evidence stream {name}")
        content = value.encode("utf-8")
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError(f"Evidence bytes changed for {name}")
    return content


def publisher_metrics(content: bytes) -> dict[str, float]:
    """Parse one complete native metric set without changing the publisher's scale."""
    text = content.decode("utf-8").replace("\r\n", "\n")
    syntax = re.findall(r"^Syntax Correctness: ([^\n]+)$", text, re.MULTILINE)
    executable = re.findall(r"^Executable Correctness: ([^\n]+)$", text, re.MULTILINE)
    coverage = COVERAGE.findall(text)
    if len(syntax) != 1 or len(executable) != 1 or len(coverage) != 1:
        raise ValueError("Native output requires one complete TestEval metric set")
    metrics = tuple(float(item) for item in (syntax[0], executable[0], *coverage[0]))
    if any(not math.isfinite(value) or not 0 <= value <= 1 for value in metrics):
        raise ValueError("Native TestEval metrics must be finite fractions")
    labels = ("syntax_correctness", "executable_correctness", "line_coverage", "branch_coverage")
    return dict(zip(labels, metrics, strict=True))


def independent_pytest(content: bytes, status_text: bytes, expected: list[str]) -> dict[str, int]:
    """Reconcile the frozen case set, JUnit case outcomes, suite counts and exit."""
    text = content.decode("utf-8")
    document = SafeXML.fromstring(text, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    if document.tag not in {"testsuite", "testsuites"}:
        raise ValueError("Independent pytest evidence must be JUnit XML")
    suites = [document] if document.tag == "testsuite" else document.findall("testsuite")
    counts = dict(tests=0, failures=0, errors=0, skipped=0)
    seen: set[str] = set()
    if not expected or len(expected) != len(set(expected)):
        raise ValueError("The contract requires distinct expected independent tests")
    for suite in suites:
        measured = dict.fromkeys(counts, 0)
        for case in suite.findall("testcase"):
            identifier = f"{case.attrib['classname']}::{case.attrib['name']}"
            if identifier in seen:
                raise ValueError(f"Duplicate independent test case {identifier}")
            seen.add(identifier)
            tags = [OUTCOMES[child.tag] for child in case if child.tag in OUTCOMES]
            if len(tags) > 1:
                raise ValueError(f"Conflicting independent outcomes for {identifier}")
            if tags:
                measured[tags[0]] += 1
            measured["tests"] += 1
        if any(int(suite.attrib[key]) != value for key, value in measured.items()):
            raise ValueError("JUnit totals disagree with the individual test cases")
        for key, count in measured.items():
            counts[key] += count
    if seen != set(expected) or len(document.findall(".//testcase")) != counts["tests"]:
        raise ValueError("Independent pytest collected a different case set")
    status = int(status_text.decode("ascii").strip())
    if status != int(bool(counts["failures"] + counts["errors"])):
        raise ValueError("Independent pytest exit disagrees with the recorded outcomes")
    passed = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    return {**counts, "passed": passed, "exit": status}


def inspect(directory: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Recompute the documented calibration from the complete pinned receipts."""
    root = (directory / "evidence").resolve(strict=True)
    if root.parent != directory.resolve(strict=True):
        raise ValueError("Evidence directory is outside the calibration")
    version = manifest["schema_version"]
    cases = manifest["cases"]
    if type(version) is not int or version not in {1, 2} or not isinstance(cases, dict) or not cases:
        raise ValueError("A versioned TestEval calibration manifest is required")
    streams = None
    if version == 2:
        streams = strict_json(_evidence(root, manifest["stream_archive"]).decode("utf-8"))
        required = {manifest["terminal"]["file"]}
        for spec in cases.values():
            required.update(spec[key]["file"] for key in ("publisher_stdout", "independent_junit", "independent_exit"))
        if not isinstance(streams, dict) or streams.keys() != required:
            raise ValueError("The archive must contain exactly the declared evidence streams")
    [terminal_count, terminal_exit] = _evidence(root, manifest["terminal"], streams).decode("ascii").splitlines()
    if (terminal_count, terminal_exit) != ("temporary_storage_removed=true", "exit=0"):
        raise ValueError("The model-free calibration did not complete cleanly")
    return {
        "schema_version": 1,
        "cases": {
            name: {
                "native_metrics": publisher_metrics(_evidence(root, spec["publisher_stdout"], streams)),
                "independent_pytest": independent_pytest(
                    _evidence(root, spec["independent_junit"], streams),
                    _evidence(root, spec["independent_exit"], streams),
                    spec["expected_independent_tests"],
                ),
            }
            for name, spec in cases.items()
        },
        "composite_score": None,
        "model_attempts": 0,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--directory", type=Path, default=DEFAULT, help="Calibration directory containing manifest.json"
    )
    parser.add_argument("--check", action="store_true", help="Verify the published result without writing")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable validation output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = inspect(args.directory, strict_json(_read(args.directory / "manifest.json").decode("utf-8")))
        if args.check:
            expected = strict_json(_read(args.directory / "result.json").decode("utf-8"))
            if expected != result:
                raise ValueError("Published TestEval calibration differs from the recorded evidence")
    except (OSError, ValueError, KeyError, TypeError, ElementTree.ParseError, DefusedXmlException) as error:
        if args.json:
            print(json.dumps({"ok": False, "error": str(error)}))
        else:
            print(str(error), file=sys.stderr)
        return 1
    if args.json or not args.check:
        print(json.dumps({"ok": True, "result": result}, indent=2))
    else:
        print(f"Verified {len(result['cases'])} TestEval calibration cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

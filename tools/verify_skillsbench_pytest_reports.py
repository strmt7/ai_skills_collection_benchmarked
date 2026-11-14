#!/usr/bin/env python3
"""Verify the pytest and CTRF 0.3.6 report profile used by a SkillsBench verifier."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any

from _trial_transcript import strict_json

PROFILE = "skillsbench-pytest-ctrf-0.3.6"
MAX_REPORT_BYTES = 512 * 1024
MAX_NODE_ID_CHARS = 4096
PROGRESS = re.compile(r"^\.\./verifier/(\S[^:]*::.+?) (PASSED|FAILED)[ \t]+\[[ \t]*\d+%\]$")
SHORT = re.compile(r"^(PASSED|FAILED) \.\./verifier/(.+)$")
TERMINAL = re.compile(r"=+ (.+?) in \d+(?:\.\d+)?s(?: \([0-9:]+\))? =+")
NODE = re.compile(r"[A-Za-z0-9_./-]+\.py::[A-Za-z0-9_:]+(?:\[.*\])?")


def _text(raw: bytes) -> str:
    if not 0 < len(raw) <= MAX_REPORT_BYTES:
        raise ValueError("Native report is empty or exceeds its size bound")
    return raw.decode("utf-8", errors="strict")


def _pytest_cases(raw: bytes, pytest_version: str) -> dict[str, str]:
    lines = _text(raw).splitlines()
    collected = [
        match[1] for line in lines if (match := re.fullmatch(r"collecting \.\.\. collected (\d+) items?", line))
    ]
    root = [line for line in lines if line.startswith("rootdir: ")]
    platforms = [line for line in lines if line.startswith("platform ")]
    plugins = [line for line in lines if line.startswith("plugins: ")]
    if (
        root != ["rootdir: /verifier"]
        or len(platforms) != 1
        or re.search(rf"\bpytest-{re.escape(pytest_version)}(?:,|\s|$)", platforms[0]) is None
        or len(plugins) != 1
        or "json-ctrf-0.3.6" not in plugins[0].removeprefix("plugins: ").split(", ")
    ):
        raise ValueError("Pytest output differs from the declared verifier profile")

    progress: dict[str, str] = {}
    for line in lines:
        match = PROGRESS.fullmatch(line)
        if match is None:
            continue
        node, status = match.groups()
        if (
            len(node) > MAX_NODE_ID_CHARS
            or NODE.fullmatch(node) is None
            or ".." in node.split("::", 1)[0].split("/")
            or node in progress
        ):
            raise ValueError("Pytest output has an invalid or duplicate case ID")
        progress[node] = status.lower()
    if not progress or collected != [str(len(progress))]:
        raise ValueError("Pytest case inventory is incomplete")

    summaries = [index for index, line in enumerate(lines) if re.fullmatch(r"=+ short test summary info =+", line)]
    terminal = TERMINAL.fullmatch(lines[-1]) if lines else None
    if len(summaries) != 1 or terminal is None:
        raise ValueError("Pytest output has no complete terminal summary")
    summary = {}
    for line in lines[summaries[0] + 1 : -1]:
        match = SHORT.fullmatch(line)
        if match is None:
            continue
        status, detail = match.groups()
        # A failure may append its diagnostic after " - ". The parameter ID
        # itself can contain that sequence, so use the recorded node IDs.
        selected = detail if detail in progress else None
        for separator in re.finditer(" - ", detail):
            if separator.start() > MAX_NODE_ID_CHARS:
                break
            candidate = detail[: separator.start()]
            if candidate in progress:
                if selected is not None:
                    raise ValueError("Pytest short summary has an ambiguous case ID")
                selected = candidate
        if selected is None or selected in summary:
            raise ValueError("Pytest short summary has an invalid or ambiguous case ID")
        summary[selected] = status.lower()
    if summary != progress:
        raise ValueError("Pytest progress and short summary disagree")

    counts = {}
    for entry in terminal[1].split(", "):
        count = re.fullmatch(r"(\d+) (passed|failed|warnings?)", entry)
        if count is None:
            raise ValueError("Pytest terminal summary contains an unsupported outcome")
        label = count[2].removesuffix("s") if count[2].startswith("warning") else count[2]
        if label in counts:
            raise ValueError("Pytest terminal summary repeats an outcome")
        counts[label] = int(count[1])
    observed = Counter(progress.values())
    if any(counts.get(status, 0) != observed[status] for status in ("passed", "failed")):
        raise ValueError("Pytest terminal counts disagree with its case outcomes")
    return progress


def _ctrf_cases(raw: bytes, pytest_version: str) -> dict[str, str]:
    report = strict_json(_text(raw))
    results = report.get("results") if isinstance(report, dict) else None
    if not isinstance(results, dict):
        raise ValueError("CTRF results are missing")
    tool = results.get("tool")
    summary, rows = results.get("summary"), results.get("tests")
    if not isinstance(tool, dict) or (tool.get("name"), tool.get("version")) != ("pytest", pytest_version):
        raise ValueError("CTRF tool differs from the declared pytest version")
    if not isinstance(rows, list) or not rows or not isinstance(summary, dict):
        raise ValueError("CTRF case outcomes are missing")
    outcomes: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("CTRF case must be an object")
        name, status = row.get("name"), row.get("status")
        if not isinstance(name, str) or not name or name in outcomes or status not in ("passed", "failed"):
            raise ValueError("CTRF has a duplicate or unsupported case outcome")
        outcomes[name] = status
    observed = Counter(outcomes.values())
    counts = {
        "tests": len(outcomes),
        "passed": observed["passed"],
        "failed": observed["failed"],
        "skipped": 0,
        "pending": 0,
        "other": 0,
    }
    if any(type(summary.get(key)) is not int or summary[key] != count for key, count in counts.items()):
        raise ValueError("CTRF summary disagrees with its case outcomes")
    return outcomes


def verify_reports(
    *,
    ctrf: bytes,
    pytest_output: bytes,
    reward: bytes,
    expected_node_ids_sha256: str,
    pytest_version: str,
) -> dict[str, Any]:
    """Retain the official grouped reward and independent per-case counts."""
    if re.fullmatch(r"[0-9a-f]{64}", expected_node_ids_sha256) is None:
        raise ValueError("An independently frozen, ordered case inventory digest is required")
    if re.fullmatch(r"[0-9]+(?:\.[0-9]+)+", pytest_version) is None:
        raise ValueError("An exact pytest version is required")
    pytest_cases = _pytest_cases(pytest_output, pytest_version)
    inventory = hashlib.sha256("\n".join(pytest_cases).encode("utf-8")).hexdigest()
    if inventory != expected_node_ids_sha256:
        raise ValueError("Pytest case inventory differs from the frozen digest")
    grouped = {node.split("[", 1)[0]: status for node, status in pytest_cases.items()}
    ctrf_cases = _ctrf_cases(ctrf, pytest_version)
    if grouped != ctrf_cases:
        raise ValueError("CTRF does not match the pinned reporter's last outcome per test function")

    value = _text(reward).strip()
    if re.fullmatch(r"(?:0|1)(?:\.\d{1,3})?", value) is None:
        raise ValueError("Native reward is missing or malformed")
    pytest_counts, ctrf_counts = Counter(pytest_cases.values()), Counter(ctrf_cases.values())
    if Decimal(value) != Decimal(str(round(ctrf_counts["passed"] / len(ctrf_cases), 3))):
        raise ValueError("Native reward disagrees with the grouped result")
    return {
        "profile": PROFILE,
        "official_grouped_reward": float(value),
        "ctrf": {"tests": len(ctrf_cases), "passed": ctrf_counts["passed"], "failed": ctrf_counts["failed"]},
        "pytest": {"tests": len(pytest_cases), "passed": pytest_counts["passed"], "failed": pytest_counts["failed"]},
        "ordered_node_ids_sha256": inventory,
        "report_sha256": {
            key: hashlib.sha256(raw).hexdigest()
            for key, raw in (("ctrf", ctrf), ("pytest_output", pytest_output), ("reward", reward))
        },
    }


def _read_report(path: Path) -> bytes:
    with path.open("rb") as stream:
        return stream.read(MAX_REPORT_BYTES + 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ctrf", type=Path, required=True)
    parser.add_argument("--pytest-output", type=Path, required=True)
    parser.add_argument("--reward", type=Path, required=True)
    parser.add_argument("--expected-node-ids-sha256", required=True)
    parser.add_argument("--pytest-version", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = verify_reports(
            ctrf=_read_report(args.ctrf),
            pytest_output=_read_report(args.pytest_output),
            reward=_read_report(args.reward),
            expected_node_ids_sha256=args.expected_node_ids_sha256,
            pytest_version=args.pytest_version,
        )
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "unscored", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "verified_reports", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

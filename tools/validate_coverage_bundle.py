"""Validate measured Python tooling reports before a Codecov upload."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from _trial_transcript import strict_json
from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

ROOT = Path(__file__).resolve().parents[1]
MAX_REPORT_BYTES = 16 * 1024 * 1024
MAX_RECEIPT_BYTES = 2 * 1024 * 1024
SHARD_RECEIPT = "coverage-shard.json"
LANE_PATTERN = re.compile(r"coverage-[a-z0-9][a-z0-9.-]{0,95}")


def git_output(root: Path, *arguments: str) -> bytes:
    """Resolve source information in the checkout being measured."""
    return subprocess.run(
        ["git", "-c", "core.longpaths=true", *arguments],
        cwd=root,
        capture_output=True,
        check=True,
        timeout=30,
    ).stdout


def source_revision(root: Path) -> str:
    """Read the exact checkout commit."""
    revision = git_output(root, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip()
    if not re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", revision):
        raise ValueError("coverage checkout revision is not a Git object ID")
    return revision


class CoverageElement(Protocol):
    """The element operations needed to inspect a Cobertura report."""

    @property
    def tag(self) -> object:
        """Return the XML element tag."""
        ...

    @property
    def attrib(self) -> dict[str, str]:
        """Return the element's attribute values."""
        ...

    def findall(self, path: str) -> Sequence[CoverageElement]:
        """Return descendants matching the requested element path."""
        ...


def _report_document(path: Path, directory: Path) -> tuple[bytes, CoverageElement]:
    """Read a bounded report and reject unsafe paths or XML declarations."""
    name = path.as_posix()
    if any(ord(char) < 32 or ord(char) == 127 or char == "," for char in name):
        raise ValueError("report path cannot be represented safely in the upload file list")
    if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
        raise ValueError("linked or escaping report")
    with path.open("rb") as stream:
        raw = stream.read(MAX_REPORT_BYTES + 1)
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError("report exceeds 16 MiB")
    text = raw.decode("utf-8")
    if "\x00" in text:
        raise ValueError("NUL bytes are not coverage data")
    try:
        document = ET.fromstring(text, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    except DefusedXmlException:
        raise ValueError("DTD/entity declarations are not coverage data") from None
    if document.tag != "coverage":
        raise ValueError("Cobertura coverage document required")
    return raw, document


def _source_name(name: str) -> str:
    """Normalize coverage.py separators and reject path aliases or traversal."""
    name = name.replace("\\", "/")
    if (
        not name
        or ":" in name
        or name.startswith("/")
        or ".." in PurePosixPath(name).parts
        or PurePosixPath(name).as_posix() != name
        or any(ord(char) < 32 or ord(char) == 127 for char in name)
    ):
        raise ValueError("noncanonical coverage source path")
    return name if name.startswith("tools/") else "tools/" + name


def _observed_sources(root: Path, document: CoverageElement) -> tuple[dict[str, str], int, int]:
    """Bind each unique source and observed line to its actual file bytes."""
    classes = document.findall("./packages/package/classes/class")
    if not classes:
        raise ValueError("coverage classes missing")
    sources: dict[str, str] = {}
    resolved_sources: set[Path] = set()
    total = covered = 0
    for item in classes:
        name = item.attrib["filename"]
        relative = _source_name(name)
        if relative in sources:
            raise ValueError(f"duplicate coverage source: {name}")
        source = root / relative
        resolved = source.resolve()
        if not source.is_file() or not resolved.is_relative_to((root / "tools").resolve()):
            raise ValueError(f"coverage source is absent or outside tools: {name}")
        if resolved in resolved_sources:
            raise ValueError(f"duplicate coverage source: {name}")
        resolved_sources.add(resolved)
        source_bytes = source.read_bytes()
        line_count = len(source_bytes.splitlines())
        seen: set[int] = set()
        for line in item.findall("./lines/line"):
            number, hits = int(line.attrib["number"]), int(line.attrib["hits"])
            if not 1 <= number <= line_count or hits < 0 or number in seen:
                raise ValueError(f"invalid or duplicate observed line in {name}")
            seen.add(number)
            total += 1
            covered += hits > 0
        sources[relative] = hashlib.sha256(source_bytes).hexdigest()
    return sources, total, covered


def _check_metrics(document: CoverageElement, total: int, covered: int) -> None:
    """Compare declared line metrics with the report's distinct observations."""
    declared_total = int(document.attrib["lines-valid"])
    declared_covered = int(document.attrib["lines-covered"])
    rate = float(document.attrib["line-rate"])
    if (
        total < 1
        or declared_total != total
        or declared_covered != covered
        or not math.isfinite(rate)
        or not 0 <= rate <= 1
        or abs(rate - covered / total) > 0.000050000001
    ):
        raise ValueError("declared coverage metrics disagree with observed lines")


def inspect_report(root: Path, path: Path, directory: Path) -> dict[str, Any]:
    """Validate a native report and identify its observed source bytes."""
    raw, document = _report_document(path, directory)
    sources, total, covered = _observed_sources(root, document)
    _check_metrics(document, total, covered)
    return {
        "path": path.as_posix(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "source_sha256": sources,
        "native_metrics": document.attrib,
    }


def shard_receipt(revision: str, lane: str, report: dict[str, Any]) -> dict[str, Any]:
    """Describe the source snapshot and report from a successful pytest lane."""
    if not LANE_PATTERN.fullmatch(lane):
        raise ValueError(f"invalid coverage matrix lane: {lane!r}")
    return {
        "schema_version": 1,
        "source_revision": revision,
        "lane": lane,
        "report_sha256": report["sha256"],
        "source_sha256": report["source_sha256"],
    }


def _verify_receipt(path: Path, directory: Path, expected: dict[str, Any]) -> str:
    receipt = path.with_name(SHARD_RECEIPT)
    if not receipt.is_file():
        raise ValueError("producer receipt missing")
    if receipt.is_symlink() or not receipt.resolve().is_relative_to(directory.resolve()):
        raise ValueError("linked or escaping producer receipt")
    with receipt.open("rb") as stream:
        raw = stream.read(MAX_RECEIPT_BYTES + 1)
    if len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError("producer receipt exceeds 2 MiB")
    actual = strict_json(raw.decode("utf-8"))
    if not isinstance(actual, dict) or type(actual.get("schema_version")) is not int or actual != expected:
        raise ValueError("producer receipt disagrees with the revision, matrix lane, report or measured sources")
    return hashlib.sha256(raw).hexdigest()


def validate_bundle(
    root: Path,
    directory: Path,
    expected_reports: int,
    revision: str,
    *,
    expected_lanes: Sequence[str] = (),
) -> tuple[dict[str, Any], list[str]]:
    """Validate every report and collect errors without discarding valid reports."""
    errors = []
    reports = []
    expected_sources: dict[str, str] | None = None
    paths = sorted(directory.glob("*/coverage.xml"))
    if expected_reports < 1 or len(paths) != expected_reports:
        errors.append(f"Expected {expected_reports} coverage reports, found {len(paths)}")
    if expected_lanes:
        lanes = {path.parent.name for path in paths}
        if len(set(expected_lanes)) != expected_reports or lanes != set(expected_lanes):
            errors.append("Coverage reports must match the declared matrix lanes")
    for path in paths:
        try:
            record = inspect_report(root, path, directory)
            lane = path.parent.name
            record["producer_receipt_sha256"] = _verify_receipt(path, directory, shard_receipt(revision, lane, record))
            sources = record["source_sha256"]
            if expected_sources is None:
                expected_sources = sources
            elif sources != expected_sources:
                raise ValueError("coverage source set differs across reports")
            reports.append(record)
        except (OSError, ValueError, KeyError, ET.ParseError) as error:
            errors.append(f"{path.name!r} in {path.parent.name!r}: {error}")
    return {
        "measurement_kind": "python_tooling_test_coverage",
        "source_scope": "tools/",
        "source_revision": revision,
        "agent_performance_claim": False,
        "reports": reports,
    }, errors


def build_parser() -> argparse.ArgumentParser:
    """Define the coverage bundle validation interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--expected-reports", type=int, required=True)
    parser.add_argument("--expected-lanes", nargs="+", default=())
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Validate the bundle and publish only verified upload paths."""
    args = build_parser().parse_args(argv)
    revision = None
    errors: list[str] = []
    report: dict[str, Any] = {"reports": []}
    try:
        revision = source_revision(args.root)
        report, errors = validate_bundle(
            args.root, args.directory, args.expected_reports, revision, expected_lanes=args.expected_lanes
        )
        if not errors:
            if args.check:
                if json.loads(args.output.read_text(encoding="utf-8")) != report:
                    errors.append("Coverage bundle receipt differs from current reports or sources")
            else:
                args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
            if args.github_output and not errors:
                with args.github_output.open("a", encoding="utf-8", newline="\n") as stream:
                    stream.write("files=" + ",".join(item["path"] for item in report["reports"]) + "\n")
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
        errors.append(str(error))
    print(json.dumps({"errors": errors, "reports": len(report["reports"]), "source_revision": revision}))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())

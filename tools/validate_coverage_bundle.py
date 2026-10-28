"""Validate measured Python tooling reports before a Codecov upload."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
MAX_REPORT_BYTES = 16 * 1024 * 1024


def _report_document(path: Path, directory: Path) -> tuple[bytes, ET.Element]:
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
    if "\x00" in text or "<!DOCTYPE" in text or "<!ENTITY" in text:
        raise ValueError("DTD/entity declarations are not coverage data")
    document = ET.fromstring(text)
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


def _observed_sources(root: Path, document: ET.Element) -> tuple[dict[str, str], int, int]:
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


def _check_metrics(document: ET.Element, total: int, covered: int) -> None:
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


def validate_bundle(root: Path, directory: Path, expected_reports: int) -> tuple[dict, list[str]]:
    """Validate every report and collect errors without discarding valid reports."""
    errors = []
    reports = []
    expected_sources: dict[str, str] | None = None
    paths = sorted(directory.glob("*/coverage.xml"))
    if expected_reports < 1 or len(paths) != expected_reports:
        errors.append(f"Expected {expected_reports} coverage reports, found {len(paths)}")
    for path in paths:
        try:
            raw, document = _report_document(path, directory)
            sources, total, covered = _observed_sources(root, document)
            _check_metrics(document, total, covered)
            if expected_sources is None:
                expected_sources = sources
            elif sources != expected_sources:
                raise ValueError("coverage source set differs across reports")
            reports.append(
                {
                    "path": path.as_posix(),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "source_sha256": sources,
                    "native_metrics": document.attrib,
                }
            )
        except (OSError, ValueError, KeyError, ET.ParseError) as error:
            errors.append(f"{path.name!r} in {path.parent.name!r}: {error}")
    return {
        "measurement_kind": "python_tooling_test_coverage",
        "source_scope": "tools/",
        "agent_performance_claim": False,
        "reports": reports,
    }, errors


def build_parser() -> argparse.ArgumentParser:
    """Define the coverage bundle validation interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--expected-reports", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Validate the bundle and publish only verified upload paths."""
    args = build_parser().parse_args(argv)
    report, errors = validate_bundle(args.root, args.directory, args.expected_reports)
    revision = None
    try:
        revision = subprocess.run(
            ["git", "-c", "core.longpaths=true", "rev-parse", "--verify", "HEAD"],
            cwd=args.root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        ).stdout.strip()
        report["source_revision"] = revision
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

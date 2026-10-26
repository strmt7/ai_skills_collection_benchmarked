"""Validate measured Python tooling reports before a Codecov upload."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate_bundle(root: Path, directory: Path, expected_reports: int) -> tuple[dict, list[str]]:
    errors = []
    reports = []
    paths = sorted(directory.glob("*/coverage.xml"))
    if expected_reports < 1 or len(paths) != expected_reports:
        errors.append(f"Expected {expected_reports} coverage reports, found {len(paths)}")
    for path in paths:
        try:
            if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
                raise ValueError("linked or escaping report")
            if path.stat().st_size > 16 * 1024 * 1024:
                raise ValueError("report exceeds 16 MiB")
            raw = path.read_bytes()
            text = raw.decode("utf-8")
            if "\x00" in text or "<!DOCTYPE" in text or "<!ENTITY" in text:
                raise ValueError("DTD/entity declarations are not coverage data")
            document = ET.fromstring(text)
            if document.tag != "coverage" or int(document.attrib["lines-valid"]) < 1:
                raise ValueError("nonempty Cobertura coverage document required")
            classes = document.findall("./packages/package/classes/class")
            if not classes:
                raise ValueError("coverage classes missing")
            sources = {}
            for item in classes:
                name = item.attrib["filename"].replace("\\", "/")
                if not name or ":" in name or name.startswith("/") or ".." in Path(name).parts:
                    raise ValueError("noncanonical coverage source path")
                relative = name if name.startswith("tools/") else "tools/" + name
                source = root / relative
                if not source.is_file() or not source.resolve().is_relative_to((root / "tools").resolve()):
                    raise ValueError(f"coverage source is absent or outside tools: {name}")
                source_bytes = source.read_bytes()
                line_count = len(source_bytes.splitlines())
                for line in item.findall("./lines/line"):
                    if not 1 <= int(line.attrib["number"]) <= line_count or int(line.attrib["hits"]) < 0:
                        raise ValueError(f"invalid observed line in {name}")
                sources[relative] = hashlib.sha256(source_bytes).hexdigest()
            reports.append(
                {
                    "path": path.as_posix(),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "source_sha256": sources,
                    "native_metrics": document.attrib,
                }
            )
        except (OSError, ValueError, KeyError, ET.ParseError) as error:
            errors.append(f"{path.name} in {path.parent.name}: {error}")
    return {
        "measurement_kind": "python_tooling_test_coverage",
        "source_scope": "tools/",
        "agent_performance_claim": False,
        "reports": reports,
    }, errors


def build_parser() -> argparse.ArgumentParser:
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

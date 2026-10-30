"""Control the source-bound Flink comparator CLI with a pinned development reference."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

COMPARATOR_SHA256 = "067dd0cc319aeedfb7b831b44b9caf2e9f42d8ba1dcd768eab4324c164791438"
REFERENCE_SHA256 = "54a97eff4388b2a195f047a37250a5bad0648c6f15437bbe35acac3cf610828c"


def read_pinned(path: Path, digest: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"Unexpected input bytes: {path.name}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparator", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    args = parser.parse_args()
    comparator = read_pinned(args.comparator, COMPARATOR_SHA256)
    lines = read_pinned(args.reference, REFERENCE_SHA256).decode("utf-8").splitlines()
    if len(lines) != 644:
        raise ValueError("Unexpected reference record count")
    reference = "\n".join(lines) + "\n"
    cases = {
        "matching": reference,
        "reversed": "\n".join(reversed(lines)) + "\n",
        "duplicate": reference + lines[0] + "\n",
        "missing": "\n".join(lines[1:]) + "\n",
        "extra": reference + "(-999999999999,1)\n",
    }
    with tempfile.TemporaryDirectory(prefix="flink-comparator-control-") as temporary:
        root = Path(temporary)
        tool = root / "compare.py"
        tool.write_bytes(comparator)
        expected = root / "expected.txt"
        expected.write_text(reference, encoding="utf-8")
        actual = root / "actual.txt"
        results = {}
        for name, content in cases.items():
            actual.write_text(content, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(tool), "--expected", str(expected), "--actual", str(actual), "--json"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            report = json.loads(result.stdout)
            if result.returncode not in (0, 1) or report["passed"] != (result.returncode == 0):
                raise ValueError(f"Invalid CLI result for {name}")
            results[name] = report["passed"]
    if results != {"matching": True, "reversed": True, "duplicate": False, "missing": False, "extra": False}:
        raise ValueError(f"Unexpected results: {results}")
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "python": platform.python_version(),
                "comparator_sha256": COMPARATOR_SHA256,
                "reference_sha256": REFERENCE_SHA256,
                "reference_records": len(lines),
                "accepted": results,
                "flink_job_executed": False,
                "model_scored": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Exercise the pinned Flink verifier's output comparison with controlled lines."""

from __future__ import annotations

import argparse
import builtins
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import platform
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

INPUTS = {
    "verifier": "5d1567a460400cbfc2b2d2ce8d75e1aa7b1d7da5892d1ee99a58eb0f4d6ec36b",
    "expected": "54a97eff4388b2a195f047a37250a5bad0648c6f15437bbe35acac3cf610828c",
}
ACTUAL_PATH = "/app/workspace/out.txt"


def pinned(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Unexpected input bytes: {path.name}")
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--expected", type=Path, required=True)
    args = parser.parse_args()
    if not __debug__:
        raise ValueError("Run without Python optimization so upstream assertions execute")
    data = {name: pinned(getattr(args, name), sha) for name, sha in INPUTS.items()}
    lines = data["expected"].decode("utf-8").strip().splitlines()
    tuples = [re.fullmatch(r"\((-?\d+),\s*(\d+)\)", line) for line in lines]
    if len(lines) != 644 or any(item is None for item in tuples):
        raise ValueError("Unexpected expected-output format")
    if len(set(lines)) != 644 or len({item.group(1) for item in tuples if item}) != 644:
        raise ValueError("Expected output no longer has one unique record per job")
    extra = "(-999999999999,1)"
    if extra in lines:
        raise ValueError("Synthetic extra line collides with expected output")
    temp_root = Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix="skillsbench-flink-control-", dir=temp_root) as tmp:
        root = Path(tmp).resolve()
        if not root.is_relative_to(temp_root):
            raise ValueError("Unexpected temporary path")
        verifier = root / "test_outputs.py"
        verifier.write_bytes(data["verifier"])
        (root / "out_lsj_001a.txt").write_bytes(data["expected"])
        spec = importlib.util.spec_from_file_location("skillsbench_flink_dev_verifier", verifier)
        if spec is None or spec.loader is None:
            raise ValueError("Cannot load the pinned verifier")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        original_isfile = os.path.isfile
        original_open = builtins.open
        actual = root / "controlled-output.txt"

        def isfile(path):
            return True if str(path) == ACTUAL_PATH else original_isfile(path)

        def open_file(path, *open_args, **open_kwargs):
            return original_open(actual if str(path) == ACTUAL_PATH else path, *open_args, **open_kwargs)

        variants = {
            "matching": lines,
            "duplicate": [*lines, lines[0]],
            "missing": lines[1:],
            "extra": [*lines, extra],
        }
        cases = {}
        for name, values in variants.items():
            actual.write_text("\n".join(values) + "\n", encoding="utf-8")
            with (
                patch.object(module.os.path, "isfile", side_effect=isfile),
                patch("builtins.open", side_effect=open_file),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                try:
                    module.test_output_matches_expected()
                except AssertionError:
                    accepted = False
                else:
                    accepted = True
            cases[name] = {"lines": len(values), "accepted": accepted}
    if {name: case["accepted"] for name, case in cases.items()} != {
        "matching": True,
        "duplicate": True,
        "missing": False,
        "extra": False,
    }:
        raise AssertionError(f"Pinned verifier outcomes changed: {cases}")
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "python": platform.python_version(),
                "input_sha256": INPUTS,
                "expected_records": len(lines),
                "expected_unique_jobs": 644,
                "flink_job_executed": False,
                "model_scored": False,
                "cases": cases,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

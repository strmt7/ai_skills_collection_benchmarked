"""Run the comparison against the pinned public reference and synthetic outputs."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Any

import compare
import numpy as np


def archive(**arrays: Any) -> bytes:
    output = io.BytesIO()
    np.savez(output, **arrays)
    return output.getvalue()


def run(reference_path: Path) -> dict[str, Any]:
    reference = reference_path.read_bytes()
    if hashlib.sha256(reference).hexdigest() != compare.REFERENCE_SHA256:
        raise ValueError("Reference does not match the pinned public development artifact")
    with np.load(io.BytesIO(reference), allow_pickle=False) as data:
        expected = data["losses"].copy()
    previous = archive(losses=expected)
    regenerated = {
        "correct": archive(losses=expected),
        "wrong_values": archive(losses=np.full(expected.shape, 42.0)),
        "wrong_key": archive(other=expected),
        "broadcastable_shape": archive(losses=expected[:, None]),
        "nonfinite": archive(losses=np.full(expected.shape, np.nan)),
    }
    if compare.compare(reference, previous)["status"] != "matching":
        raise ValueError("The prior correct output did not match")
    cases = {name: compare.compare(reference, output) for name, output in regenerated.items()}
    expected_results = {
        "correct": ("matching", "within_tolerance"),
        "wrong_values": ("nonmatching", "values_outside_tolerance"),
        "wrong_key": ("nonmatching", "missing_or_duplicate_losses"),
        "broadcastable_shape": ("nonmatching", "shape_mismatch"),
        "nonfinite": ("nonmatching", "nonfinite_values"),
    }
    if {name: (value["status"], value["reason"]) for name, value in cases.items()} != expected_results:
        raise ValueError("A component comparison differed from its independently stated expectation")
    with tempfile.TemporaryDirectory(prefix="simpo-postrun-") as temporary:
        root = Path(temporary)
        ref, output = root / "reference.npz", root / "generated.npz"
        ref.write_bytes(reference)
        output.write_bytes(previous)
        for payload, code, status in (
            (previous, 0, "matching"),
            (regenerated["wrong_values"], 1, "nonmatching"),
            (None, 2, "unavailable"),
        ):
            if payload is None:
                output.unlink()
            else:
                output.write_bytes(payload)
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                actual_code = compare.main(["--reference", str(ref), "--generated", str(output)])
            if actual_code != code or json.loads(stream.getvalue())["status"] != status:
                raise ValueError("CLI status did not match the component comparison")
    return {
        "schema_version": 1,
        "platform": platform.system(),
        "python": platform.python_version(),
        "numpy": version("numpy"),
        "reference_sha256": compare.REFERENCE_SHA256,
        "comparator_sha256": hashlib.sha256(Path(compare.__file__).read_bytes()).hexdigest(),
        "reference_shape": list(expected.shape),
        "prior_correct_sha256": hashlib.sha256(previous).hexdigest(),
        "regenerated_cases": cases,
        "subprocess_or_regeneration_executed": False,
        "actual_generation_proven": False,
        "benchmark_harness_executed": False,
        "agent_performance_tested": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run(args.reference)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

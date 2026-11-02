"""Compare captured SimPO loss archives; this does not run or score an agent."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import numpy as np

SHAPE = (100,)
RTOL = 1e-5
ATOL = 1e-6
REFERENCE_SHA256 = "162e3cd015afa98503a8419c6955523ba7c4401cd50f34e7d8f7e601e8489d2c"


class ReferenceError(ValueError):
    """The pinned reference could not be used; no comparison can be made."""


def _losses(content: bytes) -> np.ndarray[Any, Any]:
    """Read one floating-point loss vector from an in-memory NPZ snapshot."""
    try:
        loaded = np.load(io.BytesIO(content), allow_pickle=False)
    except (OSError, EOFError, ValueError, zipfile.BadZipFile) as exc:
        raise ValueError("invalid_archive") from exc
    if not isinstance(loaded, np.lib.npyio.NpzFile):
        raise ValueError("not_npz")
    with loaded:
        if loaded.files.count("losses") != 1:
            raise ValueError("missing_or_duplicate_losses")
        try:
            values = loaded["losses"]
        except (OSError, EOFError, KeyError, ValueError, zipfile.BadZipFile) as exc:
            raise ValueError("invalid_archive") from exc
    if values.shape != SHAPE:
        raise ValueError("shape_mismatch")
    if values.dtype.kind != "f" or values.dtype.itemsize > 8:
        raise ValueError("unsupported_dtype")
    if not np.isfinite(values).all():
        raise ValueError("nonfinite_values")
    return values.astype(np.float64)


def compare(reference: bytes, generated: bytes, *, expected_reference_sha256: str = REFERENCE_SHA256) -> dict[str, Any]:
    """Compare two already-captured snapshots, with tolerance relative to the reference."""
    if len(expected_reference_sha256) != 64 or any(c not in "0123456789abcdef" for c in expected_reference_sha256):
        raise ReferenceError("invalid_reference_digest")
    reference_sha = hashlib.sha256(reference).hexdigest()
    if reference_sha != expected_reference_sha256:
        raise ReferenceError("reference_digest_mismatch")
    try:
        expected = _losses(reference)
    except ValueError as exc:
        raise ReferenceError(f"invalid_reference: {exc}") from exc
    result: dict[str, Any] = {
        "reference_sha256": reference_sha,
        "generated_sha256": hashlib.sha256(generated).hexdigest(),
        "shape": list(SHAPE),
        "rtol": RTOL,
        "atol": ATOL,
        "generation_proven": False,
        "agent_performance_tested": False,
        "status": "nonmatching",
        "reason": "",
    }
    try:
        actual = _losses(generated)
    except ValueError as exc:
        result["reason"] = str(exc)
        return result
    if np.allclose(actual, expected, rtol=RTOL, atol=ATOL, equal_nan=False):
        result.update(status="matching", reason="within_tolerance")
    else:
        result["reason"] = "values_outside_tolerance"
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--generated", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        reference = args.reference.read_bytes()
    except OSError as exc:
        print(json.dumps({"status": "unavailable", "reason": "reference_unavailable", "error": str(exc)}))
        return 2
    try:
        generated = args.generated.read_bytes()
    except OSError as exc:
        print(json.dumps({"status": "unavailable", "reason": "generated_unavailable", "error": str(exc)}))
        return 2
    try:
        result = compare(reference, generated)
    except ReferenceError as exc:
        print(json.dumps({"status": "unavailable", "reason": str(exc)}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "matching" else 1


if __name__ == "__main__":
    raise SystemExit(main())

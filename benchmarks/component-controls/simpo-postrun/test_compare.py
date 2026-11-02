"""Controls for the post-regeneration comparison, independent of skill text."""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

import compare as target
import numpy as np
import pytest


def archive(**arrays: Any) -> bytes:
    result = io.BytesIO()
    np.savez(result, **arrays)
    return result.getvalue()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def reference() -> bytes:
    return archive(losses=np.linspace(0.01, 1.0, 100, dtype=np.float32))


def check(reference: bytes, generated: bytes) -> dict:
    return target.compare(reference, generated, expected_reference_sha256=sha(reference))


def test_new_output_is_compared_even_if_the_old_output_was_correct(reference: bytes):
    old_output = reference
    new_output = archive(losses=np.full(100, 42.0))
    assert check(reference, old_output)["status"] == "matching"
    result = check(reference, new_output)
    assert result["status"] == "nonmatching"
    assert result["reason"] == "values_outside_tolerance"
    assert result["generated_sha256"] == sha(new_output) != sha(old_output)


@pytest.mark.parametrize(
    "generated,reason",
    [
        (archive(other=np.zeros(100)), "missing_or_duplicate_losses"),
        (archive(losses=np.zeros((100, 1))), "shape_mismatch"),
        (archive(losses=np.array([], dtype=float)), "shape_mismatch"),
        (archive(losses=np.full(100, np.nan)), "nonfinite_values"),
        (archive(losses=np.full(100, np.inf)), "nonfinite_values"),
        (archive(losses=np.zeros(100, dtype=np.int64)), "unsupported_dtype"),
        (archive(losses=np.zeros(100, dtype=np.complex128)), "unsupported_dtype"),
        (b"not an archive", "invalid_archive"),
    ],
)
def test_invalid_generated_archives_are_not_matches(reference: bytes, generated: bytes, reason: str):
    result = check(reference, generated)
    assert result["status"] == "nonmatching"
    assert result["reason"] == reason
    assert result["generated_sha256"] == sha(generated)


def test_npy_is_not_accepted_as_an_npz_archive(reference: bytes):
    buffer = io.BytesIO()
    np.save(buffer, np.zeros(100))
    assert check(reference, buffer.getvalue())["reason"] == "not_npz"


def test_duplicate_loss_entries_are_not_accepted(reference: bytes):
    data = io.BytesIO()
    np.save(data, np.zeros(100))
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w") as bundle:
        bundle.writestr("losses.npy", data.getvalue())
        with pytest.warns(UserWarning, match="Duplicate name"):
            bundle.writestr("losses.npy", data.getvalue())
    assert check(reference, result.getvalue())["reason"] == "missing_or_duplicate_losses"


def test_shape_is_checked_before_numpy_broadcasting():
    reference = archive(losses=np.ones(100))
    broadcastable = archive(losses=np.ones((100, 1)))
    assert np.allclose(np.ones((100, 1)), np.ones(100))
    assert check(reference, broadcastable)["reason"] == "shape_mismatch"


def test_tolerance_is_relative_to_reference_not_generated_values():
    expected = np.full(100, 100.0)
    actual = np.full(100, 100.001001005)
    reference = archive(losses=expected)
    assert np.allclose(expected, actual, rtol=target.RTOL, atol=target.ATOL)
    assert not np.allclose(actual, expected, rtol=target.RTOL, atol=target.ATOL)
    assert check(reference, archive(losses=actual))["reason"] == "values_outside_tolerance"
    assert check(reference, archive(losses=expected + 0.0005))["status"] == "matching"


@pytest.mark.parametrize(
    "invalid_reference",
    [
        b"broken",
        archive(other=np.zeros(100)),
        archive(losses=np.zeros((100, 1))),
        archive(losses=np.full(100, np.nan)),
        archive(losses=np.zeros(100, dtype=int)),
    ],
)
def test_invalid_reference_is_unavailable_not_a_candidate_result(invalid_reference: bytes):
    with pytest.raises(target.ReferenceError, match="invalid_reference"):
        target.compare(invalid_reference, invalid_reference, expected_reference_sha256=sha(invalid_reference))


def test_reference_digest_must_be_valid_and_match(reference: bytes):
    with pytest.raises(target.ReferenceError, match="invalid_reference_digest"):
        target.compare(reference, reference, expected_reference_sha256="not-a-digest")
    with pytest.raises(target.ReferenceError, match="reference_digest_mismatch"):
        target.compare(reference, reference, expected_reference_sha256="0" * 64)


def test_cli_distinguishes_missing_input_from_comparison_result(tmp_path: Path):
    script = Path(target.__file__)
    ref, generated = tmp_path / "reference.npz", tmp_path / "generated.npz"
    ref.write_bytes(b"not the pinned reference")
    process = subprocess.run(
        [sys.executable, str(script), "--reference", str(ref), "--generated", str(generated)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 2
    assert json.loads(process.stdout)["status"] == "unavailable"
    generated.write_bytes(b"anything")
    process = subprocess.run(
        [sys.executable, str(script), "--reference", str(ref), "--generated", str(generated)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 2
    assert json.loads(process.stdout)["reason"] == "reference_digest_mismatch"

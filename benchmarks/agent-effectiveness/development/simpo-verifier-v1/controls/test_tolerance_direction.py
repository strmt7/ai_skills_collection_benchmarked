"""Check the explicitly required allclose argument order at asymmetric boundaries."""

from __future__ import annotations

import numpy as np
import pytest

pytest_plugins = ("test_acceptance",)


@pytest.mark.parametrize("phase", ["initial", "regenerated"])
@pytest.mark.parametrize("delta,accepted", [(6.00003e-6, True), (-5.99997e-6, False)])
def test_asymmetric_tolerance(exercise, tmp_path, monkeypatch, phase, delta, accepted):
    with np.load(tmp_path / "loss.npz", allow_pickle=False) as data:
        expected = data["losses"].copy()
    output = expected.copy()
    output[2] += delta
    assert bool(np.allclose(expected, output, rtol=1e-5, atol=1e-6)) is accepted
    assert bool(np.allclose(output, expected, rtol=1e-5, atol=1e-6)) is not accepted

    if phase == "initial":
        np.savez(tmp_path / "output.npz", losses=output)
    else:
        save = np.savez

        def save_with_boundary(path, **arrays):
            if str(path).endswith("output.npz") and "losses" in arrays:
                arrays["losses"] = output
            return save(path, **arrays)

        monkeypatch.setattr(np, "savez", save_with_boundary)

    if accepted:
        exercise("correct")
    else:
        with pytest.raises(AssertionError):
            exercise("correct")

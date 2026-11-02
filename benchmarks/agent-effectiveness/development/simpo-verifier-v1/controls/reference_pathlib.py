"""Development-only reference candidate for controlled grading calibration."""

import os
import sys
import time
from os.path import exists
from pathlib import Path
from subprocess import run

import numpy as np


def test_outputs():
    gt_path = os.path.join(os.getcwd(), "loss.npz")
    output = Path("/root/loss.npz")
    env_path = "/root/python_info.txt"
    assert exists(gt_path), "Missing ground truth"
    assert exists(output), "Missing output"
    assert exists(env_path), "Missing environment info"
    with open(env_path, encoding="utf-8") as stream:
        assert "python 3.10" in stream.read().lower(), "Wrong Python version"
    with np.load(gt_path, allow_pickle=False) as archive:
        assert "losses" in archive.files, "Reference missing losses"
        expected = archive["losses"].copy()
    with np.load(output, allow_pickle=False) as archive:
        assert "losses" in archive.files, "Initial output missing losses"
        initial = archive["losses"].copy()
    assert expected.shape == initial.shape and np.isfinite(initial).all()
    assert np.allclose(expected, initial, rtol=1e-5, atol=1e-6)
    output.unlink()
    assert not exists(output), "Failed to remove output"
    started = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = "/root/SimPO"
    result = run(
        [sys.executable, "/root/SimPO/unit_test/unit_test_1.py"],
        cwd="/root/SimPO",
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "unit_test_1.py failed"
    assert exists(output), "Regenerated output is missing"
    assert output.stat().st_mtime >= started, "Regenerated output is stale"
    with np.load(output, allow_pickle=False) as archive:
        assert "losses" in archive.files, "Regenerated output missing losses"
        regenerated = archive["losses"].copy()
    assert expected.shape == regenerated.shape, "Shape mismatch"
    assert np.isfinite(regenerated).all(), "Nonfinite generated values"
    assert np.allclose(expected, regenerated, rtol=1e-5, atol=1e-6), "Loss mismatch"

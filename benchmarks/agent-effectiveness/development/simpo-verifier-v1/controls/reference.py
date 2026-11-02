"""Development-only reference candidate for controlled grading calibration."""

import os
import subprocess
import sys
import time

import numpy as np


def test_outputs():
    gt_path = os.path.join(os.getcwd(), "loss.npz")
    output = "/root/loss.npz"
    env_path = "/root/python_info.txt"
    assert os.path.exists(gt_path), "Missing ground truth"
    assert os.path.exists(output), "Missing output"
    assert os.path.exists(env_path), "Missing environment info"
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
    os.remove(output)
    assert not os.path.exists(output), "Failed to remove output"
    started = time.time()
    env = os.environ.copy()
    env["PYTHONPATH"] = "/root/SimPO"
    result = subprocess.run(
        [sys.executable, "/root/SimPO/unit_test/unit_test_1.py"],
        cwd="/root/SimPO",
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, "unit_test_1.py failed"
    assert os.path.exists(output), "Regenerated output is missing"
    assert os.path.getmtime(output) >= started, "Regenerated output is stale"
    with np.load(output, allow_pickle=False) as archive:
        assert "losses" in archive.files, "Regenerated output missing losses"
        regenerated = archive["losses"].copy()
    assert expected.shape == regenerated.shape, "Shape mismatch"
    assert np.isfinite(regenerated).all(), "Nonfinite generated values"
    assert np.allclose(expected, regenerated, rtol=1e-5, atol=1e-6), "Loss mismatch"

"""Exercise the pinned SimPO verifier with controlled regenerated output files."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np

INPUTS = {
    "verifier": "05590869057aeaac1032f2177b0b2bf80f56828af3dba66f100e4d1346b2e62f",
    "reference": "162e3cd015afa98503a8419c6955523ba7c4401cd50f34e7d8f7e601e8489d2c",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verifier", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    args = parser.parse_args()
    if not __debug__:
        raise ValueError("Run without optimization so upstream assertions execute")
    data = {}
    for name, digest in INPUTS.items():
        content = getattr(args, name).read_bytes()
        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError(f"Unexpected input bytes: {name}")
        data[name] = content
    with tempfile.TemporaryDirectory(prefix="simpo-verifier-control-") as temp:
        root = Path(temp).resolve()
        verifier = root / "test_outputs.py"
        verifier.write_bytes(data["verifier"])
        (root / "loss.npz").write_bytes(data["reference"])
        spec = importlib.util.spec_from_file_location("upstream_simpo_verifier", verifier)
        if spec is None or spec.loader is None:
            raise ValueError("Cannot load pinned verifier")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with np.load(root / "loss.npz") as reference:
            expected = reference["losses"].copy()
        actual = root / "candidate.npz"
        envinfo = root / "python_info.txt"
        envinfo.write_text("Python 3.10 controlled fixture\n", encoding="utf-8")
        original_exists, original_mtime, original_remove = os.path.exists, os.path.getmtime, os.remove
        original_open, original_load = open, np.load

        def route(path):
            if str(path) == "/root/loss.npz":
                return actual
            if str(path) == "/root/python_info.txt":
                return envinfo
            return path

        def simulated_run(command, **kwargs):
            if _behavior == "missing":
                return subprocess.CompletedProcess(command, 0, "", "")
            if _behavior == "failed":
                return subprocess.CompletedProcess(command, 1, "", "controlled failure")
            if _behavior == "wrong_key":
                np.savez(actual, different=expected)
            else:
                value = expected if _behavior == "correct" else np.full(expected.shape, 42.0)
                np.savez(actual, losses=value)
            return subprocess.CompletedProcess(command, 0, "", "")

        cases = {}
        previous = os.getcwd()
        try:
            os.chdir(root)
            for name, _behavior in (
                ("correct", "correct"),
                ("wrong_regenerated", "wrong"),
                ("wrong_key_regenerated", "wrong_key"),
                ("missing_regenerated", "missing"),
                ("subprocess_failed", "failed"),
                ("wrong_initial", "correct"),
            ):
                initial = np.full(expected.shape, 42.0) if name == "wrong_initial" else expected
                np.savez(actual, losses=initial)
                try:
                    with (
                        patch.object(module.os.path, "exists", side_effect=lambda p: original_exists(route(p))),
                        patch.object(module.os.path, "getmtime", side_effect=lambda p: original_mtime(route(p))),
                        patch.object(module.os, "remove", side_effect=lambda p: original_remove(route(p))),
                        patch("builtins.open", side_effect=lambda p, *a, **k: original_open(route(p), *a, **k)),
                        patch.object(
                            module.np, "load", side_effect=lambda p, *a, **k: original_load(route(p), *a, **k)
                        ),
                        patch.object(module.subprocess, "run", side_effect=simulated_run),
                        contextlib.redirect_stdout(io.StringIO()),
                    ):
                        module.test_outputs()
                except AssertionError:
                    accepted = False
                else:
                    accepted = True
                cases[name] = accepted
        finally:
            os.chdir(previous)
    expected_cases = {
        "correct": True,
        "wrong_regenerated": True,
        "wrong_key_regenerated": True,
        "missing_regenerated": False,
        "subprocess_failed": False,
        "wrong_initial": False,
    }
    if cases != expected_cases:
        raise ValueError(f"Unexpected verifier _behavior: {cases}")
    print(
        json.dumps(
            {
                "platform": platform.system(),
                "python": platform.python_version(),
                "numpy": np.__version__,
                "input_sha256": INPUTS,
                "reference_shape": list(expected.shape),
                "subprocess_simulated": True,
                "simpo_training_executed": False,
                "model_scored": False,
                "accepted": cases,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

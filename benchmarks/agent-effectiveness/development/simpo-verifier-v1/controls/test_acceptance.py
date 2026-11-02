"""Development controls for the public SimPO verifier; no model is evaluated."""

from __future__ import annotations

import builtins
import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pytest

VERIFIER = Path(os.environ["SIMPO_VERIFIER"])


@pytest.fixture
def exercise(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("simpo_task_verifier", VERIFIER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Verifier could not be loaded")
    expected = np.linspace(0.1, 0.9, 5, dtype=np.float64)
    output, environment = tmp_path / "output.npz", tmp_path / "python_info.txt"
    np.savez(tmp_path / "loss.npz", losses=expected)
    np.savez(output, losses=expected)
    environment.write_text("Python 3.10 fixture", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    exists, stat, remove, unlink, open_file, load = (
        os.path.exists,
        os.stat,
        os.remove,
        os.unlink,
        builtins.open,
        np.load,
    )

    def route(path):
        if isinstance(path, (str, os.PathLike)):
            name = os.fsdecode(os.fspath(path)).replace("\\", "/")
            return {"/root/loss.npz": output, "/root/python_info.txt": environment}.get(name, path)
        return path

    def run_case(behavior):
        invocations = 0
        opened = []

        def simulated_run(command, **kwargs):
            nonlocal invocations
            invocations += 1
            if (
                invocations != 1
                or command != [sys.executable, "/root/SimPO/unit_test/unit_test_1.py"]
                or kwargs.get("cwd") != "/root/SimPO"
                or kwargs.get("env", {}).get("PYTHONPATH") != "/root/SimPO"
                or kwargs.get("capture_output") is not True
                or kwargs.get("text") is not True
                or exists(output)
            ):
                raise RuntimeError("Verifier did not invoke the expected test after removing the output")
            if behavior == "subprocess_failure":
                return subprocess.CompletedProcess(command, 1, "", "controlled failure")
            if behavior == "missing_regenerated":
                return subprocess.CompletedProcess(command, 0, "", "")
            arrays = {
                "wrong_values": {"losses": np.full(expected.shape, 42.0)},
                "wrong_key": {"wrong": expected},
                "wrong_shape": {"losses": expected[:, None]},
                "nonfinite": {"losses": np.full(expected.shape, np.nan)},
                "within_tolerance": {"losses": expected + 5e-7},
                "outside_tolerance": {"losses": expected + 2e-5},
            }.get(behavior, {"losses": expected})
            np.savez(output, **arrays)
            return subprocess.CompletedProcess(command, 0, "", "")

        with monkeypatch.context() as patch:

            def routed_stat(path, *args, **kwargs):
                value = stat(route(path), *args, **kwargs)
                if (
                    isinstance(path, (str, os.PathLike))
                    and os.fsdecode(os.fspath(path)).replace("\\", "/") == "/root/loss.npz"
                ):
                    fields = list(value)
                    fields[8] = time.time() - 3600 if behavior == "stale_regenerated" else time.time() + 1
                    return os.stat_result(fields)
                return value

            patch.setattr(os, "stat", routed_stat)
            patch.setattr(os.path, "exists", lambda path: exists(route(path)))
            patch.setattr(os.path, "getmtime", lambda path: routed_stat(path).st_mtime)
            patch.setattr(
                os,
                "remove",
                lambda path, *args, **kwargs: remove(route(path), *args, **kwargs),
            )
            patch.setattr(
                os,
                "unlink",
                lambda path, *args, **kwargs: unlink(route(path), *args, **kwargs),
            )
            patch.setattr(
                builtins,
                "open",
                lambda path, *args, **kwargs: open_file(route(path), *args, **kwargs),
            )
            original_path_open = Path.open
            patch.setattr(
                Path,
                "open",
                lambda path, *args, **kwargs: original_path_open(Path(route(path)), *args, **kwargs),
            )

            def routed_load(path, *args, **kwargs):
                result = load(route(path), *args, **kwargs)
                if isinstance(result, np.lib.npyio.NpzFile):
                    opened.append(result)
                return result

            patch.setattr(np, "load", routed_load)
            patch.setattr(subprocess, "run", simulated_run)
            if behavior == "wrong_initial":
                np.savez(output, losses=np.full(expected.shape, 42.0))
            if behavior == "wrong_initial_key":
                np.savez(output, wrong=expected)
            if behavior == "wrong_initial_shape":
                np.savez(output, losses=expected[:, None])
            if behavior == "missing_initial":
                output.unlink()
            if behavior == "missing_reference":
                (tmp_path / "loss.npz").unlink()
            if behavior == "missing_environment":
                environment.unlink()
            if behavior == "wrong_python_version":
                environment.write_text("Python 3.11 fixture", encoding="utf-8")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            try:
                module.test_outputs()
            finally:
                for archive in opened:
                    archive.close()

    return run_case


@pytest.mark.parametrize("case", ["correct", "within_tolerance"])
def test_valid_initial_and_regenerated_values_are_accepted(exercise, case):
    exercise(case)


@pytest.mark.parametrize(
    "case",
    [
        "wrong_initial",
        "wrong_initial_key",
        "wrong_initial_shape",
        "missing_initial",
        "missing_reference",
        "missing_environment",
        "wrong_python_version",
        "subprocess_failure",
        "missing_regenerated",
        "stale_regenerated",
        "wrong_values",
        "outside_tolerance",
        "wrong_key",
        "wrong_shape",
        "nonfinite",
    ],
)
def test_invalid_input_or_regenerated_output_is_rejected(exercise, case):
    with pytest.raises(AssertionError):
        exercise(case)

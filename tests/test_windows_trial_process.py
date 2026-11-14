from __future__ import annotations

import ctypes
import io
import sys
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

import pytest
from _windows_appcontainer import Native, set_last_error
from _windows_storage_budget import SpaceBudget, StorageLimits
from _windows_trial_process import run_owned

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows native job controls")


@pytest.mark.parametrize("failure", ["free_space_limit", "storage_observation_error"])
def test_active_space_budget_stops_the_owned_process_without_disk_stress(tmp_path, monkeypatch, failure):
    import _windows_storage_budget as storage

    marker = tmp_path / "started"

    def sample(_path):
        if marker.exists():
            if failure == "storage_observation_error":
                raise ValueError("owned injected space observation failure")
            return {"available_bytes": 5, "total_bytes": 1000, "volume_free_bytes": 100}
        return {"available_bytes": 100, "total_bytes": 1000, "volume_free_bytes": 100}

    monkeypatch.setattr(storage, "available_space", sample)
    budget = SpaceBudget(StorageLimits(10, 1024, 100), (tmp_path,))
    result, _, _ = run_fixture(
        tmp_path,
        "from pathlib import Path;import time;Path('started').write_text('ready');time.sleep(30)",
        timeout=5,
        python_arguments=("-I", "-B", "-S"),
        space_budget=budget,
    )
    assert marker.exists() and result["termination_reason"] == failure
    assert result["job_active_processes_after_cleanup"] == 0
    assert result["space_budget"]["termination_reason"] == failure
    assert result["space_budget"]["hard_storage_quota"] is False


def test_insufficient_space_prevents_process_launch(tmp_path, monkeypatch):
    import _windows_storage_budget as storage

    monkeypatch.setattr(
        storage, "available_space", lambda _path: {"available_bytes": 5, "total_bytes": 1000, "volume_free_bytes": 100}
    )
    budget = SpaceBudget(StorageLimits(10, 1024, 100), (tmp_path,))
    with pytest.raises(ValueError, match="free_space_limit"):
        run_fixture(tmp_path, "from pathlib import Path;Path('must-not-start').write_text('bad')", space_budget=budget)
    assert not (tmp_path / "must-not-start").exists()


def test_final_space_observation_catches_a_fast_completed_process(tmp_path, monkeypatch):
    import _windows_storage_budget as storage

    def sample(_path):
        return {
            "available_bytes": 5 if (tmp_path / "started").exists() else 100,
            "total_bytes": 1000,
            "volume_free_bytes": 100,
        }

    monkeypatch.setattr(storage, "available_space", sample)
    budget = SpaceBudget(StorageLimits(10, 1024, 100), (tmp_path,))
    result, _, _ = run_fixture(
        tmp_path,
        "from pathlib import Path;Path('started').write_text('ready')",
        python_arguments=("-I", "-B", "-S"),
        space_budget=budget,
        write_io_limit=1024**2,
    )
    assert result["termination_reason"] == "free_space_limit"
    assert result["space_budget"]["samples"][str(tmp_path)]["lowest_available_bytes"] == 5
    assert result["job_write_io_bytes"] is not None and result["job_active_processes_after_cleanup"] == 0


def run_fixture(
    tmp_path: Path,
    source: str,
    *,
    timeout: float = 10,
    output_limit: int = 1024 * 1024,
    executable: Path | None = None,
    python_arguments: tuple[str, ...] = ("-B",),
    **options,
):
    prompt = tmp_path / "prompt"
    prompt.write_bytes(b"fixture input\n")
    with (
        prompt.open("rb") as stdin,
        (tmp_path / "stdout").open("xb") as stdout,
        (tmp_path / "stderr").open("xb") as stderr,
    ):
        result = run_owned(
            [str((executable or Path(sys.executable)).resolve()), *python_arguments, "-c", source],
            cwd=tmp_path.resolve(),
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=timeout,
            output_limit=output_limit,
            **options,
        )
    return result, (tmp_path / "stdout").read_bytes(), (tmp_path / "stderr").read_bytes()


def test_success_preserves_streams_and_exit_status(tmp_path):
    result, stdout, stderr = run_fixture(
        tmp_path, "import sys; print(sys.stdin.read().strip()); print('fixture error',file=sys.stderr)"
    )
    assert stdout == b"fixture input\r\n"
    assert stderr == b"fixture error\r\n"
    peak = result.pop("job_peak_memory_used_bytes")
    assert type(peak) is int and peak > 0
    assert result == {
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "job_active_processes_after_cleanup": 0,
        "service_created_processes_tracked": False,
        "termination_reason": None,
        "exit_code": 0,
        "output_bytes": len(stdout) + len(stderr),
        "output_limit_bytes": 1024 * 1024,
        "wall_time_limit_seconds": 10.0,
        "job_memory_limit_bytes": 1024 * 1024 * 1024,
        "active_process_limit": 32,
        "explicit_environment": False,
    }


@pytest.mark.parametrize("timeout", [False, 0, -1, float("inf"), float("nan")])
def test_invalid_time_limit_never_launches(tmp_path, timeout):
    with pytest.raises(ValueError, match="limit"):
        run_fixture(tmp_path, "raise AssertionError('must not run')", timeout=timeout)


@pytest.mark.parametrize("limit", [False, 0, -1, 1024 * 1024 * 1024 + 1])
def test_invalid_output_limit_never_launches(tmp_path, limit):
    with pytest.raises(ValueError, match="limit"):
        run_fixture(tmp_path, "raise AssertionError('must not run')", output_limit=limit)


@pytest.mark.parametrize(
    "options",
    [
        {"memory_limit": False},
        {"memory_limit": 0},
        {"memory_limit": 16 * 1024 * 1024 * 1024 + 1},
        {"process_limit": False},
        {"process_limit": 0},
        {"process_limit": 129},
        {"environment": {}},
        {"environment": {"CONTROL": "value\0suffix"}},
        {"environment": {"BAD=NAME": "value"}},
        {"environment": {"CONTROL": "value", "control": "other"}},
    ],
)
def test_invalid_resource_or_environment_settings_never_launch(tmp_path, options):
    with pytest.raises(ValueError):
        run_fixture(tmp_path, "raise AssertionError('must not run')", **options)


def test_explicit_environment_does_not_inherit_parent_values(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_SKILLS_PARENT_CONTROL", "must not leak")
    result, stdout, _ = run_fixture(
        tmp_path,
        "import os; print(os.environ.get('AI_SKILLS_PARENT_CONTROL')); print(os.environ['AI_SKILLS_CHILD_CONTROL'])",
        environment={"AI_SKILLS_CHILD_CONTROL": "Unicode \u03b1", "PYTHONIOENCODING": "utf-8"},
    )
    assert result["exit_code"] == 0 and result["explicit_environment"] is True
    assert stdout.decode("utf-8") == "None\r\nUnicode \u03b1\r\n"


def test_job_memory_limit_denies_an_oversized_allocation(tmp_path):
    result, stdout, _ = run_fixture(
        tmp_path,
        "try:\n data=bytearray(256*1024*1024)\nexcept MemoryError:\n print('allocation denied')",
        memory_limit=96 * 1024 * 1024,
    )
    assert result["exit_code"] == 0
    assert stdout == b"allocation denied\r\n"
    assert result["job_memory_limit_bytes"] == 96 * 1024 * 1024


def test_explicit_model_backend_limit_is_admitted_without_allocating_the_limit(tmp_path):
    result, stdout, _ = run_fixture(tmp_path, "print('bounded backend role')", memory_limit=16 * 1024**3)
    assert result["exit_code"] == 0 and stdout == b"bounded backend role\r\n"
    assert result["job_memory_limit_bytes"] == 16 * 1024**3
    assert type(result["job_peak_memory_used_bytes"]) is int and result["job_peak_memory_used_bytes"] > 0


def test_active_process_limit_denies_a_second_process(tmp_path):
    result, stdout, _ = run_fixture(
        tmp_path,
        "import subprocess,sys\ntry:\n subprocess.run([sys.executable,'-c','pass'],check=True)\n"
        "except OSError:\n print('child denied')",
        process_limit=1,
        executable=Path(getattr(sys, "_base_executable", sys.executable)),
    )
    assert result["exit_code"] == 0
    assert stdout == b"child denied\r\n"
    assert result["active_process_limit"] == 1


def child_source(started: Path, escaped: Path) -> str:
    return (
        "from pathlib import Path; import time; "
        f"Path({str(started)!r}).write_text('started'); time.sleep(3); "
        f"Path({str(escaped)!r}).write_text('escaped')"
    )


@pytest.mark.parametrize("parent_exits", [True, False])
def test_descendants_are_stopped_after_parent_exit_or_timeout(tmp_path, parent_exits):
    started, escaped = tmp_path / "child-started", tmp_path / "child-escaped"
    child = child_source(started, escaped)
    source = (
        "import subprocess,sys,time; from pathlib import Path; "
        f"subprocess.Popen([sys.executable,'-c',{child!r}]); "
        f"p=Path({str(started)!r}); deadline=time.monotonic()+5; "
        "exec('while not p.exists() and time.monotonic()<deadline:\\n time.sleep(.01)'); "
        "assert p.exists(); print('child started',flush=True); " + ("" if parent_exits else "time.sleep(30)")
    )
    result, stdout, _ = run_fixture(tmp_path, source, timeout=10 if parent_exits else 2)
    assert b"child started" in stdout
    assert result["termination_reason"] == (None if parent_exits else "timeout")
    assert result["job_active_processes_after_cleanup"] == 0
    time.sleep(3.2)
    assert not escaped.exists()


def test_grandchild_is_stopped_after_parent_exit(tmp_path):
    started, escaped = tmp_path / "grandchild-started", tmp_path / "grandchild-escaped"
    grandchild = child_source(started, escaped)
    child = f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-c',{grandchild!r}]); time.sleep(30)"
    source = (
        "import subprocess,sys,time; from pathlib import Path; "
        f"subprocess.Popen([sys.executable,'-c',{child!r}]); "
        f"p=Path({str(started)!r}); deadline=time.monotonic()+5; "
        "exec('while not p.exists() and time.monotonic()<deadline:\\n time.sleep(.01)'); "
        "assert p.exists(); print('grandchild started',flush=True)"
    )
    result, stdout, _ = run_fixture(tmp_path, source)
    assert b"grandchild started" in stdout
    assert result["exit_code"] == 0 and result["job_active_processes_after_cleanup"] == 0
    time.sleep(3.2)
    assert not escaped.exists()


def test_output_limit_stops_the_entire_process(tmp_path):
    result, stdout, stderr = run_fixture(
        tmp_path, "import sys; sys.stdout.write('x'*2000000); sys.stdout.flush()", output_limit=4096
    )
    assert result["termination_reason"] == "output_limit"
    assert result["job_active_processes_after_cleanup"] == 0
    assert len(stdout) + len(stderr) == result["output_bytes"] == 4097


def test_write_budget_rejects_a_fast_completed_file_write(tmp_path):
    result, _, _ = run_fixture(
        tmp_path,
        "from pathlib import Path; Path('payload').write_bytes(b'x'*(2*1024**2))",
        write_io_limit=65536,
        python_arguments=("-I", "-B", "-S"),
    )
    assert result["termination_reason"] == "write_io_limit"
    assert result["job_active_processes_after_cleanup"] == 0
    assert result["job_write_io_bytes"] >= 2 * 1024**2
    assert result["write_io_overshoot_bytes"] == result["job_write_io_bytes"] - 65536
    assert result["hard_storage_quota"] is False


def test_small_file_write_completes_within_its_observed_budget(tmp_path):
    result, _, _ = run_fixture(
        tmp_path,
        "from pathlib import Path; Path('payload').write_bytes(b'x'*4096)",
        write_io_limit=65536,
        python_arguments=("-I", "-B", "-S"),
    )
    assert result["exit_code"] == 0 and result["termination_reason"] is None
    assert 4096 <= result["job_write_io_bytes"] <= 65536
    assert result["write_io_overshoot_bytes"] == 0
    assert result["write_io_limit_bytes"] == 65536


@pytest.mark.parametrize("limit", [0, -1, True, 1.5, 1024**3 + 1])
def test_invalid_write_io_budget_never_launches(tmp_path, limit):
    with pytest.raises(ValueError, match="limit"):
        run_fixture(tmp_path, "raise AssertionError('must not run')", write_io_limit=limit)


def test_write_accounting_failure_stops_the_job_and_retains_the_error(tmp_path, monkeypatch):
    original = Native.function

    def function(self, library, name, *arguments):
        actual = original(self, library, name, *arguments)
        if library == "kernel" and name == "QueryInformationJobObject":

            def query(job, information_class, *values):
                if information_class == 8:
                    set_last_error(5)
                    return False
                return actual(job, information_class, *values)

            return query
        return actual

    monkeypatch.setattr(Native, "function", function)
    result, _, _ = run_fixture(tmp_path, "import time; time.sleep(30)", write_io_limit=65536)
    assert result["termination_reason"] == "resource_observation_error"
    assert result["job_active_processes_after_cleanup"] == 0
    assert result["write_io_observation_error"]["winerror"] == 5
    assert result["job_write_io_bytes"] is None


def test_a_descendant_file_write_trips_the_shared_job_budget(tmp_path):
    escaped = tmp_path / "escaped"
    child = (
        "import time; from pathlib import Path; "
        "Path('payload').write_bytes(b'x'*(2*1024**2)); time.sleep(2); "
        f"Path({str(escaped)!r}).write_text('escaped')"
    )
    source = (
        f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-I','-B','-S','-c',{child!r}]); time.sleep(30)"
    )
    result, _, _ = run_fixture(tmp_path, source, write_io_limit=65536, python_arguments=("-I", "-B", "-S"))
    assert result["termination_reason"] == "write_io_limit"
    assert result["job_write_io_bytes"] >= 2 * 1024**2
    assert result["job_active_processes_after_cleanup"] == 0
    time.sleep(2.2)
    assert not escaped.exists()


def test_unexpected_accounting_layout_cannot_produce_a_success(tmp_path, monkeypatch):
    original = Native.function

    def function(self, library, name, *arguments):
        actual = original(self, library, name, *arguments)
        if library == "kernel" and name == "QueryInformationJobObject":

            def query(job, information_class, *values):
                if information_class == 8:
                    return True  # Deliberately omit the required returned-length value.
                return actual(job, information_class, *values)

            return query
        return actual

    monkeypatch.setattr(Native, "function", function)
    result, _, _ = run_fixture(tmp_path, "import time; time.sleep(30)", write_io_limit=65536)
    assert result["termination_reason"] == "resource_observation_error"
    assert result["job_active_processes_after_cleanup"] == 0
    assert result["write_io_observation_error"]["expected_bytes"] == 96
    assert result["write_io_observation_error"]["returned_bytes"] == 0


def test_output_write_error_also_stops_descendants(tmp_path):
    started, escaped = tmp_path / "child-started", tmp_path / "child-escaped"
    child = child_source(started, escaped)
    source = (
        "import subprocess,sys,time; from pathlib import Path; "
        f"subprocess.Popen([sys.executable,'-c',{child!r}]); "
        f"p=Path({str(started)!r}); deadline=time.monotonic()+5; "
        "exec('while not p.exists() and time.monotonic()<deadline:\\n time.sleep(.01)'); "
        "assert p.exists(); print('trigger',flush=True); time.sleep(30)"
    )

    class BrokenOutput(io.BytesIO):
        def write(self, data: Any, /) -> int:
            raise OSError("simulated output failure")

    prompt = tmp_path / "prompt"
    prompt.write_bytes(b"")
    with prompt.open("rb") as stdin, pytest.raises(OSError, match="simulated output failure"):
        run_owned(
            [str(Path(sys.executable).resolve()), "-c", source],
            cwd=tmp_path.resolve(),
            stdin=stdin,
            stdout=BrokenOutput(),
            stderr=io.BytesIO(),
            timeout=10,
            output_limit=1024,
        )
    assert started.exists()
    time.sleep(3.2)
    assert not escaped.exists()


def test_nonzero_exit_is_preserved(tmp_path):
    result, _, _ = run_fixture(tmp_path, "import sys; sys.exit(7)")
    assert result["exit_code"] == 7
    assert result["termination_reason"] is None
    assert result["job_active_processes_after_cleanup"] == 0


def test_descendant_cannot_break_away_from_the_job(tmp_path):
    started, marker = tmp_path / "started", tmp_path / "escaped"
    child = child_source(started, marker)
    source = f"""import subprocess,sys,time
from pathlib import Path
try:
    subprocess.Popen([sys.executable, '-c', sys.argv[1]], creationflags=0x01000000)
except OSError:
    print('breakaway denied')
else:
    p=Path({str(started)!r})
    deadline=time.monotonic()+5
    while not p.exists() and time.monotonic()<deadline:
        time.sleep(.01)
    assert p.exists()
    print('breakaway requested')
"""
    prompt = tmp_path / "prompt"
    prompt.write_bytes(b"")
    with (
        prompt.open("rb") as stdin,
        (tmp_path / "stdout").open("xb") as stdout,
        (tmp_path / "stderr").open("xb") as stderr,
    ):
        result = run_owned(
            [str(Path(sys.executable).resolve()), "-c", source, child],
            cwd=tmp_path.resolve(),
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=10,
            output_limit=1024,
        )
    assert result["exit_code"] == 0
    assert (tmp_path / "stdout").read_bytes() in {b"breakaway denied\r\n", b"breakaway requested\r\n"}
    time.sleep(3.2)
    assert not marker.exists()


def test_unrelated_inheritable_handle_is_not_passed_to_the_child(tmp_path):
    native: Any = Native()
    kernel = native.kernel
    kernel.CreateEventW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateEventW.restype = wintypes.HANDLE
    kernel.SetHandleInformation.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD]
    kernel.SetHandleInformation.restype = wintypes.BOOL
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    event = kernel.CreateEventW(None, True, False, None)
    assert event and kernel.SetHandleInformation(event, 1, 1)
    try:
        source = (
            "import ctypes; from ctypes import wintypes; "
            "k=ctypes.WinDLL('kernel32',use_last_error=True); "
            "k.SetEvent.argtypes=[wintypes.HANDLE]; k.SetEvent.restype=wintypes.BOOL; "
            f"k.SetEvent({event})"
        )
        result, _, _ = run_fixture(tmp_path, source)
        assert result["exit_code"] == 0
        assert kernel.WaitForSingleObject(event, 0) == 0x102
    finally:
        assert kernel.CloseHandle(event)

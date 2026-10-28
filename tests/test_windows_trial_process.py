from __future__ import annotations

import ctypes
import io
import sys
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any

import pytest
from _windows_appcontainer import Native
from _windows_trial_process import run_owned

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows native job controls")


def run_fixture(tmp_path: Path, source: str, *, timeout: float = 10, output_limit: int = 1024 * 1024):
    prompt = tmp_path / "prompt"
    prompt.write_bytes(b"fixture input\n")
    with (
        prompt.open("rb") as stdin,
        (tmp_path / "stdout").open("xb") as stdout,
        (tmp_path / "stderr").open("xb") as stderr,
    ):
        result = run_owned(
            [str(Path(sys.executable).resolve()), "-c", source],
            cwd=tmp_path.resolve(),
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            timeout=timeout,
            output_limit=output_limit,
        )
    return result, (tmp_path / "stdout").read_bytes(), (tmp_path / "stderr").read_bytes()


def test_success_preserves_streams_and_exit_status(tmp_path):
    result, stdout, stderr = run_fixture(
        tmp_path, "import sys; print(sys.stdin.read().strip()); print('fixture error',file=sys.stderr)"
    )
    assert stdout == b"fixture input\r\n"
    assert stderr == b"fixture error\r\n"
    assert result == {
        "windows_job": True,
        "assigned_before_resume": True,
        "kill_on_close": True,
        "job_active_processes_after_cleanup": 0,
        "service_created_processes_tracked": False,
        "termination_reason": None,
        "exit_code": 0,
        "output_bytes": len(stdout) + len(stderr),
    }


@pytest.mark.parametrize("timeout", [False, 0, -1, float("inf"), float("nan")])
def test_invalid_time_limit_never_launches(tmp_path, timeout):
    with pytest.raises(ValueError, match="limit"):
        run_fixture(tmp_path, "raise AssertionError('must not run')", timeout=timeout)


@pytest.mark.parametrize("limit", [False, 0, -1, 1024 * 1024 * 1024 + 1])
def test_invalid_output_limit_never_launches(tmp_path, limit):
    with pytest.raises(ValueError, match="limit"):
        run_fixture(tmp_path, "raise AssertionError('must not run')", output_limit=limit)


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

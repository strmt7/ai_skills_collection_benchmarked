"""Native frontend lifetime controls, without installation or model execution."""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

import pytest


def fixture_checkout(tmp_path: Path, script: str) -> Path:
    root = Path(__file__).resolve().parents[1]
    checkout = tmp_path / "checkout with spaces"
    bootstrap = checkout / "toolchains/bootstrap"
    bootstrap.mkdir(parents=True)
    shutil.copyfile(root / "dev.ps1", checkout / "dev.ps1")
    for name in ("NativeSupervisor.dll", "supervisor.json", "OwnedProcess.cs"):
        shutil.copyfile(root / "toolchains/bootstrap" / name, bootstrap / name)
    (bootstrap / "bootstrap.ps1").write_text(script, encoding="utf-8")
    return checkout


@pytest.mark.skipif(os.name != "nt", reason="Native Windows process lifetime contract")
def test_terminating_frontend_stops_first_bootstrap_and_descendant(tmp_path: Path) -> None:
    if sys.platform != "win32":
        pytest.skip("Native Windows process lifetime contract")
    shell = Path(os.environ["SYSTEMROOT"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    fixture = r"""param($Root,$CacheRoot,$Profile,$CommandBase64,$CommandMemoryGiB)
[IO.File]::WriteAllText((Join-Path $Root 'bootstrap.pid'),[string]$PID)
$program="[IO.File]::WriteAllText('"+$Root.Replace("'","''")+"/descendant.pid',[string]`$PID); Start-Sleep -Seconds 90"
$start=New-Object Diagnostics.ProcessStartInfo
$start.FileName=[IO.Path]::Combine([Environment]::GetFolderPath('System'),'WindowsPowerShell/v1.0/powershell.exe')
$start.Arguments='-NoLogo -NoProfile -NonInteractive -EncodedCommand '+[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($program))
$start.UseShellExecute=$false; $start.CreateNoWindow=$true
$child=[Diagnostics.Process]::Start($start)
try { Start-Sleep -Seconds 90 } finally { $child.Dispose() }
"""
    checkout = fixture_checkout(tmp_path, fixture)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)
    kernel.TerminateProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    handles: list[int] = []
    environment = {**os.environ, "TEMP": str(tmp_path), "TMP": str(tmp_path)}
    with (tmp_path / "stdout.native").open("wb") as stdout, (tmp_path / "stderr.native").open("wb") as stderr:
        process = subprocess.Popen(
            [
                str(shell),
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-File",
                str(checkout / "dev.ps1"),
                "--cache-root",
                str(tmp_path / "unused cache"),
                "python",
                "--version",
            ],
            cwd=checkout,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        try:
            deadline = time.monotonic() + 20
            for name in ("bootstrap.pid", "descendant.pid"):
                path = checkout / name
                while not path.exists():
                    if process.poll() is not None or time.monotonic() >= deadline:
                        pytest.fail("The independent bootstrap fixture did not start")
                    time.sleep(0.05)
                pid = int(path.read_text(encoding="utf-8"))
                handle = kernel.OpenProcess(0x100000 | 0x1, False, pid)
                if not handle:
                    raise ctypes.WinError(ctypes.get_last_error())
                handles.append(handle)
            process.kill()
            process.wait(timeout=5)
            assert all(kernel.WaitForSingleObject(handle, 5000) == 0 for handle in handles), (
                "A bootstrap process outlived its terminated frontend"
            )
            assert not (tmp_path / "unused cache").exists()
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
            for handle in handles:
                if kernel.WaitForSingleObject(handle, 0) != 0:
                    kernel.TerminateProcess(handle, 125)
                    kernel.WaitForSingleObject(handle, 5000)
                kernel.CloseHandle(handle)


@pytest.mark.skipif(os.name != "nt", reason="Native Windows frontend exit-status contract")
@pytest.mark.parametrize("memory", [None, 18])
def test_frontend_preserves_output_exit_status_and_declared_limits(tmp_path: Path, memory: int | None) -> None:
    if sys.platform != "win32":
        pytest.skip("Native Windows frontend exit-status contract")
    checkout = fixture_checkout(
        tmp_path, "[Console]::Out.Write('ordinary-output'); [Console]::Error.Write('ordinary-error'); exit 23"
    )
    shell = Path(os.environ["SYSTEMROOT"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    command = [str(shell), "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(checkout / "dev.ps1")]
    if memory is not None:
        command.extend(["--command-memory-gib", str(memory)])
    command.extend(["python", "--version"])
    result = subprocess.run(
        command,
        cwd=checkout,
        env={**os.environ, "TEMP": str(tmp_path), "TMP": str(tmp_path)},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=20,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    assert result.returncode == 23
    assert result.stdout.decode("utf-8") == "ordinary-output"
    assert result.stderr.decode("utf-8") == "ordinary-error"
    directories = list(tmp_path.glob("ai-skills-frontend-*"))
    assert len(directories) == 1
    resources = json.loads((directories[0] / "resources.json").read_bytes())
    assert resources["memory_limit_bytes"] == max(8, (memory or 4) + 4) * 1024**3
    assert resources["command_memory_limit_bytes"] == (memory or 4) * 1024**3
    process = json.loads((directories[0] / "process.json").read_bytes())
    assert process["exit_code"] == 23 and process["active_processes_after_cleanup"] == 0
    assert process["termination_reason"] is None

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts/repaired-skill-readiness/e2e-response-v1"
OVERLAY = ROOT / "included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/e2e-testing"
MIRROR = ROOT / "included/skills/by-category/testing-qa-benchmarking/selected-structure-reference/e2e-testing/SKILL.md"


def windows_process_cpu_seconds(pid: int) -> tuple[float, float] | None:
    """Return kernel and user CPU seconds for a live Windows process when available."""
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    try:
        created, exited, system, user = (wintypes.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(
            handle, ctypes.byref(created), ctypes.byref(exited), ctypes.byref(system), ctypes.byref(user)
        ):
            return None

        def seconds(value: wintypes.FILETIME) -> float:
            ticks = (value.dwHighDateTime << 32) | value.dwLowDateTime
            return ticks / 10_000_000  # FILETIME uses 100-nanosecond units.

        return seconds(system), seconds(user)
    finally:
        kernel.CloseHandle(handle)


def windows_thread_snapshot(pid: int) -> dict[str, object] | None:
    """Capture a best-effort Windows thread-state snapshot for a live process."""
    if sys.platform != "win32":
        return None
    shell = shutil.which("powershell.exe")
    if shell is None:
        return None
    command = f"""$ErrorActionPreference = 'Stop'
$process = [System.Diagnostics.Process]::GetProcessById({pid:d})
try {{
    $threads = @($process.Threads | ForEach-Object {{
        $state = $_.ThreadState
        $reason = if ($state -eq [System.Diagnostics.ThreadState]::Wait) {{ [string]$_.WaitReason }} else {{ $null }}
        [PSCustomObject]@{{ id = $_.Id; state = [string]$state; wait_reason = $reason; cpu_ms = $_.TotalProcessorTime.TotalMilliseconds }}
    }})
    [PSCustomObject]@{{ pid = $process.Id; threads = $threads }} | ConvertTo-Json -Depth 4 -Compress
}} finally {{ $process.Dispose() }}"""
    result = subprocess.run(
        [shell, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8-sig",
        timeout=5,
        check=True,
    )
    return json.loads(result.stdout)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_original_overlay_and_evidence_are_source_bound() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    original = OVERLAY / manifest["provenance_skill"]
    assert digest(original) == digest(MIRROR) == manifest["original_skill_sha256"]
    assert digest(OVERLAY / "SKILL.md") == manifest["repaired_skill_sha256"]
    assert digest(OVERLAY / manifest["license_file"]) == manifest["license_sha256"]
    assert manifest["model_performance_claim"] is False
    for name, expected in manifest["evidence_sha256"].items():
        assert digest(ARTIFACT / name) == expected, name


def test_recorded_controls_preserve_results_and_limit_claims() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    results = sorted(ARTIFACT.glob("*-windows.json")) + sorted(ARTIFACT.glob("*-linux.json"))
    assert len(results) == 7
    upstream = json.loads((ARTIFACT / "upstream-observation.json").read_text(encoding="utf-8"))
    for result in results:
        data = json.loads(result.read_text(encoding="utf-8"))
        assert data["overlay_sha256"] == manifest["repaired_skill_sha256"]
        source_hash = (
            upstream["normalized_sha256"] if result.name.startswith("upstream-") else manifest["original_skill_sha256"]
        )
        assert data["source_sha256"] == source_hash
        lock_platform = "windows" if data["platform"] == "win32" else "linux"
        assert data["lock_sha256"] == digest(ARTIFACT / "locks" / lock_platform / "package-lock.json")
        assert data["served"] == 31
        assert data["agent_efficacy_scored"] is False
        assert data["rejected_bad_status"] is True
        assert set(data["counts"]) == {"original", "ordering_only", "overlay"}
        assert all(item["passed"] + item["timed_out"] == 10 for item in data["counts"].values())
        assert data["counts"]["overlay"] == {"passed": 10, "timed_out": 0}


def test_control_rejects_unreviewed_overlay_before_loading_dependencies(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is not installed")
    with subprocess.Popen(
        [node, str(ARTIFACT / "control.cjs"), str(MIRROR), str(MIRROR), str(tmp_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "NODE_DEBUG": "module"},
    ) as process:
        try:
            _, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired as error:
            returncode_at_timeout = process.poll()
            error.add_note(f"Child return code at timeout: {returncode_at_timeout!r}")
            try:
                cpu = windows_process_cpu_seconds(process.pid)
                error.add_note(f"Child kernel/user CPU seconds at timeout: {cpu!r}")
            except OSError as diagnostic_error:
                error.add_note(f"Child CPU diagnostics unavailable: {diagnostic_error}")
            try:
                error.add_note(f"Child thread snapshot after timeout: {windows_thread_snapshot(process.pid)!r}")
            except (OSError, subprocess.SubprocessError, ValueError) as diagnostic_error:
                error.add_note(f"Child thread diagnostics unavailable: {diagnostic_error}")
            process.kill()
            stdout, stderr = process.communicate()
            error.add_note(f"Captured stdout after termination (first 2048 characters): {stdout[:2048]!r}")
            error.add_note(f"Captured stderr after termination (first 2048 characters): {stderr[:2048]!r}")
            raise
    assert process.returncode != 0
    assert "Source or overlay does not match the reviewed content" in stderr


def test_process_cpu_diagnostic_uses_the_current_process() -> None:
    observed = windows_process_cpu_seconds(os.getpid())
    if os.name == "nt":
        assert observed is not None and all(value >= 0 for value in observed)
    else:
        assert observed is None


def test_thread_snapshot_diagnostic_uses_the_current_process() -> None:
    observed = windows_thread_snapshot(os.getpid())
    if sys.platform == "win32" and shutil.which("powershell.exe") is not None:
        assert observed is not None and observed["pid"] == os.getpid() and observed["threads"]
    else:
        assert observed is None


def test_thread_diagnostic_failure_preserves_timeout_and_cleanup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class TimedOutProcess:
        pid = 1
        returncode = None
        killed = False

        def __enter__(self) -> TimedOutProcess:
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def communicate(self, timeout: float | None = None) -> tuple[str, str]:
            if not self.killed:
                raise subprocess.TimeoutExpired("node", 10 if timeout is None else timeout)
            return "", ""

        def poll(self) -> None:
            return None

        def kill(self) -> None:
            self.killed = True

    process = TimedOutProcess()
    monkeypatch.setattr(shutil, "which", lambda _: "node")
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: process)
    monkeypatch.setattr(sys.modules[__name__], "windows_process_cpu_seconds", lambda _: None)

    def failed_snapshot(_: int) -> None:
        raise subprocess.TimeoutExpired("thread snapshot", 5)

    monkeypatch.setattr(sys.modules[__name__], "windows_thread_snapshot", failed_snapshot)
    with pytest.raises(subprocess.TimeoutExpired, match="node") as caught:
        test_control_rejects_unreviewed_overlay_before_loading_dependencies(tmp_path)
    assert process.killed
    assert any("Child thread diagnostics unavailable" in note for note in caught.value.__notes__)

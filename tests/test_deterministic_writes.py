"""Verify concurrent and failed writes leave a complete generated artifact."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier, Lock

import pytest
from _lib_b import io_utils


def test_simultaneous_writers_stage_their_own_bytes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "receipt.json"
    payloads = ("first\n", "second\n")
    entered = Barrier(len(payloads))
    captured = Barrier(len(payloads))
    lock = Lock()
    observed: dict[Path, str] = {}
    original_replace = io_utils.os.replace

    def replace(source: Path, destination: Path) -> None:
        with lock:
            first_replace = destination == target and source not in observed
        if first_replace:
            entered.wait(timeout=10)
            with lock:
                observed[source] = source.read_text(encoding="utf-8")
            captured.wait(timeout=10)
        original_replace(source, destination)

    monkeypatch.setattr(io_utils.os, "replace", replace)
    with ThreadPoolExecutor(max_workers=len(payloads)) as executor:
        futures = [executor.submit(io_utils.write_text, target, body) for body in payloads]
        for future in futures:
            future.result(timeout=20)
    assert sorted(observed.values()) == sorted(payloads)
    assert target.read_text(encoding="utf-8") in payloads
    assert list(tmp_path.iterdir()) == [target]


def test_failed_replace_preserves_existing_artifact(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "receipt.json"
    target.write_bytes(b"existing")

    def refused_replace(source: Path, destination: Path) -> None:
        assert source.read_bytes() == b"new\n" and destination == target
        raise OSError("declined replacement")

    monkeypatch.setattr(io_utils.os, "replace", refused_replace)
    with pytest.raises(OSError, match="declined replacement"):
        io_utils.write_text(target, "new\n")
    assert target.read_bytes() == b"existing"
    assert list(tmp_path.iterdir()) == [target]


def test_transient_windows_sharing_failure_retains_the_staged_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "receipt.json"
    original_replace = io_utils.os.replace
    attempts: list[Path] = []

    class SharingFailure(PermissionError):
        winerror = 32

    def temporarily_busy(source: Path, destination: Path) -> None:
        attempts.append(source)
        assert source.read_bytes() == b"complete"
        if len(attempts) == 1:
            raise SharingFailure("target temporarily in use")
        original_replace(source, destination)

    monkeypatch.setattr(io_utils.os, "replace", temporarily_busy)
    io_utils.write_text(target, "complete")
    assert len(attempts) == 2 and attempts[0] == attempts[1]
    assert target.read_bytes() == b"complete" and list(tmp_path.iterdir()) == [target]

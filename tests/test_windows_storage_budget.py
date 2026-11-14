"""Qualify native storage observations without filling a host disk or reading file contents."""

from __future__ import annotations

import struct
import sys
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from _windows_appcontainer import set_last_error
from _windows_storage_budget import (
    STREAM_HEADER,
    SpaceBudget,
    StorageLimits,
    WorkspaceStorageExceeded,
    available_space,
    measure_workspace,
    parse_stream_buffer,
    verify_workspace_measurement,
)
from _windows_submission_reader import WorkspaceReader

native = pytest.mark.skipif(sys.platform != "win32", reason="Windows native storage metadata")


def test_last_error_boundary_rejects_unsupported_platforms(monkeypatch):
    import _windows_appcontainer as api

    monkeypatch.setattr(api, "sys", SimpleNamespace(platform="linux"))
    with pytest.raises(ValueError, match="requires Windows"):
        api.set_last_error(0)


@pytest.fixture
def limits():
    return StorageLimits(min_free_bytes=1024**3, max_workspace_bytes=1024**2, max_workspace_entries=100)


def stream_record(name: str, size: int, *, following: bool = False) -> bytes:
    encoded = name.encode("utf-16-le")
    length = (STREAM_HEADER.size + len(encoded) + 7) // 8 * 8
    return (STREAM_HEADER.pack(length if following else 0, len(encoded), size, size) + encoded).ljust(length, b"\0")


@pytest.mark.parametrize("field", ["min_free_bytes", "max_workspace_bytes", "max_workspace_entries"])
@pytest.mark.parametrize("value", [True, 0, -1, 1.0, "1", None, 2**64])
def test_invalid_storage_limits_are_rejected(limits, field, value):
    record = asdict(limits)
    record[field] = value
    with pytest.raises(ValueError):
        StorageLimits.from_record(record)


def test_explicit_storage_limit_shape_and_boundaries():
    record = {"min_free_bytes": 1024**4, "max_workspace_bytes": 1024**3, "max_workspace_entries": 65536}
    assert asdict(StorageLimits.from_record(record)) == record
    malformed_records: list[object] = [{}, {**record, "extra": 1}, None, []]
    for malformed in malformed_records:
        with pytest.raises(ValueError, match="complete explicit"):
            StorageLimits.from_record(malformed)


@pytest.mark.parametrize(
    "mutation",
    [
        {"complete": False},
        {"logical_bytes": True},
        {"logical_bytes": 1024**2 + 1},
        {"entries": 1},
        {"files": -1},
        {"measurement": "physical_allocation"},
        {"extra": 1},
    ],
)
def test_incomplete_inconsistent_or_over_budget_workspace_records_are_rejected(limits, mutation):
    record = {
        "complete": True,
        "logical_bytes": 0,
        "entries": 0,
        "files": 0,
        "directories": 0,
        "streams": 0,
        "measurement": "stopped_workspace_data_stream_lengths",
    }
    verify_workspace_measurement(record, limits)
    with pytest.raises(ValueError):
        verify_workspace_measurement({**record, **mutation}, limits)


def test_stream_parser_preserves_large_lengths_and_named_streams():
    raw = stream_record("::$DATA", 2**34, following=True) + stream_record(":cache:$DATA", 7)
    assert parse_stream_buffer(raw) == {"::$data": 2**34, ":cache:$data": 7}


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\0" * 23,
        STREAM_HEADER.pack(0, 0, 0, 0),
        STREAM_HEADER.pack(0, 1, 0, 0) + b"x",
        STREAM_HEADER.pack(0, 100, 0, 0) + b"x",
        stream_record("::$DATA", -1),
        stream_record("not-a-stream", 1),
        stream_record(":bad\0:$DATA", 1),
        stream_record("::$DATA", 1, following=True) + stream_record("::$data", 1),
        struct.pack("<I", 1) + stream_record("::$DATA", 1)[4:],
        struct.pack("<I", 8) + stream_record("::$DATA", 1)[4:],
        struct.pack("<I", 65536) + stream_record("::$DATA", 1)[4:],
    ],
)
def test_malformed_stream_metadata_is_rejected(raw):
    with pytest.raises(ValueError):
        parse_stream_buffer(raw)


@native
def test_native_space_observation_uses_full_width_values(tmp_path):
    result = available_space(tmp_path)
    assert set(result) == {"available_bytes", "total_bytes", "volume_free_bytes"}
    assert all(type(value) is int and 0 <= value < 2**64 for value in result.values())
    assert result["available_bytes"] <= result["total_bytes"]


@native
def test_nonexistent_space_query_cannot_invent_a_zero_observation(tmp_path):
    with pytest.raises(OSError):
        available_space(tmp_path / "missing")


@native
def test_empty_workspace_has_a_complete_zero_observation(tmp_path, limits):
    result = measure_workspace(tmp_path, limits)
    assert result == {
        "complete": True,
        "logical_bytes": 0,
        "entries": 0,
        "files": 0,
        "directories": 0,
        "streams": 0,
        "measurement": "stopped_workspace_data_stream_lengths",
    }


@native
def test_workspace_measurement_includes_profile_caches_without_reading_content(tmp_path, limits, monkeypatch):
    (tmp_path / "plain").write_bytes(b"abc")
    cache = tmp_path / ".trial-profile/cache"
    cache.mkdir(parents=True)
    (cache / "data").write_bytes(b"12345")

    def reject_content_reads(*_args, **_kwargs):
        raise AssertionError("Storage accounting must not read file contents")

    monkeypatch.setattr(WorkspaceReader, "read_file", reject_content_reads)
    result = measure_workspace(tmp_path, limits)
    assert result["complete"] and result["logical_bytes"] == 8
    assert (result["files"], result["directories"], result["streams"], result["entries"]) == (2, 2, 2, 6)


@native
def test_named_streams_on_file_and_root_are_included(tmp_path, limits):
    file = tmp_path / "plain"
    file.write_bytes(b"abc")
    Path(str(file) + ":payload").write_bytes(b"12345")
    Path(str(tmp_path) + ":root-payload").write_bytes(b"1234567")
    result = measure_workspace(tmp_path, limits)
    assert result["complete"] and result["logical_bytes"] == 15
    assert (result["files"], result["directories"], result["streams"], result["entries"]) == (1, 0, 3, 4)


@native
def test_sparse_logical_growth_exceeds_budget_without_a_large_write(tmp_path, limits):
    file = tmp_path / "large-logical-file"
    with file.open("wb") as stream:
        stream.truncate(2 * 1024**2)
    with pytest.raises(WorkspaceStorageExceeded, match="workspace_logical_bytes_limit") as error:
        measure_workspace(tmp_path, limits)
    observed = error.value.observation
    assert observed["complete"] is False and observed["logical_bytes"] == 2 * 1024**2
    assert file.stat().st_size == 2 * 1024**2


@native
def test_object_limit_retains_a_partial_count(tmp_path):
    (tmp_path / "plain").write_bytes(b"abc")
    with pytest.raises(WorkspaceStorageExceeded, match="workspace_entries_limit") as error:
        measure_workspace(tmp_path, StorageLimits(1, 1024, 1))
    assert error.value.observation["complete"] is False
    assert error.value.observation["entries"] == 2


@native
def test_hardlinked_file_is_rejected_instead_of_assuming_exclusive_storage(tmp_path, limits):
    original = tmp_path / "plain"
    original.write_bytes(b"abc")
    (tmp_path / "alias").hardlink_to(original)
    with pytest.raises(ValueError, match="one link"):
        measure_workspace(tmp_path, limits)


@native
def test_native_space_api_failure_is_retained_as_an_error(tmp_path, monkeypatch):
    import _windows_storage_budget as storage

    original = storage.Native.function

    def injected_failure(self, module, name, arguments, result):
        if name == "GetDiskFreeSpaceExW":

            def fail(*_args):
                set_last_error(5)
                return 0

            return fail
        return original(self, module, name, arguments, result)

    monkeypatch.setattr(storage.Native, "function", injected_failure)
    with pytest.raises(OSError) as error:
        available_space(tmp_path)
    assert getattr(error.value, "winerror", None) == 5


@native
@pytest.mark.parametrize("succeeded", [0, 1])
def test_documented_stream_eof_is_handled_for_both_native_return_values(succeeded):
    from _windows_storage_budget import data_streams

    def query(*_args):
        set_last_error(38)
        return succeeded

    reader = cast(WorkspaceReader, SimpleNamespace(kernel=SimpleNamespace(GetFileInformationByHandleEx=query)))
    assert data_streams(reader, None) == {}


@native
def test_stream_eof_with_nonempty_metadata_is_rejected():
    from _windows_storage_budget import data_streams

    def query(_handle, _kind, buffer, _length):
        buffer[0] = b"x"
        set_last_error(38)
        return 1

    reader = cast(WorkspaceReader, SimpleNamespace(kernel=SimpleNamespace(GetFileInformationByHandleEx=query)))
    with pytest.raises(ValueError, match="EOF contradicts"):
        data_streams(reader, None)


@native
def test_stream_buffer_exhaustion_is_an_error_instead_of_partial_measurement():
    from _windows_storage_budget import data_streams

    def query(*_args):
        set_last_error(234)
        return 0

    reader = cast(WorkspaceReader, SimpleNamespace(kernel=SimpleNamespace(GetFileInformationByHandleEx=query)))
    with pytest.raises(OSError) as error:
        data_streams(reader, None)
    assert getattr(error.value, "winerror", None) == 234


def test_space_polling_is_bounded_and_explicit_checks_bypass_the_interval(tmp_path, limits, monkeypatch):
    import _windows_storage_budget as storage

    calls = []
    clock = [1.0]

    def sample(path):
        calls.append(path)
        return {"available_bytes": 2 * 1024**3, "total_bytes": 4 * 1024**3, "volume_free_bytes": 3 * 1024**3}

    monkeypatch.setattr(storage, "available_space", sample)
    monkeypatch.setattr(storage.time, "monotonic", lambda: clock[0])
    budget = SpaceBudget(limits, (tmp_path, tmp_path))
    assert budget.check() is None and calls == [tmp_path]
    for _ in range(100):
        assert budget.check() is None
    assert calls == [tmp_path]
    clock[0] += 0.5
    assert budget.check() is None and len(calls) == 2
    budget.require_available()
    assert len(calls) == 3 and budget.record()["polls"] == 3


def test_free_space_limit_is_latched_and_cannot_be_erased_by_later_capacity(tmp_path, monkeypatch):
    import _windows_storage_budget as storage

    values = iter((100, 5, 100))
    calls = []

    def sample(path):
        calls.append(path)
        return {"available_bytes": next(values), "total_bytes": 1000, "volume_free_bytes": 100}

    monkeypatch.setattr(storage, "available_space", sample)
    budget = SpaceBudget(StorageLimits(10, 1000, 100), (tmp_path,))
    budget.require_available()
    assert budget.check(force=True) == "free_space_limit"
    assert budget.check(force=True) == "free_space_limit" and len(calls) == 2
    observed = budget.record()
    assert observed["samples"][str(tmp_path)]["lowest_available_bytes"] == 5
    observed["samples"][str(tmp_path)]["lowest_available_bytes"] = 999
    assert budget.record()["samples"][str(tmp_path)]["lowest_available_bytes"] == 5
    with pytest.raises(ValueError, match="free_space_limit"):
        budget.require_available()


def test_space_observation_failure_retains_previous_samples_and_does_not_become_zero(tmp_path, monkeypatch):
    import _windows_storage_budget as storage

    def sample(_path):
        return {"available_bytes": 100, "total_bytes": 1000, "volume_free_bytes": 100}

    monkeypatch.setattr(storage, "available_space", sample)
    budget = SpaceBudget(StorageLimits(10, 1000, 100), (tmp_path,))
    budget.require_available()

    def fail(_path):
        raise ValueError("owned injected observation failure")

    monkeypatch.setattr(storage, "available_space", fail)
    assert budget.check(force=True) == "storage_observation_error"
    observed = budget.record()
    assert observed["samples"][str(tmp_path)]["available_bytes"] == 100
    assert observed["observation_error"]["error_type"] == "ValueError"
    assert observed["observation_error"]["winerror"] is None
    assert budget.check(force=True) == "storage_observation_error"


def test_every_declared_location_is_observed(tmp_path, monkeypatch):
    import _windows_storage_budget as storage

    other = tmp_path / "other"
    other.mkdir()
    calls = []

    def sample(path):
        calls.append(path)
        return {"available_bytes": 100 if path == tmp_path else 5, "total_bytes": 1000, "volume_free_bytes": 100}

    monkeypatch.setattr(storage, "available_space", sample)
    budget = SpaceBudget(StorageLimits(10, 1000, 100), (tmp_path, other))
    assert budget.check(force=True) == "free_space_limit" and calls == [tmp_path, other]
    assert budget.record()["samples"][str(other)]["available_bytes"] == 5


@pytest.mark.parametrize("count", [0, 9])
def test_space_budget_requires_a_small_explicit_location_set(tmp_path, limits, count):
    with pytest.raises(ValueError, match="one to eight"):
        SpaceBudget(limits, (tmp_path,) * count)

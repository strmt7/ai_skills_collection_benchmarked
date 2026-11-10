from __future__ import annotations

import os
import struct
import sys

import pytest
from _trial_collection_policy import collection_policy, default_collection_policy, scope_allows
from _windows_directory_reader import directory_entries, inventory, parse_directory_buffer
from _windows_submission_reader import WorkspaceReader


def record(name: str, *, following: int = 0, attributes: int = 0x80, size: int = 3) -> bytes:
    encoded = name.encode("utf-16-le")
    return struct.pack("<II6qIII", following, 0, 1, 2, 3, 4, size, size, attributes, len(encoded), 0) + encoded


def test_parser_preserves_unicode_names_without_using_unstable_file_indexes():
    assert [item.name for item in parse_directory_buffer(record("δεδομένα-🧪.py"))] == ["δεδομένα-🧪.py"]
    first = record("first", following=80)
    second = record("second")
    assert [item.name for item in parse_directory_buffer(first + b"\0" * (80 - len(first)) + second)] == [
        "first",
        "second",
    ]
    assert parse_directory_buffer(record(".")) == []


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"\0" * 68,
        record("x", following=1),
        record("x", following=64),
        record("x", following=99999),
        record("x")[:-1],
        record("../x"),
        record("x\0y"),
    ],
)
def test_invalid_native_directory_records_are_rejected(data):
    with pytest.raises((ValueError, UnicodeError)):
        parse_directory_buffer(data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("max_files", True),
        ("max_total_bytes", 0),
        ("max_depth", 129),
        ("max_file_bytes", 8 * 1024**2 + 1),
        ("excluded_directory_names", ["src"]),
        ("excluded_directory_names", ["__pycache__", "__pycache__"]),
    ],
)
def test_collection_policy_rejects_unbounded_or_undeclared_inputs(field, value):
    policy = default_collection_policy()
    policy[field] = value
    with pytest.raises(ValueError):
        collection_policy(policy)


def test_directory_scopes_match_boundaries_and_windows_case_identity():
    assert scope_allows("tests/new.py", ["tests/"])
    assert scope_allows("TESTS/nested/new.py", ["tests/"])
    assert scope_allows("code.py", ["CODE.py"])
    assert not scope_allows("tests2/new.py", ["tests/"])
    assert not scope_allows("code.py.extra", ["code.py"])


native = pytest.mark.skipif(sys.platform != "win32", reason="Windows native handle enumeration")


@native
def test_native_enumeration_reads_multiple_pages_and_keeps_unicode(tmp_path):
    expected = {f"case-{index:04}.txt" for index in range(900)} | {"δοκιμή-🧪.txt"}
    for name in expected:
        (tmp_path / name).write_bytes(b"abc")
    with WorkspaceReader(tmp_path, enumerate_directories=True) as reader:
        assert {entry.name for entry in directory_entries(reader, "")} == expected
        assert {entry.name for entry in directory_entries(reader, "")} == expected
        observed, excluded, directories = inventory(reader, default_collection_policy())
        assert set(observed) == expected and excluded == [] and directories == []
        assert all(entry.size == 3 for entry in observed.values())


@native
def test_native_reader_holds_all_selected_files_and_rewinds_repeated_reads(tmp_path):
    (tmp_path / "a").write_bytes(b"first")
    (tmp_path / "b").write_bytes(b"second")
    with WorkspaceReader(tmp_path, enumerate_directories=True) as reader:
        for name in ("a", "b"):
            reader.open_file(name, max_bytes=100)
        assert reader.read_file("a", max_bytes=100) == b"first"
        assert reader.read_file("a", max_bytes=100) == b"first"
        for name in ("a", "b"):
            with pytest.raises(OSError):
                (tmp_path / name).write_bytes(b"replaced")
    (tmp_path / "a").write_bytes(b"released")
    with pytest.raises(ValueError, match="not open"):
        reader.read_file("a", max_bytes=100)
    with pytest.raises(ValueError, match="reused"), reader:
        pass


@native
def test_inventory_records_exclusions_without_traversing_their_contents(tmp_path):
    for name in (".trial-profile", "__pycache__", ".pytest_cache"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "unselected").write_bytes(b"private fixture")
    (tmp_path / ".git").write_bytes(b"gitdir: outside")
    (tmp_path / "code.py").write_bytes(b"source")
    with WorkspaceReader(tmp_path, enumerate_directories=True) as reader:
        files, excluded, directories = inventory(reader, default_collection_policy())
        assert set(files) == {"code.py"}
        assert directories == []
        assert {entry["path"] for entry in excluded} == {".trial-profile", ".git", "__pycache__", ".pytest_cache"}


@native
@pytest.mark.parametrize(
    "field,value",
    [("max_files", 1), ("max_directories", 1), ("max_file_bytes", 1), ("max_total_bytes", 1), ("max_depth", 1)],
)
def test_native_inventory_stops_at_each_frozen_budget(tmp_path, field, value):
    (tmp_path / "nested/deeper").mkdir(parents=True)
    (tmp_path / "a").write_bytes(b"abc")
    (tmp_path / "b").write_bytes(b"abc")
    policy = default_collection_policy()
    policy[field] = value
    with (
        WorkspaceReader(tmp_path, enumerate_directories=True) as reader,
        pytest.raises(ValueError, match="limit|budget"),
    ):
        inventory(reader, policy)


@native
def test_full_tree_inventory_does_not_make_a_hardlink_readable(tmp_path):
    outside = tmp_path / "owned-canary"
    outside.write_bytes(b"private")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    os.link(outside, workspace / "linked")
    with WorkspaceReader(workspace, enumerate_directories=True) as reader:
        files, _, _ = inventory(reader, default_collection_policy())
        assert set(files) == {"linked"}
        with pytest.raises(ValueError, match="one link"):
            reader.open_file("linked", max_bytes=100)
    assert outside.read_bytes() == b"private"

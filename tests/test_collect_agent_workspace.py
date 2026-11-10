from __future__ import annotations

import ctypes
import hashlib
import os
import sys
from ctypes import wintypes

import pytest
from _trial_collection_policy import default_collection_policy
from _windows_submission_reader import WorkspaceReader
from collect_agent_workspace import capture

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows native source capture")


def test_complete_capture_retains_new_files_binary_bytes_and_empty_directories(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "src/nested").mkdir(parents=True)
    (workspace / "src/old.py").write_bytes(b"old")
    (workspace / "src/old.py").unlink()
    (workspace / "src/new.py").write_bytes(b"new\n")
    (workspace / "binary.bin").write_bytes(b"\xff\0\x01")
    (workspace / ".trial-profile").mkdir()
    (workspace / ".trial-profile/private").write_bytes(b"not source")
    output = tmp_path / "captured"
    result = capture(workspace, output, default_collection_policy())
    assert result["status"] == "collected" and result["file_count"] == 2
    assert set(result["files"]) == {"src/new.py", "binary.bin"}
    assert result["total_bytes"] == 7
    for name, original in {"src/new.py": b"new\n", "binary.bin": b"\xff\0\x01"}.items():
        assert (output / name).read_bytes() == original
        assert result["files"][name] == {"sha256": hashlib.sha256(original).hexdigest(), "bytes": len(original)}
    assert result["excluded"] == [{"path": ".trial-profile", "reason": "agent_runtime_profile"}]
    assert result["post_inventory_matches"] is True and result["atomic_snapshot"] is False
    assert result["directories"] == ["src", "src/nested"]
    assert (output / "src/nested").is_dir() and list((output / "src/nested").iterdir()) == []
    assert not (output / "src/old.py").exists()


def test_hardlink_rejection_happens_before_any_output_is_created(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "a").write_bytes(b"ordinary")
    outside = tmp_path / "owned-canary"
    outside.write_bytes(b"private")
    os.link(outside, workspace / "z")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="one link"):
        capture(workspace, output, default_collection_policy())
    assert not output.exists() and outside.read_bytes() == b"private"


def test_namespace_addition_during_copy_cannot_produce_a_complete_receipt(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "source.py").write_bytes(b"source")
    original = WorkspaceReader.read_file

    def changed(reader, name, **kwargs):
        (workspace / "unexpected.py").write_bytes(b"late")
        return original(reader, name, **kwargs)

    monkeypatch.setattr(WorkspaceReader, "read_file", changed)
    with pytest.raises(ValueError, match="changed during capture"):
        capture(workspace, tmp_path / "output", default_collection_policy())


@pytest.mark.parametrize("target", ["inside", "ancestor", "existing"])
def test_capture_refuses_overlapping_or_preexisting_output(tmp_path, target):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    output = {"inside": workspace / "output", "ancestor": tmp_path, "existing": tmp_path / "already"}[target]
    if target == "existing":
        output.mkdir()
    with pytest.raises(ValueError, match="disjoint|already exists"):
        capture(workspace, output, default_collection_policy())


def test_held_handle_graph_closes_every_handle_across_repeated_snapshots(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "a").write_bytes(b"source")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetProcessHandleCount.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetProcessHandleCount.restype = wintypes.BOOL
    kernel.GetCurrentProcess.restype = wintypes.HANDLE

    def handles():
        result = wintypes.DWORD()
        assert kernel.GetProcessHandleCount(kernel.GetCurrentProcess(), ctypes.byref(result))
        return result.value

    capture(workspace, tmp_path / "warm", default_collection_policy())
    before = handles()
    for index in range(30):
        capture(workspace, tmp_path / f"snapshot-{index}", default_collection_policy())
    assert handles() == before


def test_path_metadata_budget_is_enforced_before_copy(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "longer-than-one-byte").write_bytes(b"source")
    policy = default_collection_policy()
    policy["max_total_path_bytes"] = 1
    with pytest.raises(ValueError, match="path bytes"):
        capture(workspace, tmp_path / "output", policy)


@pytest.mark.parametrize("location", ["root", "nested", "excluded-cache", "parent"])
def test_directory_junctions_are_rejected_without_reading_the_owned_canary(tmp_path, monkeypatch, location):
    import _winapi

    outside = tmp_path / "canary"
    outside.mkdir()
    (outside / "private.txt").write_bytes(b"owned private control")
    workspace = tmp_path / "workspace"
    if location == "root":
        link = workspace
    elif location == "parent":
        (outside / "subject").mkdir()
        link, workspace = tmp_path / "alias", tmp_path / "alias/subject"
    else:
        workspace.mkdir()
        link = workspace / (".pytest_cache" if location == "excluded-cache" else "nested")
    _winapi.CreateJunction(str(outside), str(link))
    monkeypatch.setattr(WorkspaceReader, "read_file", lambda *args, **kwargs: pytest.fail("no file read is permitted"))
    try:
        with pytest.raises(ValueError):
            capture(workspace, tmp_path / "output", default_collection_policy())
        assert not (tmp_path / "output").exists()
        assert (outside / "private.txt").read_bytes() == b"owned private control"
    finally:
        link.rmdir()


def test_capture_preserves_a_nested_source_path_beyond_max_path(tmp_path):
    workspace = tmp_path / "workspace"
    relative = "/".join(["component" * 5] * 7) + "/unicode-\u03bb.txt"
    source = workspace / relative
    source.parent.mkdir(parents=True)
    source.write_bytes(b"long path control")
    assert len(str(source)) > 260
    output = tmp_path / "output"
    result = capture(workspace, output, default_collection_policy())
    assert set(result["files"]) == {relative}
    assert (output / relative).read_bytes() == b"long path control"

from __future__ import annotations

import mmap
import os
import sys
from pathlib import Path

import pytest
from _windows_submission_reader import open_submission, open_workspace_file, read_submission, read_workspace_file

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows native handle boundary")


def workspace(tmp_path: Path, content: bytes = b"print('safe')\n") -> Path:
    root = tmp_path / "workspace"
    (root / "tools").mkdir(parents=True)
    (root / "tools/check_benchmark_artifact.py").write_bytes(content)
    return root


def test_regular_submission_is_read_without_changing_it(tmp_path):
    root = workspace(tmp_path)
    assert read_submission(root) == b"print('safe')\n"
    assert (root / "tools/check_benchmark_artifact.py").read_bytes() == b"print('safe')\n"


def test_open_handles_deny_rename_and_write_until_collection_finishes(tmp_path):
    root = workspace(tmp_path)
    source = root / "tools/check_benchmark_artifact.py"
    with open_submission(root):
        with pytest.raises(OSError):
            source.write_bytes(b"changed")
        with pytest.raises(OSError):
            (root / "tools").rename(root / "renamed")
    assert source.read_bytes() == b"print('safe')\n"
    (root / "tools").rename(root / "renamed")
    assert (root / "renamed/check_benchmark_artifact.py").read_bytes() == b"print('safe')\n"


def test_existing_writer_prevents_collection(tmp_path):
    root = workspace(tmp_path)
    source = root / "tools/check_benchmark_artifact.py"
    with source.open("r+b"), pytest.raises((ValueError, OSError)):
        read_submission(root)
    assert source.read_bytes() == b"print('safe')\n"


def test_hardlinked_submission_is_rejected_without_touching_source(tmp_path):
    root = workspace(tmp_path)
    source = root / "tools/check_benchmark_artifact.py"
    outside = tmp_path / "outside.py"
    outside.write_bytes(b"private sentinel\n")
    source.unlink()
    os.link(outside, source)
    with pytest.raises(ValueError, match="one link"):
        read_submission(root)
    assert outside.read_bytes() == b"private sentinel\n"


def test_oversized_submission_is_rejected(tmp_path):
    root = workspace(tmp_path, b"x" * (1024 * 1024 + 1))
    with pytest.raises(ValueError, match="size limit"):
        read_submission(root)


def test_empty_submission_remains_readable(tmp_path):
    root = workspace(tmp_path, b"")
    assert read_submission(root) == b""


def test_explicit_workspace_files_are_collected_without_changing_them(tmp_path):
    root = workspace(tmp_path)
    nested = root / "tests/deep/regressions.py"
    nested.parent.mkdir(parents=True)
    nested.write_bytes(b"independent tests\n")
    assert read_workspace_file(root, "tests/deep/regressions.py", max_bytes=128) == b"independent tests\n"
    assert nested.read_bytes() == b"independent tests\n"


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "../outside",
        "tests/../outside",
        "/outside",
        "C:/outside",
        "tests\\outside",
        "tests//file",
        "tests/file.",
    ],
)
def test_noncanonical_workspace_paths_are_rejected(tmp_path, name):
    root = workspace(tmp_path)
    with pytest.raises(ValueError):
        read_workspace_file(root, name, max_bytes=128)


def test_workspace_file_rejects_hardlinks_and_concurrent_writers(tmp_path):
    root = workspace(tmp_path)
    source = root / "tests/regressions.py"
    source.parent.mkdir()
    source.write_bytes(b"test")
    with source.open("r+b"), pytest.raises((ValueError, OSError)):
        read_workspace_file(root, "tests/regressions.py", max_bytes=128)
    outside = tmp_path / "outside"
    source.rename(outside)
    os.link(outside, source)
    with pytest.raises(ValueError, match="one link"):
        read_workspace_file(root, "tests/regressions.py", max_bytes=128)
    assert outside.read_bytes() == b"test"


def test_workspace_file_rejects_a_live_writable_mapping(tmp_path):
    root = workspace(tmp_path)
    source = root / "tools/check_benchmark_artifact.py"
    with source.open("r+b") as stream:
        mapping = mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_WRITE)
    try:
        with pytest.raises((ValueError, OSError)):
            read_workspace_file(root, "tools/check_benchmark_artifact.py", max_bytes=128)
    finally:
        mapping.close()
    assert source.read_bytes() == b"print('safe')\n"


def test_workspace_file_holds_all_ancestors_until_read_is_finished(tmp_path):
    root = workspace(tmp_path)
    path = root / "tests/deep/regressions.py"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"test")
    with open_workspace_file(root, "tests/deep/regressions.py", max_bytes=128):
        with pytest.raises(OSError):
            (root / "tests").rename(root / "moved")
        with pytest.raises(OSError):
            path.write_bytes(b"changed")
    assert path.read_bytes() == b"test"


def test_workspace_file_enforces_explicit_size_bound(tmp_path):
    root = workspace(tmp_path)
    with pytest.raises(ValueError, match="limit"):
        read_workspace_file(root, "tools/check_benchmark_artifact.py", max_bytes=4)
    for limit in (-1, True, 8 * 1024 * 1024 + 1):
        with pytest.raises(ValueError, match="limit"):
            read_workspace_file(root, "tools/check_benchmark_artifact.py", max_bytes=limit)


def test_workspace_file_accepts_large_bounded_task_input(tmp_path):
    root = workspace(tmp_path)
    source = root / "catalog.json"
    data = b"x" * (4 * 1024 * 1024)
    source.write_bytes(data)
    assert read_workspace_file(root, "catalog.json", max_bytes=len(data)) == data


def make_symlink(target: Path, link: Path, *, directory: bool = False) -> None:
    try:
        os.symlink(target, link, target_is_directory=directory)
    except OSError as error:
        if getattr(error, "winerror", None) in {50, 1314}:
            pytest.skip("Windows does not permit creating this symbolic link")
        raise


def test_file_reparse_point_is_rejected(tmp_path):
    root = workspace(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_bytes(b"private sentinel\n")
    source = root / "tools/check_benchmark_artifact.py"
    source.unlink()
    make_symlink(outside, source)
    with pytest.raises((ValueError, OSError)):
        read_submission(root)
    assert outside.read_bytes() == b"private sentinel\n"


def test_root_reparse_point_is_rejected(tmp_path):
    root = workspace(tmp_path)
    link = tmp_path / "alias"
    make_symlink(root, link, directory=True)
    with pytest.raises((ValueError, OSError)):
        read_submission(link)
    assert (root / "tools/check_benchmark_artifact.py").read_bytes() == b"print('safe')\n"


def test_ancestor_reparse_point_is_rejected(tmp_path):
    parent = tmp_path / "actual"
    parent.mkdir()
    root = workspace(parent)
    alias = tmp_path / "alias"
    make_symlink(parent, alias, directory=True)
    with pytest.raises((ValueError, OSError)):
        read_submission(alias / root.name)
    assert (root / "tools/check_benchmark_artifact.py").read_bytes() == b"print('safe')\n"


def test_tools_reparse_point_is_rejected(tmp_path):
    root = workspace(tmp_path)
    outside = tmp_path / "actual-tools"
    (root / "tools").rename(outside)
    make_symlink(outside, root / "tools", directory=True)
    with pytest.raises((ValueError, OSError)):
        read_submission(root)
    assert (outside / "check_benchmark_artifact.py").read_bytes() == b"print('safe')\n"


def test_workspace_nested_reparse_point_is_rejected(tmp_path):
    root = workspace(tmp_path)
    outside = tmp_path / "outside-dir"
    outside.mkdir()
    (outside / "file.py").write_bytes(b"sentinel")
    (root / "tests").mkdir()
    make_symlink(outside, root / "tests/link", directory=True)
    with pytest.raises((ValueError, OSError)):
        read_workspace_file(root, "tests/link/file.py", max_bytes=128)
    assert (outside / "file.py").read_bytes() == b"sentinel"

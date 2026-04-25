"""Logic tests proving the catalog tree hash is host-agnostic.

A previous implementation embedded ``stat.st_mode`` directly, which made every
tree hash depend on the clone's umask. This test flips the mode bits on a
temporary tree and asserts the resulting hash is identical, so we can't silently
regress to host-sensitive behaviour.
"""

from __future__ import annotations

import stat
from pathlib import Path

import build_catalog  # tools/ on sys.path via conftest.py


def _write_fixture(root: Path, mode_group_world: int) -> None:
    """Create a deterministic fixture tree with the requested group/world bits.

    Layout:
        root/
          SKILL.md
          scripts/run.sh   <- executable bit
          docs/note.md
    """
    root.mkdir(parents=True, exist_ok=True)
    (root / "SKILL.md").write_text("# skill\n", encoding="utf-8")
    (root / "scripts").mkdir()
    run_sh = root / "scripts" / "run.sh"
    run_sh.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "docs" / "note.md").write_text("note\n", encoding="utf-8")

    base = 0o600 | mode_group_world
    for path in (root / "SKILL.md", root / "docs" / "note.md"):
        path.chmod(base)
    # Preserve the exec bit on run.sh; the portable-mode function must still
    # distinguish executables from regular files.
    run_sh.chmod(base | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def test_sha256_tree_independent_of_umask_group_world_bits(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    _write_fixture(a, mode_group_world=0o044)  # 644 equivalent
    _write_fixture(b, mode_group_world=0o060)  # 664 equivalent (what `berfarto54` sees)
    assert build_catalog.sha256_tree(a) == build_catalog.sha256_tree(b)


def test_sha256_tree_changes_when_executable_bit_is_added(tmp_path):
    a = tmp_path / "a"
    _write_fixture(a, mode_group_world=0o044)
    before = build_catalog.sha256_tree(a)
    # Remove exec bit from the script, forcing the portable mode to flip.
    script = a / "scripts" / "run.sh"
    script.chmod(script.stat().st_mode & ~0o111)
    after = build_catalog.sha256_tree(a)
    assert before != after, "exec-bit flip must produce a different tree hash"


def test_sha256_tree_changes_when_file_content_changes(tmp_path):
    a = tmp_path / "a"
    _write_fixture(a, mode_group_world=0o044)
    before = build_catalog.sha256_tree(a)
    (a / "docs" / "note.md").write_text("note\ndifferent line\n", encoding="utf-8")
    after = build_catalog.sha256_tree(a)
    assert before != after, "content change must produce a different tree hash"


def test_sha256_tree_is_stable_on_repeat_runs(tmp_path):
    a = tmp_path / "a"
    _write_fixture(a, mode_group_world=0o044)
    hashes = {build_catalog.sha256_tree(a) for _ in range(4)}
    assert len(hashes) == 1, "repeated runs on unchanged input must return the same hash"


def test_portable_mode_maps_regular_files_to_0644(tmp_path):
    path = tmp_path / "f"
    path.write_text("x", encoding="utf-8")
    path.chmod(0o600)
    st = path.stat().st_mode
    assert build_catalog._portable_mode(st) == 0o100644


def test_portable_mode_maps_any_exec_bit_to_0755(tmp_path):
    path = tmp_path / "f"
    path.write_text("x", encoding="utf-8")
    for extra in (0o100, 0o010, 0o001):
        path.chmod(0o600 | extra)
        assert build_catalog._portable_mode(path.stat().st_mode) == 0o100755

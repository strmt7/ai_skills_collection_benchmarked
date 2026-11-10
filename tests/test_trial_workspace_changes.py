"""Independent namespace expectations for realistic additions and deletions."""

from __future__ import annotations

import hashlib

import pytest
from _trial_collection_policy import default_collection_policy
from _trial_patch import diagnostic_patch
from _trial_workspace_changes import workspace_changes


def namespace(files, directories=()):
    return {
        "collection_version": 1,
        "status": "collected",
        "policy": default_collection_policy(),
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for name, data in files.items()
        },
        "directories": sorted(directories),
        "directory_count": len(directories),
        "excluded": [],
        "file_count": len(files),
        "total_bytes": sum(map(len, files.values())),
        "post_inventory_matches": True,
        "atomic_snapshot": False,
        "precondition": "All subject execution must be stopped before capture.",
    }


def declaration(inputs, scopes, scaffolds=None):
    return {
        "collection_policy": default_collection_policy(),
        "task": {"files": list(inputs), "allowed_changes": scopes},
        "input_sha256": {name: hashlib.sha256(data).hexdigest() for name, data in inputs.items()},
        "workspace_scaffold": scaffolds or {},
    }


def test_additions_deletions_and_empty_directories_have_explicit_changes():
    protocol = declaration({"src/remove.py": b"old", "keep.txt": b"same"}, ["src/", "tests/"])
    manifest = namespace({"src/add.py": b"new", "keep.txt": b"same"}, ["src", "tests", "tests/empty"])
    changes, source, violations = workspace_changes(protocol, manifest)
    assert [(item["path"], item["object"], item["kind"]) for item in changes] == [
        ("src/add.py", "file", "created"),
        ("src/remove.py", "file", "deleted"),
        ("tests/", "directory", "created"),
        ("tests/empty/", "directory", "created"),
    ]
    assert changes[0]["before_sha256"] is None and changes[1]["after_sha256"] is None
    assert source == ["src/remove.py"] and violations == []


@pytest.mark.parametrize("scope", ["src/", "SRC/"])
def test_directory_scopes_respect_boundaries_and_include_nested_files(scope):
    manifest = namespace({"src/deep/a.py": b"a", "src-extra/b.py": b"b"}, ["src", "src/deep", "src-extra"])
    _, _, violations = workspace_changes(declaration({}, [scope]), manifest)
    assert violations == ["unauthorized directory created: src-extra/", "unauthorized file created: src-extra/b.py"]


def test_exact_file_scope_allows_necessary_parents_without_allowing_siblings():
    manifest = namespace({"new/deep/a.py": b"a", "new/deep/b.py": b"b"}, ["new", "new/deep"])
    _, _, violations = workspace_changes(declaration({}, ["new/deep/a.py"]), manifest)
    assert violations == ["unauthorized file created: new/deep/b.py"]


def test_deleted_protected_inputs_scaffolds_and_parents_are_not_omitted():
    protocol = declaration({"src/a.py": b"a"}, [], {"tests/control.txt": "original"})
    changes, source, violations = workspace_changes(protocol, namespace({}))
    assert {item["path"] for item in changes} == {"src/", "src/a.py", "tests/", "tests/control.txt"}
    assert source == ["src/a.py"]
    assert violations == [
        "protected scaffold changed: tests/control.txt",
        "protected source input changed: src/a.py",
        "unauthorized directory deleted: src/",
        "unauthorized directory deleted: tests/",
    ]


def test_case_only_rename_does_not_conceal_deletion_of_a_protected_input():
    _, source, violations = workspace_changes(declaration({"code.py": b"same"}, []), namespace({"CODE.py": b"same"}))
    assert source == ["code.py"]
    assert violations == ["protected source input changed: code.py", "unauthorized file created: CODE.py"]


def test_diagnostic_diff_shows_additions_and_deletions_without_reading_deleted_files():
    changes = [
        {"path": "a.py", "object": "file", "kind": "deleted"},
        {"path": "b.py", "object": "file", "kind": "created"},
    ]
    patch, record = diagnostic_patch(
        {"a.py": b"old\n"}, namespace({"b.py": b"new\n"}), changes, lambda name: {"b.py": b"new\n"}[name]
    )
    assert b"--- a/a.py\n+++ /dev/null\n" in patch and b"--- /dev/null\n+++ b/b.py\n" in patch
    assert record["complete"] is True and record["omitted_paths"] == []


@pytest.mark.parametrize("data", [b"\0binary", b"\xff", b"a" * (128 * 1024 + 1), b"x\n" * 2049])
def test_diagnostic_omissions_are_explicit_and_do_not_change_captured_identity(data):
    manifest = namespace({"data": data})
    patch, record = diagnostic_patch(
        {}, manifest, [{"path": "data", "object": "file", "kind": "created"}], lambda name: data
    )
    assert patch == b"" and record["complete"] is False and record["omitted_paths"] == ["data"]
    assert manifest["files"]["data"]["sha256"] == hashlib.sha256(data).hexdigest()


def test_diagnostic_time_budget_omits_later_diffs_explicitly(monkeypatch):
    import _trial_patch

    values = iter([0.0, 3.0])
    monkeypatch.setattr(_trial_patch.time, "monotonic", lambda: next(values))
    patch, record = diagnostic_patch(
        {},
        namespace({"a": b"a"}),
        [{"path": "a", "object": "file", "kind": "created"}],
        lambda name: pytest.fail("budgeted bytes must not be read"),
    )
    assert patch == b"" and record["omitted_paths"] == ["a"]

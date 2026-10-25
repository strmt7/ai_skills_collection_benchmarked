from __future__ import annotations

import hashlib

import build_catalog as builder
import pytest

COMMIT = "a" * 40


def notice_file(tmp_path):
    path = tmp_path / "artifacts/source-notices/upstream/LICENSE"
    path.parent.mkdir(parents=True)
    content = b"Copyright holder\nPermission and disclaimer.\n"
    path.write_bytes(content)
    return path, {
        "path": path.relative_to(tmp_path).as_posix(),
        "source_path": "LICENSE",
        "commit_sha": COMMIT,
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def test_verbatim_notice_is_admitted_without_rewriting_its_bytes(tmp_path):
    path, record = notice_file(tmp_path)
    before = path.read_bytes()
    assert builder.validate_preserved_notice(tmp_path, record, COMMIT) == record
    assert path.read_bytes() == before
    assert builder.validate_preserved_notice(tmp_path, None, COMMIT) is None


@pytest.mark.parametrize("mutation", ["changed", "missing", "crlf"])
def test_notice_drift_is_rejected(tmp_path, mutation):
    path, record = notice_file(tmp_path)
    if mutation == "missing":
        path.unlink()
    elif mutation == "crlf":
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    else:
        path.write_bytes(b"Different notice\n")
    with pytest.raises(ValueError, match="notice"):
        builder.validate_preserved_notice(tmp_path, record, COMMIT)


def test_notice_cannot_be_reused_for_a_different_source_commit(tmp_path):
    _, record = notice_file(tmp_path)
    with pytest.raises(ValueError, match="commit"):
        builder.validate_preserved_notice(tmp_path, record, "b" * 40)


@pytest.mark.parametrize("source_path", ["../LICENSE", ".", "/LICENSE", "sub\\LICENSE", "C:/LICENSE"])
def test_upstream_notice_path_cannot_escape_its_source(tmp_path, source_path):
    _, record = notice_file(tmp_path)
    record["source_path"] = source_path
    with pytest.raises(ValueError, match="canonical"):
        builder.validate_preserved_notice(tmp_path, record, COMMIT)


def test_notice_destination_must_stay_in_owned_notice_directory(tmp_path):
    _, record = notice_file(tmp_path)
    record["path"] = "README.md"
    with pytest.raises(ValueError, match="inside"):
        builder.validate_preserved_notice(tmp_path, record, COMMIT)

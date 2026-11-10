"""Independent full-inventory admission and extraction contracts."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

import _bootstrap_archive as archive
import pytest


def fixture(tmp_path: Path, entries: list[tuple[str, bytes, bytes]]):
    stream = io.BytesIO()
    files = {}
    with tarfile.open(fileobj=stream, mode="w:gz") as writer:
        for name, content, kind in entries:
            info = tarfile.TarInfo(name)
            info.type = kind
            info.size = len(content) if kind == tarfile.REGTYPE else 0
            if kind == tarfile.SYMTYPE:
                info.linkname = "../outside"
            writer.addfile(info, io.BytesIO(content) if kind == tarfile.REGTYPE else None)
            if kind == tarfile.REGTYPE:
                files[name] = {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}
    raw = stream.getvalue()
    source = tmp_path / "source.tar.gz"
    source.write_bytes(raw)
    return source, {
        "format": "tar-gzip",
        "archive_bytes": len(raw),
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "archive_files": files,
    }


def test_complete_archive_is_extracted_without_modifying_source(tmp_path):
    source, pin = fixture(tmp_path, [("python/hello.txt", b"hello", tarfile.REGTYPE)])
    before = source.read_bytes()
    output = tmp_path / "payload"
    assert archive.extract(source, pin, output) == 1
    assert (output / "hello.txt").read_bytes() == b"hello" and source.read_bytes() == before


@pytest.mark.parametrize(
    "name",
    [
        "python/../escape",
        "python/C:escape",
        "python/CON.txt",
        "python/a./b",
        "python/a\\b",
        "other/file",
        "python//file",
    ],
)
def test_noncanonical_source_is_rejected_before_output_is_created(tmp_path, name):
    source, pin = fixture(tmp_path, [(name, b"hello", tarfile.REGTYPE)])
    output = tmp_path / "payload"
    with pytest.raises(ValueError, match="noncanonical"):
        archive.extract(source, pin, output)
    assert not output.exists()


@pytest.mark.parametrize(
    "entries",
    [
        [("python/link", b"", tarfile.SYMTYPE)],
        [("python/hello", b"a", tarfile.REGTYPE), ("python/HELLO", b"b", tarfile.REGTYPE)],
        [("python/hello", b"a", tarfile.REGTYPE), ("python/hello/child", b"b", tarfile.REGTYPE)],
    ],
)
def test_links_case_collisions_and_parent_collisions_are_refused(tmp_path, entries):
    source, pin = fixture(tmp_path, entries)
    with pytest.raises(ValueError):
        archive.extract(source, pin, tmp_path / "payload")
    assert not (tmp_path / "payload").exists()


@pytest.mark.parametrize(
    "change", ["archive-digest", "archive-length", "member-digest", "member-length", "missing", "extra"]
)
def test_outer_hash_cannot_replace_complete_member_admission(tmp_path, change):
    source, pin = fixture(tmp_path, [("python/hello", b"hello", tarfile.REGTYPE)])
    if change == "archive-digest":
        pin["archive_sha256"] = "0" * 64
    elif change == "archive-length":
        pin["archive_bytes"] += 1
    elif change == "member-digest":
        pin["archive_files"]["python/hello"]["sha256"] = "0" * 64
    elif change == "member-length":
        pin["archive_files"]["python/hello"]["bytes"] = 6
    elif change == "missing":
        pin["archive_files"]["python/missing"] = {"bytes": 0, "sha256": hashlib.sha256(b"").hexdigest()}
    else:
        pin["archive_files"] = {}
    with pytest.raises(ValueError):
        archive.extract(source, pin, tmp_path / "payload")
    assert not (tmp_path / "payload").exists()


def test_existing_output_is_not_adopted_or_changed(tmp_path):
    source, pin = fixture(tmp_path, [("python/hello", b"hello", tarfile.REGTYPE)])
    output = tmp_path / "payload"
    output.mkdir()
    (output / "canary").write_bytes(b"preserve")
    with pytest.raises(FileExistsError):
        archive.extract(source, pin, output)
    assert sorted(path.name for path in output.iterdir()) == ["canary"]
    assert (output / "canary").read_bytes() == b"preserve"


def test_source_replacement_after_admission_cannot_change_the_extracted_snapshot(tmp_path, monkeypatch):
    source, pin = fixture(tmp_path, [("python/hello", b"original", tarfile.REGTYPE)])
    inspect = archive.inspect

    def replace_source(raw, selected):
        observed = inspect(raw, selected)
        source.write_bytes(b"replaced after admission")
        return observed

    monkeypatch.setattr(archive, "inspect", replace_source)
    output = tmp_path / "payload"
    assert archive.extract(source, pin, output) == 1
    assert (output / "hello").read_bytes() == b"original"


def test_entrypoint_reports_exact_admission_and_failures_as_json(tmp_path, capsys):
    source, pin = fixture(tmp_path, [("python/hello", b"hello", tarfile.REGTYPE)])
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"pythons": {"3.13.18": pin}}), encoding="utf-8")
    args = [
        "--archive",
        str(source),
        "--manifest",
        str(manifest),
        "--python",
        "3.13.18",
        "--output",
        str(tmp_path / "payload"),
    ]
    assert archive.main(args) == 0
    assert json.loads(capsys.readouterr().out) == {"ok": True, "admitted_files": 1}
    assert archive.main(args) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False

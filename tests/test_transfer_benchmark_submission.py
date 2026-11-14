from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest
from _trial_collection_policy import default_collection_policy
from transfer_benchmark_submission import main, plan_handoff, restore, seal


def _snapshot(root: Path, files: dict[str, bytes], empty: tuple[str, ...] = ()) -> bytes:
    root.mkdir()
    for name in empty:
        (root / name).mkdir(parents=True)
    for name, data in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    directories = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_dir())
    return json.dumps(
        {
            "collection_version": 1,
            "status": "collected",
            "policy": default_collection_policy(),
            "files": {
                name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)} for name, data in files.items()
            },
            "directories": directories,
            "directory_count": len(directories),
            "excluded": [],
            "file_count": len(files),
            "total_bytes": sum(map(len, files.values())),
            "post_inventory_matches": True,
            "atomic_snapshot": False,
            "precondition": "All subject execution must be stopped before capture.",
        }
    ).encode()


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_rebuilds_add_modify_delete_and_empty_directories(tmp_path: Path) -> None:
    base, candidate = tmp_path / "base", tmp_path / "candidate"
    previous = _snapshot(base, {"unchanged": b"same", "src/replaced": b"old", "removed": b"absent"}, ("old-empty",))
    current = _snapshot(candidate, {"unchanged": b"same", "src/replaced": b"new", "tests/added": b""}, ("new-empty",))
    handoff = plan_handoff(previous, current)
    bundle, twin, output = tmp_path / "delta.tar", tmp_path / "twin.tar", tmp_path / "grader"
    sealed = seal(handoff, candidate, bundle)
    assert seal(handoff, candidate, twin) == sealed
    assert bundle.read_bytes() == twin.read_bytes()
    assert sealed["deletes"] == ["removed"]
    assert set(sealed["writes"]) == {"src/replaced", "tests/added"}
    with tarfile.open(bundle) as archive:
        assert archive.getnames() == ["manifest.json", "payload/src/replaced", "payload/tests/added"]
    rebuilt = restore(handoff, base, bundle, sealed["archive_sha256"], output)
    assert rebuilt["file_count"] == 3
    assert sorted(path.relative_to(output).as_posix() for path in output.rglob("*")) == [
        "new-empty",
        "src",
        "src/replaced",
        "tests",
        "tests/added",
        "unchanged",
    ]
    assert (output / "src/replaced").read_bytes() == b"new"
    assert (output / "unchanged").read_bytes() == b"same"
    assert (base / "removed").is_file()


def test_completed_unchanged_capture_has_a_valid_empty_delta(tmp_path: Path) -> None:
    baseline = tmp_path / "base"
    frozen = _snapshot(baseline, {"task.py": b"unchanged"})
    handoff = plan_handoff(frozen, frozen)
    bundle = tmp_path / "empty.tar"
    result = seal(handoff, baseline, bundle)
    assert result["writes"] == {} and result["deletes"] == []
    with tarfile.open(bundle) as archive:
        assert archive.getnames() == ["manifest.json"]
    output = tmp_path / "reconstructed"
    restore(handoff, baseline, bundle, result["archive_sha256"], output)
    assert (output / "task.py").read_bytes() == b"unchanged"


def test_completed_zero_file_capture_can_delete_entire_source(tmp_path: Path) -> None:
    original, submitted = tmp_path / "base", tmp_path / "submitted"
    handoff = plan_handoff(_snapshot(original, {"src/main.py": b"content"}), _snapshot(submitted, {}))
    bundle = tmp_path / "empty-tree.tar"
    report = seal(handoff, submitted, bundle)
    assert report["writes"] == {} and report["deletes"] == ["src/main.py"]
    output = tmp_path / "output"
    restored = restore(handoff, original, bundle, report["archive_sha256"], output)
    assert restored["file_count"] == 0
    assert list(output.iterdir()) == []


@pytest.mark.parametrize("status", ["collection_error", "collected"])
def test_incomplete_collection_cannot_become_empty_delta(tmp_path: Path, status: str) -> None:
    baseline = _snapshot(tmp_path / "base", {})
    with pytest.raises(ValueError, match="completion contract"):
        plan_handoff(baseline, json.dumps({"status": status, "files": {}}).encode())


def test_failed_seal_cleans_created_archive_and_preserves_existing_archive(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    baseline = _snapshot(tmp_path / "baseline", {"same": b"a"})
    frozen = _snapshot(candidate, {"same": b"a", "changed": b"b"})
    handoff = plan_handoff(baseline, frozen)
    (candidate / "same").write_bytes(b"tampered")
    bundle = tmp_path / "delta.tar"
    with pytest.raises(ValueError, match="bytes differ"):
        seal(handoff, candidate, bundle)
    assert not bundle.exists()
    bundle.write_bytes(b"other output")
    with pytest.raises(FileExistsError):
        seal(handoff, candidate, bundle)
    assert bundle.read_bytes() == b"other output"


def test_seal_rejects_an_extra_object_even_with_no_changes(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate"
    frozen = _snapshot(candidate, {})
    handoff = plan_handoff(frozen, frozen)
    (candidate / "unexpected").touch()
    with pytest.raises(ValueError, match="undeclared entry"):
        seal(handoff, candidate, tmp_path / "bad.tar")


def test_restore_rejects_a_different_archive_digest_without_output(tmp_path: Path) -> None:
    baseline = tmp_path / "base"
    frozen = _snapshot(baseline, {"file": b"x"})
    handoff = plan_handoff(frozen, frozen)
    bundle = tmp_path / "delta.tar"
    report = seal(handoff, baseline, bundle)
    with bundle.open("ab") as stream:
        stream.write(b"extra bytes")
    output = tmp_path / "out"
    with pytest.raises(ValueError, match="controller's digest"):
        restore(handoff, baseline, bundle, report["archive_sha256"], output)
    assert not output.exists()


def test_restore_rolls_back_when_verified_shape_has_tampered_payload(tmp_path: Path) -> None:
    baseline, candidate = tmp_path / "base", tmp_path / "candidate"
    frozen = _snapshot(baseline, {})
    submission = _snapshot(candidate, {"new": b"abc"})
    handoff = plan_handoff(frozen, submission)
    bundle, tampered = tmp_path / "delta.tar", tmp_path / "tampered.tar"
    seal(handoff, candidate, bundle)
    with tarfile.open(bundle) as source, tarfile.open(tampered, "w") as output:
        for member in source:
            stream = source.extractfile(member)
            assert stream is not None
            with stream:
                data = b"xyz" if member.name == "payload/new" else stream.read()
            output.addfile(member, io.BytesIO(data))
    destination = tmp_path / "output"
    with pytest.raises(ValueError, match="payload differs"):
        restore(handoff, baseline, tampered, _digest(tampered), destination)
    assert not destination.exists()


def test_restore_verifies_baseline_even_when_changed_file_will_be_replaced(tmp_path: Path) -> None:
    baseline, candidate = tmp_path / "base", tmp_path / "candidate"
    frozen = _snapshot(baseline, {"old": b"original"})
    submission = _snapshot(candidate, {"old": b"edited"})
    handoff = plan_handoff(frozen, submission)
    bundle = tmp_path / "delta.tar"
    report = seal(handoff, candidate, bundle)
    (baseline / "old").write_bytes(b"changed after freeze")
    with pytest.raises(ValueError, match="bytes differ"):
        restore(handoff, baseline, bundle, report["archive_sha256"], tmp_path / "output")


def test_cli_refuses_output_inside_collected_source(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    candidate = tmp_path / "candidate"
    record = tmp_path / "record.json"
    record.write_bytes(_snapshot(candidate, {}))
    output = candidate / "inside.tar"
    status = main(
        [
            "--baseline-manifest",
            str(record),
            "--submission-manifest",
            str(record),
            "seal",
            "--submission-tree",
            str(candidate),
            "--bundle",
            str(output),
        ]
    )
    assert status == 2
    assert json.loads(capsys.readouterr().out)["status"] == "handoff_unverified"
    assert not output.exists()

"""Reject residual detected material before writing exact selected mirror bytes."""

import hashlib
import json

import build_catalog as catalog
import check_mirror_content_admission as admission
import pytest


def shaped_value():
    # Construct a disposable detector input, never a live or committed token.
    return ("gh" + "p_" + "independentFixture" * 3).encode()


@pytest.mark.parametrize("carrier", ["replacement", "binary", "entropy"])
def test_detected_content_is_rejected_before_writing(tmp_path, carrier):
    source = tmp_path / "source"
    source.mkdir()
    resource = source / "example.txt"
    resource.write_bytes(b"approved original\n")
    replacements = None
    if carrier == "replacement":
        attempted = b"token=" + shaped_value()
        replacements = {resource.name: attempted}
    elif carrier == "binary":
        attempted = b"\0token=" + shaped_value() + b"\xff\0"
        resource.write_bytes(attempted)
    else:
        attempted = b"password=" + hashlib.sha256(b"independent admission control").hexdigest().encode()
        resource.write_bytes(attempted)
    original = resource.read_bytes()
    destination = tmp_path / "destination"
    destination.mkdir()
    target = destination / resource.name
    target.write_bytes(b"retain existing public bytes\n")
    with pytest.raises(ValueError, match="publishable content rejected") as rejected:
        catalog.copy_sanitized_tree(source, destination, replacements=replacements)
    assert target.read_bytes() == b"retain existing public bytes\n"
    assert resource.read_bytes() == original
    assert shaped_value().decode() not in str(rejected.value)
    assert attempted.decode(errors="replace") not in str(rejected.value)


def test_declared_neutralization_and_replacement_bytes_are_preserved(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    resource = source / "example.txt"
    original = b"token=" + shaped_value() + b"\n"
    resource.write_bytes(original)
    destination = tmp_path / "destination"
    catalog.copy_sanitized_tree(source, destination)
    assert (destination / resource.name).read_bytes() == b"token=<GITHUB_TOKEN>\n"
    replacement = b' {"description": "Use <TOKEN>", "version": "2.0.0"} \n'
    catalog.copy_sanitized_tree(source, destination, replacements={resource.name: replacement})
    assert (destination / resource.name).read_bytes() == replacement
    assert resource.read_bytes() == original


@pytest.mark.parametrize("encoding", ["utf-16-le", "utf-16-be", "utf-32-le", "utf-32-be"])
def test_encoded_replacement_is_rejected_before_write(tmp_path, encoding):
    source = tmp_path / "source"
    source.mkdir()
    (source / "example.txt").write_bytes(b"approved original\n")
    destination = tmp_path / "destination"
    destination.mkdir()
    target = destination / "example.txt"
    target.write_bytes(b"retain existing public bytes\n")
    marker = shaped_value().decode()
    attempted = ("token=" + marker).encode(encoding)
    with pytest.raises(ValueError) as rejected:
        catalog.copy_sanitized_tree(source, destination, replacements={"example.txt": attempted})
    assert marker not in str(rejected.value)
    assert target.read_bytes() == b"retain existing public bytes\n"


@pytest.mark.parametrize("mode", ["accepted", "binary", "external", "empty"])
def test_complete_mirror_gate_collects_boundaries_and_binary_findings(tmp_path, mode):
    mirror = tmp_path / "included/skills/example"
    mirror.mkdir(parents=True)
    (mirror / "SKILL.md").write_bytes(b"Use <TOKEN>\n")
    if mode == "empty":
        (mirror / "SKILL.md").unlink()
    if mode == "binary":
        (mirror / "asset.bin").write_bytes(b"\0" + shaped_value() + b"\xff")
    (tmp_path / "data").mkdir()
    record = {"mirrored_path": "../external" if mode == "external" else "included/skills/example"}
    (tmp_path / "data/skills_catalog.json").write_text(json.dumps([record]), encoding="utf-8")
    report = admission.check(tmp_path)
    assert report["ok"] is (mode == "accepted")
    assert report["checked_resources"] == {"accepted": 1, "binary": 2, "external": 0, "empty": 0}[mode]
    assert len(report["errors"]) == int(mode != "accepted")
    assert shaped_value().decode() not in json.dumps(report)


def test_mirror_gate_cli_rejects_empty_catalog(tmp_path, capsys):
    (tmp_path / "data").mkdir()
    (tmp_path / "data/skills_catalog.json").write_text("[]", encoding="utf-8")
    assert admission.main(["--root", str(tmp_path), "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False

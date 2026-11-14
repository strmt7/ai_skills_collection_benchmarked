from __future__ import annotations

import hashlib
import io
import json
import tarfile
from collections.abc import Sequence
from email.message import Message
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal

import _native_replay_assets as assets
import pytest
from _native_image_archive import validate_image_archive
from test_native_image_archive import archive_fixture


def write_tar(
    path: Path, entries: Sequence[tuple[tarfile.TarInfo, bytes | None]], mode: Literal["w", "w:gz"] = "w"
) -> None:
    with tarfile.open(path, mode, format=tarfile.PAX_FORMAT) as archive:
        for member, body in entries:
            archive.addfile(member, io.BytesIO(body) if body is not None else None)


def test_untagging_changes_only_the_existing_manifest_data_extent(tmp_path: Path) -> None:
    packet = tmp_path / "image.tar"
    _, identity = archive_fixture(packet, "tag")
    before = packet.read_bytes()
    with tarfile.open(packet) as archive:
        manifest = archive.getmember("manifest.json")
        start, end = manifest.offset_data, manifest.offset_data + manifest.size
    result = assets.remove_owned_tag(packet, "owner/existing:latest")
    after = packet.read_bytes()
    assert len(after) == len(before) and after[:start] == before[:start] and after[end:] == before[end:]
    assert result["RepoTags"] == []
    validate_image_archive(packet, hashlib.sha256(after).hexdigest(), identity)


def test_unexpected_tag_is_rejected_without_a_write(tmp_path: Path) -> None:
    packet = tmp_path / "image.tar"
    archive_fixture(packet, "tag")
    before = packet.read_bytes()
    with pytest.raises(ValueError, match="owned assembly tag"):
        assets.remove_owned_tag(packet, "different:tag")
    assert packet.read_bytes() == before


@pytest.mark.parametrize("missing_license", [False, True])
def test_crane_requires_the_complete_pinned_distribution(tmp_path: Path, missing_license: bool) -> None:
    packet = tmp_path / "crane.tgz"
    bodies = {"crane.exe": b"synthetic unit fixture, never executed"}
    if not missing_license:
        bodies["LICENSE"] = b"fixture license"
    entries = []
    for name, body in bodies.items():
        member = tarfile.TarInfo(name)
        member.size = len(body)
        entries.append((member, body))
    write_tar(packet, entries, "w:gz")
    pin = {
        "archive_bytes": packet.stat().st_size,
        "archive_sha256": assets.file_sha256(packet),
        "files": {
            name: {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()} for name, body in bodies.items()
        },
    }
    if missing_license:
        with pytest.raises(ValueError, match="Incomplete"):
            assets.admit_crane(packet, pin, tmp_path / "payload")
    else:
        executable = assets.admit_crane(packet, pin, tmp_path / "payload")
        assert executable.read_bytes() == bodies["crane.exe"]
        assert executable.with_name("LICENSE").read_bytes() == bodies["LICENSE"]


def node_fixture(tmp_path: Path, link: str = "node") -> tuple[Path, dict[str, Any]]:
    body = b"node executable fixture\n"
    source = []
    expected = []
    for source_name, target_name, kind, data in (
        ("node-fixture", "opt/benchmark-node", tarfile.DIRTYPE, None),
        ("node-fixture/bin/node", "opt/benchmark-node/bin/node", tarfile.REGTYPE, body),
        ("node-fixture/bin/npm", "opt/benchmark-node/bin/npm", tarfile.SYMTYPE, None),
    ):
        original = tarfile.TarInfo(source_name)
        original.type = kind
        original.mode = 0o755
        original.uid = original.gid = 42
        original.mtime = 9999
        original.size = len(data) if data is not None else 0
        original.linkname = link if kind == tarfile.SYMTYPE else ""
        source.append((original, data))
        target = tarfile.TarInfo(target_name)
        target.type = kind
        target.mode = 0o755
        target.mtime = 1234
        target.size = len(data) if data is not None else 0
        target.linkname = original.linkname
        expected.append((target, data))
    packet, reference = tmp_path / "node.tgz", tmp_path / "reference.tar"
    write_tar(packet, source, "w:gz")
    write_tar(reference, expected)
    return packet, {
        "archive_bytes": packet.stat().st_size,
        "archive_sha256": assets.file_sha256(packet),
        "package_prefix": "node-fixture",
        "layer_epoch": 1234,
        "layer_sha256": assets.file_sha256(reference),
        "layer_entries": 3,
        "expanded_bytes": len(body),
    }


def test_node_layer_is_repeatable_and_keeps_unix_modes_and_safe_links(tmp_path: Path) -> None:
    packet, pin = node_fixture(tmp_path)
    one, two = tmp_path / "one.tar", tmp_path / "two.tar"
    assert assets.node_layer(packet, pin, one) == assets.node_layer(packet, pin, two)
    assert one.read_bytes() == two.read_bytes() == (tmp_path / "reference.tar").read_bytes()
    with tarfile.open(one) as archive:
        members = archive.getmembers()
        assert all(
            member.uid == member.gid == 0 and member.mtime == 1234 and member.mode == 0o755 for member in members
        )
        assert members[-1].issym() and members[-1].linkname == "node"


def test_node_layer_rejects_an_escaping_link(tmp_path: Path) -> None:
    packet, pin = node_fixture(tmp_path, "../../outside")
    with pytest.raises(ValueError, match="escapes"):
        assets.node_layer(packet, pin, tmp_path / "layer.tar")


@pytest.mark.parametrize("complete", [True, False])
def test_download_retains_short_transfer_bytes_without_admitting_them(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, complete: bool
) -> None:
    class Response(io.BytesIO):
        status = 200
        url = "https://nodejs.org/dist/fixture.tgz"
        headers: dict[str, str] = {}

    raw = b"fixture archive bytes"
    delivered = raw if complete else raw[:-1]
    monkeypatch.setattr(
        assets.urllib.request,
        "build_opener",
        lambda *args: SimpleNamespace(open=lambda *args, **kwargs: Response(delivered)),
    )
    pin = {"url": Response.url, "archive_bytes": len(raw), "archive_sha256": hashlib.sha256(raw).hexdigest()}
    target = tmp_path / "download"
    if complete:
        assert assets.download(pin, target)["sha256"] == pin["archive_sha256"]
    else:
        with pytest.raises(ValueError, match="differs"):
            assets.download(pin, target)
    assert target.read_bytes() == delivered
    receipt = json.loads(target.with_name(target.name + ".capture.json").read_bytes())
    assert receipt["admitted"] is complete and receipt["bytes"] == len(delivered)


def test_denied_download_preserves_bounded_native_response(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    url = "https://nodejs.org/dist/fixture.tgz"
    body = b"publisher denied fixture"
    response = io.BytesIO(body)

    def denied(*args: Any, **kwargs: Any) -> None:
        raise assets.urllib.error.HTTPError(url, 403, "Forbidden", Message(), response)

    monkeypatch.setattr(assets.urllib.request, "build_opener", lambda *args: SimpleNamespace(open=denied))
    target = tmp_path / "download"
    with pytest.raises(assets.urllib.error.HTTPError):
        assets.download({"url": url, "archive_bytes": 4}, target)
    receipt = json.loads(target.with_name(target.name + ".capture.json").read_bytes())
    assert not receipt["admitted"] and receipt["status"] == 403 and receipt["bytes"] == 0
    assert target.with_name(target.name + ".http-error.native").read_bytes() == body
    assert response.closed


def test_download_rejects_unrelated_publishers_before_network_access(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="official publisher"):
        assets.download({"url": "https://example.org/fixture", "archive_bytes": 4}, tmp_path / "download")
    assert not (tmp_path / "download").exists()

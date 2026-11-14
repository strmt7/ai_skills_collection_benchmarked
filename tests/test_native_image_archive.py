from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest
from _native_image_archive import validate_image_archive


def archive_fixture(path: Path, change: str = "") -> tuple[str, str]:
    content = b"fixture application data\n"
    uncompressed = io.BytesIO()
    with tarfile.open(fileobj=uncompressed, mode="w") as inner:
        member = tarfile.TarInfo("app.txt")
        member.size = len(content)
        inner.addfile(member, io.BytesIO(content))
    layer = gzip.compress(uncompressed.getvalue(), mtime=0)
    digest = hashlib.sha256(layer).hexdigest()
    config = json.dumps(
        {
            "os": "windows" if change == "platform" else "linux",
            "architecture": "amd64",
            "rootfs": {"type": "layers", "diff_ids": ["sha256:" + hashlib.sha256(uncompressed.getvalue()).hexdigest()]},
        }
    ).encode()
    identity = "sha256:" + hashlib.sha256(config).hexdigest()
    config_name = identity
    layer_name = digest + ".tar.gz"
    manifest = [{"Config": config_name, "RepoTags": [], "Layers": [layer_name]}]
    if change == "tag":
        manifest[0]["RepoTags"] = ["owner/existing:latest"]
    if change == "multiple":
        manifest *= 2
    entries = [(config_name, config), (layer_name, b"wrong layer" if change == "layer" else layer)]
    if change == "traversal":
        entries.append(("../outside", b"unexpected"))
    if change == "extra":
        entries.append(("a" * 64 + ".tar", b"undeclared"))
    if change == "duplicate":
        entries.append(entries[0])
    entries.append(("manifest.json", json.dumps(manifest).encode()))
    with tarfile.open(path, "w") as archive:
        for name, body in entries:
            member = tarfile.TarInfo(name)
            member.size = len(body)
            archive.addfile(member, io.BytesIO(body))
    return hashlib.sha256(path.read_bytes()).hexdigest(), identity


def test_admits_one_untagged_content_addressed_linux_image(tmp_path: Path) -> None:
    path = tmp_path / "image.tar"
    digest, identity = archive_fixture(path)
    validate_image_archive(path, digest, identity)


@pytest.mark.parametrize("change", ["platform", "tag", "multiple", "layer", "traversal", "extra", "duplicate"])
def test_rejects_archives_that_could_load_unintended_content(tmp_path: Path, change: str) -> None:
    path = tmp_path / "image.tar"
    digest, identity = archive_fixture(path, change)
    with pytest.raises(ValueError):
        validate_image_archive(path, digest, identity)


@pytest.mark.parametrize("changed", ["archive", "identity"])
def test_requires_both_archive_and_configuration_identity(tmp_path: Path, changed: str) -> None:
    path = tmp_path / "image.tar"
    digest, identity = archive_fixture(path)
    with pytest.raises(ValueError, match="differs"):
        validate_image_archive(
            path,
            "0" * 64 if changed == "archive" else digest,
            "sha256:" + "0" * 64 if changed == "identity" else identity,
        )

"""Validate a content-addressed, untagged local benchmark image before loading it."""

from __future__ import annotations

import hashlib
import re
import tarfile
from pathlib import Path
from typing import IO

from _trial_transcript import strict_json


def _digest_stream(stream: IO[bytes]) -> str:
    digest = hashlib.sha256()
    while block := stream.read(1024**2):
        digest.update(block)
    return digest.hexdigest()


def validate_image_archive(path: Path, expected_sha256: str, image_id: str) -> None:
    """Admit one Linux AMD64 image without changing any existing engine tags."""
    if not re.fullmatch(r"[a-f0-9]{64}", expected_sha256) or not re.fullmatch(r"sha256:[a-f0-9]{64}", image_id):
        raise ValueError("Malformed local image digest")
    if not 0 < path.stat().st_size <= 2 * 1024**3:
        raise ValueError("Local image archive exceeds its byte budget")
    with path.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != expected_sha256:
            raise ValueError("Local image archive differs from its declared digest")
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r:") as archive:
            members: dict[str, tarfile.TarInfo] = {}
            for member in archive:
                if (
                    not member.isfile()
                    or member.name in members
                    or len(members) >= 130
                    or not re.fullmatch(
                        r"manifest\.json|(?:sha256:)?[a-f0-9]{64}(?:\.json|\.tar(?:\.gz)?)?", member.name
                    )
                ):
                    raise ValueError("Unexpected local image archive resource")
                members[member.name] = member

            def read_json(name: str) -> object:
                if name not in members or members[name].size > 1024**2:
                    raise ValueError("Missing or oversized image metadata")
                source = archive.extractfile(members[name])
                if source is None:
                    raise ValueError("Missing image metadata bytes")
                with source:
                    return strict_json(source.read().decode("utf-8"))

            manifest = read_json("manifest.json")
            if not isinstance(manifest, list) or len(manifest) != 1 or not isinstance(manifest[0], dict):
                raise ValueError("Expected exactly one local image")
            item = manifest[0]
            if set(item) != {"Config", "RepoTags", "Layers"} or item["RepoTags"] not in (None, []):
                raise ValueError("Local image archive must be untagged")
            config_name, layers = item["Config"], item["Layers"]
            if (
                not isinstance(config_name, str)
                or not isinstance(layers, list)
                or not 1 <= len(layers) <= 128
                or any(not isinstance(name, str) for name in layers)
                or len(set(layers)) != len(layers)
                or set(members) != {"manifest.json", config_name, *layers}
            ):
                raise ValueError("Image resources differ from the manifest")
            config = read_json(config_name)
            source = archive.extractfile(members[config_name])
            if source is None:
                raise ValueError("Missing image configuration")
            with source:
                digest = _digest_stream(source)
            if "sha256:" + digest != image_id:
                raise ValueError("Local image configuration differs from the declared identity")
            if not isinstance(config, dict) or config.get("os") != "linux" or config.get("architecture") != "amd64":
                raise ValueError("Local image platform is incompatible")
            rootfs = config.get("rootfs")
            if (
                not isinstance(rootfs, dict)
                or rootfs.get("type") != "layers"
                or not isinstance(rootfs.get("diff_ids"), list)
                or len(rootfs["diff_ids"]) != len(layers)
                or any(
                    not isinstance(value, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", value)
                    for value in rootfs["diff_ids"]
                )
            ):
                raise ValueError("Local image filesystem metadata is inconsistent")
            for name in layers:
                if not re.fullmatch(r"[a-f0-9]{64}\.tar(?:\.gz)?", name):
                    raise ValueError("Expected content-addressed image layers")
                source = archive.extractfile(members[name])
                if source is None:
                    raise ValueError("Missing image layer bytes")
                with source:
                    if _digest_stream(source) != name.split(".", 1)[0]:
                        raise ValueError("Local image layer differs from its content address")

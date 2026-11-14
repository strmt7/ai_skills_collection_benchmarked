"""Pinned, private assets for the optional Windows native benchmark replay builder."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import posixpath
import re
import shutil
import tarfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath
from typing import Any

from _bootstrap_archive import ordinary


def file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class _ArchiveRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        target = urllib.parse.urlsplit(newurl)
        if target.scheme != "https" or target.hostname != "release-assets.githubusercontent.com":
            raise ValueError("Unexpected publisher archive redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(pin: dict[str, Any], path: Path) -> dict[str, Any]:
    """Retain partial transfers on failure; never execute an unverified download."""
    ordinary(path)
    if type(pin["archive_bytes"]) is not int or not 0 < pin["archive_bytes"] <= 128 * 1024**2:
        raise ValueError("Archive exceeds the replay download budget")
    url = pin["url"]
    endpoint = urllib.parse.urlsplit(url)
    if endpoint.scheme != "https" or endpoint.hostname not in {"github.com", "nodejs.org"}:
        raise ValueError("Expected a pinned official publisher endpoint")
    deadline = time.monotonic() + 180
    received = 0
    digest = hashlib.sha256()
    opener = urllib.request.build_opener(_ArchiveRedirect())
    request = urllib.request.Request(url, headers={"User-Agent": "ai-skills-collection-benchmarked/replay-setup"})
    receipt: dict[str, Any] = {"url": url, "admitted": False}
    try:
        with opener.open(request, timeout=30) as response, path.open("xb") as output:
            final = urllib.parse.urlsplit(response.url)
            receipt.update(final_host=final.hostname, status=response.status, server_date=response.headers.get("Date"))
            if (
                response.status != 200
                or final.scheme != "https"
                or final.hostname not in {endpoint.hostname, "release-assets.githubusercontent.com"}
            ):
                raise ValueError("Unexpected archive response")
            while block := response.read(1024**2):
                received += len(block)
                if received > pin["archive_bytes"] or time.monotonic() > deadline:
                    raise ValueError("Archive transfer exceeded its byte or time budget")
                output.write(block)
                digest.update(block)
        if received != pin["archive_bytes"] or digest.hexdigest() != pin["archive_sha256"]:
            raise ValueError("Archive differs from its publisher pin")
        receipt["admitted"] = True
        return receipt
    except (OSError, ValueError) as error:
        receipt.update(error_type=type(error).__name__, error=str(error))
        if isinstance(error, urllib.error.HTTPError):
            with error:
                body = error.read(65536)
            body_path = path.with_name(path.name + ".http-error.native")
            with body_path.open("xb") as writer:
                writer.write(body)
            receipt.update(
                status=error.code, error_body_bytes=len(body), error_body_sha256=hashlib.sha256(body).hexdigest()
            )
        raise
    finally:
        receipt.update(
            bytes=path.stat().st_size if path.exists() else 0, received_bytes=received, sha256=digest.hexdigest()
        )
        with path.with_name(path.name + ".capture.json").open("x", encoding="utf-8", newline="\n") as writer:
            json.dump(receipt, writer, indent=2)
            writer.write("\n")


def admit_crane(packet: Path, pin: dict[str, Any], output: Path) -> Path:
    """Admit the full publisher inventory, including its license, before execution."""
    if packet.stat().st_size != pin["archive_bytes"] or file_sha256(packet) != pin["archive_sha256"]:
        raise ValueError("Crane package differs from its pin")
    ordinary(output)
    output.mkdir()
    observed: dict[str, dict[str, Any]] = {}
    with tarfile.open(packet, "r|gz") as archive:
        for member in archive:
            expected = pin["files"].get(member.name)
            if (
                not re.fullmatch(r"[A-Za-z0-9_.-]+", member.name)
                or member.name in {".", ".."}
                or member.name.endswith(".")
                or PurePosixPath(member.name).name != member.name
                or not member.isfile()
                or member.name in observed
                or expected is None
                or member.size != expected["bytes"]
                or not 0 <= member.size <= 32 * 1024**2
                or len(observed) >= 8
            ):
                raise ValueError("Unexpected crane archive member")
            source = archive.extractfile(member)
            if source is None:
                raise ValueError("Missing crane member bytes")
            target = output / member.name
            ordinary(target)
            with source, target.open("xb") as writer:
                shutil.copyfileobj(source, writer, 1024**2)
            observed[member.name] = {"bytes": target.stat().st_size, "sha256": file_sha256(target)}
            if observed[member.name] != expected:
                raise ValueError("Crane member bytes differ from their pin")
    if observed != pin["files"] or "LICENSE" not in observed or "crane.exe" not in observed:
        raise ValueError("Incomplete crane distribution")
    return output / "crane.exe"


def node_layer(packet: Path, pin: dict[str, Any], output: Path) -> dict[str, Any]:
    """Preserve official Node bytes in a deterministic, non-extracted Linux layer."""
    if packet.stat().st_size != pin["archive_bytes"] or file_sha256(packet) != pin["archive_sha256"]:
        raise ValueError("Node package differs from its pin")
    ordinary(output)
    seen: set[str] = set()
    expanded = 0
    prefix = pin["package_prefix"]
    with (
        tarfile.open(packet, "r|gz") as source,
        output.open("xb") as stream,
        tarfile.open(fileobj=stream, mode="w", format=tarfile.PAX_FORMAT) as target,
    ):
        for member in source:
            name = member.name.rstrip("/")
            path = PurePosixPath(name)
            if (
                path.as_posix() != name
                or not path.parts
                or path.parts[0] != prefix
                or any(part in {".", ".."} for part in path.parts)
                or name in seen
                or not (member.isfile() or member.isdir() or member.issym())
            ):
                raise ValueError("Unexpected Node package member")
            seen.add(name)
            expanded += member.size
            if expanded > 512 * 1024**2 or len(seen) > 12000:
                raise ValueError("Node layer exceeds its resource budget")
            if member.issym():
                resolved = posixpath.normpath(posixpath.join(str(path.parent), member.linkname))
                if PurePosixPath(member.linkname).is_absolute() or not resolved.startswith(prefix + "/"):
                    raise ValueError("Node package symlink escapes its root")
            converted = copy.copy(member)
            converted.name = "opt/benchmark-node" + name[len(prefix) :]
            converted.uid = converted.gid = 0
            converted.uname = converted.gname = ""
            converted.mtime = pin["layer_epoch"]
            converted.pax_headers = {}
            converted.mode &= 0o777
            body = source.extractfile(member) if member.isfile() else None
            try:
                target.addfile(converted, body)
            finally:
                if body is not None:
                    body.close()
    digest = file_sha256(output)
    if digest != pin["layer_sha256"] or len(seen) != pin["layer_entries"] or expanded != pin["expanded_bytes"]:
        raise ValueError("Node layer differs from its qualified deterministic pin")
    return {"sha256": digest, "bytes": output.stat().st_size, "entries": len(seen), "expanded_bytes": expanded}


def remove_owned_tag(path: Path, expected_tag: str) -> dict[str, Any]:
    """Change only manifest bytes in place; no image or layer is extracted or copied."""
    ordinary(path)
    if not 0 < path.stat().st_size <= 2 * 1024**3:
        raise ValueError("Image archive exceeds its byte budget")
    with path.open("r+b") as stream, tarfile.open(fileobj=stream, mode="r:") as archive:
        items: list[tarfile.TarInfo] = []
        for member in archive:
            if len(items) >= 130:
                raise ValueError("Image archive exceeds its member budget")
            items.append(member)
        manifests = [member for member in items if member.name == "manifest.json"]
        if len(manifests) != 1 or not manifests[0].isfile() or manifests[0].size > 1024**2:
            raise ValueError("Expected one bounded image manifest")
        member = manifests[0]
        source = archive.extractfile(member)
        if source is None:
            raise ValueError("Missing image manifest bytes")
        with source:
            manifest = json.loads(source.read())
        if (
            not isinstance(manifest, list)
            or len(manifest) != 1
            or not isinstance(manifest[0], dict)
            or manifest[0].get("RepoTags") != [expected_tag]
        ):
            raise ValueError("Image archive does not have the owned assembly tag")
        manifest[0]["RepoTags"] = []
        raw = json.dumps(manifest, separators=(",", ":")).encode("utf-8")
        if len(raw) > member.size:
            raise ValueError("Untagged manifest exceeds its original extent")
        stream.seek(member.offset_data)
        stream.write(raw.ljust(member.size, b" "))
        stream.flush()
        os.fsync(stream.fileno())
    return manifest[0]

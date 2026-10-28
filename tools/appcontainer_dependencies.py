"""Prepare the pinned offline dependency graph for the modern confined grader."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import stat
import sys
import tarfile
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

import appcontainer_runtime as runtime
from _windows_appcontainer import checked_path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "toolchains/appcontainer-modern/source.json"
MAX_ARCHIVE = 16 * 1024 * 1024
MAX_EXPANDED = 20 * 1024 * 1024


def load_specification(path: Path = SOURCE) -> dict[str, Any]:
    """Read explicit path/digest records and reject ambiguous file inventories."""
    specification = json.loads(path.read_bytes())
    if not isinstance(specification, dict):
        raise ValueError("dependency specification must be an object")
    records = specification.get("files")
    if not isinstance(records, list) or not records:
        raise ValueError("dependency file inventory must be a nonempty list")
    files: dict[str, str] = {}
    for record in records:
        if (
            not isinstance(record, dict)
            or set(record) != {"path", "sha256"}
            or not isinstance(record["path"], str)
            or not isinstance(record["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"])
            or record["path"] in files
        ):
            raise ValueError("invalid or duplicate dependency file record")
        files[record["path"]] = record["sha256"]
    specification["files"] = files
    return specification


def _official_package_url(value: str) -> bool:
    parsed = urllib.parse.urlsplit(value)
    return (
        parsed.scheme == "https"
        and parsed.hostname == "files.pythonhosted.org"
        and parsed.port in (None, 443)
        and parsed.username is None
        and parsed.password is None
        and not parsed.query
        and not parsed.fragment
        and parsed.path.startswith("/packages/")
    )


class _OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request: Any, fp: Any, code: int, message: str, headers: Any, new_url: str) -> Any:
        if not _official_package_url(new_url):
            raise ValueError("dependency redirect leaves the official package host")
        return super().redirect_request(request, fp, code, message, headers, new_url)


def capture(item: dict[str, Any], archive_dir: Path | None) -> bytes:
    name = item["filename"]
    if not isinstance(name, str) or Path(name).name != name or ":" in name or "\\" in name:
        raise ValueError("invalid archive filename")
    size = item["bytes"]
    if type(size) is not int or not 0 < size <= MAX_ARCHIVE:
        raise ValueError("invalid archive byte budget")
    source: Any
    if archive_dir is not None:
        source = checked_path(archive_dir / name).open("rb")
    else:
        if not _official_package_url(item["url"]):
            raise ValueError("archive URL must identify the official HTTPS package host")
        source = urllib.request.build_opener(_OfficialRedirect()).open(item["url"], timeout=30)
    with source as response:
        if archive_dir is None and (response.status != 200 or not _official_package_url(response.geturl())):
            raise ValueError("archive response is outside the official package host")
        deadline = time.monotonic() + 120
        chunks: list[bytes] = []
        remaining = size
        while chunk := response.read(min(1024 * 1024, remaining + 1)):
            if time.monotonic() > deadline:
                raise TimeoutError("dependency archive capture timed out")
            remaining -= len(chunk)
            if remaining < 0:
                raise ValueError("dependency archive exceeds its pinned size")
            chunks.append(chunk)
    data = b"".join(chunks)
    if len(data) != size or hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise ValueError("dependency archive does not match its pinned bytes")
    return data


def install_archives(home: Path, specification: dict[str, Any], archive_dir: Path | None = None) -> None:
    """Capture exact archives, construct a deterministic bundle, and extract admitted bytes."""
    checked_path(home)
    home.mkdir(parents=True, exist_ok=False)
    packages = specification["packages"]
    if not isinstance(packages, list) or len({x["filename"] for x in packages}) != len(packages):
        raise ValueError("invalid dependency package list")
    data = {item["filename"]: capture(item, archive_dir) for item in packages}
    bundle = home / "dependencies.zip"
    with zipfile.ZipFile(bundle, "x", compression=zipfile.ZIP_STORED) as bundle_zip:
        for name in sorted(data):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            bundle_zip.writestr(info, data[name])
    if (
        bundle.stat().st_size != specification["archive_bytes"]
        or runtime.digest(bundle) != specification["archive_sha256"]
    ):
        raise ValueError("dependency bundle differs from its pinned bytes")
    destination = home / "runtime"
    destination.mkdir()
    expected = specification["files"]
    seen: set[str] = set()
    written: set[str] = set()
    total = 0

    def admit(name: str, content: bytes) -> None:
        nonlocal total
        relative = PurePosixPath(name)
        if (
            relative.is_absolute()
            or not relative.parts
            or any(part in {"", ".", ".."} or ":" in part or "\\" in part for part in relative.parts)
        ):
            raise ValueError("dependency archive contains an unsafe path")
        folded = str(relative).casefold()
        if folded in seen:
            raise ValueError("dependency archives contain duplicate paths")
        seen.add(folded)
        total += len(content)
        if total > MAX_EXPANDED or expected.get(str(relative)) != hashlib.sha256(content).hexdigest():
            raise ValueError("dependency file is unexpected or changed")
        target = destination.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        written.add(str(relative))

    for item in packages:
        name = item["filename"]
        if name.endswith(".whl"):
            with zipfile.ZipFile(io.BytesIO(data[name])) as wheel:
                for member in wheel.infolist():
                    if member.is_dir():
                        continue
                    mode = (member.external_attr >> 16) & 0xFFFF
                    if (
                        member.orig_filename != member.filename
                        or "\0" in member.orig_filename
                        or stat.S_ISLNK(mode)
                        or stat.S_IFMT(mode) not in (0, stat.S_IFREG)
                        or member.file_size > MAX_ARCHIVE
                        or member.filename.endswith(".pth")
                        or ".data/" in member.filename
                    ):
                        raise ValueError("unsupported dependency wheel member")
                    admit(member.filename, wheel.read(member))
        elif item["name"] == "PyYAML" and name.endswith(".tar.gz"):
            with tarfile.open(fileobj=io.BytesIO(data[name]), mode="r:gz") as archive:
                for tar_member in archive.getmembers():
                    if tar_member.name == "pyyaml-6.0.3/LICENSE":
                        target = "licenses/PyYAML-LICENSE"
                    elif tar_member.name.startswith("pyyaml-6.0.3/lib/yaml/") and tar_member.name.endswith(".py"):
                        parts = PurePosixPath(tar_member.name).parts
                        if len(parts) != 4 or any(part in {".", ".."} for part in parts):
                            raise ValueError("unsupported PyYAML source path")
                        target = "yaml/" + parts[-1]
                    else:
                        continue
                    if not tar_member.isfile() or tar_member.size > 1024 * 1024:
                        raise ValueError("unsupported PyYAML source member")
                    stream = archive.extractfile(tar_member)
                    if stream is None:
                        raise ValueError("missing PyYAML member bytes")
                    with stream:
                        admit(target, stream.read())
        else:
            raise ValueError("unsupported dependency archive")
    if written != set(expected):
        raise ValueError("dependency archive graph is incomplete")
    if errors := runtime.verify(home, specification):
        raise ValueError("; ".join(errors))
    (home / "source.json").write_text(json.dumps(specification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    runtime._prepare_private_home(home, specification)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "check"])
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path, help="Optional directory containing all exact pinned archives")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if sys.platform != "win32":
            raise ValueError("The confined dependency graph is qualified for Windows x64")
        home = checked_path(args.home)
        cache = checked_path(ROOT / ".venv")
        if home == cache or not home.is_relative_to(cache):
            raise ValueError("Dependency home must be a dedicated directory inside this clone's .venv")
        specification = load_specification()
        if args.command == "setup":
            install_archives(home, specification, checked_path(args.archive_dir) if args.archive_dir else None)
        errors = runtime.verify(home, specification)
        if not errors:
            with runtime.lease(home, specification):
                pass
        print(json.dumps({"errors": errors, "home": str(home), "files": len(specification["files"])}))
        return int(bool(errors))
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, zipfile.BadZipFile, tarfile.TarError) as error:
        print(json.dumps({"errors": [str(error)]}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

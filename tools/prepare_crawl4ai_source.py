#!/usr/bin/env python3
"""Prepare and verify the pinned, explicitly identified Crawl4AI source adaptation.

This tool never executes setup.py, builds a wheel, installs packages or changes
an existing provider. The upstream archive remains immutable.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import stat
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any

from _catalog_publication import checked_path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = "toolchains/crawl4ai"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def runtime_sources(pin: dict[str, Any]) -> dict[str, str]:
    entries = pin["runtime_files"]
    sources = {entry["path"]: entry["sha256"] for entry in entries}
    if not sources or len(sources) != len(entries):
        raise ValueError("runtime source inventory must contain unique files")
    return sources


def files(directory: Path) -> dict[str, str]:
    result = {}

    def fail(error: OSError) -> None:
        raise error

    for parent, directories, names in os.walk(directory, followlinks=False, onerror=fail):
        for name in directories + names:
            path = Path(parent) / name
            info = path.lstat()
            if path.is_symlink() or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError("source stage contains a link/reparse point")
            if name in names:
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("source stage contains a special file")
                result[path.relative_to(directory).as_posix()] = digest(path.read_bytes())
    return result


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("source adaptation anchor changed")
    return text.replace(old, new)


def adapt(source: dict[str, bytes], vendor: bytes, notice: bytes, version: str) -> dict[str, bytes]:
    """Apply only the three reviewed repairs and their version/license metadata."""
    result = source.copy()
    strategy = source["crawl4ai/async_crawler_strategy.py"].decode("utf-8")
    strategy = replace_once(
        strategy,
        "    return os.open(path, flags | os.O_NOFOLLOW)",
        "    from .catalog_download import open_download\n    return open_download(path, flags)",
    )
    anchor = '    safe_name = os.path.basename(filename or "")'
    strategy = replace_once(
        strategy,
        anchor,
        anchor + "\n    from .catalog_download import validate_download_name\n    validate_download_name(safe_name)",
    )
    result["crawl4ai/async_crawler_strategy.py"] = strategy.encode("utf-8")

    models = source["crawl4ai/models.py"].decode("utf-8")
    classes = [node for node in ast.parse(models).body if isinstance(node, ast.ClassDef) and node.name == "CrawlResult"]
    if len(classes) != 1:
        raise ValueError("CrawlResult source class changed")
    methods = [node for node in classes[0].body if isinstance(node, ast.FunctionDef) and node.name == "fit_html"]
    if len(methods) != 1 or len(methods[0].decorator_list) != 1:
        raise ValueError("conflicting fit_html property changed")
    method = methods[0]
    if ast.unparse(method.decorator_list[0]) != "property" or method.end_lineno is None:
        raise ValueError("fit_html is no longer the reviewed property")
    lines = models.splitlines(keepends=True)
    result["crawl4ai/models.py"] = "".join(
        lines[: method.decorator_list[0].lineno - 1] + lines[method.end_lineno :]
    ).encode("utf-8")

    browser = source["crawl4ai/browser_manager.py"].decode("utf-8")
    hidden = '            "--disable-blink-features=AutomationControlled",\n'
    if browser.count(hidden) != 2:
        raise ValueError("automation-hiding flag sites changed")
    browser = browser.replace(hidden, "")
    managed = "        # GPU flags disable WebGL which anti-bot sensors detect as headless."
    ordinary = "        if self.config.memory_saving_mode:"
    browser = replace_once(
        browser,
        managed,
        '        if config.enable_stealth:\n            flags.append("--disable-blink-features=AutomationControlled")\n'
        + managed,
    )
    browser = replace_once(
        browser,
        ordinary,
        '        if self.config.enable_stealth:\n            args.append("--disable-blink-features=AutomationControlled")\n\n'
        + ordinary,
    )
    result["crawl4ai/browser_manager.py"] = browser.encode("utf-8")
    result["crawl4ai/catalog_download.py"] = vendor
    result["crawl4ai/__version__.py"] = replace_once(
        source["crawl4ai/__version__.py"].decode("utf-8"), '__version__ = "0.9.5"', f'__version__ = "{version}"'
    ).encode("utf-8")
    result["pyproject.toml"] = replace_once(
        source["pyproject.toml"].decode("utf-8"),
        'license = "Apache-2.0"',
        'license = "Apache-2.0"\nlicense-files = ["LICENSE", "CATALOG_BUILD_NOTICE.txt"]',
    ).encode("utf-8")
    result["CATALOG_BUILD_NOTICE.txt"] = notice
    return result


def archive_files(raw: bytes, pin: dict[str, Any]) -> dict[str, bytes]:
    if len(raw) != pin["archive_bytes"] or digest(raw) != pin["archive_sha256"]:
        raise ValueError("upstream archive differs from pinned bytes")
    result: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = archive.getmembers()
        if len(members) != pin["archive_members"]:
            raise ValueError("upstream archive member count changed")
        for member in members:
            path = PurePosixPath(member.name)
            if (
                path.is_absolute()
                or any(part in {".", ".."} for part in path.parts)
                or path.parts[0] != pin["archive_root"]
            ):
                raise ValueError("archive contains an external path")
            if member.isdir():
                continue
            relative = PurePosixPath(*path.parts[1:]).as_posix()
            if not member.isfile() or relative in result:
                raise ValueError("archive contains a link, special file or duplicate")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("archive member cannot be read")
            result[relative] = stream.read()
    if len(result) != pin["source_files"] or sum(map(len, result.values())) != pin["unpacked_bytes"]:
        raise ValueError("upstream source inventory changed")
    return result


def inputs(root: Path, archive: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    directory = root / INPUTS
    pin = json.loads((directory / "source.json").read_bytes())
    vendor = (directory / "vendor/crawl4ai_download_opener.py").read_bytes()
    notice = (directory / "CATALOG_BUILD_NOTICE.txt").read_bytes()
    if digest(vendor) != pin["vendor_sha256"] or digest(notice) != pin["notice_sha256"]:
        raise ValueError("licensed adaptation inputs differ from source pin")
    source = archive_files(archive.read_bytes(), pin)
    if source["LICENSE"] != (directory / "vendor/LICENSE").read_bytes():
        raise ValueError("complete upstream Apache license differs")
    repaired = adapt(source, vendor, notice, pin["version"])
    if {name: digest(repaired[name]) for name in pin["changed_file_sha256"]} != pin["changed_file_sha256"]:
        raise ValueError("adapted source differs from qualified source bytes")
    return pin, repaired


def prepare(root: Path, archive: Path, stage: Path, *, check: bool = False) -> dict[str, Any]:
    root, stage = root.resolve(), stage.absolute()
    # Only an explicit disposable workspace stage; never a mirror or provider.
    if stage == root / ".venv" or not stage.is_relative_to(root / ".venv"):
        raise ValueError("source stage must be a new directory under workspace .venv")
    stage = checked_path(root, stage.relative_to(root).as_posix())
    pin, repaired = inputs(root, archive)
    expected = {name: digest(data) for name, data in repaired.items()}
    if not check:
        if stage.exists():
            raise ValueError("source stage already exists; refusing replacement")
        stage.mkdir(parents=True)
        for name, data in repaired.items():
            path = checked_path(stage, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if not stage.is_dir() or files(stage) != expected:
        raise ValueError("source stage differs from pinned adaptation")
    return {
        "ok": True,
        "evidence_class": "crawl4ai-source-adaptation-provenance",
        "version": pin["version"],
        "archive_sha256": pin["archive_sha256"],
        "source_date_epoch": pin["source_date_epoch"],
        "source_file_sha256": expected,
        "provider_built_or_installed": False,
        "agent_efficacy_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True, help="Exact pinned upstream sdist; no source execution")
    parser.add_argument("--stage", type=Path, required=True, help="New workspace .venv directory")
    parser.add_argument("--check", action="store_true", help="Verify existing stage without replacing it")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = prepare(ROOT, args.archive, args.stage, check=args.check)
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError, SyntaxError) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    print(json.dumps(result, indent=2) if args.json else result)
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

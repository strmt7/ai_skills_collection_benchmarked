"""Prepare the source-locked local-only CocoIndex Code provider without installation."""

from __future__ import annotations

import argparse
import json
import tarfile
from pathlib import Path
from typing import Any

from _catalog_publication import checked_path
from prepare_crawl4ai_source import archive_files, digest, files, replace_once
from prepare_semantic_corpus import checked_output

ROOT = Path(__file__).resolve().parents[1]
INPUTS = "toolchains/cocoindex-code"


def adapt(source: dict[str, bytes], notice: bytes, version: str) -> dict[str, bytes]:
    result = source.copy()
    project = source["pyproject.toml"].decode("utf-8")
    project = replace_once(project, 'requires = ["hatchling", "hatch-vcs"]', 'requires = ["hatchling"]')
    project = replace_once(project, 'dynamic = ["version"]', f'version = "{version}"')
    project = replace_once(project, '"cocoindex[litellm]>=1.0.17,<1.1.0"', '"cocoindex>=1.0.17,<1.1.0"')
    project = replace_once(
        project,
        '[tool.hatch.version]\nsource = "vcs"\nfallback-version = "999.0.0"\n\n'
        '[tool.hatch.build.hooks.vcs]\nversion-file = "src/cocoindex_code/_version.py"\n\n',
        "",
    )
    result["pyproject.toml"] = (
        "# Catalog local-only build: see src/cocoindex_code/CATALOG_BUILD_NOTICE.txt.\n" + project
    ).encode("utf-8")
    version_source = replace_once(
        source["src/cocoindex_code/_version.py"].decode("utf-8"),
        "__version__ = version = '0.2.42'",
        f"__version__ = version = '{version}'",
    )
    version_source = replace_once(
        version_source,
        "__version_tuple__ = version_tuple = (0, 2, 42)",
        "__version_tuple__ = version_tuple = (0, 2, 42, 'catalog.local1')",
    )
    result["src/cocoindex_code/_version.py"] = (
        "# Catalog local-only build version; original archive remains source-locked.\n" + version_source
    ).encode("utf-8")
    shared = replace_once(
        source["src/cocoindex_code/shared.py"].decode("utf-8"), "trust_remote_code=True,", "trust_remote_code=False,"
    )
    result["src/cocoindex_code/shared.py"] = (
        "# Catalog local-only build: disable remote model code; see CATALOG_BUILD_NOTICE.txt.\n" + shared
    ).encode("utf-8")
    result["src/cocoindex_code/CATALOG_BUILD_NOTICE.txt"] = notice
    return result


def inputs(root: Path, archive: Path) -> tuple[dict[str, Any], dict[str, bytes]]:
    directory = root / INPUTS
    pin = json.loads((directory / "source.json").read_bytes())
    notice = (directory / "CATALOG_BUILD_NOTICE.txt").read_bytes()
    license_bytes = (directory / "LICENSE").read_bytes()
    if digest(notice) != pin["notice_sha256"] or digest(license_bytes) != pin["license_sha256"]:
        raise ValueError("CocoIndex provider license or change notice differs from its source pin")
    source = archive_files(archive.read_bytes(), pin)
    if {name: digest(raw) for name, raw in source.items()} != pin["original_source_sha256"]:
        raise ValueError("Original CocoIndex Code source inventory differs from its pin")
    if source["LICENSE"] != license_bytes:
        raise ValueError("Complete upstream Apache license differs")
    prepared = adapt(source, notice, pin["version"])
    if {name: digest(raw) for name, raw in prepared.items()} != pin["prepared_source_sha256"]:
        raise ValueError("Local-only provider adaptation differs from its qualified source")
    return pin, prepared


def prepare(root: Path, archive: Path, stage: Path, *, check: bool = False) -> dict[str, Any]:
    root = root.resolve(strict=True)
    stage = checked_output(root, stage)
    if stage == root / ".venv":
        raise ValueError("Select a dedicated source stage under workspace .venv")
    pin, expected = inputs(root, archive)
    if not check:
        stage.mkdir(parents=True, exist_ok=False)
        for name, raw in expected.items():
            path = checked_path(stage, name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    if files(stage) != {name: digest(raw) for name, raw in expected.items()}:
        raise ValueError("Prepared source stage differs from its exact admitted inventory")
    return {
        "ok": True,
        "upstream_version": pin["upstream_version"],
        "version": pin["version"],
        "original_source_files": len(pin["original_source_sha256"]),
        "prepared_source_files": len(expected),
        "cloud_embeddings_supported": False,
        "remote_model_code_supported": False,
        "dependencies_installed_by_this_tool": False,
        "agent_efficacy_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = prepare(ROOT, args.archive, args.stage, check=args.check)
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError) as error:
        result = {"ok": False, "errors": [str(error)]}
    print(json.dumps(result, indent=2) if args.json else result)
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Admit a reproducible Crawl4AI wheel and derive its complete hashed install lock."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any

from _catalog_publication import checked_path
from prepare_crawl4ai_source import INPUTS, ROOT, digest, files, runtime_sources


def verify_wheel(root: Path, wheel: Path) -> tuple[dict[str, Any], bytes]:
    directory = root / INPUTS
    pin = json.loads((directory / "source.json").read_bytes())
    raw = wheel.read_bytes()
    if digest(raw) != pin["qualified_wheel_sha256"]:
        raise ValueError("wheel differs from qualified reproducible build")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names):
            raise ValueError("wheel contains duplicate members")
        actual = {
            name: digest(archive.read(name))
            for name in names
            if name.startswith("crawl4ai/") and not name.endswith("/")
        }
        if actual != runtime_sources(pin):
            raise ValueError("wheel runtime sources differ from source admission")
        for name, expected in (
            ("LICENSE", directory / "vendor/LICENSE"),
            ("CATALOG_BUILD_NOTICE.txt", directory / "CATALOG_BUILD_NOTICE.txt"),
        ):
            candidates = [item for item in names if item.endswith("/licenses/" + name)]
            if len(candidates) != 1 or archive.read(candidates[0]) != expected.read_bytes():
                raise ValueError("wheel license or attribution differs")
    # Retain public upstream coordinates in version-control for advisory services.
    # Only this generated install lock substitutes the admitted downstream wheel.
    lock = (directory / "requirements.txt").read_text(encoding="utf-8")
    pattern = r"(?im)^crawl4ai==0\.9\.5 --hash=sha256:[0-9a-f]{64}$"
    lock, count = re.subn(pattern, f"Crawl4AI=={pin['version']} --hash=sha256:{pin['qualified_wheel_sha256']}", lock)
    if count != 1:
        raise ValueError("public runtime lock must contain exactly one pinned upstream Crawl4AI record")
    return pin, lock.encode("utf-8")


def installed_files(pin: dict[str, Any]) -> int:
    distribution = importlib.metadata.distribution("crawl4ai")
    if distribution.version != pin["version"]:
        raise ValueError("installed Crawl4AI version differs from admitted source build")
    for relative, expected in runtime_sources(pin).items():
        path = Path(str(distribution.locate_file(relative)))
        if not path.resolve().is_relative_to(Path(sys.prefix).resolve()) or digest(path.read_bytes()) != expected:
            raise ValueError(f"installed provider source differs: {relative}")
    return len(runtime_sources(pin))


def prepare(root: Path, wheel: Path, stage: Path, *, check: bool = False, installed: bool = False) -> dict[str, Any]:
    root, stage = root.resolve(), stage.absolute()
    if stage == root / ".venv" or not stage.is_relative_to(root / ".venv"):
        raise ValueError("wheel admission stage must be under workspace .venv")
    stage = checked_path(root, stage.relative_to(root).as_posix())
    pin, lock = verify_wheel(root, wheel)
    sources_checked = installed_files(pin) if installed else 0
    metadata = {
        "schema_version": 1,
        "version": pin["version"],
        "wheel_sha256": pin["qualified_wheel_sha256"],
        "runtime_files": pin["runtime_files"],
        "runtime_lock_sha256": digest(lock),
    }
    outputs = {
        "requirements.txt": lock,
        "source-admission.json": (json.dumps(metadata, indent=2) + "\n").encode("utf-8"),
    }
    if not check:
        if stage.exists():
            raise ValueError("wheel admission stage already exists; refusing replacement")
        stage.mkdir(parents=True)
        for name, data in outputs.items():
            (stage / name).write_bytes(data)
    if not stage.is_dir() or files(stage) != {name: digest(data) for name, data in outputs.items()}:
        raise ValueError("wheel admission stage differs from pinned inputs")
    return {
        "ok": True,
        "version": pin["version"],
        "wheel_sha256": pin["qualified_wheel_sha256"],
        "wheel_runtime_files_checked": len(runtime_sources(pin)),
        "installed_source_files_checked": sources_checked,
        "dependencies_installed_by_this_tool": False,
        "agent_efficacy_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument(
        "--stage", type=Path, required=True, help="New workspace .venv directory for derived lock and admission"
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument(
        "--installed", action="store_true", help="Also check every admitted installed runtime source file"
    )
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = prepare(ROOT, args.wheel, args.stage, check=args.check, installed=args.installed)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        zipfile.BadZipFile,
        importlib.metadata.PackageNotFoundError,
    ) as exc:
        result = {"ok": False, "errors": [str(exc)]}
    print(json.dumps(result, indent=2) if args.json else result)
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

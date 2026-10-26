"""Admit the local-only CocoIndex wheel, install lock and installed provider bytes."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import re
import sys
import zipfile
from email.parser import BytesParser
from pathlib import Path
from typing import Any

from prepare_cocoindex_source import INPUTS, ROOT
from prepare_crawl4ai_source import digest, files, runtime_sources
from prepare_semantic_corpus import checked_output, regular_file


def verify_metadata(directory: Path, archive: zipfile.ZipFile, names: list[str], pin: dict[str, Any]) -> None:
    licenses = [name for name in names if name.endswith("/licenses/LICENSE")]
    metadata_files = [name for name in names if name.endswith(".dist-info/METADATA")]
    if len(licenses) != 1 or archive.read(licenses[0]) != (directory / "LICENSE").read_bytes():
        raise ValueError("Complete upstream CocoIndex Code license differs")
    if len(metadata_files) != 1:
        raise ValueError("CocoIndex wheel must contain one distribution metadata file")
    metadata = BytesParser().parsebytes(archive.read(metadata_files[0]))
    if metadata["Version"] != pin["version"] or any(
        "litellm" in value.lower() for value in metadata.get_all("Requires-Dist", [])
    ):
        raise ValueError("CocoIndex local-only metadata has an unexpected version or cloud embedding dependency")
    if archive.read("cocoindex_code/CATALOG_BUILD_NOTICE.txt") != (directory / "CATALOG_BUILD_NOTICE.txt").read_bytes():
        raise ValueError("CocoIndex provider change notice differs")


def verify_wheel(root: Path, wheel: Path) -> tuple[dict[str, Any], bytes]:
    directory = root / INPUTS
    pin = json.loads((directory / "source.json").read_bytes())
    if digest(wheel.read_bytes()) != pin["qualified_wheel_sha256"]:
        raise ValueError("CocoIndex wheel differs from its qualified reproducible build")
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names):
            raise ValueError("CocoIndex wheel contains duplicate members")
        actual = {
            name: digest(archive.read(name))
            for name in names
            if name.startswith("cocoindex_code/") and not name.endswith("/")
        }
        if actual != runtime_sources(pin):
            raise ValueError("CocoIndex wheel runtime sources differ from their exact source admission")
        verify_metadata(directory, archive, names, pin)
    # Advisory services receive the original upstream identity. Only the admitted
    # installation substitutes the local-only wheel; other runtime records stay exact.
    lock = (directory / "requirements.txt").read_text(encoding="utf-8")
    pattern = (
        r"(?im)^cocoindex-code\[embeddings-local\]=="
        + re.escape(pin["upstream_version"])
        + r" --hash=sha256:[0-9a-f]{64}$"
    )
    lock, count = re.subn(
        pattern,
        f"cocoindex-code[embeddings-local]=={pin['version']} --hash=sha256:{pin['qualified_wheel_sha256']}",
        lock,
    )
    if count != 1 or digest(lock.encode("utf-8")) != pin["qualified_runtime_lock_sha256"]:
        raise ValueError("Derived CocoIndex install lock differs from its qualified complete runtime graph")
    return pin, lock.encode("utf-8")


def installed_versions() -> dict[str, str]:
    result = {}
    for distribution in importlib.metadata.distributions():
        name = re.sub(r"[-_.]+", "-", distribution.metadata["Name"]).lower()
        if name in result:
            raise ValueError("Duplicate installed provider distribution: " + name)
        result[name] = distribution.version
    return result


def installed_files(pin: dict[str, Any]) -> int:
    if installed_versions() != pin["runtime_versions"]:
        raise ValueError("Installed CocoIndex dependency versions differ from the complete admitted graph")
    records = {**runtime_sources(pin), **runtime_sources(pin["core"])}
    prefix = Path(sys.prefix).resolve(strict=True)
    distribution = importlib.metadata.distribution("cocoindex-code")
    errors = []
    for name, expected in records.items():
        path = Path(str(distribution.locate_file(name)))
        try:
            relative = path.relative_to(prefix).as_posix()
            if digest(regular_file(prefix, relative).read_bytes()) != expected:
                errors.append("changed provider source: " + name)
        except (OSError, ValueError) as error:
            errors.append(f"invalid provider source {name}: {error}")
    if errors:
        raise ValueError("; ".join(errors))
    return len(records)


def prepare(root: Path, wheel: Path, stage: Path, *, check: bool = False, installed: bool = False) -> dict[str, Any]:
    root = root.resolve(strict=True)
    stage = checked_output(root, stage)
    if stage == root / ".venv":
        raise ValueError("Select a dedicated wheel admission stage under workspace .venv")
    pin, lock = verify_wheel(root, wheel)
    sources_checked = installed_files(pin) if installed else 0
    metadata = {
        "schema_version": 1,
        "version": pin["version"],
        "wheel_sha256": pin["qualified_wheel_sha256"],
        "provider_source_files": len(pin["runtime_files"]),
        "core_source_files": len(pin["core"]["runtime_files"]),
        "runtime_lock_sha256": digest(lock),
        "advisory_coordinate_mapping": pin["advisory_coordinate_mapping"],
    }
    outputs = {
        "requirements.txt": lock,
        "source-admission.json": (json.dumps(metadata, indent=2) + "\n").encode("utf-8"),
    }
    if not check:
        stage.mkdir(parents=True, exist_ok=False)
        for name, raw in outputs.items():
            (stage / name).write_bytes(raw)
    if files(stage) != {name: digest(raw) for name, raw in outputs.items()}:
        raise ValueError("CocoIndex wheel admission stage differs from its pinned inputs")
    return {
        "ok": True,
        "version": pin["version"],
        "wheel_sha256": pin["qualified_wheel_sha256"],
        "installed_source_files_checked": sources_checked,
        "runtime_distributions": len(pin["runtime_versions"]),
        "dependencies_installed_by_this_tool": False,
        "agent_efficacy_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--installed", action="store_true")
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
    ) as error:
        result = {"ok": False, "errors": [str(error)]}
    print(json.dumps(result, indent=2) if args.json else result)
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

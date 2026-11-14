#!/usr/bin/env python3
"""Install a frozen Windows subject dependency graph using the admitted UV installer."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

from _native_benchmark_runtime import sha256, write_json
from _trial_context import SYSTEM_VARIABLES, profile_directories
from _trial_transcript import strict_json
from _windows_appcontainer import checked_path
from _windows_storage_budget import SpaceBudget
from _windows_trial_process import ProcessBudgetOptions, run_owned
from appcontainer_dependencies import _official_package_url, capture

ROOT = Path(__file__).resolve().parents[1]
MAX_FILES = 16000
MAX_BYTES = 512 * 1024**2


def load_specification(raw: bytes) -> dict[str, Any]:
    """Admit a complete explicit wheel graph; UV independently resolves its dependencies."""
    if len(raw) > 1024**2:
        raise ValueError("Subject dependency specification exceeds one MiB")
    spec = strict_json(raw.decode("utf-8"))
    if (
        not isinstance(spec, dict)
        or set(spec) != {"schema_version", "python_version", "architecture", "imports", "packages"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] != 1
        or not isinstance(spec["python_version"], str)
        or not re.fullmatch(r"3\.\d+\.\d+", spec["python_version"])
        or spec["architecture"] != "AMD64"
        or not isinstance(spec["imports"], list)
        or not 1 <= len(spec["imports"]) <= 64
        or any(
            not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*", name)
            for name in spec["imports"]
        )
        or not isinstance(spec["packages"], list)
        or not 1 <= len(spec["packages"]) <= 128
    ):
        raise ValueError("Expected a frozen Windows x64 dependency specification")
    names, filenames = set(), set()
    for item in spec["packages"]:
        if not isinstance(item, dict) or set(item) != {
            "name",
            "version",
            "extras",
            "filename",
            "url",
            "bytes",
            "sha256",
        }:
            raise ValueError("Expected an exact dependency wheel declaration")
        if (
            not isinstance(item["name"], str)
            or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item["name"])
            or not isinstance(item["version"], str)
            or not re.fullmatch(r"\d+(?:\.\d+)*(?:\.post\d+)?", item["version"])
            or not isinstance(item["extras"], list)
            or len(item["extras"]) > 32
            or any(
                not isinstance(extra, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", extra)
                for extra in item["extras"]
            )
            or len(set(item["extras"])) != len(item["extras"])
            or not isinstance(item["filename"], str)
            or not re.fullmatch(r"[A-Za-z0-9_.+-]+\.whl", item["filename"])
            or not isinstance(item["url"], str)
            or not _official_package_url(item["url"])
            or type(item["bytes"]) is not int
            or not 0 < item["bytes"] <= 16 * 1024**2
            or not isinstance(item["sha256"], str)
            or not re.fullmatch(r"[a-f0-9]{64}", item["sha256"])
            or item["name"] in names
            or item["filename"].casefold() in filenames
        ):
            raise ValueError("Invalid or repeated subject dependency wheel")
        names.add(item["name"])
        filenames.add(item["filename"].casefold())
    if sum(item["bytes"] for item in spec["packages"]) > 128 * 1024**2:
        raise ValueError("Subject dependency archive graph exceeds its byte budget")
    return spec


def installer_identity(path: Path) -> dict[str, Any]:
    """Bind the actual executable, never an ambient PATH command or version string."""
    path = checked_path(path)
    expected = strict_json((ROOT / "toolchains/bootstrap/manifest.json").read_text(encoding="utf-8"))["uv"]
    identity = expected["files"]["uv.exe"]
    if path.stat().st_size != identity["bytes"] or sha256(path.read_bytes()) != identity["sha256"]:
        raise ValueError("Subject installer differs from the qualified UV executable")
    return {"version": expected["version"], **identity}


def inventory(root: Path) -> dict[str, Any]:
    """Retain the entire namespace, including empty directories, with bounded traversal."""
    pending, files, directories, total = [checked_path(root)], {}, [], 0
    while pending:
        current = pending.pop()
        for path in current.iterdir():
            path = checked_path(path)
            name = path.relative_to(root).as_posix()
            if path.is_dir():
                directories.append(name)
                pending.append(path)
            elif path.is_file():
                total += path.stat().st_size
                if total > MAX_BYTES:
                    raise ValueError("Installed dependency bytes exceed the profile budget")
                files[name] = sha256(path.read_bytes())
            else:
                raise ValueError("Only regular dependency files and directories are admitted")
            if len(files) + len(directories) > MAX_FILES:
                raise ValueError("Installed dependency namespace exceeds the profile budget")
    return {"files": files, "directories": sorted(directories), "bytes": total}


def verify(receipt: dict[str, Any]) -> Path:
    packages = checked_path(Path(receipt["packages"]))
    if inventory(packages) != receipt["inventory"]:
        raise ValueError("Subject dependency installation changed since qualification")
    return packages


def _phase(
    output: Path, label: str, argv: list[str], environment: dict[str, str], *, space_budget: SpaceBudget | None = None
) -> None:
    resources: ProcessBudgetOptions = {}
    if space_budget is not None:
        resources["space_budget"] = space_budget
    with (
        (output / (label + ".stdout.native")).open("xb") as stdout,
        (output / (label + ".stderr.native")).open("xb") as stderr,
        open(os.devnull, "rb") as stdin,
    ):
        process = run_owned(
            argv,
            cwd=output,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            environment=environment,
            timeout=120,
            output_limit=4 * 1024**2,
            memory_limit=2 * 1024**3,
            process_limit=16,
            **resources,
        )
    write_json(output / (label + ".process.json"), process)
    if process["exit_code"] or process["termination_reason"] or process["job_active_processes_after_cleanup"] != 0:
        raise ValueError(f"Subject dependency {label} failed; retained diagnostics: {output}")


def prepare(
    raw: bytes,
    python: Path,
    installer: Path,
    output: Path,
    *,
    archive_dir: Path | None = None,
    space_budget: SpaceBudget | None = None,
) -> dict[str, Any]:
    """Use a fresh owned profile; simultaneous attempts never share a writable install target."""
    spec = load_specification(raw)
    if space_budget is not None:
        space_budget.require_available()
    python, installer, output = (checked_path(path) for path in (python, installer, output))
    admitted_installer = installer_identity(installer)
    if not output.is_relative_to(ROOT / ".venv") or output == ROOT / ".venv":
        raise ValueError("Subject dependency output must be a fresh owned directory under .venv")
    if any(output.is_relative_to(path) or path.is_relative_to(output) for path in (python.parent, installer.parent)):
        raise ValueError("Dependency output must be disjoint from interpreter and installer inputs")
    if archive_dir is not None:
        archive_dir = checked_path(archive_dir)
        if output.is_relative_to(archive_dir) or archive_dir.is_relative_to(output):
            raise ValueError("Dependency archives and installation output must be disjoint")
    output.mkdir(parents=True, exist_ok=False)
    (output / "specification.json").write_bytes(raw)
    wheels, packages = output / "wheels", output / "packages"
    wheels.mkdir()
    for item in spec["packages"]:
        if space_budget is not None:
            space_budget.require_available()
        local = archive_dir if archive_dir is not None and (archive_dir / item["filename"]).exists() else None
        (wheels / item["filename"]).write_bytes(capture(item, local))
        if space_budget is not None:
            space_budget.require_available()
    lines = []
    for item in spec["packages"]:
        extras = "[" + ",".join(item["extras"]) + "]" if item["extras"] else ""
        lines.append(f"{item['name']}{extras}=={item['version']} --hash=sha256:{item['sha256']}")
    requirements = output / "requirements.txt"
    requirements.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    environment = {key: value for key, value in os.environ.items() if key.upper() in SYSTEM_VARIABLES}
    environment.update(profile_directories(output / "private"))
    environment.update(
        PATH=os.pathsep.join((str(python.parent), str(Path(environment["SYSTEMROOT"]) / "System32"))),
        UV_PYTHON_DOWNLOADS="never",
        UV_NO_PROGRESS="1",
        UV_HTTP_RETRIES="0",
        PYTHONDONTWRITEBYTECODE="1",
    )
    python_hash = sha256(python.read_bytes())
    _phase(
        output,
        "install",
        [
            str(installer),
            "--no-config",
            "--offline",
            "--cache-dir",
            str(output / "cache"),
            "pip",
            "install",
            "--python",
            str(python),
            "--target",
            str(packages),
            "--require-hashes",
            "--only-binary",
            ":all:",
            "--no-index",
            "--find-links",
            str(wheels),
            "--link-mode",
            "copy",
            "-r",
            str(requirements),
        ],
        environment,
        **({"space_budget": space_budget} if space_budget is not None else {}),
    )
    _phase(
        output,
        "check",
        [
            str(python),
            "-I",
            "-B",
            str(ROOT / "tools/_bootstrap_doctor.py"),
            "--packages",
            str(packages),
            "--require-package-imports",
            "--requirements",
            str(requirements),
            *[arg for name in spec["imports"] for arg in ("--import", name)],
        ],
        environment,
        **({"space_budget": space_budget} if space_budget is not None else {}),
    )
    metadata = strict_json((output / "check.stdout.native").read_text(encoding="utf-8"))
    if (
        metadata["python"] != spec["python_version"]
        or metadata["implementation"] != "cpython"
        or metadata["bits"] != 64
        or metadata["os"] != "Windows"
        or metadata["machine"] != "AMD64"
    ):
        raise ValueError("Subject dependency runtime differs from its frozen interpreter requirements")
    if sha256(python.read_bytes()) != python_hash or installer_identity(installer) != admitted_installer:
        raise ValueError("Subject dependency setup changed its interpreter or installer")
    receipt = {
        "schema_version": 1,
        "packages": str(packages),
        "specification_sha256": sha256(raw),
        "python_sha256": python_hash,
        "installer": admitted_installer,
        "metadata": metadata,
        "inventory": inventory(packages),
    }
    write_json(output / "receipt.json", receipt)
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specification", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    parser.add_argument("--installer", type=Path, default=os.environ.get("AI_SKILLS_UV"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--archive-dir", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.installer is None:
        raise ValueError("Use dev.ps1 python or supply the admitted UV executable with --installer")
    receipt = prepare(
        args.specification.read_bytes(), args.python, args.installer, args.output, archive_dir=args.archive_dir
    )
    print(json.dumps({"ready": True, "packages": receipt["packages"], "receipt": str(args.output / "receipt.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

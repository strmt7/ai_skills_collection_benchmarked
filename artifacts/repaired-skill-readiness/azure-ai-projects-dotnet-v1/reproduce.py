"""Compile locked Azure SDK controls without calling the Azure service."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = (
    ROOT
    / "included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-ai-projects-dotnet/SKILL.md"
)
EXAMPLE = (
    ROOT
    / "included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-ai-projects-dotnet-stable/examples"
)
SOURCE_SHA256 = "bf35c77776ab18146a39b7cfcea14747545b3cd441e268e9e7addfed542fabc2"
SDK_VERSION = "10.0.403"
CASES = {
    "classic-api-classic-version": (0, ()),
    "classic-api-modern-version": (0, ()),
    "preview-example-older-packages": (1, ("CA2252",)),
    "preview-example-older-opt-in": (0, ()),
    "preview-example-current-packages": (1, ("CS1061", "Agents", "OpenAI")),
    "modern-agent-example": (0, ()),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(dotnet: Path, output: Path) -> dict[str, Any]:
    original = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    if digest(original) != SOURCE_SHA256:
        raise ValueError("The pinned source skill differs from the control")
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output / "global.json").write_text(json.dumps({"sdk": {"version": SDK_VERSION, "rollForward": "disable"}}) + "\n")
    config = output / "NuGet.Config"
    config.write_text(
        '<?xml version="1.0" encoding="utf-8"?><configuration><packageSources><clear/>'
        '<add key="nuget.org" value="https://api.nuget.org/v3/index.json"/>'
        "</packageSources></configuration>\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env.update(
        DOTNET_CLI_HOME=str(output / "dotnet-home"),
        NUGET_PACKAGES=str(output / "nuget-packages"),
        NUGET_HTTP_CACHE_PATH=str(output / "nuget-http-cache"),
        NUGET_PLUGINS_CACHE_PATH=str(output / "nuget-plugins-cache"),
        DOTNET_CLI_TELEMETRY_OPTOUT="1",
        DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1",
        DOTNET_NOLOGO="1",
        DOTNET_CLI_UI_LANGUAGE="en-US",
    )
    version = subprocess.run(
        [str(dotnet), "--version"], cwd=output, env=env, capture_output=True, timeout=30, check=False
    )
    if version.returncode or version.stdout.decode("utf-8").strip() != SDK_VERSION:
        raise ValueError(f"The control requires .NET SDK {SDK_VERSION}")
    results = []
    for name, (expected_exit, expected_markers) in CASES.items():
        source = EXAMPLE if name == "modern-agent-example" else HERE / "fixtures" / name
        project_name = "Example.csproj" if name == "modern-agent-example" else "control.csproj"
        case_dir = output / name
        case_dir.mkdir()
        for filename in ("Program.cs", project_name, "packages.lock.json"):
            shutil.copyfile(source / filename, case_dir / filename)
        streams = {}
        for phase, args in (
            ("restore", ["restore", project_name, "--locked-mode", "--configfile", str(config), "--nologo"]),
            ("build", ["build", project_name, "--no-restore", "--nologo"]),
        ):
            result = subprocess.run(
                [str(dotnet), *args], cwd=case_dir, env=env, capture_output=True, timeout=300, check=False
            )
            for label in ("stdout", "stderr"):
                raw = getattr(result, label)
                (case_dir / f"{phase}.{label}").write_bytes(raw)
                streams[f"{phase}_{label}_sha256"] = digest(raw)
            if phase == "restore" and result.returncode:
                raise ValueError(f"Locked restore failed for {name}; inspect retained streams")
            if phase == "build":
                combined = (result.stdout + result.stderr).decode("utf-8", errors="replace")
                if result.returncode != expected_exit or any(marker not in combined for marker in expected_markers):
                    raise ValueError(f"Unexpected build result for {name}; inspect retained streams")
                results.append(
                    {
                        "case": name,
                        "build_exit_code": result.returncode,
                        "expected_error_markers": list(expected_markers),
                        "source_sha256": digest((case_dir / "Program.cs").read_bytes()),
                        "project_sha256": digest((case_dir / project_name).read_bytes()),
                        "lock_sha256": digest((case_dir / "packages.lock.json").read_bytes()),
                        **streams,
                    }
                )
    report = {
        "schema_version": 1,
        "sdk_version": SDK_VERSION,
        "platform": platform.system(),
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "source_skill_sha256": SOURCE_SHA256,
        "azure_service_called": False,
        "agent_performance_tested": False,
        "cases": results,
    }
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dotnet", type=Path, required=True, help="Absolute path to the dotnet executable")
    parser.add_argument("--output", type=Path, required=True, help="New isolated output and NuGet cache directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.dotnet.is_absolute() or not args.dotnet.is_file():
        raise ValueError("--dotnet must be an absolute path to an existing executable")
    report = run(args.dotnet.resolve(), args.output)
    print(json.dumps({"ok": True, "cases": len(report["cases"]), "azure_service_called": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

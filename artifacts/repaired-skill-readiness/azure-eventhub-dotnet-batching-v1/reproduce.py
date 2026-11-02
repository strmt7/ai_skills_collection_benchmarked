"""Compile the pinned and repaired Event Hubs batching examples without service access."""

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
BASE = Path("by-category/cloud-azure-microsoft-sdks/official-vendor-reference")
SOURCE = ROOT / "included/skills" / BASE / "azure-eventhub-dotnet/SKILL.md"
EXAMPLE = ROOT / "included/repaired/skills" / BASE / "azure-eventhub-dotnet-batching/examples"
SDK_VERSION = "10.0.403"
SOURCE_SHA256 = "90eb8a7b1103670312148fccb43eb3746eae4cef41a24ca2cfe7191b053ca356"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def original_program(source: bytes) -> bytes:
    text = source.decode("utf-8").replace("\r\n", "\n")
    block = text.split("### 1. Send Events (Batch)", 1)[1].split("```csharp", 1)[1].split("```", 1)[0].strip()
    marker = "using Azure.Messaging.EventHubs.Producer;"
    if block.count(marker) != 1:
        raise ValueError("Unexpected pinned example")
    declarations = (
        '\nstring fullyQualifiedNamespace = "example.servicebus.windows.net";\nstring eventHubName = "example";'
    )
    return (block.replace(marker, marker + declarations) + "\n").encode("utf-8")


def run(dotnet: Path, output: Path) -> dict[str, Any]:
    source = SOURCE.read_bytes().replace(b"\r\n", b"\n")
    if sha(source) != SOURCE_SHA256:
        raise ValueError("Pinned skill changed")
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
    version = subprocess.run([str(dotnet), "--version"], cwd=output, env=env, capture_output=True, timeout=30)
    if version.returncode or version.stdout.decode("utf-8").strip() != SDK_VERSION:
        raise ValueError(f"The control requires .NET SDK {SDK_VERSION}")
    results = []
    for name, program, expected in (
        ("original", original_program(source), 1),
        ("repaired", (EXAMPLE / "Program.cs").read_bytes(), 0),
    ):
        case = output / name
        case.mkdir()
        for filename in ("Example.csproj", "packages.lock.json"):
            shutil.copyfile(EXAMPLE / filename, case / filename)
        (case / "Program.cs").write_bytes(program)
        streams = {}
        for phase, args in (
            ("restore", ["restore", "Example.csproj", "--locked-mode", "--configfile", str(config), "--nologo"]),
            ("build", ["build", "Example.csproj", "--no-restore", "--nologo"]),
        ):
            result = subprocess.run([str(dotnet), *args], cwd=case, env=env, capture_output=True, timeout=300)
            for label in ("stdout", "stderr"):
                raw = getattr(result, label)
                (case / f"{phase}.{label}").write_bytes(raw)
                streams[f"{phase}_{label}_sha256"] = sha(raw)
            combined = (result.stdout + result.stderr).decode("utf-8", errors="replace")
            if phase == "restore" and result.returncode:
                raise ValueError(f"Locked restore failed for {name}; inspect retained streams")
            if phase == "build":
                if result.returncode != expected or (name == "original" and "CS1656" not in combined):
                    raise ValueError(f"Unexpected build result for {name}; inspect retained streams")
                results.append(
                    {
                        "case": name,
                        "build_exit_code": result.returncode,
                        "source_sha256": sha(program),
                        "project_sha256": sha((case / "Example.csproj").read_bytes()),
                        "lock_sha256": sha((case / "packages.lock.json").read_bytes()),
                        **streams,
                    }
                )
    report = {
        "schema_version": 1,
        "sdk_version": SDK_VERSION,
        "platform": platform.system(),
        "source_skill_sha256": SOURCE_SHA256,
        "azure_service_called": False,
        "agent_performance_tested": False,
        "cases": results,
    }
    (output / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dotnet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.dotnet.is_absolute() or not args.dotnet.is_file():
        raise ValueError("--dotnet must be an absolute path to an existing executable")
    report = run(args.dotnet.resolve(), args.output)
    print(json.dumps({"ok": True, "cases": len(report["cases"]), "azure_service_called": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

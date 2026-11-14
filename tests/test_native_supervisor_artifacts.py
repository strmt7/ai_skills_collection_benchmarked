"""Reject stale tracked bootstrap seeds before the native CI qualification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "toolchains/bootstrap"


def test_bootstrap_seed_matches_its_source_and_deterministic_build_inputs():
    pin = json.loads((HOME / "supervisor.json").read_bytes())
    binary = (HOME / "NativeSupervisor.dll").read_bytes()
    assert pin["schema_version"] == 1
    assert len(binary) == pin["assembly_bytes"]
    assert hashlib.sha256(binary).hexdigest() == pin["assembly_sha256"]
    assert hashlib.sha256((HOME / "OwnedProcess.cs").read_bytes()).hexdigest() == pin["source_sha256"]
    assert set(pin["build_inputs"]) == {
        "powershell.json",
        "framework-references.json",
        "CompileSupervisor.ps1",
        "build_supervisor.ps1",
    }
    for name, digest in pin["build_inputs"].items():
        assert hashlib.sha256((HOME / name).read_bytes()).hexdigest() == digest, name


def test_framework_reference_package_preserves_metadata_and_license():
    pin = json.loads((HOME / "framework-references.json").read_bytes())
    assert set(pin["files"]) == {
        "mscorlib.dll",
        "System.dll",
        "System.Core.dll",
        "Microsoft.NETFramework.ReferenceAssemblies.net48.nuspec",
    }
    assert set(pin["file_map"].values()) == set(pin["files"])
    assert all(name.startswith("build/.NETFramework/v4.8/") for name in pin["file_map"] if name.endswith(".dll"))
    license_text = (HOME / "FRAMEWORK-REFERENCES-LICENSE.txt").read_text(encoding="utf-8")
    assert "Copyright (c) 2019 Microsoft" in license_text
    assert "Permission is hereby granted" in license_text

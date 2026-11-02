"""Verify the source binding and compile evidence for the Event Hubs repair."""

import hashlib
import json
import runpy
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("by-category/cloud-azure-microsoft-sdks/official-vendor-reference")
SOURCE = ROOT / "included/skills" / BASE / "azure-eventhub-dotnet"
OVERLAY = ROOT / "included/repaired/skills" / BASE / "azure-eventhub-dotnet-batching"
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/azure-eventhub-dotnet-batching-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_repair_preserves_source_and_binds_all_evidence() -> None:
    manifest = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert manifest["azure_service_run"] is False and manifest["model_performance_claim"] is False
    assert (SOURCE / "SKILL.md").read_bytes().replace(b"\r\n", b"\n") == (
        OVERLAY / "provenance/original.SKILL.md"
    ).read_bytes().replace(b"\r\n", b"\n")
    for base, key, ignored in [(OVERLAY, "overlay_sha256", {"repair.json"}), (EVIDENCE, "evidence_sha256", set())]:
        actual = {
            path.relative_to(base).as_posix(): sha(path)
            for path in base.rglob("*")
            if path.is_file() and path.relative_to(base).as_posix() not in ignored
        }
        assert actual == manifest[key]


def test_compile_observations_bind_original_repair_and_lock() -> None:
    result = json.loads((EVIDENCE / "windows-result.json").read_text(encoding="utf-8"))
    assert result["platform"] == "Windows" and result["sdk_version"] == "10.0.403"
    assert result["azure_service_called"] is False and result["agent_performance_tested"] is False
    cases = {item["case"]: item for item in result["cases"]}
    assert {name: item["build_exit_code"] for name, item in cases.items()} == {"original": 1, "repaired": 0}
    control = runpy.run_path(str(EVIDENCE / "reproduce.py"))
    original = control["original_program"]((SOURCE / "SKILL.md").read_bytes())
    assert cases["original"]["source_sha256"] == hashlib.sha256(original).hexdigest()
    assert cases["repaired"]["source_sha256"] == sha(OVERLAY / "examples/Program.cs")
    for case in cases.values():
        assert case["project_sha256"] == sha(OVERLAY / "examples/Example.csproj")
        assert case["lock_sha256"] == sha(OVERLAY / "examples/packages.lock.json")


def test_direct_package_versions_match_lock() -> None:
    example = OVERLAY / "examples"
    project = ET.parse(example / "Example.csproj")
    versions = {node.attrib["Include"]: node.attrib["Version"] for node in project.findall(".//PackageReference")}
    assert versions == {"Azure.Identity": "1.21.0", "Azure.Messaging.EventHubs": "5.12.2"}
    locked = json.loads((example / "packages.lock.json").read_text(encoding="utf-8"))["dependencies"]["net10.0"]
    assert {name: item["resolved"] for name, item in locked.items() if item["type"] == "Direct"} == versions
    assert all(item["contentHash"] for item in locked.values())

"""Verify Azure AI Projects source provenance and locked compile observations."""

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("by-category/cloud-azure-microsoft-sdks/official-vendor-reference")
SOURCE = ROOT / "included/skills" / BASE / "azure-ai-projects-dotnet"
OVERLAY = ROOT / "included/repaired/skills" / BASE / "azure-ai-projects-dotnet-stable"
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/azure-ai-projects-dotnet-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_overlay_preserves_source_and_binds_all_evidence() -> None:
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


def test_compile_observations_bind_projects_sources_and_locks() -> None:
    result = json.loads((EVIDENCE / "windows-result.json").read_text(encoding="utf-8"))
    assert result["platform"] == "Windows" and result["sdk_version"] == "10.0.403"
    assert result["azure_service_called"] is False and result["agent_performance_tested"] is False
    cases = {item["case"]: item for item in result["cases"]}
    assert {name: item["build_exit_code"] for name, item in cases.items()} == {
        "classic-api-classic-version": 0,
        "classic-api-modern-version": 0,
        "preview-example-older-packages": 1,
        "preview-example-older-opt-in": 0,
        "preview-example-current-packages": 1,
        "modern-agent-example": 0,
    }
    assert cases["preview-example-older-packages"]["expected_error_markers"] == ["CA2252"]
    assert cases["preview-example-current-packages"]["expected_error_markers"] == ["CS1061", "Agents", "OpenAI"]
    for name, case in cases.items():
        base = OVERLAY / "examples" if name == "modern-agent-example" else EVIDENCE / "fixtures" / name
        project = "Example.csproj" if name == "modern-agent-example" else "control.csproj"
        assert case["source_sha256"] == sha(base / "Program.cs")
        assert case["project_sha256"] == sha(base / project)
        assert case["lock_sha256"] == sha(base / "packages.lock.json")


def test_stable_example_direct_dependencies_match_lock() -> None:
    example = OVERLAY / "examples"
    project = ET.parse(example / "Example.csproj")
    versions = {node.attrib["Include"]: node.attrib["Version"] for node in project.findall(".//PackageReference")}
    assert versions == {
        "Azure.AI.Projects": "2.0.1",
        "Azure.AI.Projects.Agents": "2.0.0",
        "Azure.AI.Extensions.OpenAI": "2.0.0",
        "Azure.Identity": "1.21.0",
    }
    locked = json.loads((example / "packages.lock.json").read_text(encoding="utf-8"))["dependencies"]["net10.0"]
    assert {name: item["resolved"] for name, item in locked.items() if item["type"] == "Direct"} == versions
    assert all(item["contentHash"] for item in locked.values())

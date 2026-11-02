"""Verify Rust Event Hubs repair provenance and locked compile evidence."""

import hashlib
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("by-category/cloud-azure-microsoft-sdks/official-vendor-reference")
SOURCE = ROOT / "included/skills" / BASE / "azure-eventhub-rust"
OVERLAY = ROOT / "included/repaired/skills" / BASE / "azure-eventhub-rust-batching"
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/azure-eventhub-rust-batching-v1"


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


def test_compile_observation_binds_project_and_lock() -> None:
    result = json.loads((EVIDENCE / "windows-result.json").read_text(encoding="utf-8"))
    assert result["platform"] == "Windows" and result["check_exit_code"] == 0
    assert result["toolchain"]["rustc"].startswith("rustc 1.99.1 ")
    assert result["toolchain"]["cargo"].startswith("cargo 1.99.1 ")
    assert result["azure_service_called"] is False and result["agent_performance_tested"] is False
    assert result["source_sha256"] == sha(OVERLAY / "examples/src/main.rs")
    assert result["manifest_sha256"] == sha(OVERLAY / "examples/Cargo.toml")
    assert result["lock_sha256"] == sha(OVERLAY / "examples/Cargo.lock")


def test_direct_versions_are_present_in_lock() -> None:
    example = OVERLAY / "examples"
    project = tomllib.loads((example / "Cargo.toml").read_text(encoding="utf-8"))
    dependencies = project["dependencies"]
    assert dependencies["azure_messaging_eventhubs"] == "=0.15.0"
    assert dependencies["azure_identity"] == "=1.0.0"
    assert dependencies["tokio"]["version"] == "=1.54.1"
    locked = tomllib.loads((example / "Cargo.lock").read_text(encoding="utf-8"))["package"]
    versions = {(item["name"], item["version"]) for item in locked}
    assert {("azure_messaging_eventhubs", "0.15.0"), ("azure_identity", "1.0.0"), ("tokio", "1.54.1")} <= versions
    assert all(item.get("checksum") for item in locked if item.get("source", "").startswith("registry+"))

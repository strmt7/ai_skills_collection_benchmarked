"""Verify Java Event Hubs repair provenance and SDK-control evidence."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("by-category/cloud-azure-microsoft-sdks/official-vendor-reference")
SOURCE = ROOT / "included/skills" / BASE / "azure-eventhub-java"
OVERLAY = ROOT / "included/repaired/skills" / BASE / "azure-eventhub-java-batching"
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/azure-eventhub-java-batching-v1"


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


def test_windows_observations_bind_examples_and_dependency_graph() -> None:
    for major in (17, 27):
        result = json.loads((EVIDENCE / f"windows-jdk{major}.json").read_text(encoding="utf-8"))
        assert result["platform"] == "Windows" and result["java_version"].startswith(f"openjdk {major}")
        assert result["maven_version"].startswith("Apache Maven 3.10.0 ")
        assert result["azure_service_called"] is False and result["agent_performance_tested"] is False
        assert result["dependency_tree_matched"] is True and len(set(result["test_cases"])) == 9
        assert "originalRetryPatternOmitsRejectedEvent" in result["test_cases"]
        assert set(result["file_sha256"]) == {
            "pom.xml",
            "dependency-tree.json",
            "src/main/java/example/EventBatchSender.java",
            "src/test/java/com/azure/messaging/eventhubs/EventBatchSenderTest.java",
        }
        for name, digest in result["file_sha256"].items():
            assert sha(OVERLAY / "examples" / name) == digest


def test_dependency_snapshot_contains_the_qualified_direct_packages() -> None:
    tree = json.loads((OVERLAY / "examples/dependency-tree.json").read_text(encoding="utf-8"))
    direct = {(item["groupId"], item["artifactId"], item["version"]) for item in tree["children"]}
    assert ("com.azure", "azure-messaging-eventhubs", "5.21.7") in direct
    assert ("org.junit.jupiter", "junit-jupiter", "6.1.3") in direct

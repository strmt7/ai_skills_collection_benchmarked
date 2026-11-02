"""Verify provenance and offline evidence for synchronous Event Hubs checkpointing."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("by-category/cloud-azure-microsoft-sdks/official-vendor-reference")
SOURCE = ROOT / "included/skills" / BASE / "azure-eventhub-py"
OVERLAY = ROOT / "included/repaired/skills" / BASE / "azure-eventhub-python-checkpoint"
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/azure-eventhub-python-checkpoint-v1"


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


def test_observation_matches_the_example_and_package_snapshot() -> None:
    result = json.loads((EVIDENCE / "windows-result.json").read_text(encoding="utf-8"))
    assert result["platform"] == "Windows" and result["python_version"] == "3.13.17"
    assert result["azure_service_called"] is False and result["agent_performance_tested"] is False
    assert (result["tests_run"], result["failures"], result["errors"]) == (6, 0, 0)
    assert result["example_sha256"] == sha(OVERLAY / "examples/checkpoint_consumer.py")
    requirements = {}
    for line in (OVERLAY / "examples/requirements-test.txt").read_text(encoding="utf-8").splitlines():
        name, version = line.split("==", 1)
        requirements[name.lower().replace("_", "-")] = version
    assert all(requirements[name] == version for name, version in result["packages"].items())
    assert "azure-eventhub-checkpointstoreblob-aio" not in requirements

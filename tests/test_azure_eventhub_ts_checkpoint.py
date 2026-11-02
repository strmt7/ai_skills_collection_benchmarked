"""Verify the TypeScript checkpoint repair and its source-bound observations."""

import hashlib
import json

from helpers import ROOT

OVERLAY = ROOT / (
    "included/repaired/skills/by-category/cloud-azure-microsoft-sdks/"
    "official-vendor-reference/azure-eventhub-ts-checkpoint"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/azure-eventhub-ts-checkpoint-v1"
ORIGINAL = ROOT / (
    "included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-ts/SKILL.md"
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_original():
    return ORIGINAL.read_bytes().replace(b"\r\n", b"\n")


def test_repair_preserves_original_and_binds_all_evidence():
    repair = json.loads((OVERLAY / "repair.json").read_text(encoding="utf-8"))
    assert (OVERLAY / "provenance/original.SKILL.md").read_bytes() == canonical_original()
    assert repair["original_skill_sha256"] == hashlib.sha256(canonical_original()).hexdigest()
    for path, digest in repair["overlay_sha256"].items():
        assert sha(OVERLAY / path) == digest, path
    for path, digest in repair["evidence_sha256"].items():
        assert sha(EVIDENCE / path) == digest, path
    assert repair["azure_service_run"] is False
    assert repair["model_performance_claim"] is False


def test_platform_results_bind_inputs_and_retained_output():
    empty_digest = hashlib.sha256(b"").hexdigest()
    for platform in ("windows", "linux"):
        result = json.loads((EVIDENCE / f"{platform}-result.json").read_text(encoding="utf-8"))
        assert result["status"] == "passed"
        assert result["platform"].lower() == platform
        assert result["original_sha256"] == hashlib.sha256(canonical_original()).hexdigest()
        assert result["example_sha256"] == sha(OVERLAY / "examples/checkpoint-consumer.ts")
        assert result["azure_service_called"] is False
        assert result["agent_performance_tested"] is False
        for name, digest in result["control_sha256"].items():
            assert sha(EVIDENCE / name) == digest, name
        assert [item["name"] for item in result["commands"]] == [
            "node-version",
            "npm-version",
            "install",
            "typecheck",
            "callbacks",
        ]
        for item in result["commands"]:
            assert item["returncode"] == 0
            assert item["stderr_sha256"] == empty_digest
            stdout = EVIDENCE / "raw" / platform / f"{item['name']}.stdout"
            assert item["stdout_sha256"] == (sha(stdout) if stdout.exists() else empty_digest)
        callbacks = (EVIDENCE / "raw" / platform / "callbacks.stdout").read_text(encoding="utf-8")
        assert "# tests 5\n" in callbacks
        assert "# pass 5\n" in callbacks
        assert "# fail 0\n" in callbacks

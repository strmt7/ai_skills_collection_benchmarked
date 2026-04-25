import json
import re

import audit_skill_quality
import create_repaired_skill_overlays
import evaluate_external_benchmark_methods
from helpers import ROOT, load


def test_external_benchmark_registry_and_smoke_artifacts_cover_all_methods():
    registry = load("data/external_benchmark_methods.json")
    manifest = load(
        "artifacts/external-benchmark-integrations/2026-04-19-external-benchmark-method-smoke/manifest.json"
    )
    expected = evaluate_external_benchmark_methods.registry()

    assert registry == expected
    assert registry["method_count"] == 14
    assert manifest["summary"]["method_count"] == registry["method_count"]
    assert manifest["summary"]["adapter_ready"] == registry["method_count"]
    assert manifest["summary"]["adapter_incomplete"] == 0

    method_ids = {method["id"] for method in registry["methods"]}
    assert {item["method_id"] for item in manifest["artifacts"]} == method_ids
    for item in manifest["artifacts"]:
        artifact_path = ROOT / item["artifact_path"]
        assert artifact_path.is_file()
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert artifact["artifact_kind"] == "external_benchmark_method_smoke"
        assert artifact["input_snapshot"]["is_real"] is True
        assert re.fullmatch(r"[0-9a-f]{40}", artifact["input_snapshot"]["head_sha"])
        assert artifact["input_snapshot"]["tree_path_count"] > 0
        assert artifact["metrics"]["integration_status"] == "adapter_ready"
        assert artifact["metrics"]["score_percent"] == 100.0
        assert (ROOT / artifact["outputs"]["schema"]).is_file()
        assert artifact["method"]["primary_metrics"]
        assert artifact["method"]["integration_requirements"]


def test_external_benchmark_docs_are_generated_from_registry_and_manifest():
    registry = load("data/external_benchmark_methods.json")
    manifest = load(
        "artifacts/external-benchmark-integrations/2026-04-19-external-benchmark-method-smoke/manifest.json"
    )
    assert (ROOT / "docs" / "objective-benchmark-methods.md").read_text(
        encoding="utf-8"
    ) == evaluate_external_benchmark_methods.render_methods_doc(registry)
    assert (ROOT / "docs" / "external-benchmark-adapter-smoke.md").read_text(
        encoding="utf-8"
    ) == evaluate_external_benchmark_methods.render_smoke_report(manifest)


def test_repaired_overlays_cover_failed_runtime_artifacts_without_changing_originals():
    catalog = {entry["id"]: entry for entry in load("data/skills_catalog.json")}
    manifest = load("included/repaired/skills/manifest.json")
    failed_runtime = create_repaired_skill_overlays.failed_runtime_artifacts()

    assert manifest["summary"]["overlay_count"] == len(failed_runtime) == 34
    assert manifest["summary"]["passed"] == 34
    assert manifest["summary"]["failed"] == 0
    assert manifest["summary"]["average_score_percent"] == 100.0

    failed_skill_ids = {item["artifact"]["skill_id"] for item in failed_runtime}
    assert {item["skill_id"] for item in manifest["repairs"]} == failed_skill_ids
    for item in manifest["repairs"]:
        entry = catalog[item["skill_id"]]
        original_skill = ROOT / entry["mirrored_path"] / "SKILL.md"
        repaired_dir = ROOT / item["repaired_path"]
        repaired_skill = repaired_dir / "SKILL.md"
        original_copy = repaired_dir / "provenance" / "original.SKILL.md"
        repair_record = json.loads((repaired_dir / "repair.json").read_text(encoding="utf-8"))

        assert original_skill.is_file()
        assert repaired_skill.is_file()
        assert original_copy.read_text(encoding="utf-8") == original_skill.read_text(encoding="utf-8")
        assert (
            audit_skill_quality.missing_markdown_links(repaired_dir, repaired_skill.read_text(encoding="utf-8")) == []
        )
        assert repair_record["original_skill_file_sha256"] == entry["skill_file_sha256"]
        assert repair_record["repaired_path"] == item["repaired_path"]
        assert repair_record["actions"]


def test_repaired_readiness_artifacts_are_complete_and_docs_current():
    manifest = load("included/repaired/skills/manifest.json")
    artifact_manifest = load("artifacts/repaired-skill-readiness/2026-04-19-runtime-failure-repairs/manifest.json")

    assert artifact_manifest == manifest
    assert (ROOT / "docs" / "repaired-skill-readiness.md").read_text(
        encoding="utf-8"
    ) == create_repaired_skill_overlays.render_manifest_doc(manifest)
    for item in manifest["repairs"]:
        artifact_path = ROOT / item["artifact_path"]
        assert artifact_path.is_file()
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        result = json.loads((artifact_path.parent / "result.json").read_text(encoding="utf-8"))
        assert artifact["artifact_kind"] == "repaired_skill_readiness"
        assert artifact["input_snapshot"]["is_real"] is True
        assert artifact["input_snapshot"]["original_runtime_artifact"] == item["original_runtime_artifact"]
        assert artifact["metrics"]["benchmark_verdict"] == "passed"
        assert artifact["metrics"]["score_percent"] == 100.0
        assert (ROOT / artifact["outputs"]["schema"]).is_file()
        assert result["outputs"]["blocking_failures"] == []
        assert all(check["passed"] for check in result["outputs"]["checks"])


def test_repaired_directory_contains_one_skill_file_per_overlay_root():
    manifest = load("included/repaired/skills/manifest.json")
    for item in manifest["repairs"]:
        repaired_dir = ROOT / item["repaired_path"]
        skill_files = [path.relative_to(repaired_dir).as_posix() for path in repaired_dir.rglob("SKILL.md")]
        assert skill_files == ["SKILL.md"]

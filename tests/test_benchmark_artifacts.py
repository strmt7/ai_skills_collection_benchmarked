import json
import tempfile
from pathlib import Path

from helpers import ROOT, complete_artifacts, load

import check_benchmark_artifact


def assert_real_dataset_snapshot_resolved(snapshot):
    assert snapshot["resolved"] is True
    if snapshot["kind"] == "real-github-repository-tree":
        assert snapshot["tree_path_count"] > 0
    else:
        assert 200 <= snapshot["status"] < 400


def test_static_benchmark_results_are_real_and_current():
    results = load("data/static_benchmark_results.json")
    catalog = load("data/skills_catalog.json")
    artifacts = complete_artifacts()
    runtime_paths = {path.relative_to(ROOT).as_posix() for path, artifact, _ in artifacts if artifact["artifact_kind"] == "independent_benchmark"}
    provenance_paths = {path.relative_to(ROOT).as_posix() for path, artifact, _ in artifacts if artifact["artifact_kind"] == "provenance_check"}
    assert results["summary"]["skill_count"] == len(catalog)
    assert results["summary"]["runtime_artifacts_recorded"] == len(runtime_paths)
    assert results["summary"]["runtime_artifacts_recorded"] >= 10
    assert results["summary"]["runtime_artifacts_passed"] + results["summary"]["runtime_artifacts_failed"] == len(runtime_paths)
    assert results["summary"]["provenance_artifacts_recorded"] == len(provenance_paths)
    assert results["summary"]["provenance_artifacts_recorded"] >= 10
    assert {item["artifact_path"] for item in results["runtime_artifacts"]} == runtime_paths
    assert {item["artifact_path"] for item in results["provenance_artifacts"]} == provenance_paths
    for item in results["runtime_artifacts"]:
        assert item["artifact_kind"] == "independent_benchmark"
        assert item["benchmark_verdict"] in {"passed", "failed"}
        assert isinstance(item["score_percent"], (int, float))
    assert sum(track["runtime_artifacts_recorded"] for track in results["tracks"]) == len(runtime_paths)
    assert sum(item["runtime_artifacts_recorded"] for item in results["skills"]) == len(runtime_paths)
    assert {item["skill_id"] for item in results["skills"]} == {entry["id"] for entry in catalog}
    assert sum(item["static_checks_passed"] for item in results["skills"]) == results["summary"]["static_checks_passed"]
    assert sum(item["quality_fix_point_count"] for item in results["skills"]) == results["summary"]["quality_fix_points"]
    text = (ROOT / "docs" / "benchmark-results.md").read_text(encoding="utf-8")
    assert "Static checks passed" in text
    assert "Runtime scenario artifacts passed" in text
    assert "Runtime scenario artifacts failed" in text
    assert "Source-proof artifacts are provenance checks, not runtime benchmark passes" in text
    quality_text = (ROOT / "docs" / "skill-quality-findings.md").read_text(encoding="utf-8")
    assert "| Skill | Category | Static score | Failed checks | Fix points |" in quality_text


def test_independent_runtime_batch_is_separate_and_scored():
    manifest = load("artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/manifest.json")
    tasks = load("benchmarks/independent-runtime-readiness/batch-01/tasks.json")
    scenarios = {item["id"]: item for item in load("data/benchmark_scenarios.json")}
    assert manifest["artifact_kind"] == "independent_benchmark"
    assert manifest["summary"]["artifact_count"] == 10
    assert manifest["summary"]["passed"] == 0
    assert manifest["summary"]["failed"] == 10
    assert tasks["task_count"] == manifest["summary"]["artifact_count"]
    assert "excluding visual/browser categories" in tasks["selection_policy"]
    task_by_id = {task["task_id"]: task for task in tasks["tasks"]}
    for item in manifest["artifacts"]:
        artifact_path = ROOT / item["artifact_path"]
        artifact = load(item["artifact_path"])
        result = load(item["result_path"])
        assert artifact_path.is_file()
        assert artifact["artifact_kind"] == "independent_benchmark"
        assert artifact["independence"]["task_defined_outside_skill"] is True
        assert artifact["independence"]["evaluator_defined_outside_skill"] is True
        assert artifact["independence"]["expected_result_defined_outside_skill"] is True
        assert artifact["independence"]["uses_exact_skill_content_for_expected_result"] is False
        assert artifact["scenario_id"] == item["scenario_id"]
        assert scenarios[item["scenario_id"]]["dataset_track_id"] != "source-skill-repository"
        task = task_by_id[result["inputs"]["task_id"]]
        assert task["expected_result"]["all_required_checks_pass"] is True
        assert task["skill_id"] == item["skill_id"]
        assert result["metrics"]["benchmark_verdict"] == item["benchmark_verdict"]
        assert result["metrics"]["score_percent"] == item["score_percent"]
        assert result["outputs"]["blocking_failures"] == item["blocking_failures"]
        assert_real_dataset_snapshot_resolved(result["inputs"]["dataset_snapshot"])


def test_independent_runtime_batch_02_is_category_spread_and_non_overlapping():
    batch_01 = load("artifacts/benchmark-runs/2026-04-17-independent-runtime-readiness-batch-01/manifest.json")
    batch_02 = load("artifacts/benchmark-runs/2026-04-18-independent-runtime-readiness-batch-02/manifest.json")
    tasks = load("benchmarks/independent-runtime-readiness/batch-02/tasks.json")
    catalog = {entry["id"]: entry for entry in load("data/skills_catalog.json")}
    scenarios = {item["id"]: item for item in load("data/benchmark_scenarios.json")}
    batch_01_skill_ids = {item["skill_id"] for item in batch_01["artifacts"]}
    batch_02_skill_ids = {item["skill_id"] for item in batch_02["artifacts"]}

    assert batch_02["artifact_kind"] == "independent_benchmark"
    assert batch_02["summary"]["artifact_count"] == 12
    assert batch_02["summary"]["passed"] == 0
    assert batch_02["summary"]["failed"] == 12
    assert tasks["task_count"] == batch_02["summary"]["artifact_count"]
    assert "category-spread" in tasks["selection_policy"]
    assert "excluding skills already covered" in tasks["selection_policy"]
    assert not (batch_01_skill_ids & batch_02_skill_ids)
    assert len({catalog[skill_id]["category"] for skill_id in batch_02_skill_ids}) >= 8

    task_by_id = {task["task_id"]: task for task in tasks["tasks"]}
    for item in batch_02["artifacts"]:
        artifact = load(item["artifact_path"])
        result = load(item["result_path"])
        task = task_by_id[result["inputs"]["task_id"]]
        assert artifact["artifact_kind"] == "independent_benchmark"
        assert artifact["runner"]["batch_name"] == batch_02["batch_name"]
        assert artifact["independence"]["uses_exact_skill_content_for_expected_result"] is False
        assert artifact["scenario_id"] == item["scenario_id"]
        assert scenarios[item["scenario_id"]]["dataset_track_id"] != "source-skill-repository"
        assert task["skill_id"] == item["skill_id"]
        assert result["metrics"]["benchmark_verdict"] == item["benchmark_verdict"]
        assert result["metrics"]["score_percent"] == item["score_percent"]
        assert result["outputs"]["blocking_failures"] == item["blocking_failures"]
        assert_real_dataset_snapshot_resolved(result["inputs"]["dataset_snapshot"])


def test_benchmark_artifact_checker_accepts_complete_artifact_and_rejects_incomplete_visual():
    catalog = load("data/skills_catalog.json")
    entry = catalog[0]
    scenario_id = entry["benchmark_scenarios"][0]
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "transcript.txt").write_text("commands and transcript", encoding="utf-8")
        (base / "result.json").write_text("{}", encoding="utf-8")
        artifact = {
            "artifact_version": "1.0",
            "artifact_kind": "provenance_check",
            "skill_id": entry["id"],
            "scenario_id": scenario_id,
            "catalog_commit": "0" * 40,
            "source_commit": entry["commit_sha"],
            "source_repo": entry["source_repo"],
            "source_path": entry["source_path"],
            "runner": {"timestamp_utc": "2026-04-17T00:00:00Z", "tool": "pytest", "model_or_runtime": "local"},
            "scenario_requirements": {"visual_or_browser": False, "context_memory": False, "token_efficiency_claim": False},
            "input_snapshot": {"kind": "source", "identifier": entry["immutable_source_url"], "is_real": True},
            "execution": {"fresh_session": True, "commands_or_transcript_path": "transcript.txt"},
            "outputs": {"path": "result.json"},
            "metrics": {"checks": 1},
            "independence": {
                "task_defined_outside_skill": False,
                "evaluator_defined_outside_skill": True,
                "expected_result_defined_outside_skill": False,
                "uses_exact_skill_content_for_expected_result": True,
                "skill_content_usage": "source text used for provenance check only",
            },
            "evidence": {"artifact_paths": ["result.json"], "citations_or_paths": [entry["source_path"]]},
            "objective_checks": ["source citations present"],
        }
        artifact_path = base / "artifact.json"
        artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
        assert check_benchmark_artifact.validate_artifact(artifact_path)["verdict"] == "artifact_complete"
        artifact["scenario_requirements"]["visual_or_browser"] = True
        artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
        result = check_benchmark_artifact.validate_artifact(artifact_path)
        assert result["verdict"] == "artifact_incomplete"
        assert any("visual" in error for error in result["errors"])

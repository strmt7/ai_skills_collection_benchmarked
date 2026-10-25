import copy
import hashlib
import json

import _source_history as history
import check_benchmark_artifact
import create_repaired_skill_overlays
import pytest
from helpers import ROOT, load


def history_fixture(tmp_path):
    content = b"Original source instructions\n"
    name = "artifacts/source-history/skill/old/SKILL.md"
    snapshot = tmp_path / name
    snapshot.parent.mkdir(parents=True)
    snapshot.write_bytes(content)
    entry = {
        "id": "skill",
        "commit_sha": "a" * 40,
        "skill_file_sha256": hashlib.sha256(content).hexdigest(),
        "source_repo": "owner/repo",
        "source_path": "skills/example/SKILL.md",
        "mirrored_path": "included/skills/example",
        "benchmark_scenarios": ["scenario"],
    }
    record = {
        "entry": entry,
        "observed_catalog_revision": "b" * 40,
        "observed_catalog_sha256": "c" * 64,
        "skill_snapshot": name,
        "skill_snapshot_sha256": hashlib.sha256(content).hexdigest(),
    }
    registry = tmp_path / "data/catalog_source_history.json"
    registry.parent.mkdir()
    registry.write_text(json.dumps({"schema_version": 1, "versions": [record]}), encoding="utf-8")
    return entry, record, registry, snapshot


def test_source_resolution_requires_the_exact_known_commit(tmp_path):
    entry, _, _, _ = history_fixture(tmp_path)
    current = {**entry, "commit_sha": "d" * 40}
    assert history.resolve_entry(tmp_path, current, "skill", current["commit_sha"]) == (current, False)
    assert history.resolve_entry(tmp_path, current, "skill", entry["commit_sha"]) == (entry, True)
    with pytest.raises(ValueError, match="does not match"):
        history.resolve_entry(tmp_path, current, "skill", "e" * 40)
    with pytest.raises(ValueError, match="does not match"):
        history.resolve_entry(tmp_path, current, "different-skill", entry["commit_sha"])
    with pytest.raises(ValueError, match="does not match"):
        history.resolve_entry(tmp_path, current, "different-skill", current["commit_sha"])


@pytest.mark.parametrize("mutation", ["bytes", "catalog_hash", "duplicate", "external", "traversal", "missing"])
def test_historical_source_drift_or_ambiguous_admission_is_rejected(tmp_path, mutation):
    entry, record, registry, snapshot = history_fixture(tmp_path)
    records = [record]
    if mutation == "bytes":
        snapshot.write_bytes(b"Changed historical instructions\n")
    elif mutation == "catalog_hash":
        entry["skill_file_sha256"] = "f" * 64
    elif mutation == "duplicate":
        records.append(copy.deepcopy(record))
    elif mutation == "external":
        record["skill_snapshot"] = "README.md"
    elif mutation == "traversal":
        record["skill_snapshot"] = "artifacts/source-history/../../README.md"
    else:
        snapshot.unlink()
    registry.write_text(json.dumps({"schema_version": 1, "versions": records}), encoding="utf-8")
    with pytest.raises(ValueError):
        history.historical_entries(tmp_path)


def test_old_playwright_failure_remains_valid_but_does_not_qualify_new_source():
    skill_id = "lackeyjb-playwright-skill-skills-playwright-skill-skill-md"
    artifact_path = ROOT / (
        "artifacts/benchmark-runs/2026-04-18-independent-runtime-readiness-batch-02/"
        + skill_id
        + "/testing-qa-and-benchmarking-swe-bench-lite/artifact.json"
    )
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    before = artifact_path.read_bytes()
    result = check_benchmark_artifact.validate_artifact(artifact_path)
    assert result["verdict"] == "artifact_complete"
    assert any("historical source version" in item for item in result["warnings"])
    assert artifact["metrics"]["benchmark_verdict"] == "failed"
    assert artifact_path.read_bytes() == before
    current = next(
        item for item in load("data/static_benchmark_results.json")["skills"] if item["skill_id"] == skill_id
    )
    assert current["runtime_artifacts_recorded"] == 0
    assert current["historical_runtime_artifacts_recorded"] == 1


def test_historical_failure_cannot_trigger_destructive_repair_regeneration(monkeypatch):
    def forbidden_cleanup():
        pytest.fail("cleanup must not run before source-version validation")

    monkeypatch.setattr(create_repaired_skill_overlays, "clean_generated_outputs", forbidden_cleanup)
    with pytest.raises(ValueError, match="requires reevaluation"):
        create_repaired_skill_overlays.run()

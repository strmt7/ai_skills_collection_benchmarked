"""Logic + property tests for tools/create_source_proof_batch.py."""

from __future__ import annotations

import importlib
import io
import json
from contextlib import redirect_stdout

import pytest

create_source_proof_batch = importlib.import_module("create_source_proof_batch")


@pytest.fixture
def fake_entry() -> dict[str, object]:
    return {
        "id": "example-org-example-repo-agents-skills-demo-skill-md",
        "name": "demo-skill",
        "description": "Demonstration skill for a synthetic test.",
        "category": "Testing, QA & benchmarking",
        "subcategory": "latest-release-testing",
        "source_repo": "example-org/example-repo",
        "source_path": "agents/skills/demo/SKILL.md",
        "commit_sha": "0123456789abcdef0123456789abcdef01234567",
        "skill_file_sha256": "a" * 64,
        "immutable_source_url": (
            "https://github.com/example-org/example-repo/blob/"
            "0123456789abcdef0123456789abcdef01234567/agents/skills/demo/SKILL.md"
        ),
        "mirrored_path": "included/skills/by-category/test/demo-skill",
    }


@pytest.fixture
def fake_scenario() -> dict[str, object]:
    return {
        "id": "skill-proof-example-org-example-repo-agents-skills-demo-skill-md",
        "evaluator_path": "evaluators/source_grounded_skill_proof.schema.json",
        "objective_checks": ["frontmatter_present", "description_matches_activation"],
    }


@pytest.fixture
def fake_skill_text() -> str:
    return (
        "---\n"
        "name: demo-skill\n"
        "description: Demonstration skill for a synthetic test.\n"
        "---\n"
        "# Demo\n"
        "\n"
        "## Workflow\n"
        "\n"
        "1. Do a thing.\n"
        "2. Do another thing.\n"
    )


def test_scenario_id_for_uses_skill_proof_prefix(fake_entry):
    assert create_source_proof_batch.scenario_id_for(fake_entry) == (
        "skill-proof-" + fake_entry["id"]
    )


def test_build_result_is_deterministic(fake_entry, fake_scenario, fake_skill_text):
    a = create_source_proof_batch.build_result(fake_entry, fake_scenario, fake_skill_text)
    b = create_source_proof_batch.build_result(fake_entry, fake_scenario, fake_skill_text)
    assert a == b


def test_build_result_shape(fake_entry, fake_scenario, fake_skill_text):
    result = create_source_proof_batch.build_result(fake_entry, fake_scenario, fake_skill_text)
    for key in (
        "skill_id",
        "scenario_id",
        "source_repo",
        "source_path",
        "source_commit",
        "skill_file_sha256",
        "observed_headings",
        "proof_evidence",
        "activation_conditions",
        "workflow_steps",
    ):
        assert key in result, f"missing key: {key}"
    assert result["skill_id"] == fake_entry["id"]
    assert result["scenario_id"] == fake_scenario["id"]
    assert result["skill_file_sha256"] == fake_entry["skill_file_sha256"]


def test_build_transcript_embeds_stable_fields(fake_entry, fake_skill_text):
    transcript = create_source_proof_batch.build_transcript(
        batch_name="test-batch",
        timestamp_utc="2026-04-25T00:00:00Z",
        catalog_commit="deadbeef" * 5,
        entry=fake_entry,
        skill_text=fake_skill_text,
    )
    assert "batch: test-batch" in transcript
    assert "timestamp_utc: 2026-04-25T00:00:00Z" in transcript
    assert "skill_id: " + fake_entry["id"] in transcript
    assert transcript.endswith("\n")


def test_build_artifact_shape(fake_entry, fake_scenario, fake_skill_text):
    result = create_source_proof_batch.build_result(fake_entry, fake_scenario, fake_skill_text)
    artifact = create_source_proof_batch.build_artifact(
        batch_name="test-batch",
        catalog_commit="f" * 40,
        entry=fake_entry,
        scenario=fake_scenario,
        timestamp_utc="2026-04-25T00:00:00Z",
        result=result,
        skill_text=fake_skill_text,
    )
    assert artifact["artifact_kind"] == "provenance_check"
    assert artifact["skill_id"] == fake_entry["id"]
    assert artifact["scenario_id"] == fake_scenario["id"]
    assert artifact["runner"]["batch_name"] == "test-batch"
    assert artifact["outputs"]["schema"] == fake_scenario["evaluator_path"]
    assert artifact["outputs"]["result_sha256"].isalnum()
    assert len(artifact["outputs"]["result_sha256"]) == 64


def test_build_artifact_is_byte_identical_on_rerun(fake_entry, fake_scenario, fake_skill_text):
    result = create_source_proof_batch.build_result(fake_entry, fake_scenario, fake_skill_text)
    kwargs = dict(
        batch_name="b",
        catalog_commit="f" * 40,
        entry=fake_entry,
        scenario=fake_scenario,
        timestamp_utc="2026-04-25T00:00:00Z",
        result=result,
        skill_text=fake_skill_text,
    )
    assert create_source_proof_batch.build_artifact(**kwargs) == (
        create_source_proof_batch.build_artifact(**kwargs)
    )


def test_select_category_spread_distinct_categories_first():
    catalog = [
        {"id": "one", "category": "A"},
        {"id": "two", "category": "A"},
        {"id": "three", "category": "B"},
        {"id": "four", "category": "C"},
        {"id": "five", "category": "B"},
    ]
    selected = create_source_proof_batch.select_category_spread(catalog, limit=3)
    assert [e["id"] for e in selected] == ["one", "three", "four"]


def test_main_dry_run_json_emits_envelope_and_writes_nothing(tmp_path, monkeypatch):
    # Redirect the tool's write target into a tmp batch name that does not
    # correspond to an existing dir; dry-run should still not create it.
    out = io.StringIO()
    with redirect_stdout(out):
        rc = create_source_proof_batch.main(
            ["--dry-run", "--json", "--limit", "2", "--batch-name", "pytest-fake-batch"]
        )
    assert rc == 0
    payload = json.loads(out.getvalue())
    assert payload["dry_run"] is True
    assert payload["artifact_count"] == 2
    assert payload["incomplete_count"] == 0
    assert not (create_source_proof_batch.ROOT / "artifacts" / "benchmark-runs" / "pytest-fake-batch").exists()

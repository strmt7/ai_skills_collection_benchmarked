"""Keep original native build evidence distinct from task and model readiness."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import verify_swe_skills_bench_build_result as verifier

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "artifacts/research/2026-11-13/publisher-build-scorer"


def test_published_native_build_controls_keep_the_original_scorer_results():
    review = json.loads((FOLDER / "review.json").read_bytes())
    for name, digest in review["artifacts"].items():
        assert hashlib.sha256((FOLDER / name).read_bytes()).hexdigest() == digest, name
    for name, digest in review["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    results = {}
    for directory in sorted((FOLDER / "native").iterdir()):
        data = {
            name: (directory / filename).read_bytes()
            for name, filename in (
                ("inventory", "inventory.json"),
                ("execution", "execution.json"),
                ("publisher", "publisher.json"),
                ("stdout", "stdout.native"),
                ("stderr", "stderr.native"),
            )
        }
        result = verifier.verify_result(**data)
        assert result["admitted"]
        results[directory.name] = result["score"]
    assert results == {
        "compiled-source": 1.0,
        "syntax-failure": 0.0,
        "declared-nonzero": 1.0,
        "diagnostic-text-zero": 1.0,
        "owned-timeout": 0.0,
    }
    assert review["native_commands"] == 5 and review["publisher_contract_controls"] == 6
    assert review["selected_frame_tasks"] == 12 and review["selected_frame_evaluator_stages"] == 15
    assert not review["selected_task_builds_qualified"]
    assert not review["full_build_stage_controller_integrated"]
    assert not review["publisher_modular_aggregate_qualified"]
    assert review["model_invocations"] == review["counted_attempts"] == 0
    assert not review["agent_efficacy_established"]


def test_upstream_recheck_preserves_the_existing_community_baseline():
    upstream = json.loads((FOLDER / "upstream-recheck.json").read_bytes())
    assert upstream["canonical_repository"] == "multica-ai/andrej-karpathy-skills"
    assert upstream["head"] == "2c606141936f1eeef17fa3043a72095b4765b9c2"
    assert upstream["pinned_head_unchanged"] and not upstream["new_skill_content_imported"]
    assert len(upstream["official_repositories"]) == 3
    assert all(row["matches_previous_review"] for row in upstream["official_repositories"])

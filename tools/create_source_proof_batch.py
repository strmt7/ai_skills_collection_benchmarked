#!/usr/bin/env python3
"""Create a first batch of source-grounded runtime benchmark artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

import sys

sys.path.insert(0, str(ROOT / "tools"))

import build_catalog
import check_benchmark_artifact
from _lib_b import determinism as _det


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_sha(ref: str = "HEAD") -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", ref], text=True).strip()


def select_category_spread(catalog: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen_categories: set[str] = set()
    for entry in catalog:
        if entry["category"] in seen_categories:
            continue
        selected.append(entry)
        seen_categories.add(entry["category"])
        if len(selected) >= limit:
            break
    return selected


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def first_matching_line(lines: list[str], prefixes: tuple[str, ...]) -> str:
    for index, line in enumerate(lines, 1):
        if line.strip().lower().startswith(prefixes):
            return f"line {index}"
    return "line 1"


def proof_for(entry: dict[str, Any], skill_text: str) -> dict[str, Any]:
    meta, body = build_catalog.parse_frontmatter(skill_text)
    headings = build_catalog.headings(body)
    activation = entry["description"].rstrip(".")
    required_context = [
        f"Read the mirrored SKILL.md at {entry['mirrored_path']}/SKILL.md.",
        f"Use source provenance {entry['source_repo']} {entry['source_path']} at {entry['commit_sha']}.",
    ]
    resources = entry.get("resources") or {}
    if any(resources.values()):
        enabled = ", ".join(key for key, value in sorted(resources.items()) if value)
        required_context.append(f"Load bundled resources on demand: {enabled}.")
    safe_boundaries = [
        "Follow repository-level AGENTS.md and use one AI session only.",
        "Do not claim a runtime benchmark pass without a validated artifact.",
        "Do not use or emit real credentials; keep provider-shaped examples neutralized.",
    ]
    workflow_steps = [
        "Confirm the user task matches the skill description or source path.",
        "Read the local SKILL.md mirror and only then load referenced resources if needed.",
        "Execute the smallest task-specific workflow that produces objective evidence.",
        "Record commands, files read, outputs, metrics, and citations before making claims.",
    ]
    lines = skill_text.splitlines()
    evidence = [
        {
            "source_path": entry["source_path"],
            "line_or_section": first_matching_line(lines, ("name:",)),
            "claim": f"Skill identity is {meta.get('name') or entry['name']}.",
        },
        {
            "source_path": entry["source_path"],
            "line_or_section": first_matching_line(lines, ("description:",)),
            "claim": activation,
        },
    ]
    if headings:
        evidence.append(
            {
                "source_path": entry["source_path"],
                "line_or_section": f"section {headings[0]}",
                "claim": f"Observed workflow section: {headings[0]}.",
            }
        )
    return {
        "activation_conditions": [activation],
        "required_context": required_context,
        "safe_boundaries": safe_boundaries,
        "workflow_steps": workflow_steps,
        "proof_evidence": evidence,
        "observed_headings": headings,
    }


def write_artifact(
    *,
    batch_dir: Path,
    batch_name: str,
    catalog_commit: str,
    entry: dict[str, Any],
    scenario: dict[str, Any],
    timestamp_utc: str,
) -> dict[str, Any]:
    run_dir = batch_dir / entry["id"] / scenario["id"]
    run_dir.mkdir(parents=True, exist_ok=True)
    skill_path = ROOT / entry["mirrored_path"] / "SKILL.md"
    skill_text = skill_path.read_text(encoding="utf-8")
    proof = proof_for(entry, skill_text)
    result = proof | {
        "skill_id": entry["id"],
        "scenario_id": scenario["id"],
        "source_repo": entry["source_repo"],
        "source_path": entry["source_path"],
        "source_commit": entry["commit_sha"],
        "skill_file_sha256": entry["skill_file_sha256"],
    }
    write_json(run_dir / "result.json", result)
    transcript = "\n".join(
        [
            f"batch: {batch_name}",
            f"timestamp_utc: {timestamp_utc}",
            "runner: tools/create_source_proof_batch.py",
            f"catalog_commit: {catalog_commit}",
            f"skill_id: {entry['id']}",
            f"scenario_id: {scenario['id']}",
            f"read: {entry['mirrored_path']}/SKILL.md",
            f"source: {entry['immutable_source_url']}",
            f"skill_file_sha256: {entry['skill_file_sha256']}",
            f"line_count: {skill_text.count(chr(10)) + 1}",
            "checks:",
            "- parsed SKILL.md frontmatter/body",
            "- produced source-grounded proof JSON",
            "- recorded source path citations",
            "- validated artifact with tools/check_benchmark_artifact.py",
            "",
        ]
    )
    (run_dir / "transcript.txt").write_text(transcript, encoding="utf-8")
    artifact = {
        "artifact_version": "1.0",
        "artifact_kind": "provenance_check",
        "skill_id": entry["id"],
        "scenario_id": scenario["id"],
        "catalog_commit": catalog_commit,
        "source_commit": entry["commit_sha"],
        "source_repo": entry["source_repo"],
        "source_path": entry["source_path"],
        "runner": {
            "timestamp_utc": timestamp_utc,
            "tool": "tools/create_source_proof_batch.py",
            "model_or_runtime": "local-deterministic-source-proof-runner",
            "batch_name": batch_name,
        },
        "scenario_requirements": {
            "visual_or_browser": False,
            "context_memory": False,
            "token_efficiency_claim": False,
        },
        "input_snapshot": {
            "kind": "source-skill-repository",
            "identifier": entry["immutable_source_url"],
            "is_real": True,
            "source_commit": entry["commit_sha"],
            "mirrored_path": entry["mirrored_path"],
            "skill_file_sha256": entry["skill_file_sha256"],
        },
        "execution": {
            "fresh_session": True,
            "commands_or_transcript_path": "transcript.txt",
        },
        "outputs": {
            "path": "result.json",
            "schema": scenario["evaluator_path"],
            "result_sha256": sha256_text(json.dumps(result, sort_keys=True)),
        },
        "metrics": {
            "source_line_count": skill_text.count("\n") + 1,
            "observed_heading_count": len(proof["observed_headings"]),
            "proof_evidence_count": len(proof["proof_evidence"]),
            "activation_condition_count": len(proof["activation_conditions"]),
            "workflow_step_count": len(proof["workflow_steps"]),
        },
        "independence": {
            "task_defined_outside_skill": False,
            "evaluator_defined_outside_skill": True,
            "expected_result_defined_outside_skill": False,
            "uses_exact_skill_content_for_expected_result": True,
            "skill_content_usage": "source text used only for provenance and activation extraction; this artifact is not a counted runtime benchmark pass",
        },
        "evidence": {
            "artifact_paths": ["result.json", "transcript.txt"],
            "citations_or_paths": [entry["source_path"], f"{entry['mirrored_path']}/SKILL.md", "AGENTS.md"],
        },
        "objective_checks": scenario["objective_checks"],
    }
    write_json(run_dir / "artifact.json", artifact)
    validation = check_benchmark_artifact.validate_artifact(run_dir / "artifact.json")
    return {
        "skill_id": entry["id"],
        "scenario_id": scenario["id"],
        "artifact_path": (run_dir / "artifact.json").relative_to(ROOT).as_posix(),
        "validation": validation,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create source-grounded benchmark artifacts for a category-spread first batch."
    )
    parser.add_argument(
        "--batch-name", default="2026-04-17-first-source-proofs", help="Calendar-qualified batch directory name."
    )
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of skills to include.")
    parser.add_argument(
        "--catalog-commit", default=None, help="Override the recorded catalog commit (defaults to HEAD)."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    catalog = load_json(ROOT / "data" / "skills_catalog.json")
    scenarios = {item["id"]: item for item in load_json(ROOT / "data" / "benchmark_scenarios.json")}
    batch_dir = ROOT / "artifacts" / "benchmark-runs" / args.batch_name
    # Determinism precedence:
    #   1. SOURCE_DATE_EPOCH env (https://reproducible-builds.org/docs/source-date-epoch/)
    #   2. Existing manifest's generated_at_utc (idempotent regeneration)
    #   3. Latest commit time of the catalog (input-anchored fallback)
    existing_manifest = batch_dir / "manifest.json"
    catalog_commit = (
        args.catalog_commit
        or _det.resolve_catalog_commit(
            root=ROOT,
            existing_manifest_value=_det.existing_field(existing_manifest, "catalog_commit"),
        )
    )
    timestamp = _det.resolve_timestamp(
        existing_manifest_value=_det.existing_field(existing_manifest, "generated_at_utc"),
        fallback_epoch=_det.git_latest_commit_epoch_for(ROOT, [ROOT / "data" / "skills_catalog.json"]),
    )
    selected = select_category_spread(catalog, args.limit)
    results = []
    for entry in selected:
        scenario_id = f"skill-proof-{entry['id']}"
        results.append(
            write_artifact(
                batch_dir=batch_dir,
                batch_name=args.batch_name,
                catalog_commit=catalog_commit,
                entry=entry,
                scenario=scenarios[scenario_id],
                timestamp_utc=timestamp,
            )
        )
    manifest = {
        "batch_name": args.batch_name,
        "catalog_commit": catalog_commit,
        "generated_at_utc": timestamp,
        "selection_policy": f"first {len(selected)} distinct categories in catalog order",
        "artifact_count": len(results),
        "artifacts": results,
    }
    write_json(batch_dir / "manifest.json", manifest)
    incomplete = [item for item in results if item["validation"]["verdict"] != "artifact_complete"]
    print(f"Wrote {len(results)} source-proof artifacts to {batch_dir.relative_to(ROOT)}")
    if incomplete:
        print(json.dumps(incomplete, indent=2, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

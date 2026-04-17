#!/usr/bin/env python3
"""Validate benchmark run artifacts without claiming benchmark success."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HEX40 = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_TOP_LEVEL = [
    "artifact_version",
    "skill_id",
    "scenario_id",
    "catalog_commit",
    "source_commit",
    "source_repo",
    "source_path",
    "runner",
    "scenario_requirements",
    "input_snapshot",
    "execution",
    "outputs",
    "metrics",
    "evidence",
    "objective_checks",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_artifact_path(base: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    local = base / path
    if local.exists():
        return local
    return ROOT / path


def non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def validate_artifact(artifact_path: Path, catalog_path: Path | None = None, scenarios_path: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    base = artifact_path.parent
    try:
        artifact = load_json(artifact_path)
    except Exception as exc:
        return {"verdict": "artifact_invalid", "errors": [f"cannot read artifact JSON: {exc}"], "warnings": warnings}
    if not isinstance(artifact, dict):
        return {"verdict": "artifact_invalid", "errors": ["artifact root must be an object"], "warnings": warnings}

    for key in REQUIRED_TOP_LEVEL:
        if key not in artifact:
            errors.append(f"missing required field: {key}")
    if errors:
        return {"verdict": "artifact_invalid", "errors": errors, "warnings": warnings}

    if artifact.get("benchmark_status") == "passed" or artifact.get("verdict") == "passed":
        errors.append("artifact must not self-claim benchmark_status/verdict passed")
    for key in ["catalog_commit", "source_commit"]:
        if not HEX40.fullmatch(str(artifact.get(key, ""))):
            errors.append(f"{key} must be a 40-character lowercase git SHA")

    catalog_file = catalog_path or ROOT / "data" / "skills_catalog.json"
    scenarios_file = scenarios_path or ROOT / "data" / "benchmark_scenarios.json"
    try:
        catalog = {entry["id"]: entry for entry in load_json(catalog_file)}
        scenarios = {scenario["id"]: scenario for scenario in load_json(scenarios_file)}
    except Exception as exc:
        errors.append(f"cannot load catalog/scenarios: {exc}")
        catalog = {}
        scenarios = {}

    skill = catalog.get(artifact["skill_id"])
    if not skill:
        errors.append(f"unknown skill_id: {artifact['skill_id']}")
    else:
        if artifact["source_commit"] != skill["commit_sha"]:
            errors.append("source_commit does not match catalog commit_sha")
        if artifact["source_repo"] != skill["source_repo"]:
            errors.append("source_repo does not match catalog")
        if artifact["source_path"] != skill["source_path"]:
            errors.append("source_path does not match catalog")
        if artifact["scenario_id"] not in skill["benchmark_scenarios"]:
            errors.append("scenario_id is not assigned to this skill")
    if artifact["scenario_id"] not in scenarios:
        errors.append(f"unknown scenario_id: {artifact['scenario_id']}")

    runner = artifact["runner"]
    if not isinstance(runner, dict) or not all(runner.get(key) for key in ["timestamp_utc", "tool", "model_or_runtime"]):
        errors.append("runner must include timestamp_utc, tool, and model_or_runtime")

    execution = artifact["execution"]
    if not isinstance(execution, dict) or execution.get("fresh_session") is not True:
        errors.append("execution.fresh_session must be true")
    transcript = execution.get("commands_or_transcript_path") if isinstance(execution, dict) else None
    if not isinstance(transcript, str) or not transcript:
        errors.append("execution.commands_or_transcript_path must be a path")
    elif not resolve_artifact_path(base, transcript).exists():
        errors.append(f"missing transcript artifact: {transcript}")

    input_snapshot = artifact["input_snapshot"]
    if not isinstance(input_snapshot, dict) or input_snapshot.get("is_real") is not True:
        errors.append("input_snapshot.is_real must be true for a complete benchmark artifact")
    if not input_snapshot.get("identifier"):
        errors.append("input_snapshot.identifier is required")

    evidence = artifact["evidence"]
    if not isinstance(evidence, dict):
        errors.append("evidence must be an object")
        evidence = {}
    artifact_paths = evidence.get("artifact_paths")
    citations_or_paths = evidence.get("citations_or_paths")
    if not non_empty_list(artifact_paths):
        errors.append("evidence.artifact_paths must be a non-empty string list")
    else:
        missing = [path for path in artifact_paths if not resolve_artifact_path(base, path).exists()]
        if missing:
            errors.append(f"missing evidence artifact paths: {missing}")
    if not non_empty_list(citations_or_paths):
        errors.append("evidence.citations_or_paths must be a non-empty string list")
    if not non_empty_list(artifact.get("objective_checks")):
        errors.append("objective_checks must be a non-empty string list")

    requirements = artifact["scenario_requirements"]
    if not isinstance(requirements, dict):
        errors.append("scenario_requirements must be an object")
        requirements = {}

    if requirements.get("visual_or_browser") is True:
        visual = evidence.get("visual")
        if not isinstance(visual, dict):
            errors.append("visual/browser artifact requires evidence.visual")
        else:
            screenshot_paths = visual.get("screenshot_paths")
            if not non_empty_list(screenshot_paths):
                errors.append("visual evidence requires screenshot_paths")
            else:
                missing_screenshots = [path for path in screenshot_paths if not resolve_artifact_path(base, path).exists()]
                if missing_screenshots:
                    errors.append(f"missing visual screenshot paths: {missing_screenshots}")
            if not visual.get("website_url_or_mirror"):
                errors.append("visual evidence requires website_url_or_mirror")
            if not isinstance(visual.get("viewport"), dict):
                errors.append("visual evidence requires viewport object")

    if requirements.get("context_memory") is True:
        memory = evidence.get("context_memory")
        if not isinstance(memory, dict):
            errors.append("context/memory artifact requires evidence.context_memory")
        else:
            probes = memory.get("delayed_recall_probes")
            if not isinstance(probes, list) or not probes:
                errors.append("context/memory evidence requires delayed_recall_probes")
            before = memory.get("token_usage_before")
            after = memory.get("token_usage_after")
            if not isinstance(before, int) or not isinstance(after, int) or before <= 0 or after <= 0:
                errors.append("context/memory evidence requires positive integer token usage before and after")
            elif after > before and not isinstance(memory.get("quality_delta"), (int, float)):
                errors.append("token usage increased without numeric quality_delta")
            if requirements.get("token_efficiency_claim") is True and isinstance(before, int) and isinstance(after, int) and after > before:
                errors.append("token_efficiency_claim requires token_usage_after <= token_usage_before")

    verdict = "artifact_complete" if not errors else "artifact_incomplete"
    return {"verdict": verdict, "errors": errors, "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a benchmark run artifact.")
    parser.add_argument("artifact", help="Path to benchmark run artifact JSON")
    parser.add_argument("--catalog", default=str(ROOT / "data" / "skills_catalog.json"))
    parser.add_argument("--scenarios", default=str(ROOT / "data" / "benchmark_scenarios.json"))
    args = parser.parse_args()
    result = validate_artifact(Path(args.artifact), Path(args.catalog), Path(args.scenarios))
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["verdict"] == "artifact_complete":
        return 0
    return 1 if result["verdict"] == "artifact_invalid" else 2


if __name__ == "__main__":
    sys.exit(main())

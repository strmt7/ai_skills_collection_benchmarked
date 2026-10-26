"""Trusted validator API cases; this module never enters the candidate runtime."""

from __future__ import annotations

import copy
from typing import Any


def cases(source: dict[str, Any], revision: str) -> list[tuple[str, dict[str, Any], bool, bool]]:
    valid = {
        "artifact_version": "1.0",
        "artifact_kind": "provenance_check",
        "skill_id": source["id"],
        "scenario_id": source["benchmark_scenarios"][0],
        "catalog_commit": revision,
        "source_commit": source["commit_sha"],
        "source_repo": source["source_repo"],
        "source_path": source["source_path"],
        "runner": {"timestamp_utc": "2026-10-02T00:00:00Z", "tool": "external-grader", "model_or_runtime": "grader"},
        "scenario_requirements": {"visual_or_browser": False, "context_memory": False, "token_efficiency_claim": False},
        "input_snapshot": {"kind": "source", "identifier": source["immutable_source_url"], "is_real": True},
        "execution": {"fresh_session": True, "commands_or_transcript_path": "transcript.txt"},
        "outputs": {"path": "result.json"},
        "metrics": {"checks": 1},
        "independence": {
            "task_defined_outside_skill": False,
            "evaluator_defined_outside_skill": True,
            "expected_result_defined_outside_skill": False,
            "uses_exact_skill_content_for_expected_result": True,
            "skill_content_usage": "Provenance record used only to test the validator API",
        },
        "evidence": {"artifact_paths": ["result.json"], "citations_or_paths": [source["source_path"]]},
        "objective_checks": ["source provenance"],
    }
    result = [("valid_provenance", valid, True, False)]
    extra = copy.deepcopy(valid)
    extra["notes"] = "Permitted extra metadata"
    extra["metrics"]["custom_score"] = 0.25
    result.append(("valid_extra_metadata", extra, True, False))
    for field in (
        "skill_id",
        "scenario_id",
        "artifact_kind",
        "input_snapshot",
        "execution",
        "runner",
        "independence",
        "evidence",
        "metrics",
        "outputs",
        "scenario_requirements",
    ):
        invalid = copy.deepcopy(valid)
        invalid[field] = []
        result.append(("malformed_" + field, invalid, False, False))
    empty = copy.deepcopy(valid)
    empty["input_snapshot"]["kind"] = ""
    result.append(("schema_minimum_string_length", empty, False, False))
    transcript, evidence = copy.deepcopy(valid), copy.deepcopy(valid)
    transcript["execution"]["commands_or_transcript_path"] = "directory"
    evidence["evidence"]["artifact_paths"] = ["directory"]
    result.extend(
        [
            ("transcript_must_be_file", transcript, False, False),
            ("evidence_must_be_file", evidence, False, False),
            ("missing_schema_rejected", copy.deepcopy(valid), False, True),
        ]
    )
    return result


def accepted(response: Any, complete: bool) -> bool:
    if not isinstance(response, dict) or response.get("kind") != "candidate_result":
        return False
    value = response.get("value")
    if (
        not isinstance(value, dict)
        or not isinstance(value.get("verdict"), str)
        or not isinstance(value.get("errors"), list)
        or not isinstance(value.get("warnings"), list)
    ):
        return False
    if complete:
        return value.get("verdict") == "artifact_complete" and not value["errors"]
    return value.get("verdict") in {"artifact_invalid", "artifact_incomplete"} and bool(value["errors"])

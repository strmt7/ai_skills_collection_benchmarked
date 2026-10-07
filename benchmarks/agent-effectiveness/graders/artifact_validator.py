"""Behavioral grader kept outside the agent task workspace."""

from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
from pathlib import Path
from typing import Any


def evaluate(workspace: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location(
        "trial_artifact_validator", workspace / "tools/check_benchmark_artifact.py"
    )
    if spec is None or spec.loader is None:
        return {"status": "harness_error", "error": "cannot import validator"}
    module: Any = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        return {"status": "task_failed", "error": f"submitted validator cannot import: {type(exc).__name__}: {exc}"}
    catalog = json.loads((workspace / "data/skills_catalog.json").read_text(encoding="utf-8"))
    source = catalog[0]
    results = []
    with tempfile.TemporaryDirectory() as temporary:
        base = Path(temporary)
        (base / "transcript.txt").write_text("Recorded commands\n", encoding="utf-8")
        (base / "result.json").write_text("{}\n", encoding="utf-8")
        (base / "directory").mkdir()
        valid = {
            "artifact_version": "1.0",
            "artifact_kind": "provenance_check",
            "skill_id": source["id"],
            "scenario_id": source["benchmark_scenarios"][0],
            "catalog_commit": "4bd209752567f5c35074d4ee4a73600e1c45c283",
            "source_commit": source["commit_sha"],
            "source_repo": source["source_repo"],
            "source_path": source["source_path"],
            "runner": {
                "timestamp_utc": "2026-10-02T00:00:00Z",
                "tool": "external-grader",
                "model_or_runtime": "grader",
            },
            "scenario_requirements": {
                "visual_or_browser": False,
                "context_memory": False,
                "token_efficiency_claim": False,
            },
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

        def check(case: str, record: dict[str, Any], expected_complete: bool) -> None:
            path = base / "artifact.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            try:
                result = module.validate_artifact(path)
                structured = (
                    isinstance(result, dict)
                    and isinstance(result.get("errors"), list)
                    and isinstance(result.get("warnings"), list)
                )
                passed = structured and (
                    result.get("verdict") == "artifact_complete" and not result["errors"]
                    if expected_complete
                    else result.get("verdict") in {"artifact_invalid", "artifact_incomplete"} and bool(result["errors"])
                )
                results.append({"case": case, "passed": bool(passed), "validator_result": result})
            except Exception as exc:
                results.append({"case": case, "passed": False, "exception": f"{type(exc).__name__}: {exc}"})

        check("valid_provenance", valid, True)
        extra = copy.deepcopy(valid)
        extra["notes"] = "Permitted extra metadata"
        extra["metrics"]["custom_score"] = 0.25
        check("valid_extra_metadata", extra, True)
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
            malformed = copy.deepcopy(valid)
            malformed[field] = []
            check(f"malformed_{field}", malformed, False)
        empty_kind = copy.deepcopy(valid)
        empty_kind["input_snapshot"]["kind"] = ""
        check("schema_minimum_string_length", empty_kind, False)
        directory_transcript = copy.deepcopy(valid)
        directory_transcript["execution"]["commands_or_transcript_path"] = "directory"
        check("transcript_must_be_file", directory_transcript, False)
        directory_evidence = copy.deepcopy(valid)
        directory_evidence["evidence"]["artifact_paths"] = ["directory"]
        check("evidence_must_be_file", directory_evidence, False)
        schema_path = module.SCHEMA_PATH
        module.SCHEMA_PATH = base / "unavailable.schema.json"
        try:
            check("missing_schema_rejected", valid, False)
        finally:
            module.SCHEMA_PATH = schema_path
    return {
        "status": "task_passed" if all(item["passed"] for item in results) else "task_failed",
        "checks_passed": sum(item["passed"] for item in results),
        "checks_total": len(results),
        "checks": results,
        "scope": "Validator behavior on an independent development probe; not a skill-performance claim",
    }

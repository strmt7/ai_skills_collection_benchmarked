#!/usr/bin/env python3
"""Validate benchmark run artifacts without claiming benchmark success.

This validator performs two layers of checks on a ``artifact.json`` file:

1. A structural pass driven by ``evaluators/benchmark_run_artifact.schema.json``
   (JSON Schema Draft 2020-12). The implementation is pure Python and only
   walks the subset of keywords that the schema actually uses:
   ``type``, ``enum``, ``pattern``, ``required``, ``properties``,
   ``additionalProperties``, ``items``, and ``minItems``. Each error carries
   a JSON-Pointer style path (e.g. ``/evidence/artifact_paths/0``) so that
   callers can pinpoint which field is broken.

2. A domain pass that enforces catalog/scenario cross-references, independence
   invariants, transcript/evidence file existence, and visual/context-memory
   requirements. These rules go beyond pure JSON Schema (they touch the
   filesystem and other JSON data files).

The ``validate_artifact(path, ...)`` entry point is imported by
``tests/helpers.py`` and the CI workflow. Its verdict set is stable:

- ``artifact_complete`` -- no errors
- ``artifact_incomplete`` -- domain-level problems
- ``artifact_invalid`` -- the file cannot be parsed or the root is wrong type

CLI:

    python tools/check_benchmark_artifact.py ARTIFACT_JSON
    python tools/check_benchmark_artifact.py --validate-all DIR

Exit codes: 0 complete, 1 invalid, 2 incomplete.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "evaluators" / "benchmark_run_artifact.schema.json"

HEX40 = re.compile(r"^[0-9a-f]{40}$")

# Preserved for backward compatibility: existing callers / tests import this
# list to reason about required top-level fields. Kept in sync with the schema
# at import time (see _load_schema below).
REQUIRED_TOP_LEVEL = [
    "artifact_version",
    "artifact_kind",
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
    "independence",
    "evidence",
    "objective_checks",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_schema() -> dict[str, Any] | None:
    try:
        schema = load_json(SCHEMA_PATH)
    except Exception:
        return None
    if not isinstance(schema, dict):
        return None
    return schema


def resolve_artifact_path(base: Path, value: str) -> Path:
    """Resolve a path recorded in the artifact.

    Artifact evidence paths are stored as either repo-relative paths (e.g.
    ``benchmarks/.../tasks.json``) or artifact-directory-relative paths (e.g.
    ``result.json``). Try the artifact's own directory first, then the repo
    root.
    """
    path = Path(value)
    if path.is_absolute():
        return path
    local = base / path
    if local.exists():
        return local
    return ROOT / path


def non_empty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)


def _pointer(parts: Iterable[str | int]) -> str:
    out = []
    for part in parts:
        text = str(part).replace("~", "~0").replace("/", "~1")
        out.append(text)
    return "/" + "/".join(out) if out else ""


# ---------------------------------------------------------------------------
# Schema walker (Draft 2020-12 subset)
# ---------------------------------------------------------------------------


_JSON_TYPE_MAP: dict[str, tuple[type, ...] | type] = {
    "object": dict,
    "array": list,
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "null": type(None),
}


def _matches_type(value: Any, declared: Any) -> bool:
    if declared is None:
        return True
    if isinstance(declared, list):
        return any(_matches_type(value, option) for option in declared)
    expected = _JSON_TYPE_MAP.get(declared)
    if expected is None:
        return True
    # In JSON, booleans are not integers/numbers; Python disagrees.
    if declared in {"integer", "number"} and isinstance(value, bool):
        return False
    if declared == "integer" and isinstance(value, float):
        return value.is_integer()
    return isinstance(value, expected)


def _schema_walk(
    schema: dict[str, Any],
    instance: Any,
    path: list[str | int],
    errors: list[str],
) -> None:
    declared_type = schema.get("type")
    if declared_type is not None and not _matches_type(instance, declared_type):
        errors.append(f"{_pointer(path) or '/'}: expected type {declared_type!r}, got {type(instance).__name__}")
        return

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{_pointer(path) or '/'}: value {instance!r} not in enum {schema['enum']}")

    if "pattern" in schema and isinstance(instance, str) and not re.search(schema["pattern"], instance):
        errors.append(f"{_pointer(path) or '/'}: value does not match pattern {schema['pattern']!r}")

    if isinstance(instance, dict):
        for required in schema.get("required", []) or []:
            if required not in instance:
                errors.append(f"{_pointer(path + [required])}: missing required field")
        for key, sub_schema in (schema.get("properties") or {}).items():
            if key in instance and isinstance(sub_schema, dict):
                _schema_walk(sub_schema, instance[key], path + [key], errors)

    if isinstance(instance, list):
        min_items = schema.get("minItems")
        if isinstance(min_items, int) and len(instance) < min_items:
            errors.append(f"{_pointer(path) or '/'}: expected at least {min_items} items, got {len(instance)}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, element in enumerate(instance):
                _schema_walk(item_schema, element, path + [index], errors)


def _schema_errors(artifact: Any) -> list[str]:
    schema = _load_schema()
    if schema is None:
        return []
    errors: list[str] = []
    _schema_walk(schema, artifact, [], errors)
    return errors


# ---------------------------------------------------------------------------
# Domain validation
# ---------------------------------------------------------------------------


def validate_artifact(
    artifact_path: Path,
    catalog_path: Path | None = None,
    scenarios_path: Path | None = None,
) -> dict[str, Any]:
    """Validate a single benchmark run artifact.

    Returns a dict with ``verdict``, ``errors`` and ``warnings``. ``verdict`` is
    one of ``artifact_complete``, ``artifact_incomplete`` or ``artifact_invalid``.
    """
    warnings: list[str] = []
    base = artifact_path.parent
    try:
        artifact = load_json(artifact_path)
    except Exception as exc:
        return {
            "verdict": "artifact_invalid",
            "errors": [f"cannot read artifact JSON: {exc}"],
            "warnings": warnings,
        }
    if not isinstance(artifact, dict):
        return {
            "verdict": "artifact_invalid",
            "errors": ["artifact root must be an object"],
            "warnings": warnings,
        }

    # Layer 1: schema-driven structural pre-pass. Converts missing-required /
    # wrong-type problems into precise JSON-Pointer messages. We still need the
    # legacy top-level check below so that callers that skip the schema (e.g.
    # tests that run without an evaluators/ directory) still fail safely.
    errors: list[str] = []
    errors.extend(_schema_errors(artifact))

    legacy_missing = [key for key in REQUIRED_TOP_LEVEL if key not in artifact]
    for key in legacy_missing:
        msg = f"missing required field: {key}"
        if msg not in errors and f"/{key}: missing required field" not in errors:
            errors.append(msg)
    # If the artifact is missing basic fields, stop before domain checks.
    if legacy_missing:
        return {
            "verdict": "artifact_invalid",
            "errors": errors,
            "warnings": warnings,
        }

    # Layer 2: domain checks (catalog/scenarios cross-reference, evidence
    # existence on disk, independence invariants, visual/context-memory).
    if artifact.get("benchmark_status") == "passed" or artifact.get("verdict") == "passed":
        errors.append("artifact must not self-claim benchmark_status/verdict passed")

    artifact_kind = artifact.get("artifact_kind")
    if artifact_kind not in {"provenance_check", "independent_benchmark"}:
        errors.append("artifact_kind must be provenance_check or independent_benchmark")

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

    independence = artifact["independence"]
    if not isinstance(independence, dict):
        errors.append("independence must be an object")
        independence = {}
    if not independence.get("skill_content_usage"):
        errors.append("independence.skill_content_usage is required")
    if artifact_kind == "independent_benchmark":
        required_true = [
            "task_defined_outside_skill",
            "evaluator_defined_outside_skill",
            "expected_result_defined_outside_skill",
        ]
        for key in required_true:
            if independence.get(key) is not True:
                errors.append(f"independent_benchmark requires independence.{key} true")
        if independence.get("uses_exact_skill_content_for_expected_result") is not False:
            errors.append("independent_benchmark requires uses_exact_skill_content_for_expected_result false")
        scenario = scenarios.get(artifact["scenario_id"])
        if scenario and scenario.get("dataset_track_id") == "source-skill-repository":
            errors.append("source-skill-repository scenarios are provenance checks, not independent benchmarks")
    elif artifact_kind == "provenance_check":
        warnings.append(
            "provenance_check artifacts are complete evidence records but do not count as runtime benchmark passes"
        )

    runner = artifact["runner"]
    if not isinstance(runner, dict) or not all(
        runner.get(key) for key in ["timestamp_utc", "tool", "model_or_runtime"]
    ):
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
        assert isinstance(artifact_paths, list)  # narrowed by non_empty_list
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
                assert isinstance(screenshot_paths, list)  # narrowed by non_empty_list
                missing_screenshots = [
                    path for path in screenshot_paths if not resolve_artifact_path(base, path).exists()
                ]
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
            if (
                requirements.get("token_efficiency_claim") is True
                and isinstance(before, int)
                and isinstance(after, int)
                and after > before
            ):
                errors.append("token_efficiency_claim requires token_usage_after <= token_usage_before")

    verdict = "artifact_complete" if not errors else "artifact_incomplete"
    return {"verdict": verdict, "errors": errors, "warnings": warnings}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _validate_all(
    directory: Path,
    catalog_path: Path,
    scenarios_path: Path,
) -> tuple[int, int, list[tuple[Path, dict[str, Any]]]]:
    artifacts = sorted(directory.rglob("artifact.json"))
    failures: list[tuple[Path, dict[str, Any]]] = []
    for artifact_path in artifacts:
        result = validate_artifact(artifact_path, catalog_path, scenarios_path)
        if result["verdict"] != "artifact_complete":
            failures.append((artifact_path, result))
    return len(artifacts), len(failures), failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_benchmark_artifact.py",
        description="Validate a benchmark run artifact.",
    )
    parser.add_argument(
        "artifact",
        nargs="?",
        help="Path to benchmark run artifact JSON (omit with --validate-all).",
    )
    parser.add_argument(
        "--validate-all",
        dest="validate_all",
        metavar="DIR",
        help="Validate every artifact.json found under DIR and exit non-zero on any failure.",
    )
    parser.add_argument("--catalog", default=str(ROOT / "data" / "skills_catalog.json"))
    parser.add_argument("--scenarios", default=str(ROOT / "data" / "benchmark_scenarios.json"))
    args = parser.parse_args(argv)

    catalog_path = Path(args.catalog)
    scenarios_path = Path(args.scenarios)

    if args.validate_all:
        directory = Path(args.validate_all)
        if not directory.is_dir():
            print(f"not a directory: {directory}", file=sys.stderr)
            return 1
        total, failed, failures = _validate_all(directory, catalog_path, scenarios_path)
        if failed:
            for artifact_path, result in failures:
                print(f"{artifact_path}: {result['verdict']}", file=sys.stderr)
                for error in result["errors"]:
                    print(f"  - {error}", file=sys.stderr)
            return 2
        print(f"validated {total} benchmark/provenance artifacts")
        return 0

    if not args.artifact:
        parser.error("either ARTIFACT or --validate-all DIR is required")

    result = validate_artifact(Path(args.artifact), catalog_path, scenarios_path)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["verdict"] == "artifact_complete":
        return 0
    return 1 if result["verdict"] == "artifact_invalid" else 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Run offline benchmark checks that can be proven from this repository.

The tool measures static structural properties of the mirrored skill catalog
(hashes, scenario coverage, frontmatter, human catalog page existence) and
folds in every validated runtime or provenance artifact under
``artifacts/benchmark-runs/``. It writes three outputs:

* ``data/static_benchmark_results.json`` (canonical JSON)
* ``docs/benchmark-results.md`` (human report)
* ``docs/skill-quality-findings.md`` (per-skill fix-point table)

The ``--check`` subcommand re-runs the measurement in-memory and compares it
byte-for-byte against the committed files. When inputs genuinely drift (for
example because a mirrored directory hash changes upstream), ``--check``
prints a compact, sortable drift report pointing at the exact fields that
moved rather than a vague "is stale" message. Operators can then decide
whether to regenerate (`run_static_benchmarks.py`) or fix the upstream input.

The CI contract (`--check` exit codes 0/1) is preserved; progress output is
routed to stderr so stdout remains machine-consumable.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_catalog
import check_benchmark_artifact
from _lib_c import (
    describe_data_drift,
    describe_text_drift,
    load_json,
    log_progress,
    progress_iter,
    write_json_canonical,
    write_text,
)

DATA_PATH = ROOT / "data" / "static_benchmark_results.json"
RESULTS_DOC = ROOT / "docs" / "benchmark-results.md"
QUALITY_DOC = ROOT / "docs" / "skill-quality-findings.md"


# --------------------------------------------------------------------------- #
# artifact discovery
# --------------------------------------------------------------------------- #


def _iter_artifacts(artifact_kind: str | None) -> list[dict[str, Any]]:
    root = ROOT / "artifacts" / "benchmark-runs"
    if not root.exists():
        return []
    records: list[dict[str, Any]] = []
    for artifact_path in sorted(root.rglob("artifact.json")):
        validation = check_benchmark_artifact.validate_artifact(artifact_path)
        if validation["verdict"] != "artifact_complete":
            continue
        try:
            artifact = load_json(artifact_path)
        except Exception:  # pragma: no cover - validator would have caught this
            continue
        if artifact_kind and artifact.get("artifact_kind") != artifact_kind:
            continue
        records.append(
            {
                "artifact_path": artifact_path.relative_to(ROOT).as_posix(),
                "artifact_kind": artifact["artifact_kind"],
                "skill_id": artifact["skill_id"],
                "scenario_id": artifact["scenario_id"],
                "source_repo": artifact["source_repo"],
                "source_path": artifact["source_path"],
                "catalog_commit": artifact["catalog_commit"],
                "runner": artifact["runner"],
                "metrics": artifact.get("metrics", {}),
                "benchmark_verdict": artifact.get("metrics", {}).get("benchmark_verdict"),
                "score_percent": artifact.get("metrics", {}).get("score_percent"),
                "validation": validation,
            }
        )
    return records


# --------------------------------------------------------------------------- #
# per-skill static checks
# --------------------------------------------------------------------------- #


def _skill_doc_path(entry: dict[str, Any]) -> Path:
    return (
        ROOT
        / "docs"
        / "catalog"
        / "skills"
        / "by-category"
        / build_catalog.slug(entry["category"])
        / build_catalog.slug(entry["subcategory"])
        / f"{entry['install_name']}.md"
    )


def _check_entry(
    entry: dict[str, Any],
    scenarios: dict[str, dict[str, Any]],
    artifacts_by_skill: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    mirror = ROOT / entry["mirrored_path"]
    skill_file = mirror / "SKILL.md"
    agent_ready = ROOT / entry["agent_ready_path"]
    skill_doc = _skill_doc_path(entry)
    agent_ready_text = agent_ready.read_text(encoding="utf-8") if agent_ready.is_file() else ""

    checks = {
        "mirror_directory_exists": mirror.is_dir(),
        "root_skill_file_exists": skill_file.is_file(),
        "no_nested_skill_files": len(list(mirror.rglob("SKILL.md"))) == 1 if mirror.exists() else False,
        "skill_file_hash_matches": skill_file.is_file()
        and build_catalog.sha256_file(skill_file) == entry["skill_file_sha256"],
        "skill_directory_hash_matches": mirror.is_dir()
        and build_catalog.sha256_tree(mirror) == entry["skill_dir_sha256"],
        "agent_ready_skill_exists": agent_ready.is_file(),
        "agent_ready_frontmatter_present": agent_ready_text.startswith("---\n"),
        "agent_ready_markdown_concise": len(agent_ready_text.splitlines()) <= 120,
        "scenario_count_ok": len(entry["benchmark_scenarios"]) >= build_catalog.MIN_SCENARIOS + 1,
        "source_proof_first": bool(entry["benchmark_scenarios"])
        and entry["benchmark_scenarios"][0] == f"skill-proof-{entry['id']}",
        "all_assigned_scenarios_exist": all(s in scenarios for s in entry["benchmark_scenarios"]),
        "human_skill_page_exists": skill_doc.is_file(),
    }
    passed = sum(1 for value in checks.values() if value)
    total = len(checks)
    failed = [name for name, value in checks.items() if not value]
    return {
        "skill_id": entry["id"],
        "name": entry["name"],
        "category": entry["category"],
        "subcategory": entry["subcategory"],
        "source_repo": entry["source_repo"],
        "source_path": entry["source_path"],
        "mirrored_path": entry["mirrored_path"],
        "agent_ready_path": entry["agent_ready_path"],
        "runtime_artifacts_recorded": len(artifacts_by_skill.get(entry["id"], [])),
        "runtime_artifact_paths": [item["artifact_path"] for item in artifacts_by_skill.get(entry["id"], [])],
        "static_checks_passed": passed,
        "static_checks_total": total,
        "static_score_percent": round((passed / total) * 100, 2),
        "checks": checks,
        "failed_checks": failed,
        "quality_fix_point_count": len(entry.get("improvement_notes", [])),
        "quality_fix_points": entry.get("improvement_notes", []),
    }


# --------------------------------------------------------------------------- #
# rendering
# --------------------------------------------------------------------------- #


def _cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_results(results: dict[str, Any]) -> str:
    lines = [
        "# Benchmark Results",
        "",
        "This page reports measured results only. Offline static checks were run against the mirrored files in this repository. Runtime benchmark counts include only committed independent benchmark artifacts that pass `tools/check_benchmark_artifact.py`. Source-proof artifacts are provenance checks, not runtime benchmark passes.",
        "",
        "## Summary",
        "",
        f"- Skills checked: `{results['summary']['skill_count']}`",
        f"- Static checks passed: `{results['summary']['static_checks_passed']}` / `{results['summary']['static_checks_total']}`",
        f"- Average static score: `{results['summary']['average_static_score_percent']}`",
        f"- Runtime scenario artifacts recorded: `{results['summary']['runtime_artifacts_recorded']}`",
        f"- Runtime scenario artifacts passed: `{results['summary']['runtime_artifacts_passed']}`",
        f"- Runtime scenario artifacts failed: `{results['summary']['runtime_artifacts_failed']}`",
        f"- Source-proof provenance artifacts recorded: `{results['summary']['provenance_artifacts_recorded']}`",
        "",
        "## Benchmark Tracks",
        "",
        "| Track | Assigned scenarios | Runtime artifacts |",
        "|---|---:|---:|",
    ]
    for track in results["tracks"]:
        lines.append(f"| `{track['id']}` | {track['assigned_scenarios']} | {track['runtime_artifacts_recorded']} |")
    lines.extend(
        [
            "",
            "## Skill Scores",
            "",
            "| Skill | Category | Static checks | Static score | Runtime artifacts | Fix points | Failed static checks |",
            "|---|---|---:|---:|---:|---:|---|",
        ]
    )
    for item in results["skills"]:
        failed = ", ".join(item["failed_checks"]) if item["failed_checks"] else "none"
        checks = f"{item['static_checks_passed']}/{item['static_checks_total']}"
        lines.append(
            f"| `{item['skill_id']}` | {_cell(item['category'])} | {checks} | {item['static_score_percent']} | "
            f"{item['runtime_artifacts_recorded']} | {item['quality_fix_point_count']} | {_cell(failed)} |"
        )
    lines.extend(
        [
            "",
            "## Runtime Artifacts",
            "",
            "| Artifact | Skill | Scenario | Verdict | Score | Runner |",
            "|---|---|---|---|---:|---|",
        ]
    )
    if results["runtime_artifacts"]:
        for artifact in results["runtime_artifacts"]:
            runner = artifact.get("runner", {})
            verdict = artifact.get("benchmark_verdict") or "recorded"
            score = artifact.get("score_percent")
            score_text = "n/a" if score is None else str(score)
            lines.append(
                f"| `{artifact['artifact_path']}` | `{artifact['skill_id']}` | `{artifact['scenario_id']}` | "
                f"`{verdict}` | {score_text} | {_cell(runner.get('tool', 'unknown'))} |"
            )
    else:
        lines.append("| none | none | none | none | n/a | none |")
    lines.extend(
        [
            "",
            "## Source-Proof Provenance Artifacts",
            "",
            "| Artifact | Skill | Scenario | Runner |",
            "|---|---|---|---|",
        ]
    )
    if results["provenance_artifacts"]:
        for artifact in results["provenance_artifacts"]:
            runner = artifact.get("runner", {})
            lines.append(
                f"| `{artifact['artifact_path']}` | `{artifact['skill_id']}` | `{artifact['scenario_id']}` | "
                f"{_cell(runner.get('tool', 'unknown'))} |"
            )
    else:
        lines.append("| none | none | none | none |")
    return "\n".join(lines) + "\n"


def render_quality_findings(results: dict[str, Any]) -> str:
    lines = [
        "# Skill Quality Findings",
        "",
        "This table is compiled from measured static checks and observed source structure. It lists every skill, its static benchmark score, failed checks, and concrete fix points from the source audit.",
        "",
        "| Skill | Category | Static score | Failed checks | Fix points |",
        "|---|---|---:|---|---|",
    ]
    for item in results["skills"]:
        failed = ", ".join(item["failed_checks"]) if item["failed_checks"] else "none"
        fix_points = "; ".join(item["quality_fix_points"]) if item["quality_fix_points"] else "none"
        lines.append(
            f"| `{item['skill_id']}` | {_cell(item['category'])} | {item['static_score_percent']} | "
            f"{_cell(failed)} | {_cell(fix_points)} |"
        )
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# core run
# --------------------------------------------------------------------------- #


def run(*, verbose: bool = False) -> dict[str, Any]:
    catalog = load_json(ROOT / "data" / "skills_catalog.json")
    scenarios = {item["id"]: item for item in load_json(ROOT / "data" / "benchmark_scenarios.json")}
    assignments = load_json(ROOT / "data" / "benchmark_assignments.json")
    tracks = load_json(ROOT / "data" / "benchmark_tracks.json")
    if verbose:
        log_progress(f"[static-benchmarks] catalog size: {len(catalog)}")
    runtime_artifacts = _iter_artifacts("independent_benchmark")
    provenance_artifacts = _iter_artifacts("provenance_check")
    if verbose:
        log_progress(
            f"[static-benchmarks] runtime artifacts: {len(runtime_artifacts)}, "
            f"provenance artifacts: {len(provenance_artifacts)}"
        )
    runtime_passed = sum(1 for a in runtime_artifacts if a.get("benchmark_verdict") == "passed")
    runtime_failed = sum(1 for a in runtime_artifacts if a.get("benchmark_verdict") == "failed")

    artifacts_by_skill: dict[str, list[dict[str, Any]]] = {}
    artifacts_by_track: dict[str, int] = {}
    for artifact in runtime_artifacts:
        artifacts_by_skill.setdefault(artifact["skill_id"], []).append(artifact)
        track_id = scenarios[artifact["scenario_id"]]["dataset_track_id"]
        artifacts_by_track[track_id] = artifacts_by_track.get(track_id, 0) + 1

    iterator = progress_iter(catalog, label="static-checks") if verbose else catalog
    skill_results = [_check_entry(entry, scenarios, artifacts_by_skill) for entry in iterator]

    total_checks = sum(item["static_checks_total"] for item in skill_results)
    passed_checks = sum(item["static_checks_passed"] for item in skill_results)

    assigned_by_track = {track["id"]: 0 for track in tracks}
    for scenario_ids in [item["scenario_ids"] for item in assignments]:
        for scenario_id in scenario_ids:
            track_id = scenarios[scenario_id]["dataset_track_id"]
            assigned_by_track[track_id] += 1

    track_results = [
        {
            "id": track["id"],
            "title": track["title"],
            "assigned_scenarios": assigned_by_track[track["id"]],
            "runtime_artifacts_recorded": artifacts_by_track.get(track["id"], 0),
        }
        for track in tracks
    ]
    return {
        "benchmark_result_version": 1,
        "generated_on": build_catalog.BUILD_DATE,
        "summary": {
            "skill_count": len(skill_results),
            "static_checks_passed": passed_checks,
            "static_checks_total": total_checks,
            "average_static_score_percent": round(
                sum(item["static_score_percent"] for item in skill_results) / len(skill_results), 2
            ),
            "runtime_artifacts_recorded": len(runtime_artifacts),
            "runtime_artifacts_passed": runtime_passed,
            "runtime_artifacts_failed": runtime_failed,
            "provenance_artifacts_recorded": len(provenance_artifacts),
            "quality_fix_points": sum(item["quality_fix_point_count"] for item in skill_results),
        },
        "tracks": track_results,
        "runtime_artifacts": runtime_artifacts,
        "provenance_artifacts": provenance_artifacts,
        "skills": skill_results,
    }


# --------------------------------------------------------------------------- #
# outputs
# --------------------------------------------------------------------------- #


def _write_all(results: dict[str, Any]) -> None:
    write_json_canonical(DATA_PATH, results)
    write_text(RESULTS_DOC, render_results(results))
    write_text(QUALITY_DOC, render_quality_findings(results))


def _check_all(results: dict[str, Any]) -> int:
    committed = load_json(DATA_PATH)
    rendered_results = render_results(results)
    rendered_quality = render_quality_findings(results)
    committed_results_doc = RESULTS_DOC.read_text(encoding="utf-8")
    committed_quality_doc = QUALITY_DOC.read_text(encoding="utf-8")

    reports = [
        describe_data_drift("data/static_benchmark_results.json", committed, results),
        describe_text_drift("docs/benchmark-results.md", committed_results_doc, rendered_results),
        describe_text_drift("docs/skill-quality-findings.md", committed_quality_doc, rendered_quality),
    ]
    stale = [r for r in reports if r.is_stale]
    if not stale:
        print("Static benchmark outputs are current.")
        return 0
    for report in stale:
        sys.stderr.write(report.render() + "\n")
    sys.stderr.write(
        "Stale static benchmark outputs detected. Inputs drifted from the committed snapshot;"
        " run `tools/run_static_benchmarks.py` after confirming the drift is legitimate.\n"
    )
    return 1


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run offline static benchmarks and write real benchmark result tables.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write files; emit a compact drift report and exit 1 if outputs are stale.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Log per-phase progress on stderr. Stdout remains machine-consumable.",
    )
    args = parser.parse_args(argv)
    results = run(verbose=args.verbose)
    if args.check:
        return _check_all(results)
    _write_all(results)
    print(
        f"Static benchmarks: {results['summary']['static_checks_passed']}/"
        f"{results['summary']['static_checks_total']} checks across {results['summary']['skill_count']} skills."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

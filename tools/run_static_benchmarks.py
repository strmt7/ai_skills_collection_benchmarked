#!/usr/bin/env python3
"""Run offline benchmark checks that can be proven from this repository."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_catalog
import check_benchmark_artifact


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def artifact_records(artifact_kind: str | None = None) -> list[dict[str, Any]]:
    root = ROOT / "artifacts" / "benchmark-runs"
    if not root.exists():
        return []
    records: list[dict[str, Any]] = []
    for artifact_path in sorted(root.rglob("artifact.json")):
        validation = check_benchmark_artifact.validate_artifact(artifact_path)
        try:
            artifact = load_json_path(artifact_path)
        except Exception:
            artifact = {}
        if validation["verdict"] != "artifact_complete":
            continue
        if artifact_kind and artifact.get("artifact_kind") != artifact_kind:
            continue
        records.append({
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
        })
    return records


def load_json_path(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check_entry(entry: dict[str, Any], scenarios: dict[str, dict[str, Any]], artifacts_by_skill: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    mirror = ROOT / entry["mirrored_path"]
    skill_file = mirror / "SKILL.md"
    agent_ready = ROOT / entry["agent_ready_path"]
    skill_doc = ROOT / "docs" / "catalog" / "skills" / "by-category" / build_catalog.slug(entry["category"]) / build_catalog.slug(entry["subcategory"]) / f"{entry['install_name']}.md"
    agent_ready_text = agent_ready.read_text(encoding="utf-8") if agent_ready.is_file() else ""
    checks = {
        "mirror_directory_exists": mirror.is_dir(),
        "root_skill_file_exists": skill_file.is_file(),
        "no_nested_skill_files": len(list(mirror.rglob("SKILL.md"))) == 1 if mirror.exists() else False,
        "skill_file_hash_matches": skill_file.is_file() and build_catalog.sha256_file(skill_file) == entry["skill_file_sha256"],
        "skill_directory_hash_matches": mirror.is_dir() and build_catalog.sha256_tree(mirror) == entry["skill_dir_sha256"],
        "agent_ready_skill_exists": agent_ready.is_file(),
        "agent_ready_frontmatter_present": agent_ready_text.startswith("---\n"),
        "agent_ready_markdown_concise": len(agent_ready_text.splitlines()) <= 120,
        "scenario_count_ok": len(entry["benchmark_scenarios"]) >= build_catalog.MIN_SCENARIOS + 1,
        "source_proof_first": bool(entry["benchmark_scenarios"]) and entry["benchmark_scenarios"][0] == f"skill-proof-{entry['id']}",
        "all_assigned_scenarios_exist": all(scenario_id in scenarios for scenario_id in entry["benchmark_scenarios"]),
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


def table_cell(value: Any) -> str:
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
    lines.extend([
        "",
        "## Skill Scores",
        "",
        "| Skill | Category | Static checks | Static score | Runtime artifacts | Fix points | Failed static checks |",
        "|---|---|---:|---:|---:|---:|---|",
    ])
    for item in results["skills"]:
        failed = ", ".join(item["failed_checks"]) if item["failed_checks"] else "none"
        checks = f"{item['static_checks_passed']}/{item['static_checks_total']}"
        lines.append(f"| `{item['skill_id']}` | {table_cell(item['category'])} | {checks} | {item['static_score_percent']} | {item['runtime_artifacts_recorded']} | {item['quality_fix_point_count']} | {table_cell(failed)} |")
    lines.extend([
        "",
        "## Runtime Artifacts",
        "",
        "| Artifact | Skill | Scenario | Verdict | Score | Runner |",
        "|---|---|---|---|---:|---|",
    ])
    if results["runtime_artifacts"]:
        for artifact in results["runtime_artifacts"]:
            runner = artifact.get("runner", {})
            verdict = artifact.get("benchmark_verdict") or "recorded"
            score = artifact.get("score_percent")
            score_text = "n/a" if score is None else str(score)
            lines.append(
                f"| `{artifact['artifact_path']}` | `{artifact['skill_id']}` | `{artifact['scenario_id']}` | "
                f"`{verdict}` | {score_text} | {table_cell(runner.get('tool', 'unknown'))} |"
            )
    else:
        lines.append("| none | none | none | none | n/a | none |")
    lines.extend([
        "",
        "## Source-Proof Provenance Artifacts",
        "",
        "| Artifact | Skill | Scenario | Runner |",
        "|---|---|---|---|",
    ])
    if results["provenance_artifacts"]:
        for artifact in results["provenance_artifacts"]:
            runner = artifact.get("runner", {})
            lines.append(f"| `{artifact['artifact_path']}` | `{artifact['skill_id']}` | `{artifact['scenario_id']}` | {table_cell(runner.get('tool', 'unknown'))} |")
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
        lines.append(f"| `{item['skill_id']}` | {table_cell(item['category'])} | {item['static_score_percent']} | {table_cell(failed)} | {table_cell(fix_points)} |")
    return "\n".join(lines) + "\n"


def run() -> dict[str, Any]:
    catalog = load("data/skills_catalog.json")
    scenarios = {item["id"]: item for item in load("data/benchmark_scenarios.json")}
    assignments = load("data/benchmark_assignments.json")
    tracks = load("data/benchmark_tracks.json")
    runtime_artifacts = artifact_records("independent_benchmark")
    provenance_artifacts = artifact_records("provenance_check")
    runtime_passed = sum(1 for artifact in runtime_artifacts if artifact.get("benchmark_verdict") == "passed")
    runtime_failed = sum(1 for artifact in runtime_artifacts if artifact.get("benchmark_verdict") == "failed")
    artifacts_by_skill: dict[str, list[dict[str, Any]]] = {}
    artifacts_by_track: dict[str, int] = {}
    for artifact in runtime_artifacts:
        artifacts_by_skill.setdefault(artifact["skill_id"], []).append(artifact)
        track_id = scenarios[artifact["scenario_id"]]["dataset_track_id"]
        artifacts_by_track[track_id] = artifacts_by_track.get(track_id, 0) + 1
    skill_results = [check_entry(entry, scenarios, artifacts_by_skill) for entry in catalog]
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
            "average_static_score_percent": round(sum(item["static_score_percent"] for item in skill_results) / len(skill_results), 2),
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run offline static benchmarks and write real benchmark result tables.")
    parser.add_argument("--check", action="store_true", help="Do not write files; fail if generated outputs would differ.")
    args = parser.parse_args()
    results = run()
    data_path = ROOT / "data" / "static_benchmark_results.json"
    doc_path = ROOT / "docs" / "benchmark-results.md"
    quality_doc_path = ROOT / "docs" / "skill-quality-findings.md"
    rendered = render_results(results)
    rendered_quality = render_quality_findings(results)
    if args.check:
        if load("data/static_benchmark_results.json") != results:
            raise SystemExit("data/static_benchmark_results.json is stale")
        if doc_path.read_text(encoding="utf-8") != rendered:
            raise SystemExit("docs/benchmark-results.md is stale")
        if quality_doc_path.read_text(encoding="utf-8") != rendered_quality:
            raise SystemExit("docs/skill-quality-findings.md is stale")
    else:
        write_json(data_path, results)
        doc_path.write_text(rendered, encoding="utf-8")
        quality_doc_path.write_text(rendered_quality, encoding="utf-8")
    print(
        f"Static benchmarks: {results['summary']['static_checks_passed']}/"
        f"{results['summary']['static_checks_total']} checks across {results['summary']['skill_count']} skills."
    )


if __name__ == "__main__":
    main()

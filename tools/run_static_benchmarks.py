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


def load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_entry(entry: dict[str, Any], scenarios: dict[str, dict[str, Any]]) -> dict[str, Any]:
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
        "runtime_artifacts_recorded": 0,
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
        "This page reports measured results only. Offline static checks were run against the mirrored files in this repository. Runtime artifact counts are shown separately and stay at zero unless a validated artifact is committed.",
        "",
        "## Summary",
        "",
        f"- Skills checked: `{results['summary']['skill_count']}`",
        f"- Static checks passed: `{results['summary']['static_checks_passed']}` / `{results['summary']['static_checks_total']}`",
        f"- Average static score: `{results['summary']['average_static_score_percent']}`",
        f"- Runtime scenario artifacts recorded: `{results['summary']['runtime_artifacts_recorded']}`",
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
    skill_results = [check_entry(entry, scenarios) for entry in catalog]
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
            "runtime_artifacts_recorded": 0,
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
            "runtime_artifacts_recorded": 0,
            "quality_fix_points": sum(item["quality_fix_point_count"] for item in skill_results),
        },
        "tracks": track_results,
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

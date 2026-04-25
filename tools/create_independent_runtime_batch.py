#!/usr/bin/env python3
"""Create independent runtime-readiness benchmark artifacts.

This runner deliberately keeps task definitions and expected checks outside the
skill text being evaluated. It records whether a mirrored skill package is
loadable and ready for a fresh single-session agent to attempt a real repository
workflow. It does not edit mirrored skills and it does not turn failures into
passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import audit_skill_quality
import build_catalog
import check_benchmark_artifact
from _lib_b import determinism as _det

BATCH_NAME = "2026-04-17-independent-runtime-readiness-batch-01"
RUNNER_ID = "tools/create_independent_runtime_batch.py"
RISK_LEVEL = "likely_non_working"
EXCLUDED_CATEGORIES = {"Game, mobile & visual QA"}

REQUIRED_CHECKS = [
    "real_dataset_snapshot_resolved",
    "assigned_non_provenance_scenario",
    "independent_task_brief_present",
    "mirror_skill_file_exists",
    "agent_ready_entrypoint_exists",
    "source_hash_matches_catalog",
    "required_frontmatter_present",
    "local_markdown_links_resolve",
    "single_session_entrypoint_clean",
    "generic_workflow_schema_recorded",
]

SUBAGENT_PATTERNS = [
    re.compile(r"\bsubagents?\b", re.IGNORECASE),
    re.compile(r"\bparallel agents?\b", re.IGNORECASE),
    re.compile(r"\bmulti-agent\b", re.IGNORECASE),
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_text(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def run_command(command: list[str], cwd: Path = ROOT) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def github_repo_from_url(url: str) -> tuple[str, str, str | None] | None:
    match = re.match(r"https://github\.com/([^/]+)/([^/#?]+)(?:/(?:tree|blob)/[^/]+/(.+))?/?$", url)
    if not match:
        return None
    owner, repo, subpath = match.groups()
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo, subpath


def fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "ai-skills-runtime-benchmark/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def resolve_dataset_snapshot(track: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    commands: list[dict[str, Any]] = []
    url = track["url"]
    parsed = github_repo_from_url(url)
    if not parsed:
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ai-skills-runtime-benchmark/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return {
                    "kind": "real-url",
                    "url": url,
                    "status": response.status,
                    "resolved": 200 <= response.status < 400,
                }, commands
        except urllib.error.URLError as exc:
            return {"kind": "real-url", "url": url, "resolved": False, "error": str(exc)}, commands

    owner, repo, subpath = parsed
    repo_url = f"https://github.com/{owner}/{repo}"
    ls_remote = run_command(["git", "ls-remote", repo_url, "HEAD"])
    commands.append(ls_remote)
    head_sha = ""
    if ls_remote["returncode"] == 0 and ls_remote["stdout"]:
        head_sha = ls_remote["stdout"].split()[0]
    snapshot: dict[str, Any] = {
        "kind": "real-github-repository-tree",
        "url": url,
        "repo_url": repo_url,
        "head_sha": head_sha,
        "track_subpath": subpath,
        "resolved": bool(head_sha),
        "tree_api_url": f"https://api.github.com/repos/{owner}/{repo}/git/trees/{head_sha}?recursive=1"
        if head_sha
        else "",
        "sampled_paths": [],
        "tree_path_count": 0,
        "tree_truncated": None,
        "track_subpath_present": None,
    }
    if not head_sha:
        return snapshot, commands
    try:
        tree = fetch_json(snapshot["tree_api_url"])
    except Exception as exc:
        snapshot["resolved"] = False
        snapshot["tree_error"] = str(exc)
        return snapshot, commands
    paths = sorted(item["path"] for item in tree.get("tree", []) if item.get("path"))
    snapshot["tree_path_count"] = len(paths)
    snapshot["tree_truncated"] = bool(tree.get("truncated"))
    if subpath:
        prefix = subpath.strip("/") + "/"
        matching = [path for path in paths if path == subpath or path.startswith(prefix)]
        snapshot["track_subpath_present"] = bool(matching)
        snapshot["sampled_paths"] = matching[:20]
        snapshot["resolved"] = snapshot["resolved"] and bool(matching)
    else:
        snapshot["sampled_paths"] = paths[:20]
        snapshot["track_subpath_present"] = True
    return snapshot, commands


def first_non_provenance_scenario(entry: dict[str, Any], scenarios: dict[str, dict[str, Any]]) -> dict[str, Any]:
    for scenario_id in entry["benchmark_scenarios"]:
        scenario = scenarios[scenario_id]
        if scenario.get("dataset_track_id") != "source-skill-repository":
            return scenario
    raise ValueError(f"no non-provenance scenario assigned to {entry['id']}")


def batch_paths(batch_name: str, batch_slug: str) -> dict[str, Path]:
    return {
        "tasks": ROOT / "benchmarks" / "independent-runtime-readiness" / batch_slug / "tasks.json",
        "output": ROOT / "artifacts" / "benchmark-runs" / batch_name,
        "report": ROOT / "docs" / f"runtime-benchmark-{batch_slug}.md",
    }


def existing_independent_skill_ids(current_batch_name: str) -> set[str]:
    skill_ids: set[str] = set()
    for artifact_path in (ROOT / "artifacts" / "benchmark-runs").rglob("artifact.json"):
        if current_batch_name in artifact_path.parts:
            continue
        try:
            artifact = load_json(artifact_path)
        except Exception:
            continue
        if artifact.get("artifact_kind") == "independent_benchmark" and artifact.get("skill_id"):
            skill_ids.add(str(artifact["skill_id"]))
    return skill_ids


def select_candidates(
    limit: int,
    *,
    risk_level: str,
    include_visual: bool = False,
    category_spread: bool = False,
    exclude_skill_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    audit = load_json(ROOT / "data" / "skill_risk_audit.json")
    excluded = exclude_skill_ids or set()
    pool: list[dict[str, Any]] = []
    for item in audit["skills"]:
        if item["risk_level"] != risk_level:
            continue
        if not include_visual and item["category"] in EXCLUDED_CATEGORIES:
            continue
        if item["skill_id"] in excluded:
            continue
        pool.append(item)

    if not category_spread:
        candidates = pool[:limit]
    else:
        candidates = []
        seen_categories: set[str] = set()
        for item in pool:
            if item["category"] in seen_categories:
                continue
            candidates.append(item)
            seen_categories.add(item["category"])
            if len(candidates) == limit:
                break
        if len(candidates) < limit:
            selected_ids = {item["skill_id"] for item in candidates}
            for item in pool:
                if item["skill_id"] in selected_ids:
                    continue
                candidates.append(item)
                if len(candidates) == limit:
                    break

    if len(candidates) < limit:
        raise SystemExit(f"only found {len(candidates)} {risk_level} candidates for this batch")
    return candidates


def build_task(entry: dict[str, Any], scenario: dict[str, Any], track: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": f"runtime-readiness-{entry['id']}-{scenario['id']}",
        "task_version": "1.0",
        "skill_id": entry["id"],
        "scenario_id": scenario["id"],
        "dataset_track_id": track["id"],
        "dataset_url": track["url"],
        "objective": (
            "Independently determine whether the mirrored skill package is loadable "
            "and ready for a fresh single-session agent to attempt the assigned real "
            "repository workflow."
        ),
        "workflow": scenario["workflow"],
        "required_checks": REQUIRED_CHECKS,
        "expected_result": {
            "all_required_checks_pass": True,
            "score_percent": 100.0,
            "blocking_failures": [],
        },
        "independence_note": (
            "This task brief, evaluator, required checks, and expected result are defined "
            "outside the evaluated skill text."
        ),
    }


def check_single_session_entrypoint(agent_ready: Path) -> bool:
    if not agent_ready.is_file():
        return False
    text = agent_ready.read_text(encoding="utf-8", errors="replace")
    return not any(pattern.search(text) for pattern in SUBAGENT_PATTERNS)


def evaluate_skill(
    entry: dict[str, Any],
    manifest_entry: dict[str, Any],
    scenario: dict[str, Any],
    task: dict[str, Any],
    dataset_snapshot: dict[str, Any],
    tasks_path: Path,
    risk_level: str,
) -> dict[str, Any]:
    mirror = ROOT / entry["mirrored_path"]
    skill_file = mirror / "SKILL.md"
    agent_ready = ROOT / entry["agent_ready_path"]
    missing_links = []
    if skill_file.is_file():
        missing_links = audit_skill_quality.missing_markdown_links(
            mirror,
            skill_file.read_text(encoding="utf-8", errors="replace"),
        )
    checks = [
        {
            "name": "real_dataset_snapshot_resolved",
            "passed": dataset_snapshot.get("resolved") is True,
            "evidence": dataset_snapshot.get("repo_url") or dataset_snapshot.get("url"),
            "measured": {
                "head_sha": dataset_snapshot.get("head_sha"),
                "tree_path_count": dataset_snapshot.get("tree_path_count"),
                "track_subpath_present": dataset_snapshot.get("track_subpath_present"),
            },
        },
        {
            "name": "assigned_non_provenance_scenario",
            "passed": scenario.get("dataset_track_id") != "source-skill-repository"
            and scenario["id"] in entry["benchmark_scenarios"],
            "evidence": scenario["id"],
        },
        {
            "name": "independent_task_brief_present",
            "passed": task["expected_result"]["all_required_checks_pass"] is True
            and task["required_checks"] == REQUIRED_CHECKS,
            "evidence": tasks_path.relative_to(ROOT).as_posix(),
        },
        {
            "name": "mirror_skill_file_exists",
            "passed": skill_file.is_file(),
            "evidence": entry["mirrored_path"] + "/SKILL.md",
        },
        {
            "name": "agent_ready_entrypoint_exists",
            "passed": agent_ready.is_file(),
            "evidence": entry["agent_ready_path"],
        },
        {
            "name": "source_hash_matches_catalog",
            "passed": skill_file.is_file() and build_catalog.sha256_file(skill_file) == entry["skill_file_sha256"],
            "evidence": entry["skill_file_sha256"],
        },
        {
            "name": "required_frontmatter_present",
            "passed": entry.get("has_required_frontmatter") is True,
            "evidence": "catalog.has_required_frontmatter",
        },
        {
            "name": "local_markdown_links_resolve",
            "passed": not missing_links,
            "evidence": missing_links,
        },
        {
            "name": "single_session_entrypoint_clean",
            "passed": check_single_session_entrypoint(agent_ready),
            "evidence": entry["agent_ready_path"],
        },
        {
            "name": "generic_workflow_schema_recorded",
            "passed": scenario.get("evaluator_path") == "evaluators/generic_workflow_result.schema.json",
            "evidence": scenario.get("evaluator_path"),
        },
    ]
    passed = sum(1 for check in checks if check["passed"])
    total = len(checks)
    blocking_failures = [check["name"] for check in checks if not check["passed"]]
    return {
        "inputs": {
            "skill_id": entry["id"],
            "skill_name": entry["name"],
            "risk_level": risk_level,
            "scenario_id": scenario["id"],
            "dataset_track_id": scenario["dataset_track_id"],
            "task_id": task["task_id"],
            "task_brief_path": tasks_path.relative_to(ROOT).as_posix(),
            "mirrored_path": entry["mirrored_path"],
            "agent_ready_path": entry["agent_ready_path"],
            "source_repo": entry["source_repo"],
            "source_path": entry["source_path"],
            "dataset_snapshot": dataset_snapshot,
        },
        "steps": [
            f"Selected a {risk_level} skill from data/skill_risk_audit.json.",
            "Selected the first assigned non-provenance scenario for the skill.",
            "Resolved the real repository workflow snapshot from the benchmark track URL.",
            "Evaluated the mirrored package against independently defined loadability checks.",
            "Recorded pass/fail metrics without modifying the mirrored skill.",
        ],
        "outputs": {
            "benchmark_verdict": "passed" if not blocking_failures else "failed",
            "score_percent": round((passed / total) * 100, 2),
            "checks": checks,
            "blocking_failures": blocking_failures,
            "risk_findings": manifest_entry.get("risk_findings", []),
        },
        "metrics": {
            "checks_passed": passed,
            "checks_total": total,
            "score_percent": round((passed / total) * 100, 2),
            "benchmark_verdict": "passed" if not blocking_failures else "failed",
            "blocking_failure_count": len(blocking_failures),
            "missing_local_link_count": len(missing_links),
            "dataset_tree_path_count": dataset_snapshot.get("tree_path_count", 0),
        },
        "citations_or_paths": [
            tasks_path.relative_to(ROOT).as_posix(),
            entry["mirrored_path"] + "/SKILL.md",
            entry["agent_ready_path"],
            "data/benchmark_scenarios.json",
            "data/benchmark_tracks.json",
            "data/skill_risk_audit.json",
            dataset_snapshot.get("repo_url") or dataset_snapshot.get("url"),
        ],
    }


def render_transcript(
    entry: dict[str, Any],
    scenario: dict[str, Any],
    task: dict[str, Any],
    dataset_snapshot: dict[str, Any],
    commands: list[dict[str, Any]],
    result: dict[str, Any],
    batch_name: str,
) -> str:
    lines = [
        f"Batch: {batch_name}",
        f"Runner: {RUNNER_ID}",
        f"Skill: {entry['id']}",
        f"Scenario: {scenario['id']}",
        f"Task: {task['task_id']}",
        "",
        "Independence:",
        "- Task brief, required checks, and expected result came from the batch runner and task fixture.",
        "- Skill text was read only as the object under test for loadability checks.",
        "- Mirrored skill files were not edited by this runner.",
        "",
        "Dataset snapshot:",
        json.dumps(dataset_snapshot, indent=2, sort_keys=True),
        "",
        "Commands:",
    ]
    for command in commands:
        lines.append(json.dumps(command, indent=2, sort_keys=True))
    lines.extend(
        [
            "",
            "Result metrics:",
            json.dumps(result["metrics"], indent=2, sort_keys=True),
            "",
            "Blocking failures:",
            json.dumps(result["outputs"]["blocking_failures"], indent=2, sort_keys=True),
        ]
    )
    return "\n".join(lines) + "\n"


def artifact_for(
    entry: dict[str, Any],
    scenario: dict[str, Any],
    track: dict[str, Any],
    task: dict[str, Any],
    dataset_snapshot: dict[str, Any],
    result: dict[str, Any],
    timestamp: str,
    catalog_commit: str,
    artifact_dir: Path,
    batch_name: str,
    tasks_path: Path,
) -> dict[str, Any]:
    result_path = artifact_dir / "result.json"
    return {
        "artifact_version": "1.0",
        "artifact_kind": "independent_benchmark",
        "skill_id": entry["id"],
        "scenario_id": scenario["id"],
        "catalog_commit": catalog_commit,
        "source_commit": entry["commit_sha"],
        "source_repo": entry["source_repo"],
        "source_path": entry["source_path"],
        "runner": {
            "timestamp_utc": timestamp,
            "tool": RUNNER_ID,
            "model_or_runtime": "local-deterministic-runtime-readiness-runner",
            "batch_name": batch_name,
        },
        "scenario_requirements": {
            "visual_or_browser": False,
            "context_memory": False,
            "token_efficiency_claim": False,
            "real_repository_workflow": True,
            "dataset_track_id": track["id"],
        },
        "input_snapshot": {
            "kind": dataset_snapshot["kind"],
            "identifier": dataset_snapshot.get("repo_url") or dataset_snapshot.get("url"),
            "is_real": True,
            "dataset_track_id": track["id"],
            "dataset_url": track["url"],
            "resolved_commit": dataset_snapshot.get("head_sha"),
            "tree_path_count": dataset_snapshot.get("tree_path_count"),
            "track_subpath": dataset_snapshot.get("track_subpath"),
            "track_subpath_present": dataset_snapshot.get("track_subpath_present"),
            "mirrored_path": entry["mirrored_path"],
        },
        "execution": {
            "fresh_session": True,
            "commands_or_transcript_path": "transcript.txt",
        },
        "outputs": {
            "path": "result.json",
            "schema": "evaluators/generic_workflow_result.schema.json",
            "result_sha256": sha256_file(result_path),
        },
        "metrics": result["metrics"],
        "independence": {
            "task_defined_outside_skill": True,
            "evaluator_defined_outside_skill": True,
            "expected_result_defined_outside_skill": True,
            "uses_exact_skill_content_for_expected_result": False,
            "skill_content_usage": (
                "skill text was read only as the object under test for package loadability, "
                "frontmatter, hash, and local-link checks; task and expected results came "
                f"from {tasks_path.relative_to(ROOT).as_posix()} and this runner"
            ),
        },
        "evidence": {
            "artifact_paths": [
                "result.json",
                "transcript.txt",
                "dataset_snapshot.json",
                tasks_path.relative_to(ROOT).as_posix(),
            ],
            "citations_or_paths": result["citations_or_paths"],
        },
        "objective_checks": REQUIRED_CHECKS,
    }


def render_report(manifest: dict[str, Any], batch_slug: str) -> str:
    lines = [
        f"# Runtime Benchmark {batch_slug.replace('-', ' ').title()}",
        "",
        "This batch records independent runtime-readiness results for selected high-risk skills. It checks whether each mirrored skill package is loadable and ready for an assigned real repository workflow. It does not claim full task-solution quality.",
        "",
        "## Summary",
        "",
        f"- Batch: `{manifest['batch_name']}`",
        f"- Catalog commit: `{manifest['catalog_commit']}`",
        f"- Skills evaluated: `{manifest['summary']['artifact_count']}`",
        f"- Passed: `{manifest['summary']['passed']}`",
        f"- Failed: `{manifest['summary']['failed']}`",
        f"- Average score: `{manifest['summary']['average_score_percent']}`",
        "",
        "## Results",
        "",
        "| Skill | Scenario | Track | Verdict | Score | Failed checks | Artifact |",
        "|---|---|---|---|---:|---|---|",
    ]
    for item in manifest["artifacts"]:
        failed = ", ".join(item["blocking_failures"]) if item["blocking_failures"] else "none"
        lines.append(
            f"| `{item['skill_id']}` | `{item['scenario_id']}` | `{item['dataset_track_id']}` | "
            f"`{item['benchmark_verdict']}` | {item['score_percent']} | "
            f"{failed} | `{item['artifact_path']}` |"
        )
    return "\n".join(lines) + "\n"


def run(
    limit: int,
    *,
    batch_name: str = BATCH_NAME,
    batch_slug: str = "batch-01",
    risk_level: str = RISK_LEVEL,
    include_visual: bool = False,
    category_spread: bool = False,
    avoid_existing_independent: bool = False,
) -> dict[str, Any]:
    catalog = {entry["id"]: entry for entry in load_json(ROOT / "data" / "skills_catalog.json")}
    manifest = {entry["id"]: entry for entry in load_json(ROOT / "included" / "skills" / "manifest.json")}
    scenarios = {scenario["id"]: scenario for scenario in load_json(ROOT / "data" / "benchmark_scenarios.json")}
    tracks = {track["id"]: track for track in load_json(ROOT / "data" / "benchmark_tracks.json")}
    paths = batch_paths(batch_name, batch_slug)
    excluded = existing_independent_skill_ids(batch_name) if avoid_existing_independent else set()
    candidates = select_candidates(
        limit,
        risk_level=risk_level,
        include_visual=include_visual,
        category_spread=category_spread,
        exclude_skill_ids=excluded,
    )
    existing_manifest = paths["output"] / "manifest.json"
    catalog_commit = _det.resolve_catalog_commit(
        root=ROOT,
        existing_manifest_value=_det.existing_field(existing_manifest, "catalog_commit"),
    )
    # Determinism: prefer SOURCE_DATE_EPOCH, then prior manifest, then the
    # catalog's own commit time. Avoids wall-clock drift across reruns.
    timestamp = _det.resolve_timestamp(
        existing_manifest_value=_det.existing_field(existing_manifest, "generated_at_utc"),
        fallback_epoch=_det.git_latest_commit_epoch_for(ROOT, [ROOT / "data" / "skills_catalog.json"]),
    )

    selected: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]] = []
    tasks: list[dict[str, Any]] = []
    for candidate in candidates:
        entry = catalog[candidate["skill_id"]]
        scenario = first_non_provenance_scenario(entry, scenarios)
        track = tracks[scenario["dataset_track_id"]]
        task = build_task(entry, scenario, track)
        selected.append((entry, scenario, track, task))
        tasks.append(task)
    write_json(
        paths["tasks"],
        {
            "batch_name": batch_name,
            "task_count": len(tasks),
            "selection_policy": (
                ("category-spread " if category_spread else "first ")
                + f"{limit} {risk_level} skills with assigned non-provenance repository workflows"
                + (
                    " including visual categories"
                    if include_visual
                    else " excluding visual/browser categories for this readiness batch"
                )
                + (
                    " and excluding skills already covered by earlier independent runtime artifacts"
                    if avoid_existing_independent
                    else ""
                )
            ),
            "required_checks": REQUIRED_CHECKS,
            "tasks": tasks,
        },
    )

    artifact_summaries: list[dict[str, Any]] = []
    output_root = paths["output"]
    output_root.mkdir(parents=True, exist_ok=True)
    for entry, scenario, track, task in selected:
        dataset_snapshot, commands = resolve_dataset_snapshot(track)
        artifact_dir = output_root / build_catalog.slug(entry["id"]) / build_catalog.slug(scenario["id"])
        artifact_dir.mkdir(parents=True, exist_ok=True)
        write_json(artifact_dir / "dataset_snapshot.json", dataset_snapshot)
        result = evaluate_skill(
            entry, manifest[entry["id"]], scenario, task, dataset_snapshot, paths["tasks"], risk_level
        )
        write_json(artifact_dir / "result.json", result)
        (artifact_dir / "transcript.txt").write_text(
            render_transcript(entry, scenario, task, dataset_snapshot, commands, result, batch_name),
            encoding="utf-8",
        )
        artifact = artifact_for(
            entry,
            scenario,
            track,
            task,
            dataset_snapshot,
            result,
            timestamp,
            catalog_commit,
            artifact_dir,
            batch_name,
            paths["tasks"],
        )
        write_json(artifact_dir / "artifact.json", artifact)
        validation = check_benchmark_artifact.validate_artifact(artifact_dir / "artifact.json")
        if validation["verdict"] != "artifact_complete":
            raise SystemExit(f"incomplete artifact for {entry['id']}: {validation}")
        artifact_summaries.append(
            {
                "skill_id": entry["id"],
                "scenario_id": scenario["id"],
                "dataset_track_id": track["id"],
                "artifact_path": (artifact_dir / "artifact.json").relative_to(ROOT).as_posix(),
                "result_path": (artifact_dir / "result.json").relative_to(ROOT).as_posix(),
                "benchmark_verdict": result["metrics"]["benchmark_verdict"],
                "score_percent": result["metrics"]["score_percent"],
                "blocking_failures": result["outputs"]["blocking_failures"],
            }
        )

    passed = sum(1 for item in artifact_summaries if item["benchmark_verdict"] == "passed")
    failed = sum(1 for item in artifact_summaries if item["benchmark_verdict"] == "failed")
    average_score = round(sum(item["score_percent"] for item in artifact_summaries) / len(artifact_summaries), 2)
    manifest_data = {
        "batch_name": batch_name,
        "artifact_kind": "independent_benchmark",
        "runner": RUNNER_ID,
        "generated_at_utc": timestamp,
        "catalog_commit": catalog_commit,
        "task_definitions_path": paths["tasks"].relative_to(ROOT).as_posix(),
        "summary": {
            "artifact_count": len(artifact_summaries),
            "passed": passed,
            "failed": failed,
            "average_score_percent": average_score,
        },
        "artifacts": artifact_summaries,
    }
    write_json(output_root / "manifest.json", manifest_data)
    paths["report"].write_text(render_report(manifest_data, batch_slug), encoding="utf-8")
    return manifest_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create independent runtime-readiness benchmark artifacts.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of skills to evaluate in this batch.")
    parser.add_argument(
        "--batch-name", default=BATCH_NAME, help="Calendar-qualified batch identifier (e.g. 2026-04-17-…)."
    )
    parser.add_argument("--batch-slug", default="batch-01", help="Short slug appended to the batch directory name.")
    parser.add_argument(
        "--risk-level", default=RISK_LEVEL, help="Skill risk level filter (matches audit_skill_quality output)."
    )
    parser.add_argument(
        "--include-visual", action="store_true", help="Include visual/browser categories in this readiness batch."
    )
    parser.add_argument(
        "--category-spread", action="store_true", help="Select across categories before filling remaining slots."
    )
    parser.add_argument(
        "--avoid-existing-independent",
        action="store_true",
        help="Exclude skills already covered by earlier independent runtime artifacts.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = run(
        args.limit,
        batch_name=args.batch_name,
        batch_slug=args.batch_slug,
        risk_level=args.risk_level,
        include_visual=args.include_visual,
        category_spread=args.category_spread,
        avoid_existing_independent=args.avoid_existing_independent,
    )
    print(
        f"Independent runtime readiness artifacts: {manifest['summary']['artifact_count']} "
        f"created, {manifest['summary']['passed']} passed, {manifest['summary']['failed']} failed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

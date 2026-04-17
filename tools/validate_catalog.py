#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_catalog

MIN_CATALOG = 200
MIN_SCENARIOS = 3
HEX64 = re.compile(r"[0-9a-f]{64}")
PACKAGE_LOCK_MINIMUMS = {
    "node_modules/brace-expansion": (2, 0, 3),
    "node_modules/protobufjs": (7, 5, 5),
}

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def fail(message):
    print(f"FAIL: {message}")
    sys.exit(1)

def require(condition, message):
    if not condition:
        fail(message)

def unique_ids(items, key, label):
    ids = [item[key] for item in items]
    require(len(ids) == len(set(ids)), f"duplicate {label} ids")
    return ids

def version_tuple(version):
    return tuple(int(part) for part in str(version).split(".")[:3] if part.isdigit())

catalog = load("data/skills_catalog.json")
track_items = load("data/benchmark_tracks.json")
scenario_items = load("data/benchmark_scenarios.json")
assignment_items = load("data/benchmark_assignments.json")
priority_manifest = load("included/priority/manifest.json")
skills_manifest = load("included/skills/manifest.json")
agent_ready_manifest = load("included/agent-ready/manifest.json")
source_lock = load("data/source_lock.json")
best_practice_sources = load("data/best_practice_sources.json")
readme = (ROOT / "README.md").read_text(encoding="utf-8")

unique_ids(track_items, "id", "track")
unique_ids(scenario_items, "id", "scenario")
unique_ids(assignment_items, "skill_id", "assignment skill")
unique_ids(priority_manifest, "id", "priority manifest")
unique_ids(skills_manifest, "id", "skills manifest")
unique_ids(agent_ready_manifest, "id", "agent-ready manifest")

tracks = {item["id"]: item for item in track_items}
scenarios = {item["id"]: item for item in scenario_items}
assignments = {item["skill_id"]: item["scenario_ids"] for item in assignment_items}
assigned_scenario_ids = {scenario_id for scenario_ids in assignments.values() for scenario_id in scenario_ids}

require(len(catalog) >= MIN_CATALOG, f"catalog has {len(catalog)} entries")
ids = unique_ids(catalog, "id", "catalog")
require(set(assignments) <= set(ids), "assignment for unknown skill id")
for scenario_id in scenarios:
    require(scenario_id in assigned_scenario_ids, f"unassigned scenario {scenario_id}")
required_repos = {
    "strmt7/simple_ai_bitcoin_trading_binance",
    "strmt7/ome-zarr-C",
    "strmt7/project_air_defense",
    "ZMB-UZH/omero-docker-extended",
    "Varnan-Tech/opendirectory",
    "supermemoryai/skills",
    "hardikpandya/stop-slop",
}
missing_required = required_repos - {entry["source_repo"] for entry in catalog}
require(not missing_required, f"missing required repos: {sorted(missing_required)}")

readme_expectations = {
    f"- `{len(catalog)}` source-backed skill entries.": "catalog count",
    f"- `{len(catalog)}` written skill mirrors under `included/skills/`.": "mirror count",
    f"- `{len(catalog)}` compact agent-ready skill entrypoints under `included/agent-ready/`.": "agent-ready count",
    f"- `{sum(1 for entry in catalog if entry['source_tier'].startswith('priority'))}` selected repository entries.": "selected count",
    f"- `{len({entry['category'] for entry in catalog})}` categories.": "category count",
    f"- `{len(scenarios)}` real-data scenario templates.": "scenario count",
    f"- Minimum `{MIN_SCENARIOS}` benchmark scenarios assigned per scenario-covered candidate.": "minimum scenario count",
}
for snippet, label in readme_expectations.items():
    require(snippet in readme, f"README {label} is stale")
require("Early alpha" in readme, "README missing early alpha note")
require("priority entries from requested repositories" not in readme, "README uses requested repositories wording")
for forbidden in [
    "strmt7/simple_ai_bitcoin_trading_binance",
    "strmt7/ome-zarr-C",
    "strmt7/project_air_defense",
    "ZMB-UZH/omero-docker-extended",
]:
    require(forbidden not in readme, f"README reveals direct source {forbidden}")

expected_tracks = [{"id": t[0], "title": t[1], "url": t[2], "kind": "real dataset or repository workflow", "problem": t[3], "metrics": t[4]} for t in build_catalog.TRACKS]
require(track_items == expected_tracks, "benchmark_tracks.json is stale against build_catalog.TRACKS")
require(best_practice_sources == build_catalog.BEST_PRACTICE_SOURCES, "best_practice_sources.json is stale against build_catalog.BEST_PRACTICE_SOURCES")
benchmarks_doc = (ROOT / "docs" / "benchmarks.md").read_text(encoding="utf-8")
for track in expected_tracks:
    require(track["url"] in benchmarks_doc, f"benchmarks.md missing track URL {track['url']}")

catalog_by_id = {entry["id"]: entry for entry in catalog}
skills_manifest_by_id = {entry["id"]: entry for entry in skills_manifest}
require(set(skills_manifest_by_id) == set(catalog_by_id), "included skills manifest does not match catalog entries")
require(len(list((ROOT / "included" / "skills").rglob("SKILL.md"))) == len(catalog), "included skill SKILL.md count does not match catalog")
agent_ready_by_id = {entry["id"]: entry for entry in agent_ready_manifest}
require(set(agent_ready_by_id) == set(catalog_by_id), "agent-ready manifest does not match catalog entries")
require(len(list((ROOT / "included" / "agent-ready").rglob("SKILL.md"))) == len(catalog), "agent-ready SKILL.md count does not match catalog")
install_names = [entry.get("install_name") for entry in catalog]
require(all(install_names), "catalog entry missing install_name")
require(len(install_names) == len(set(install_names)), "duplicate catalog install_name")

locked_skills = {
    skill["id"]: source | {"skill": skill}
    for source in source_lock.get("sources", [])
    for skill in source.get("skills", [])
}
require(source_lock.get("lock_version") == 1, "source lock version mismatch")
require(source_lock.get("hash_algorithm") == "sha256", "source lock hash algorithm mismatch")
require(set(locked_skills) == set(catalog_by_id), "source lock skills do not match catalog")

agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
for phrase in ["mandatory single-session rule", "do not spawn", "subagents", "one ai session only"]:
    require(phrase in agents_text, f"AGENTS.md missing single-session rule phrase: {phrase}")

for agent_ready_path in (ROOT / "included" / "agent-ready").rglob("SKILL.md"):
    text = agent_ready_path.read_text(encoding="utf-8").lower()
    for phrase in ["subagent", "parallel agent", "multi-agent orchestration"]:
        require(phrase not in text, f"{agent_ready_path} recommends delegated AI work: {phrase}")

for lock_path in (ROOT / "included" / "skills").rglob("package-lock.json"):
    try:
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fail(f"{lock_path} is not valid JSON")
    packages = lock_data.get("packages", {})
    require(isinstance(packages, dict), f"{lock_path} missing package lock packages")
    for package_path, minimum in PACKAGE_LOCK_MINIMUMS.items():
        package_data = packages.get(package_path)
        if not isinstance(package_data, dict):
            continue
        observed = version_tuple(package_data.get("version"))
        require(observed >= minimum, f"{lock_path} keeps vulnerable {package_path} version {package_data.get('version')}")

for entry in catalog:
    for key in ["name", "description", "category", "subcategory", "install_name", "mirrored_path", "agent_ready_path", "source_repo", "source_path", "source_url", "immutable_source_url", "commit_sha", "selection_policy", "skill_file_sha256", "skill_dir_sha256"]:
        require(entry.get(key), f"{entry['id']} missing {key}")
    require(isinstance(entry.get("has_required_frontmatter"), bool), f"{entry['id']} invalid has_required_frontmatter")
    require(entry["source_path"].endswith("SKILL.md"), f"{entry['id']} is not SKILL.md")
    require(re.fullmatch(r"[0-9a-f]{40}", entry["commit_sha"]) is not None, f"{entry['id']} invalid commit_sha")
    require(HEX64.fullmatch(entry["skill_file_sha256"]) is not None, f"{entry['id']} invalid skill_file_sha256")
    require(HEX64.fullmatch(entry["skill_dir_sha256"]) is not None, f"{entry['id']} invalid skill_dir_sha256")
    require(entry["mirrored_path"] == build_catalog.skill_mirror_path(entry["category"], entry["subcategory"], entry["install_name"]), f"{entry['id']} mirrored_path/install_name mismatch")
    require(entry["agent_ready_path"] == build_catalog.skill_agent_ready_path(entry["category"], entry["subcategory"], entry["install_name"]), f"{entry['id']} agent_ready_path/install_name mismatch")
    expected_immutable = f"https://github.com/{entry['source_repo']}/blob/{entry['commit_sha']}/{entry['source_path']}"
    require(entry["immutable_source_url"] == expected_immutable, f"{entry['id']} immutable_source_url mismatch")
    if entry.get("latest_release_tag"):
        expected_source = f"https://github.com/{entry['source_repo']}/blob/{entry['latest_release_tag']}/{entry['source_path']}"
        require(entry["selected_ref"] == entry["latest_release_tag"], f"{entry['id']} selected_ref does not match latest_release_tag")
        require(entry["source_url"] == expected_source, f"{entry['id']} release source_url mismatch")
    else:
        require(entry["source_url"] == expected_immutable, f"{entry['id']} source_url should be commit-pinned without release tag")
    require(entry.get("benchmark_status") == "artifact_gated", f"{entry['id']} benchmark_status must remain artifact-gated until validated runtime artifacts exist")
    manifest_entry = skills_manifest_by_id[entry["id"]]
    for key in ["subcategory", "install_name", "mirrored_path", "agent_ready_path", "source_repo", "source_path", "immutable_source_url", "commit_sha", "skill_file_sha256", "skill_dir_sha256"]:
        require(manifest_entry.get(key) == entry[key], f"{entry['id']} skills manifest {key} mismatch")
    agent_ready = agent_ready_by_id[entry["id"]]
    require(agent_ready.get("agent_ready_path") == entry["agent_ready_path"], f"{entry['id']} agent-ready path mismatch")
    agent_ready_path = ROOT / entry["agent_ready_path"]
    require(agent_ready_path.is_file(), f"{entry['id']} missing agent-ready SKILL.md")
    agent_text = agent_ready_path.read_text(encoding="utf-8")
    require(agent_text.startswith("---\n"), f"{entry['id']} agent-ready SKILL.md missing frontmatter")
    require(entry["mirrored_path"] in agent_text or "../" in agent_text, f"{entry['id']} agent-ready SKILL.md missing local source pointer")
    locked = locked_skills[entry["id"]]
    require(locked["repo"] == entry["source_repo"], f"{entry['id']} source lock repo mismatch")
    require(locked["commit_sha"] == entry["commit_sha"], f"{entry['id']} source lock commit mismatch")
    require(locked["skill"]["source_path"] == entry["source_path"], f"{entry['id']} source lock path mismatch")
    require(locked["skill"]["skill_file_sha256"] == entry["skill_file_sha256"], f"{entry['id']} source lock file hash mismatch")
    require(locked["skill"]["skill_dir_sha256"] == entry["skill_dir_sha256"], f"{entry['id']} source lock dir hash mismatch")
    mirror_path = ROOT / entry["mirrored_path"]
    require(mirror_path.is_dir(), f"{entry['id']} missing mirrored directory")
    require((mirror_path / "SKILL.md").is_file(), f"{entry['id']} mirrored directory missing SKILL.md")
    require(len(list(mirror_path.rglob("SKILL.md"))) == 1, f"{entry['id']} mirrored directory contains nested SKILL.md files")
    require(build_catalog.sha256_file(mirror_path / "SKILL.md") == entry["skill_file_sha256"], f"{entry['id']} mirrored SKILL.md hash mismatch")
    require(build_catalog.sha256_tree(mirror_path) == entry["skill_dir_sha256"], f"{entry['id']} mirrored directory hash mismatch")
    if entry["scenario_covered_candidate"]:
        scenario_ids = assignments.get(entry["id"], [])
        require(scenario_ids == entry["benchmark_scenarios"], f"{entry['id']} assignment does not match catalog")
        require(len(scenario_ids) >= MIN_SCENARIOS, f"{entry['id']} has insufficient scenarios")
        require(scenario_ids[0] == f"skill-proof-{entry['id']}", f"{entry['id']} missing source-grounded first scenario")
        for scenario_id in scenario_ids:
            scenario = scenarios.get(scenario_id)
            require(scenario is not None, f"{entry['id']} unknown scenario {scenario_id}")
            require(scenario.get("real_data_or_workflow"), f"{scenario_id} not real-data/workflow")
            require(scenario["dataset_track_id"] in tracks, f"{scenario_id} unknown track")
            for scenario_key in ["expected_output_schema", "environment_requirements", "evaluator_path", "input_selector", "dataset_snapshot_policy"]:
                require(scenario.get(scenario_key), f"{scenario_id} missing {scenario_key}")
            require((ROOT / scenario["evaluator_path"]).is_file(), f"{scenario_id} missing evaluator file {scenario['evaluator_path']}")

priority_ids = {entry["id"] for entry in catalog if entry["source_tier"].startswith("priority")}
manifest_ids = {entry["id"] for entry in priority_manifest}
require(manifest_ids == priority_ids, "priority manifest does not match priority catalog entries")
priority_install_names = [item.get("install_name") for item in priority_manifest]
require(all(priority_install_names), "priority manifest entry missing install_name")
require(len(priority_install_names) == len(set(priority_install_names)), "duplicate priority install_name")
for item in priority_manifest:
    catalog_entry = catalog_by_id[item["id"]]
    for key in ["subcategory", "install_name", "mirrored_path", "agent_ready_path", "source_repo", "source_path", "immutable_source_url", "commit_sha", "skill_file_sha256", "skill_dir_sha256"]:
        require(item.get(key) == catalog_entry[key], f"{item['id']} priority manifest {key} mismatch")
    mirror_path = ROOT / item["mirrored_path"]
    require(mirror_path.is_dir(), f"{item['id']} missing mirrored directory")
    require((mirror_path / "SKILL.md").is_file(), f"{item['id']} mirrored directory missing SKILL.md")
    require(item["standalone_installable"] == item["has_required_frontmatter"], f"{item['id']} standalone_installable/frontmatter mismatch")
    require(item["bulk_install_safe"] == (item["has_required_frontmatter"] and item["name_conflict_group"] is None), f"{item['id']} invalid bulk_install_safe")

text = readme.lower()
for phrase in ["bug-free", "error-free", "guaranteed", "best skills", "fully proven"]:
    require(phrase not in text, f"README overclaim: {phrase}")
print(f"OK: {len(catalog)} catalog entries, {len(tracks)} dataset tracks, {len(scenarios)} scenarios")

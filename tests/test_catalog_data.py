import re
from pathlib import Path

import build_catalog
from helpers import MIN_SCENARIOS, ROOT, assert_unique, load


def test_catalog_scale_and_unique_ids():
    catalog = load("data/skills_catalog.json")
    assert len(catalog) >= 200
    assert_unique(catalog, "id")


def test_entry_provenance():
    for entry in load("data/skills_catalog.json"):
        assert entry["name"]
        assert entry["description"]
        assert entry["install_name"]
        assert entry["mirrored_path"] == build_catalog.skill_mirror_path(
            entry["category"], entry["subcategory"], entry["install_name"]
        )
        assert entry["agent_ready_path"] == build_catalog.skill_agent_ready_path(
            entry["category"], entry["subcategory"], entry["install_name"]
        )
        assert isinstance(entry["selected_subset"], bool)
        assert not entry["source_tier"].startswith("priority")
        assert "requested" not in entry["source_tier"]
        assert isinstance(entry["has_required_frontmatter"], bool)
        assert entry["source_path"].endswith("SKILL.md")
        assert re.fullmatch(r"[0-9a-f]{40}", entry["commit_sha"])
        assert re.fullmatch(r"[0-9a-f]{64}", entry["skill_file_sha256"])
        assert re.fullmatch(r"[0-9a-f]{64}", entry["skill_dir_sha256"])
        expected_immutable = (
            f"https://github.com/{entry['source_repo']}/blob/{entry['commit_sha']}/{entry['source_path']}"
        )
        assert entry["immutable_source_url"] == expected_immutable
        if entry["latest_release_tag"]:
            expected_source = (
                f"https://github.com/{entry['source_repo']}/blob/{entry['latest_release_tag']}/{entry['source_path']}"
            )
            assert entry["selected_ref"] == entry["latest_release_tag"]
            assert entry["source_url"] == expected_source
        else:
            assert entry["source_url"] == expected_immutable
        assert entry["selection_policy"]


def test_install_names_are_concrete_and_not_elided():
    catalog = load("data/skills_catalog.json")
    install_names = [entry["install_name"] for entry in catalog]
    assert len(install_names) == len(set(install_names))
    assert max(len(name) for name in install_names) <= 80
    for entry in catalog:
        for key in ["install_name", "mirrored_path", "agent_ready_path", "source_path", "immutable_source_url"]:
            assert "..." not in entry[key], (entry["id"], key)
        assert Path(entry["mirrored_path"]).name == entry["install_name"]
        assert Path(entry["agent_ready_path"]).parent.name == entry["install_name"]


def test_selected_repositories_present():
    repos = {entry["source_repo"] for entry in load("data/skills_catalog.json")}
    assert {
        "strmt7/simple_ai_bitcoin_trading_binance",
        "strmt7/ome-zarr-C",
        "strmt7/project_air_defense",
        "ZMB-UZH/omero-docker-extended",
    }.issubset(repos)


def test_reddit_verified_repositories_present():
    repos = {entry["source_repo"] for entry in load("data/skills_catalog.json")}
    assert {
        "Varnan-Tech/opendirectory",
        "supermemoryai/skills",
        "hardikpandya/stop-slop",
        "affaan-m/everything-claude-code",
    }.issubset(repos)


def test_ready_candidates_have_real_scenarios():
    scenario_items = load("data/benchmark_scenarios.json")
    assignment_items = load("data/benchmark_assignments.json")
    assert_unique(scenario_items, "id")
    assert_unique(assignment_items, "skill_id")
    scenarios = {item["id"]: item for item in scenario_items}
    assignments = {item["skill_id"]: item["scenario_ids"] for item in assignment_items}
    catalog = load("data/skills_catalog.json")
    assert set(assignments) <= {entry["id"] for entry in catalog}
    assigned_scenario_ids = {scenario_id for scenario_ids in assignments.values() for scenario_id in scenario_ids}
    assert set(scenarios) <= assigned_scenario_ids
    for entry in catalog:
        assert entry["benchmark_status"] == "artifact_gated"
        if not entry["scenario_covered_candidate"]:
            continue
        scenario_ids = assignments.get(entry["id"], [])
        assert scenario_ids == entry["benchmark_scenarios"], entry["id"]
        assert len(scenario_ids) >= MIN_SCENARIOS, entry["id"]
        assert scenario_ids[0] == f"skill-proof-{entry['id']}"
        for scenario_id in scenario_ids:
            assert scenarios[scenario_id]["real_data_or_workflow"] is True
            assert scenarios[scenario_id]["expected_output_schema"]["required"]
            assert scenarios[scenario_id]["environment_requirements"]
            assert scenarios[scenario_id]["evaluator_path"]
            assert (ROOT / scenarios[scenario_id]["evaluator_path"]).is_file()


def test_tracks_are_real_urls():
    tracks = load("data/benchmark_tracks.json")
    assert tracks
    assert_unique(tracks, "id")
    for track in tracks:
        assert track["url"].startswith("https://")
        assert track["problem"]
        assert track["metrics"]


def test_source_lock_matches_catalog():
    catalog = {entry["id"]: entry for entry in load("data/skills_catalog.json")}
    lock = load("data/source_lock.json")
    assert lock["lock_version"] == 1
    assert lock["hash_algorithm"] == "sha256"
    locked = {skill["id"]: (source, skill) for source in lock["sources"] for skill in source["skills"]}
    assert set(locked) == set(catalog)
    for skill_id, (source, skill) in locked.items():
        entry = catalog[skill_id]
        assert source["repo"] == entry["source_repo"]
        assert source["commit_sha"] == entry["commit_sha"]
        assert skill["source_path"] == entry["source_path"]
        assert skill["install_name"] == entry["install_name"]
        assert skill["skill_file_sha256"] == entry["skill_file_sha256"]
        assert skill["skill_dir_sha256"] == entry["skill_dir_sha256"]


def test_generated_files_match_generator_constants():
    expected_tracks = [
        {
            "id": t[0],
            "title": t[1],
            "url": t[2],
            "kind": "real dataset or repository workflow",
            "problem": t[3],
            "metrics": t[4],
        }
        for t in build_catalog.TRACKS
    ]
    assert load("data/benchmark_tracks.json") == expected_tracks
    assert load("data/best_practice_sources.json") == build_catalog.BEST_PRACTICE_SOURCES


def test_category_keyword_matching_uses_tokens():
    source = {"repo": "example/tools"}
    assert (
        build_catalog.category_for(
            source, "skills/dockerfile-generator/SKILL.md", "dockerfile-generator", "Generate Dockerfiles"
        )
        == "DevOps, cloud & operations"
    )
    assert (
        build_catalog.category_for(
            source, "skills/gitlab-helper/SKILL.md", "gitlab-helper", "Elaborate workflow generator"
        )
        != "Science, research & data analysis"
    )
    assert (
        build_catalog.category_for(
            source, "skills/bash-script-generator/SKILL.md", "bash-script-generator", "Generate shell scripts"
        )
        != "Agent infrastructure & skill creation"
    )
    assert (
        build_catalog.category_for(source, "skills/gene-analysis/SKILL.md", "gene-analysis", "Analyze gene expression")
        == "Science, research & data analysis"
    )

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_catalog
import check_benchmark_artifact
import check_no_secret_patterns

MIN_SCENARIOS = 3

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def complete_artifacts():
    artifact_root = ROOT / "artifacts" / "benchmark-runs"
    if not artifact_root.exists():
        return []
    artifacts = []
    for path in sorted(artifact_root.rglob("artifact.json")):
        result = check_benchmark_artifact.validate_artifact(path)
        assert result["verdict"] == "artifact_complete", (path, result)
        artifacts.append((path, json.loads(path.read_text(encoding="utf-8")), result))
    return artifacts

def assert_unique(items, key):
    values = [item[key] for item in items]
    assert len(values) == len(set(values))
    return values

def test_catalog_scale_and_unique_ids():
    catalog = load("data/skills_catalog.json")
    assert len(catalog) >= 200
    assert_unique(catalog, "id")

def test_entry_provenance():
    for entry in load("data/skills_catalog.json"):
        assert entry["name"]
        assert entry["description"]
        assert entry["install_name"]
        assert entry["mirrored_path"] == build_catalog.skill_mirror_path(entry["category"], entry["subcategory"], entry["install_name"])
        assert entry["agent_ready_path"] == build_catalog.skill_agent_ready_path(entry["category"], entry["subcategory"], entry["install_name"])
        assert isinstance(entry["selected_subset"], bool)
        assert not entry["source_tier"].startswith("priority")
        assert "requested" not in entry["source_tier"]
        assert isinstance(entry["has_required_frontmatter"], bool)
        assert entry["source_path"].endswith("SKILL.md")
        assert re.fullmatch(r"[0-9a-f]{40}", entry["commit_sha"])
        assert re.fullmatch(r"[0-9a-f]{64}", entry["skill_file_sha256"])
        assert re.fullmatch(r"[0-9a-f]{64}", entry["skill_dir_sha256"])
        expected_immutable = f"https://github.com/{entry['source_repo']}/blob/{entry['commit_sha']}/{entry['source_path']}"
        assert entry["immutable_source_url"] == expected_immutable
        if entry["latest_release_tag"]:
            expected_source = f"https://github.com/{entry['source_repo']}/blob/{entry['latest_release_tag']}/{entry['source_path']}"
            assert entry["selected_ref"] == entry["latest_release_tag"]
            assert entry["source_url"] == expected_source
        else:
            assert entry["source_url"] == expected_immutable
        assert entry["selection_policy"]

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

def test_readme_does_not_overclaim():
    text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for phrase in ["bug-free", "error-free", "guaranteed", "best skills", "fully proven"]:
        assert phrase not in text

def test_generated_counts_are_documented():
    catalog = load("data/skills_catalog.json")
    scenarios = load("data/benchmark_scenarios.json")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"- `{len(catalog)}` source-backed skill entries." in readme
    assert f"- `{len(catalog)}` written skill mirrors under `included/skills/`." in readme
    assert f"- `{len(catalog)}` compact agent-ready skill entrypoints under `included/agent-ready/`." in readme
    assert f"- `{sum(1 for entry in catalog if entry['selected_subset'])}` selected repository entries." in readme
    assert f"- `{len({entry['category'] for entry in catalog})}` categories." in readme
    assert f"- `{len(scenarios)}` real-data scenario templates." in readme
    assert f"- Minimum `{MIN_SCENARIOS}` benchmark scenarios assigned per scenario-covered candidate." in readme
    assert "[Benchmark runner requirements](docs/benchmark-runner-requirements.md)" in readme
    assert "[Benchmark results](docs/benchmark-results.md)" in readme
    assert "[Skill risk findings](docs/skill-risk-findings.md)" in readme
    assert "[Immutable audit model](docs/immutable-audit-model.md)" in readme
    assert "[Included skill mirrors](included/skills/README.md)" in readme
    assert "[Agent-ready skills](included/agent-ready/README.md)" in readme
    assert "[Selected skills](docs/selected-skills.md)" in readme
    assert "Early alpha" in readme
    assert "priority entries from requested repositories" not in readme
    assert "AI-generated" not in readme
    assert "generated by AI" not in readme
    for forbidden in [
        "strmt7/simple_ai_bitcoin_trading_binance",
        "strmt7/ome-zarr-C",
        "strmt7/project_air_defense",
        "ZMB-UZH/omero-docker-extended",
    ]:
        assert forbidden not in readme
    assert not (ROOT / "docs" / "priority-skills.md").exists()

def test_benchmark_runner_requirements_are_explicit():
    text = (ROOT / "docs/benchmark-runner-requirements.md").read_text(encoding="utf-8")
    for phrase in [
        "actual websites",
        "delayed recall probes",
        "token usage before and after",
        "real public datasets",
        "runtime claim",
    ]:
        assert phrase in text

def test_selected_manifest_matches_mirrors():
    catalog = load("data/skills_catalog.json")
    manifest = load("included/selected/manifest.json")
    selected_ids = {entry["id"] for entry in catalog if entry["selected_subset"]}
    assert {entry["id"] for entry in manifest} == selected_ids
    assert not (ROOT / "included" / "priority").exists()
    install_names = [entry["install_name"] for entry in manifest]
    assert len(install_names) == len(set(install_names))
    for entry in manifest:
        mirror_path = ROOT / entry["mirrored_path"]
        assert mirror_path.is_dir(), entry["id"]
        assert (mirror_path / "SKILL.md").is_file(), entry["id"]
        assert entry["standalone_installable"] == entry["has_required_frontmatter"]
        assert entry["bulk_install_safe"] == (entry["has_required_frontmatter"] and entry["name_conflict_group"] is None)

def test_all_skills_are_physically_mirrored_and_documented():
    catalog = load("data/skills_catalog.json")
    manifest = load("included/skills/manifest.json")
    agent_ready_manifest = load("included/agent-ready/manifest.json")
    manifest_by_id = {entry["id"]: entry for entry in manifest}
    agent_ready_by_id = {entry["id"]: entry for entry in agent_ready_manifest}
    assert set(manifest_by_id) == {entry["id"] for entry in catalog}
    assert set(agent_ready_by_id) == {entry["id"] for entry in catalog}
    assert len(list((ROOT / "included" / "skills").rglob("SKILL.md"))) == len(catalog)
    assert len(list((ROOT / "included" / "agent-ready").rglob("SKILL.md"))) == len(catalog)
    install_names = [entry["install_name"] for entry in catalog]
    assert len(install_names) == len(set(install_names))
    for entry in catalog:
        mirrored = ROOT / entry["mirrored_path"]
        assert mirrored.is_dir(), entry["id"]
        assert (mirrored / "SKILL.md").is_file(), entry["id"]
        assert len(list(mirrored.rglob("SKILL.md"))) == 1
        assert build_catalog.sha256_file(mirrored / "SKILL.md") == entry["skill_file_sha256"]
        assert build_catalog.sha256_tree(mirrored) == entry["skill_dir_sha256"]
        item = manifest_by_id[entry["id"]]
        assert item["mirrored_path"] == entry["mirrored_path"]
        skill_doc = ROOT / "docs" / "catalog" / "skills" / "by-category" / build_catalog.slug(entry["category"]) / build_catalog.slug(entry["subcategory"]) / f"{entry['install_name']}.md"
        assert skill_doc.is_file(), entry["id"]
        agent_ready = ROOT / entry["agent_ready_path"]
        assert agent_ready.is_file(), entry["id"]
        assert agent_ready.read_text(encoding="utf-8").startswith("---\n")

def test_source_lock_matches_catalog():
    catalog = {entry["id"]: entry for entry in load("data/skills_catalog.json")}
    lock = load("data/source_lock.json")
    assert lock["lock_version"] == 1
    assert lock["hash_algorithm"] == "sha256"
    locked = {
        skill["id"]: (source, skill)
        for source in lock["sources"]
        for skill in source["skills"]
    }
    assert set(locked) == set(catalog)
    for skill_id, (source, skill) in locked.items():
        entry = catalog[skill_id]
        assert source["repo"] == entry["source_repo"]
        assert source["commit_sha"] == entry["commit_sha"]
        assert skill["source_path"] == entry["source_path"]
        assert skill["skill_file_sha256"] == entry["skill_file_sha256"]
        assert skill["skill_dir_sha256"] == entry["skill_dir_sha256"]

def test_generated_files_match_generator_constants():
    expected_tracks = [{"id": t[0], "title": t[1], "url": t[2], "kind": "real dataset or repository workflow", "problem": t[3], "metrics": t[4]} for t in build_catalog.TRACKS]
    assert load("data/benchmark_tracks.json") == expected_tracks
    assert load("data/best_practice_sources.json") == build_catalog.BEST_PRACTICE_SOURCES

def test_static_benchmark_results_are_real_and_current():
    results = load("data/static_benchmark_results.json")
    catalog = load("data/skills_catalog.json")
    artifacts = complete_artifacts()
    runtime_paths = {path.relative_to(ROOT).as_posix() for path, artifact, _ in artifacts if artifact["artifact_kind"] == "independent_benchmark"}
    provenance_paths = {path.relative_to(ROOT).as_posix() for path, artifact, _ in artifacts if artifact["artifact_kind"] == "provenance_check"}
    assert results["summary"]["skill_count"] == len(catalog)
    assert results["summary"]["runtime_artifacts_recorded"] == len(runtime_paths)
    assert results["summary"]["provenance_artifacts_recorded"] == len(provenance_paths)
    assert results["summary"]["provenance_artifacts_recorded"] >= 10
    assert {item["artifact_path"] for item in results["runtime_artifacts"]} == runtime_paths
    assert {item["artifact_path"] for item in results["provenance_artifacts"]} == provenance_paths
    assert sum(track["runtime_artifacts_recorded"] for track in results["tracks"]) == len(runtime_paths)
    assert sum(item["runtime_artifacts_recorded"] for item in results["skills"]) == len(runtime_paths)
    assert {item["skill_id"] for item in results["skills"]} == {entry["id"] for entry in catalog}
    assert sum(item["static_checks_passed"] for item in results["skills"]) == results["summary"]["static_checks_passed"]
    assert sum(item["quality_fix_point_count"] for item in results["skills"]) == results["summary"]["quality_fix_points"]
    text = (ROOT / "docs" / "benchmark-results.md").read_text(encoding="utf-8")
    assert "Static checks passed" in text
    assert "Source-proof artifacts are provenance checks, not runtime benchmark passes" in text
    quality_text = (ROOT / "docs" / "skill-quality-findings.md").read_text(encoding="utf-8")
    assert "| Skill | Category | Static score | Failed checks | Fix points |" in quality_text

def test_skill_risk_audit_covers_every_skill():
    audit = load("data/skill_risk_audit.json")
    catalog = load("data/skills_catalog.json")
    assert audit["summary"]["skill_count"] == len(catalog)
    assert {item["skill_id"] for item in audit["skills"]} == {entry["id"] for entry in catalog}
    assert sum(audit["summary"][key] for key in [
        "likely_non_working",
        "subpar_needs_review",
        "usable_with_listing_gaps",
        "no_static_risk_found",
    ]) == len(catalog)
    assert audit["summary"]["subpar_needs_review"] > 0
    text = (ROOT / "docs" / "skill-risk-findings.md").read_text(encoding="utf-8")
    assert "static, source-backed evidence" in text
    assert "| Risk | Skill | Category | Blocking | Warnings | Key findings |" in text

def test_agent_instructions_forbid_subagents():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8").lower()
    for phrase in ["mandatory single-session rule", "do not spawn", "subagents", "one ai session only"]:
        assert phrase in text
    for phrase in [
        "separate work loops",
        "skill mirror loop",
        "artifact and test loop",
        "benchmark independence rule",
        "must not be counted as runtime benchmark passes",
    ]:
        assert phrase in text


def test_agent_ready_entrypoints_do_not_recommend_delegation():
    for path in (ROOT / "included" / "agent-ready").rglob("SKILL.md"):
        text = path.read_text(encoding="utf-8").lower()
        assert "subagent" not in text, path
        assert "parallel agent" not in text, path
        assert "multi-agent orchestration" not in text, path


def test_mirrored_package_locks_keep_known_advisory_floors():
    minimums = {
        "node_modules/brace-expansion": (2, 0, 3),
        "node_modules/protobufjs": (7, 5, 5),
    }
    for path in (ROOT / "included" / "skills").rglob("package-lock.json"):
        lock = json.loads(path.read_text(encoding="utf-8"))
        for package_path, minimum in minimums.items():
            package_data = lock.get("packages", {}).get(package_path)
            if not package_data:
                continue
            observed = tuple(int(part) for part in package_data["version"].split(".")[:3])
            assert observed >= minimum, (path, package_path, package_data["version"])


def test_benchmark_artifact_checker_accepts_complete_artifact_and_rejects_incomplete_visual():
    catalog = load("data/skills_catalog.json")
    entry = catalog[0]
    scenario_id = entry["benchmark_scenarios"][0]
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "transcript.txt").write_text("commands and transcript", encoding="utf-8")
        (base / "result.json").write_text("{}", encoding="utf-8")
        artifact = {
            "artifact_version": "1.0",
            "artifact_kind": "provenance_check",
            "skill_id": entry["id"],
            "scenario_id": scenario_id,
            "catalog_commit": "0" * 40,
            "source_commit": entry["commit_sha"],
            "source_repo": entry["source_repo"],
            "source_path": entry["source_path"],
            "runner": {"timestamp_utc": "2026-04-17T00:00:00Z", "tool": "pytest", "model_or_runtime": "local"},
            "scenario_requirements": {"visual_or_browser": False, "context_memory": False, "token_efficiency_claim": False},
            "input_snapshot": {"kind": "source", "identifier": entry["immutable_source_url"], "is_real": True},
            "execution": {"fresh_session": True, "commands_or_transcript_path": "transcript.txt"},
            "outputs": {"path": "result.json"},
            "metrics": {"checks": 1},
            "independence": {
                "task_defined_outside_skill": False,
                "evaluator_defined_outside_skill": True,
                "expected_result_defined_outside_skill": False,
                "uses_exact_skill_content_for_expected_result": True,
                "skill_content_usage": "source text used for provenance check only",
            },
            "evidence": {"artifact_paths": ["result.json"], "citations_or_paths": [entry["source_path"]]},
            "objective_checks": ["source citations present"],
        }
        artifact_path = base / "artifact.json"
        artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
        assert check_benchmark_artifact.validate_artifact(artifact_path)["verdict"] == "artifact_complete"
        artifact["scenario_requirements"]["visual_or_browser"] = True
        artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
        result = check_benchmark_artifact.validate_artifact(artifact_path)
        assert result["verdict"] == "artifact_incomplete"
        assert any("visual" in error for error in result["errors"])

def test_history_secret_scan_rename_parser_uses_existing_commit_paths(monkeypatch):
    def fake_git_bytes(*args):
        assert args == ("diff-tree", "-z", "--no-commit-id", "--name-status", "-r", "-M", "commit")
        return (
            b"R100\0old/path.txt\0new/path.txt\0"
            b"D\0removed/path.txt\0"
            b"M\0kept/path.txt\0"
            b"A\0added/path.txt\0"
        )

    monkeypatch.setattr(check_no_secret_patterns, "git_bytes", fake_git_bytes)
    assert check_no_secret_patterns.commit_changed_names("commit") == [
        "new/path.txt",
        "kept/path.txt",
        "added/path.txt",
    ]

def test_category_keyword_matching_uses_tokens():
    source = {"repo": "example/tools"}
    assert build_catalog.category_for(source, "skills/dockerfile-generator/SKILL.md", "dockerfile-generator", "Generate Dockerfiles") == "DevOps, cloud & operations"
    assert build_catalog.category_for(source, "skills/gitlab-helper/SKILL.md", "gitlab-helper", "Elaborate workflow generator") != "Science, research & data analysis"
    assert build_catalog.category_for(source, "skills/bash-script-generator/SKILL.md", "bash-script-generator", "Generate shell scripts") != "Agent infrastructure & skill creation"
    assert build_catalog.category_for(source, "skills/gene-analysis/SKILL.md", "gene-analysis", "Analyze gene expression") == "Science, research & data analysis"

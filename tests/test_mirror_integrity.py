import json

import build_catalog
from helpers import ROOT, load


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
        assert entry["bulk_install_safe"] == (
            entry["has_required_frontmatter"] and entry["name_conflict_group"] is None
        )


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
        skill_doc = (
            ROOT
            / "docs"
            / "catalog"
            / "skills"
            / "by-category"
            / build_catalog.slug(entry["category"])
            / build_catalog.slug(entry["subcategory"])
            / f"{entry['install_name']}.md"
        )
        assert skill_doc.is_file(), entry["id"]
        agent_ready = ROOT / entry["agent_ready_path"]
        assert agent_ready.is_file(), entry["id"]
        assert agent_ready.read_text(encoding="utf-8").startswith("---\n")


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

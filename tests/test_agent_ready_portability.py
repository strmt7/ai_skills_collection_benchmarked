from __future__ import annotations

import json
import re
from pathlib import Path

import build_catalog
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_entrypoints_have_portable_headers_and_resolvable_links():
    catalog = json.loads((ROOT / "data/skills_catalog.json").read_bytes())
    aliases = set()
    for entry in catalog:
        path = ROOT / entry["agent_ready_path"]
        text = path.read_text(encoding="utf-8")
        header, separator, body = text.removeprefix("---\n").partition("\n---\n")
        assert text.startswith("---\n") and separator
        metadata = yaml.safe_load(header)
        assert set(metadata) == {"name", "description", "metadata"}
        alias = metadata["name"]
        assert alias == path.parent.name and 1 <= len(alias) <= 64
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", alias) and alias not in aliases
        aliases.add(alias)
        assert metadata["description"] == entry["description"]
        assert 1 <= len(metadata["description"]) <= 1024
        details = metadata["metadata"]
        assert all(isinstance(value, str) for value in details.values())
        assert details["source_skill_id"] == entry["id"]
        assert (path.parent / details["source_mirror"]).resolve().samefile(ROOT / entry["mirrored_path"] / "SKILL.md")
        for label, relative in (
            ("Mandatory agent tools", "docs/agent-tools.md"),
            ("Static benchmark results", "docs/benchmark-results.md"),
        ):
            pattern = rf"\[{re.escape(label)}\]\(([^)]+)\)"
            link = re.search(pattern, body)
            assert link and (path.parent / link[1]).resolve().samefile(ROOT / relative)


def test_shortened_alias_collision_is_rejected_before_touching_output(tmp_path, monkeypatch):
    long_name = "owned-long-catalog-skill-with-a-human-readable-prefix-and-a-distinct-source"
    alias = build_catalog.agent_ready_name(long_name)
    assert len(alias) <= 64 and alias != long_name
    rows = []
    for identity, name in (("original", long_name), ("conflict", alias)):
        rows.append(
            {
                "id": identity,
                "name": identity,
                "description": "Owned fixture for validating a portable name.",
                "install_name": name,
                "category": identity,
                "subcategory": "fixture",
                "mirrored_path": "included/skills/fixture",
                "agent_ready_path": build_catalog.skill_agent_ready_path(identity, "fixture", name),
                "commit_sha": "1" * 40,
                "benchmark_scenarios": [],
                "benchmark_status": "artifact_gated",
            }
        )
    monkeypatch.setattr(build_catalog, "ROOT", tmp_path)
    sentinel = tmp_path / "included/agent-ready/previous.json"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_bytes(b"previous valid output")
    with pytest.raises(ValueError, match="duplicate agent-ready alias"):
        build_catalog.write_agent_ready_skills(rows)
    assert list(sentinel.parent.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"previous valid output"

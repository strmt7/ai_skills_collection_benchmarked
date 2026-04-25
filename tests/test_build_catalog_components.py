"""Component + property tests for tools/build_catalog.py.

The full ``main()`` writes to repo-relative output paths (``data/``,
``included/``, etc.), so a true end-to-end smoke would risk clobbering the
committed catalog. We instead exercise the individual helpers with real and
synthetic inputs, plus property tests via Hypothesis where applicable. This
covers the riskiest internal logic without redirecting the writer.
"""

from __future__ import annotations

import build_catalog
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# slug()
# ---------------------------------------------------------------------------


def test_slug_lowercases_and_dashes():
    assert build_catalog.slug("Hello World!") == "hello-world"


def test_slug_collapses_repeated_separators():
    assert build_catalog.slug("foo--bar  baz__qux") == "foo-bar-baz-qux"


def test_slug_strips_leading_trailing_separators():
    assert build_catalog.slug("---foo---") == "foo"


def test_slug_keeps_alphanumerics_only():
    assert build_catalog.slug("a/b.c+d&e") == "a-b-c-d-e"


@given(st.text(min_size=1, max_size=64))
@settings(max_examples=80)
def test_slug_is_idempotent(text: str):
    once = build_catalog.slug(text)
    twice = build_catalog.slug(once)
    assert once == twice, f"slug not idempotent: {text!r} -> {once!r} -> {twice!r}"


@given(st.text(min_size=0, max_size=64))
@settings(max_examples=80)
def test_slug_output_is_lowercase_alnum_dashes(text: str):
    out = build_catalog.slug(text)
    assert all(c.isalnum() and c.islower() or c == "-" or c.isdigit() for c in out), (
        f"unexpected character in slug({text!r}) -> {out!r}"
    )
    assert "--" not in out, f"slug({text!r}) -> {out!r} contains a doubled dash"


# ---------------------------------------------------------------------------
# parse_frontmatter()
# ---------------------------------------------------------------------------


def test_parse_frontmatter_full_document():
    text = "---\nname: my-skill\ndescription: hi\n---\n# Body\ncontent\n"
    meta, body = build_catalog.parse_frontmatter(text)
    assert meta == {"name": "my-skill", "description": "hi"}
    assert body.lstrip("\n") == "# Body\ncontent\n"


def test_parse_frontmatter_no_frontmatter():
    meta, body = build_catalog.parse_frontmatter("# Just markdown\nhello\n")
    assert meta == {}
    assert body == "# Just markdown\nhello\n"


def test_parse_frontmatter_empty_yaml_block_returns_empty_meta():
    text = "---\n\n---\n# body\n"
    meta, body = build_catalog.parse_frontmatter(text)
    assert meta == {}


def test_parse_frontmatter_handles_quoted_values_in_fallback(monkeypatch):
    # Force the fallback parser by clobbering yaml; helpers strip surrounding quotes.
    monkeypatch.setattr(build_catalog, "yaml", None)
    meta, _ = build_catalog.parse_frontmatter('---\nname: "quoted"\n---\nbody\n')
    assert meta == {"name": "quoted"}


# ---------------------------------------------------------------------------
# install_name resolution
# ---------------------------------------------------------------------------


def test_unique_install_name_first_wins():
    used: set[str] = set()
    counts = {"context-budget": 1}
    entry = {
        "source_repo": "alice/example",
        "source_path": ".agents/skills/context-budget/SKILL.md",
        "name": "context-budget",
    }
    name = build_catalog.unique_install_name(entry, used, counts)
    assert name == "context-budget"
    assert name in used


def test_unique_install_name_disambiguates_collision():
    used = {"context-budget"}
    counts = {"context-budget": 2}  # forces disambiguation path
    entry = {
        "source_repo": "alice/example",
        "source_path": ".agents/skills/context-budget/SKILL.md",
        "name": "context-budget",
    }
    name = build_catalog.unique_install_name(entry, used, counts)
    assert name != "context-budget", "must disambiguate when collision in same group"
    assert name not in {"context-budget"}
    assert name.startswith("context-budget"), f"expected hashed-suffix variant, got {name!r}"


# ---------------------------------------------------------------------------
# is_under_nested_skill — tree pruning invariant
# ---------------------------------------------------------------------------


def test_is_under_nested_skill_detects_inner_skill(tmp_path):
    root = tmp_path / "outer"
    root.mkdir()
    (root / "SKILL.md").write_text("outer\n", encoding="utf-8")
    inner = root / "examples" / "nested-skill"
    inner.mkdir(parents=True)
    (inner / "SKILL.md").write_text("inner\n", encoding="utf-8")
    target = inner / "fixture.txt"
    target.write_text("data", encoding="utf-8")
    assert build_catalog.is_under_nested_skill(root, target) is True


def test_is_under_nested_skill_returns_false_for_top_level_files(tmp_path):
    root = tmp_path / "outer"
    root.mkdir()
    (root / "SKILL.md").write_text("outer\n", encoding="utf-8")
    f = root / "scripts" / "run.sh"
    f.parent.mkdir()
    f.write_text("#!/bin/sh\n", encoding="utf-8")
    assert build_catalog.is_under_nested_skill(root, f) is False


# ---------------------------------------------------------------------------
# keyword_matches + category_for — pure categorisation logic
# ---------------------------------------------------------------------------


def test_keyword_matches_word_boundary():
    assert build_catalog.keyword_matches("docker patterns", "docker") is True
    # Partial word must NOT match (substring "dock" inside "docker" should not
    # trigger when keyword is "dock").
    assert build_catalog.keyword_matches("docker patterns", "dock") is False


def test_keyword_matches_multi_word_phrase():
    assert build_catalog.keyword_matches("the visual-qa pipeline", "visual qa") is True
    assert build_catalog.keyword_matches("qa visual", "visual qa") is False


def test_keyword_matches_empty_keyword_returns_false():
    assert build_catalog.keyword_matches("anything", "") is False
    assert build_catalog.keyword_matches("", "docker") is False


@pytest.fixture
def _source_stub():
    return {"repo": "example-org/example-repo"}


def test_category_for_by_keyword_match(_source_stub):
    cat = build_catalog.category_for(_source_stub, "skills/gene/SKILL.md", "gene-analysis", "RDKit + scanpy pipeline")
    assert cat == "Science, research & data analysis"


def test_category_for_microsoft_special_case():
    ms_source = {"repo": "microsoft/skills"}
    cat = build_catalog.category_for(ms_source, "skills/foo", "foo", "foo")
    assert cat == "Cloud, Azure & Microsoft SDKs"


def test_category_for_kdense_special_case():
    kd_source = {"repo": "K-Dense-AI/scientific-agent-skills"}
    cat = build_catalog.category_for(kd_source, "whatever", "widget", "widget desc")
    assert cat == "Science, research & data analysis"


def test_category_for_fallback_to_coding(_source_stub):
    cat = build_catalog.category_for(_source_stub, "rel", "unrelated", "does nothing special")
    assert cat == "Coding, refactoring & repository automation"


def test_scenario_ids_returns_three_distinct_tracks():
    # category_scenario_id replaces "&" with "and" BEFORE slugging, so scenario
    # IDs use "and" where skill paths do not — an intentional asymmetry between
    # category-labelled URLs (scenarios) and directory layouts (mirrors).
    ids = build_catalog.scenario_ids("Science, research & data analysis")
    assert len(ids) == 3
    assert len(set(ids)) == 3
    for scenario_id in ids:
        assert "-" in scenario_id
        assert scenario_id.startswith("science-research-and-data-analysis-")


def test_scenario_ids_unknown_category_falls_back_to_coding():
    # Unknown category falls back to "Coding, refactoring & repository automation".
    ids = build_catalog.scenario_ids("not a real category ever")
    # Unknown category SLUG becomes "not-a-real-category-ever" (no "and" because
    # & wasn't present); the track list mirrors Coding's defaults.
    assert len(ids) == 3
    assert all("not-a-real-category-ever-" in scenario_id for scenario_id in ids)


# ---------------------------------------------------------------------------
# flags — filesystem shape detection for resource flags
# ---------------------------------------------------------------------------


def test_flags_all_false_on_bare_skill(tmp_path):
    skill = tmp_path / "SKILL.md"
    skill.write_text("x", encoding="utf-8")
    assert build_catalog.flags(skill) == {
        "has_agents_metadata": False,
        "has_scripts": False,
        "has_references": False,
        "has_assets": False,
        "has_examples": False,
    }


def test_flags_detects_each_shape(tmp_path):
    skill_dir = tmp_path
    skill = skill_dir / "SKILL.md"
    skill.write_text("x", encoding="utf-8")
    (skill_dir / "scripts").mkdir()
    (skill_dir / "references").mkdir()
    (skill_dir / "assets").mkdir()
    (skill_dir / "examples.md").write_text("e", encoding="utf-8")
    (skill_dir / "agents").mkdir()
    (skill_dir / "agents" / "openai.yaml").write_text("x", encoding="utf-8")
    flags = build_catalog.flags(skill)
    assert flags == {
        "has_agents_metadata": True,
        "has_scripts": True,
        "has_references": True,
        "has_assets": True,
        "has_examples": True,
    }


# ---------------------------------------------------------------------------
# skill_mirror_path / skill_agent_ready_path
# ---------------------------------------------------------------------------


def test_skill_mirror_path_layout():
    # skill_mirror_path uses raw slug() (no "&"→"and" substitution), so "&"
    # collapses out of the path.
    path = build_catalog.skill_mirror_path(
        "Science, research & data analysis",
        "latest-release-community",
        "demo-skill",
    )
    assert path == ("included/skills/by-category/science-research-data-analysis/latest-release-community/demo-skill")


def test_skill_agent_ready_path_layout():
    path = build_catalog.skill_agent_ready_path(
        "DevOps, cloud & operations",
        "selected-project-reference",
        "devops-demo",
    )
    assert path == (
        "included/agent-ready/by-category/devops-cloud-operations/selected-project-reference/devops-demo/SKILL.md"
    )

"""Component + property tests for tools/build_catalog.py.

The full ``main()`` writes to repo-relative output paths (``data/``,
``included/``, etc.), so a true end-to-end smoke would risk clobbering the
committed catalog. We instead exercise the individual helpers with real and
synthetic inputs, plus property tests via Hypothesis where applicable. This
covers the riskiest internal logic without redirecting the writer.
"""

from __future__ import annotations

from hypothesis import given, settings, strategies as st

import build_catalog


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


def test_parse_frontmatter_handles_quoted_values_in_fallback():
    # Force the fallback parser by clobbering yaml; helpers strip surrounding quotes.
    saved = build_catalog.yaml
    build_catalog.yaml = None
    try:
        meta, _ = build_catalog.parse_frontmatter('---\nname: "quoted"\n---\nbody\n')
        assert meta == {"name": "quoted"}
    finally:
        build_catalog.yaml = saved


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

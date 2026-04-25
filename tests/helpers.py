"""Shared test helpers for the ai-skills-collection-benchmarked test suite.

Public surface (relied on by other test modules):

- ``ROOT``: absolute :class:`pathlib.Path` pointing at the repository root.
  Discovery walks up from this file's location so it is correct regardless of
  the current working directory the test runner was invoked from.
- ``MIN_SCENARIOS``: minimum number of benchmark scenarios expected per skill.
- ``load(path)``: load a JSON file relative to ``ROOT``. Cached on the relative
  path string so repeated ``load("data/skills_catalog.json")`` calls across
  many parametrized tests do not re-read from disk.
- ``complete_artifacts()``: iterate every real benchmark-run ``artifact.json``
  under ``artifacts/benchmark-runs`` and return ``(path, parsed, result)``
  triples, asserting that each artifact passes ``check_benchmark_artifact``.
- ``assert_unique(items, key)``: assert uniqueness of a projected value and
  return the projected values for convenience.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

import check_benchmark_artifact  # tests/conftest.py puts tools/ on sys.path


def _discover_root() -> Path:
    """Return the repository root by walking up from this file.

    The repository root is identified by the presence of a ``pyproject.toml``
    file so helper callers can invoke tests from any working directory.
    """

    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    # Fall back to the previous "one level above tests/" behavior.
    return here.parents[1]


ROOT = _discover_root()

MIN_SCENARIOS = 3


@cache
def _load_cached(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def load(path):
    """Return the JSON payload at ``ROOT / path``.

    The raw file contents are cached per-path so repeatedly loading the same
    file across a parametrized suite is free after the first call. A fresh
    ``json.loads`` call is returned so callers can safely mutate the result
    without poisoning the cache.
    """

    return json.loads(_load_cached(str(path)))


def complete_artifacts():
    """Yield validated benchmark-run artifacts as ``(path, parsed, result)``.

    Every ``artifact.json`` under ``artifacts/benchmark-runs`` is parsed and
    asserted to pass ``check_benchmark_artifact.validate_artifact``. If the
    directory does not exist (e.g. a minimal clone without real artifacts) an
    empty list is returned.
    """

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
    """Assert uniqueness of ``item[key]`` across ``items`` and return the values."""

    values = [item[key] for item in items]
    assert len(values) == len(set(values))
    return values

"""Logic tests for tools/create_independent_runtime_batch.py pure helpers.

The tool's main() is network-backed (resolves GitHub trees and performs
real git ls-remote calls), so we don't exercise it end-to-end here. Instead
every pure helper + the offline file-based ``check_single_session_entrypoint``
is covered.
"""

from __future__ import annotations

import importlib

import pytest

crib = importlib.import_module("create_independent_runtime_batch")


# ---------------------------------------------------------------------------
# github_repo_from_url
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/owner/repo", ("owner", "repo", None)),
        ("https://github.com/owner/repo.git", ("owner", "repo", None)),
        ("https://github.com/o/r/tree/main/path/to/thing", ("o", "r", "path/to/thing")),
        ("https://github.com/o/r/blob/main/README.md", ("o", "r", "README.md")),
        ("https://github.com/o/r/", ("o", "r", None)),
    ],
)
def test_github_repo_from_url_parses(url, expected):
    assert crib.github_repo_from_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://gitlab.com/o/r",
        "http://github.com/o/r",  # wrong scheme
        "not-a-url",
        "https://github.com/only-owner",
    ],
)
def test_github_repo_from_url_rejects(url):
    assert crib.github_repo_from_url(url) is None


# ---------------------------------------------------------------------------
# first_non_provenance_scenario
# ---------------------------------------------------------------------------


def test_first_non_provenance_scenario_skips_source_skill_repository():
    scenarios = {
        "skill-proof-s1": {"id": "skill-proof-s1", "dataset_track_id": "source-skill-repository"},
        "skill-runtime-s1": {"id": "skill-runtime-s1", "dataset_track_id": "some-other-track"},
    }
    entry = {"id": "s1", "benchmark_scenarios": ["skill-proof-s1", "skill-runtime-s1"]}
    assert crib.first_non_provenance_scenario(entry, scenarios)["id"] == "skill-runtime-s1"


def test_first_non_provenance_scenario_raises_when_all_are_provenance():
    scenarios = {
        "skill-proof-s1": {"id": "skill-proof-s1", "dataset_track_id": "source-skill-repository"},
    }
    entry = {"id": "s1", "benchmark_scenarios": ["skill-proof-s1"]}
    with pytest.raises(ValueError, match="no non-provenance scenario"):
        crib.first_non_provenance_scenario(entry, scenarios)


# ---------------------------------------------------------------------------
# batch_paths
# ---------------------------------------------------------------------------


def test_batch_paths_returns_repo_relative_layout():
    paths = crib.batch_paths("2026-04-18-independent-runtime-readiness-batch-02", "batch-02")
    assert paths["tasks"].as_posix().endswith("benchmarks/independent-runtime-readiness/batch-02/tasks.json")
    assert paths["output"].as_posix().endswith(
        "artifacts/benchmark-runs/2026-04-18-independent-runtime-readiness-batch-02"
    )
    assert paths["report"].as_posix().endswith("docs/runtime-benchmark-batch-02.md")


# ---------------------------------------------------------------------------
# build_task
# ---------------------------------------------------------------------------


def test_build_task_shape_and_determinism():
    entry = {"id": "entry-id"}
    scenario = {"id": "scenario-id", "workflow": ["step one", "step two"]}
    track = {"id": "track-id", "url": "https://example.com/track"}
    a = crib.build_task(entry, scenario, track)
    b = crib.build_task(entry, scenario, track)
    assert a == b
    assert a["task_id"] == "runtime-readiness-entry-id-scenario-id"
    assert a["expected_result"]["all_required_checks_pass"] is True
    assert a["expected_result"]["score_percent"] == 100.0
    assert a["required_checks"] == crib.REQUIRED_CHECKS


# ---------------------------------------------------------------------------
# check_single_session_entrypoint
# ---------------------------------------------------------------------------


def test_check_single_session_entrypoint_true_for_clean_file(tmp_path):
    f = tmp_path / "SKILL.md"
    f.write_text("---\nname: s\ndescription: d\n---\n# body\n", encoding="utf-8")
    assert crib.check_single_session_entrypoint(f) is True


def test_check_single_session_entrypoint_false_for_missing_file(tmp_path):
    assert crib.check_single_session_entrypoint(tmp_path / "nope.md") is False


@pytest.mark.parametrize(
    "snippet",
    [
        "spawn subagent workers in parallel to speed up",
        "use parallel agents to delegate the work",
        "adopt multi-agent orchestration via Task subagents",
    ],
)
def test_check_single_session_entrypoint_flags_delegation_wording(tmp_path, snippet):
    f = tmp_path / "SKILL.md"
    f.write_text(f"---\nname: s\ndescription: d\n---\n# body\n{snippet}\n", encoding="utf-8")
    assert crib.check_single_session_entrypoint(f) is False


# ---------------------------------------------------------------------------
# resolve_dataset_snapshot with monkey-patched network
# ---------------------------------------------------------------------------


def test_resolve_dataset_snapshot_non_github_url_uses_head(monkeypatch):
    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def fake_urlopen(request, timeout=30):  # noqa: ARG001
        return FakeResponse()

    monkeypatch.setattr(crib.urllib.request, "urlopen", fake_urlopen)
    snap, commands = crib.resolve_dataset_snapshot({"id": "t", "url": "https://example.org/data"})
    assert snap["kind"] == "real-url"
    assert snap["resolved"] is True
    assert snap["status"] == 200
    assert commands == []


def test_resolve_dataset_snapshot_github_subpath_reports_resolved(monkeypatch):
    monkeypatch.setattr(
        crib, "run_command",
        lambda cmd, cwd=crib.ROOT: {  # noqa: ARG005
            "command": list(cmd),
            "returncode": 0,
            "stdout": "abc123\tHEAD",
            "stderr": "",
        },
    )
    monkeypatch.setattr(
        crib, "fetch_json",
        lambda url: {"tree": [  # noqa: ARG005
            {"path": "benchmarks/metrics.py"},
            {"path": "benchmarks/README.md"},
            {"path": "LICENSE"},
        ], "truncated": False},
    )
    track = {"id": "t", "url": "https://github.com/ex/repo/tree/main/benchmarks"}
    snap, commands = crib.resolve_dataset_snapshot(track)
    assert snap["kind"] == "real-github-repository-tree"
    assert snap["resolved"] is True
    assert snap["head_sha"] == "abc123"
    assert snap["track_subpath_present"] is True
    assert snap["tree_path_count"] == 3
    assert "benchmarks/metrics.py" in snap["sampled_paths"]
    assert len(commands) == 1


def test_resolve_dataset_snapshot_github_head_fail(monkeypatch):
    monkeypatch.setattr(
        crib, "run_command",
        lambda cmd, cwd=crib.ROOT: {  # noqa: ARG005
            "command": list(cmd), "returncode": 128, "stdout": "", "stderr": "network down",
        },
    )
    snap, commands = crib.resolve_dataset_snapshot({"id": "t", "url": "https://github.com/ex/repo"})
    assert snap["resolved"] is False
    assert snap["head_sha"] == ""
    assert len(commands) == 1

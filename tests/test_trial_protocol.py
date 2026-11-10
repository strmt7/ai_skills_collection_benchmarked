"""Protocol errors must be rejected before a task workspace or model is created."""

from __future__ import annotations

from typing import Any

import pytest
from _trial_collection_policy import default_collection_policy
from _trial_protocol import relative_path, validate_declaration


@pytest.fixture
def protocol() -> dict[str, Any]:
    return {
        "protocol_version": 4,
        "collection_policy": default_collection_policy(),
        "task": {
            "id": "owned-development",
            "partition": "development",
            "brief": "Repair an independently specified behavior.",
            "source_commit": "a" * 40,
            "grader": "tools/grade.py",
            "files": ["src/code.py"],
            "allowed_changes": ["src/code.py"],
        },
        "input_sha256": {"src/code.py": "b" * 64},
        "workspace_scaffold": {"tests/regression.py": ""},
        "prompt_template": "<TASK_BRIEF>\nUse <PYTHON_RUNTIME>.",
        "model": "gpt-6.1-sol",
        "reasoning_effort": "high",
        "time_limit_seconds": 120,
        "limitations": [],
        "conditions": {
            "default": {"skills": []},
            "candidate": {"skills": [{"path": "skills/a.md", "sha256": "c" * 64}]},
        },
        "planned_order": [
            {"repetition": 1, "conditions": ["default", "candidate"]},
            {"repetition": 2, "conditions": ["candidate", "default"]},
        ],
    }


def test_new_file_and_directory_scopes_are_valid_without_precreated_files(protocol):
    protocol["task"]["allowed_changes"] = ["src/", "tests/new.py", "assets/"]
    validate_declaration(protocol)


def test_provider_declaration_is_part_of_the_frozen_plan(protocol):
    protocol["provider"] = {"base_url": "https://model.example.test/v1", "credential_env": "TRIAL_TOKEN"}
    validate_declaration(protocol)
    protocol["provider"]["api_key"] = "fixture-value"
    with pytest.raises(ValueError, match="exactly base_url"):
        validate_declaration(protocol)


@pytest.mark.parametrize("scope", ["src/../outside/", "__pycache__/", "src/.pytest_cache/", "tests//", "tests/\\bad"])
def test_noncanonical_or_excluded_directory_scopes_are_rejected(protocol, scope):
    protocol["task"]["allowed_changes"] = [scope]
    with pytest.raises(ValueError):
        validate_declaration(protocol)


def test_cache_specific_task_must_explicitly_capture_its_cache_directory(protocol):
    protocol["task"]["allowed_changes"] = ["__pycache__/"]
    protocol["collection_policy"]["excluded_directory_names"] = []
    validate_declaration(protocol)


def test_matched_declaration_is_data_only(protocol, monkeypatch):
    import subprocess

    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: pytest.fail("unexpected process"))
    validate_declaration(protocol, "candidate")


def test_declared_scaffolding_and_new_file_scopes_are_admitted(protocol):
    protocol["task"]["allowed_changes"].append("tests/regression.py")
    validate_declaration(protocol)
    protocol["task"]["allowed_changes"].append("undeclared.py")
    validate_declaration(protocol)
    protocol["task"]["allowed_changes"].append("../outside.py")
    with pytest.raises(ValueError, match="relative POSIX"):
        validate_declaration(protocol)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("protocol_version", 5),
        ("protocol_version", True),
        ("task", {}),
        ("task", []),
        ("input_sha256", {"src/code.py": "invalid"}),
        ("model", ""),
        ("model", "model\nsetting"),
        ("reasoning_effort", None),
        ("reasoning_effort", "unsupported"),
        ("time_limit_seconds", True),
        ("time_limit_seconds", 0),
        ("time_limit_seconds", 1.5),
        ("limitations", "not a list"),
        ("limitations", [None]),
        ("prompt_template", "Missing placeholders"),
        ("prompt_template", "<TASK_BRIEF><TASK_BRIEF><PYTHON_RUNTIME>"),
        ("conditions", {}),
        ("conditions", {"default": []}),
        ("conditions", {"default": {"skills": "unhashed"}}),
        ("conditions", {"candidate": {"skills": []}}),
        ("conditions", {"default": {"skills": [{"path": "skill.md", "sha256": "a" * 64}]}}),
        ("conditions", {"default": {"skills": []}, "../escape": {"skills": []}}),
        ("planned_order", []),
        ("planned_order", [None]),
        ("planned_order", [{"repetition": True, "conditions": ["default", "candidate"]}]),
        ("planned_order", [{"repetition": 1, "conditions": ["default", "default"]}]),
        ("planned_order", [{"repetition": 1, "conditions": ["default", []]}]),
    ],
)
def test_invalid_declarations_raise_value_error(protocol, field, value):
    protocol[field] = value
    with pytest.raises(ValueError):
        validate_declaration(protocol)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("partition", []),
        ("id", "../escape"),
        ("source_commit", "main"),
        ("grader", "."),
        ("allowed_changes", ["../outside.py"]),
        ("allowed_changes", [[], "src/code.py"]),
    ],
)
def test_invalid_task_fields_are_rejected(protocol, field, value):
    protocol["task"][field] = value
    with pytest.raises(ValueError):
        validate_declaration(protocol)


@pytest.mark.parametrize(
    "path",
    [
        ".",
        "..",
        "../escape",
        "/absolute",
        "C:/absolute",
        "a\\b",
        "a//b",
        "a/./b",
        "a/../b",
        "a/",
        "a:stream",
        "NUL.txt",
        "COM¹.txt",
        "CON .txt",
        "a/b.",
        "a/b ",
        "a/\x00b",
        "a/*.py",
    ],
)
def test_noncanonical_or_ambiguous_paths_are_rejected(path):
    with pytest.raises(ValueError):
        relative_path(path)


@pytest.mark.parametrize(
    "path", [".trial-profile/temp.txt", "AGENTS.md", ".Agents/skills/a.md", ".codex/config.toml", ".git/config"]
)
def test_workspace_cannot_inject_automatic_context(protocol, path):
    protocol["workspace_scaffold"] = {path: "owned marker"}
    with pytest.raises(ValueError, match="context or profiles"):
        validate_declaration(protocol)


@pytest.mark.parametrize("scaffold", [{"SRC/code.py": ""}, {"src": ""}, {"src/code.py/nested": ""}])
def test_workspace_file_identity_collisions_are_rejected(protocol, scaffold):
    protocol["workspace_scaffold"] = scaffold
    with pytest.raises(ValueError, match="identit|descendant"):
        validate_declaration(protocol)


@pytest.mark.parametrize(
    "skills",
    [
        [None],
        [{"path": "skill.md", "sha256": "x" * 64}],
        [{"path": "a.md", "sha256": "c" * 64}, {"path": "A.md", "sha256": "c" * 64}],
    ],
)
def test_condition_skills_require_distinct_paths_and_exact_hashes(protocol, skills):
    protocol["conditions"]["candidate"]["skills"] = skills
    with pytest.raises(ValueError):
        validate_declaration(protocol)


def test_unknown_condition_and_duplicate_repetition_cannot_start_trials(protocol):
    with pytest.raises(ValueError, match="requested condition"):
        validate_declaration(protocol, "undeclared")
    protocol["planned_order"][1]["repetition"] = 1
    with pytest.raises(ValueError, match="distinct positive repetition"):
        validate_declaration(protocol)

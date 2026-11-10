from __future__ import annotations

import json
import os
import tomllib
from dataclasses import replace
from pathlib import Path

import _trial_context as context
import pytest


@pytest.fixture
def paths(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    cli, python = runtime / "codex.exe", runtime / "python.exe"
    cli.write_bytes(b"owned CLI fixture")
    python.write_bytes(b"owned Python fixture")
    parent = {
        "SystemRoot": str(tmp_path / "system"),
        "WINDIR": str(tmp_path / "system"),
        "COMSPEC": str(tmp_path / "system/cmd.exe"),
        "PATHEXT": ".EXE;.CMD",
        "SystemDrive": tmp_path.anchor,
        "PATH": "unrelated-personal-bin",
        "PARENT_CANARY": "must stay in the controller's parent",
    }
    return tmp_path / "controller", workspace, cli, python, (runtime,), parent


def create(paths):
    home, workspace, cli, python, roots, parent = paths
    return context.create_context(home, workspace, cli, python, roots, parent=parent)


def test_controller_reservation_uses_the_os_temporary_location_outside_a_deep_checkout(tmp_path, monkeypatch):
    checkout = tmp_path / "deep/checkout"
    checkout.mkdir(parents=True)
    system_temporary = tmp_path / "os-temporary"
    system_temporary.mkdir()
    monkeypatch.chdir(checkout)
    monkeypatch.setattr(context.tempfile, "tempdir", str(system_temporary))
    first, second = context.temporary_home(), context.temporary_home()
    assert first != second and first.parent.is_dir() and second.parent.is_dir()
    assert not first.exists() and not second.exists()
    assert first.is_relative_to(system_temporary) and second.is_relative_to(system_temporary)
    assert not first.is_relative_to(Path.cwd())


def test_private_context_has_separate_empty_profiles_and_no_parent_state(paths):
    value = create(paths)
    assert "PARENT_CANARY" not in value.controller_environment
    assert "unrelated-personal-bin" not in value.controller_environment["PATH"]
    assert "CODEX_HOME" not in value.tool_environment
    assert value.controller_environment["CODEX_HOME"] == str(value.home / "profile")
    assert not (value.home / "profile/AGENTS.md").exists()
    assert not (value.home / "profile/config.toml").exists()
    assert value.tool_environment["HOME"] == str(value.workspace / ".trial-profile/profile")
    assert value.tool_environment["PYTHONNOUSERSITE"] == "1"
    assert os.pathsep.join([str(value.python.parent), str(value.cli.parent)]) in value.tool_environment["PATH"]


def test_permission_and_context_settings_are_valid_toml_and_explicit(paths):
    value = create(paths)
    args = context.options(value, "gpt-6.1-sol", "high")
    settings = {}
    for option, text in zip(args[::2], args[1::2], strict=True):
        assert option == "-c"
        key, raw = text.split("=", 1)
        settings[key] = tomllib.loads("value=" + raw)["value"]
    assert settings["default_permissions"] == "trial"
    assert settings["windows.sandbox"] == "mxc"
    assert settings["permissions.trial.network.enabled"] is False
    assert settings["permissions.trial.filesystem"][":minimal"] == "read"
    assert settings["permissions.trial.filesystem"][str(value.readable_roots[0])] == "read"
    assert settings["shell_environment_policy.set"] == value.tool_environment
    assert settings["shell_environment_policy.inherit"] == "none"
    assert settings["project_doc_max_bytes"] == 0
    assert settings["skills.include_instructions"] is False
    assert settings["skills.bundled.enabled"] is False
    assert settings["tools.experimental_request_user_input.enabled"] is False
    assert all(settings[f"features.{name}"] is False for name in context.DISABLED_FEATURES)
    assert settings["features.multi_agent_v2.enabled"] is False
    assert settings["features.multi_agent_v2.disable_native_tools"] is True
    command = context.command(value, "gpt-6.1-sol", "high")
    assert "--ignore-user-config" in command and "--ephemeral" in command
    assert "--sandbox" not in command
    assert not any("bypass" in argument or "ignore-rules" in argument for argument in command)


@pytest.mark.parametrize("problem", ["existing", "reserved", "overlap", "broad", "uncovered", "environment"])
def test_invalid_context_is_rejected_before_creating_controller_state(paths, problem):
    home, workspace, cli, python, roots, parent = paths
    if problem == "existing":
        home.mkdir()
        (home / "sentinel").write_text("existing state", encoding="utf-8")
    elif problem == "reserved":
        (workspace / ".trial-profile").mkdir()
    elif problem == "overlap":
        home = workspace / "controller"
    elif problem == "broad":
        roots = (workspace.parent,)
    elif problem == "uncovered":
        roots = (cli.parent / "other",)
        roots[0].mkdir()
    elif problem == "environment":
        parent.pop("SystemDrive")
    with pytest.raises(ValueError):
        context.create_context(home, workspace, cli, python, roots, parent=parent)
    if problem == "existing":
        assert (home / "sentinel").read_text(encoding="utf-8") == "existing state"
    else:
        assert not home.exists()


def test_invalid_model_settings_are_rejected(paths):
    value = create(paths)
    for model, effort in [("", "high"), ("model\0suffix", "high"), ("gpt-6.1-sol", "invented")]:
        with pytest.raises(ValueError):
            context.options(value, model, effort)


def test_launch_command_survives_sorted_json_environment_round_trip(paths):
    value = create(paths)
    restored = replace(value, tool_environment=json.loads(json.dumps(value.tool_environment, sort_keys=True)))
    original_command = context.command(value, "fixture-model", "high")
    assert context.command(restored, "fixture-model", "high") == original_command
    changed = replace(restored, tool_environment={**restored.tool_environment, "PATH": "different-runtime"})
    assert context.command(changed, "fixture-model", "high") != original_command

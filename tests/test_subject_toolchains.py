"""Native commands must stay bound to complete payloads, including scripts and empty directories."""

from __future__ import annotations

import json
import runpy
import subprocess
import sys
from pathlib import Path

import _subject_toolchains as toolchains
import pytest
from _native_benchmark_runtime import sha256


def frozen_payload(tmp_path: Path) -> tuple[Path, dict]:
    root = tmp_path / "owned tool payload"
    (root / "pnpm/bin").mkdir(parents=True)
    (root / "empty").mkdir()
    files = {"node.exe": b"native runtime fixture", "pnpm/bin/pnpm.cjs": b"script fixture", "LICENSE": b"license"}
    for name, content in files.items():
        (root / name).write_bytes(content)
    return root, {
        "schema_version": 1,
        "toolchains": [
            {
                "name": "node-pnpm",
                "version": "26.13.1",
                "root": str(root),
                "files": {name: {"bytes": len(data), "sha256": sha256(data)} for name, data in files.items()},
                "directories": ["empty", "pnpm", "pnpm/bin"],
                "commands": {"node": ["node.exe"], "pnpm": ["node.exe", "pnpm/bin/pnpm.cjs"]},
            }
        ],
    }


def admit(tmp_path: Path, value: dict) -> toolchains.NativeToolchains:
    raw = json.dumps(value).encode()
    location = tmp_path / "toolchains.json"
    location.write_bytes(raw)
    return toolchains.load_toolchains({"path": str(location), "sha256": sha256(raw)})


def prepare_workspace(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "task workspace"
    temporary = workspace / ".trial-profile/temporary"
    temporary.mkdir(parents=True)
    return workspace, temporary


def test_launcher_preserves_prefix_arguments_and_child_exit(tmp_path, monkeypatch):
    root, value = frozen_payload(tmp_path)
    admitted = admit(tmp_path, value)
    assert admitted.roots() == (root,)
    workspace, temporary = prepare_workspace(tmp_path)
    prepared = admitted.prepare(workspace, Path(sys.executable), temporary)
    assert prepared is not None
    assert "Available native tools: node, pnpm" in prepared.instructions
    assert str(prepared.launcher) in prepared.instructions

    def child(arguments, *, env, check):
        assert arguments == [str(root / "node.exe"), str(root / "pnpm/bin/pnpm.cjs"), "test", "", "owner's value"]
        assert env["TEMP"] == env["TMP"] == str(temporary)
        assert env["LAUNCH_FIXTURE"] == "preserved"
        assert check is False
        return subprocess.CompletedProcess(arguments, 7)

    monkeypatch.setenv("LAUNCH_FIXTURE", "preserved")
    monkeypatch.setattr(subprocess, "run", child)
    monkeypatch.setattr(sys, "argv", [str(prepared.launcher), "pnpm", "test", "", "owner's value"])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(prepared.launcher), run_name="__main__")
    assert error.value.code == 7
    admitted.verify()
    prepared.verify()


def test_go_uses_bound_proxy_and_private_directories(tmp_path, monkeypatch):
    root, value = frozen_payload(tmp_path)
    payload = value["toolchains"][0]
    payload.update(name="go", commands={"go": ["node.exe"]})
    proxy = tmp_path / "module proxy's inputs"
    proxy.mkdir()
    (proxy / "data").write_bytes(b"frozen dependency")
    value["toolchains"].append(
        {
            "name": "go-module-proxy",
            "version": "1",
            "root": str(proxy),
            "files": {"data": {"bytes": 17, "sha256": sha256(b"frozen dependency")}},
            "directories": [],
            "commands": {},
        }
    )
    workspace, temporary = prepare_workspace(tmp_path)
    launcher = admit(tmp_path, value).prepare(workspace, Path(sys.executable), temporary)
    assert launcher is not None
    assert "go test ./..." in launcher.instructions

    def child(arguments, *, env, check):
        assert arguments == [str(root / "node.exe"), "test", "./..."]
        assert env["GOPROXY"] == proxy.as_uri()
        assert env["GOTMPDIR"] == env["TMP"] == env["TEMP"] == str(temporary)
        assert Path(env["GOCACHE"]).is_relative_to(workspace / ".trial-profile")
        assert Path(env["GOMODCACHE"]).is_relative_to(workspace / ".trial-profile")
        assert env["GOTOOLCHAIN"] == "local"
        assert env["GOSUMDB"] == "sum.golang.org"
        return subprocess.CompletedProcess(arguments, 0)

    monkeypatch.setenv("GOSUMDB", "sum.golang.org")
    monkeypatch.setattr(subprocess, "run", child)
    monkeypatch.setattr(sys, "argv", [str(launcher.launcher), "go", "test", "./..."])
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(launcher.launcher), run_name="__main__")
    assert error.value.code == 0
    launcher.launcher.write_bytes(b"changed runtime launcher")
    with pytest.raises(ValueError, match="launcher changed"):
        launcher.verify()


@pytest.mark.parametrize("mutation", ["contents", "size", "missing", "new-file", "new-directory", "missing-empty"])
def test_changes_after_admission_cannot_be_accepted(tmp_path, mutation):
    root, value = frozen_payload(tmp_path)
    admitted = admit(tmp_path, value)
    if mutation == "contents":
        (root / "node.exe").write_bytes(b"x" * (root / "node.exe").stat().st_size)
    elif mutation == "size":
        (root / "node.exe").write_bytes(b"short")
    elif mutation == "missing":
        (root / "pnpm/bin/pnpm.cjs").unlink()
    elif mutation == "new-file":
        (root / "unlisted.exe").write_bytes(b"unlisted")
    elif mutation == "new-directory":
        (root / "unlisted").mkdir()
    else:
        (root / "empty").rmdir()
    with pytest.raises(ValueError):
        admitted.verify()


@pytest.mark.parametrize(
    "mutation",
    [
        "version",
        "schema",
        "unknown",
        "relative-root",
        "case-collision",
        "parent-path",
        "undeclared-command",
        "empty-prefix",
        "boolean-size",
        "digest",
        "file-directory",
        "duplicate-command",
    ],
)
def test_incomplete_or_ambiguous_declarations_fail_before_launch(tmp_path, mutation):
    root, value = frozen_payload(tmp_path)
    item = value["toolchains"][0]
    if mutation == "version":
        item["version"] = "not a bounded version"
    elif mutation == "schema":
        value["schema_version"] = True
    elif mutation == "unknown":
        item["ambient_path"] = True
    elif mutation == "relative-root":
        item["root"] = "relative"
    elif mutation == "case-collision":
        item["files"]["NODE.exe"] = item["files"]["node.exe"]
    elif mutation == "parent-path":
        item["files"]["../outside"] = item["files"]["node.exe"]
    elif mutation == "undeclared-command":
        item["commands"]["node"] = ["unlisted.exe"]
    elif mutation == "empty-prefix":
        item["commands"]["node"] = []
    elif mutation == "boolean-size":
        item["files"]["node.exe"]["bytes"] = True
    elif mutation == "digest":
        item["files"]["node.exe"]["sha256"] = "0" * 64
    elif mutation == "file-directory":
        item["directories"].append("node.exe")
    else:
        second = json.loads(json.dumps(item))
        second.update(name="second", root=str(root.parent / "second"))
        value["toolchains"].append(second)
    with pytest.raises(ValueError):
        admit(tmp_path, value)


def test_manifest_is_reverified_when_preparing_the_launcher(tmp_path):
    _, value = frozen_payload(tmp_path)
    admitted = admit(tmp_path, value)
    workspace, temporary = prepare_workspace(tmp_path)
    Path(admitted.location).write_bytes(b"changed declaration")
    with pytest.raises(ValueError):
        admitted.prepare(workspace, Path(sys.executable), temporary)


@pytest.mark.parametrize("budget", ["entries", "bytes"])
def test_combined_payloads_cannot_multiply_resource_limits(tmp_path, monkeypatch, budget):
    _, value = frozen_payload(tmp_path)
    _, second = frozen_payload(tmp_path / "second")
    second["toolchains"][0].update(name="other", commands={"other": ["node.exe"]})
    value["toolchains"].extend(second["toolchains"])
    if budget == "entries":
        monkeypatch.setattr(toolchains, "MAX_ENTRIES", 8)
    else:
        monkeypatch.setattr(toolchains, "MAX_BYTES", 60)
    with pytest.raises(ValueError, match="Combined"):
        admit(tmp_path, value)


def test_frozen_dependency_data_have_a_mount_without_an_executable_prefix(tmp_path):
    root, value = frozen_payload(tmp_path)
    value["toolchains"][0]["commands"] = {}
    admitted = admit(tmp_path, value)
    assert admitted.roots() == (root,)
    workspace, temporary = prepare_workspace(tmp_path)
    assert admitted.prepare(workspace, Path(sys.executable), temporary) is None
    (root / "pnpm/bin/pnpm.cjs").write_bytes(b"changed frozen dependency")
    with pytest.raises(ValueError):
        admitted.verify()

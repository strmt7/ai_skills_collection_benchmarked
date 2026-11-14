"""Native commands must stay bound to complete payloads, including scripts and empty directories."""

from __future__ import annotations

import json
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


def test_explicit_command_prefixes_cover_native_and_script_tools(tmp_path):
    root, value = frozen_payload(tmp_path)
    admitted = admit(tmp_path, value)
    assert admitted.roots() == (root,)
    instructions = admitted.instructions()
    commands = json.loads(instructions[instructions.index("{") :])
    assert commands == {
        "node": [str(root / "node.exe")],
        "pnpm": [str(root / "node.exe"), str(root / "pnpm/bin/pnpm.cjs")],
    }
    admitted.verify()


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


def test_manifest_is_reverified_when_producing_command_instructions(tmp_path):
    _, value = frozen_payload(tmp_path)
    admitted = admit(tmp_path, value)
    Path(admitted.location).write_bytes(b"changed declaration")
    with pytest.raises(ValueError):
        admitted.instructions()


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

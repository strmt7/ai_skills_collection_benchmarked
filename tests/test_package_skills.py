from __future__ import annotations

import hashlib
import json
import os
import subprocess
import zipfile
from pathlib import Path
from typing import Any

import package_skills
import pytest
import yaml

ENTRY: dict[str, Any] = {
    "id": "example-skill",
    "name": "Example skill",
    "description": "Check a portable output package.",
    "category": "Engineering",
    "install_name": "example-skill",
    "mirrored_path": "included/skills/by-category/engineering/reference/example-skill",
    "source_path": "skills/example/SKILL.md",
    "source_repo": "example/project",
    "commit_sha": "a" * 40,
    "selected_ref": "v1",
    "immutable_source_url": "https://github.com/example/project/blob/" + "a" * 40 + "/skills/example/SKILL.md",
    "skill_file_sha256": "b" * 64,
    "skill_dir_sha256": "c" * 64,
    "benchmark_scenarios": ["fixture"],
    "benchmark_status": "artifact_gated",
}


@pytest.fixture
def published_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "collection"
    root.mkdir()
    for name in list(os.environ):
        if name.startswith("GIT_"):
            monkeypatch.delenv(name)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)

    def git(*arguments: str) -> None:
        subprocess.run(
            [
                "git",
                "-c",
                "core.longpaths=true",
                "-c",
                "core.autocrlf=false",
                "-c",
                "commit.gpgsign=false",
                "-C",
                str(root),
                *arguments,
            ],
            check=True,
            capture_output=True,
            timeout=20,
        )

    def place(name: str, data: bytes) -> None:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    git("init", "-q", "--initial-branch=main")
    git("config", "--local", "core.autocrlf", "true")
    git("config", "--local", "core.hooksPath", str(tmp_path / "no-hooks"))
    for name in package_skills.RUNTIME_PATHS:
        place(name, b"locked fixture\n")
    place(
        ENTRY["mirrored_path"] + "/SKILL.md",
        b"---\nname: example-skill\ndescription: Check a portable output package.\n---\n",
    )
    place(ENTRY["mirrored_path"] + "/scripts/run.sh", b"#!/bin/sh\nexit 0\n")
    notice = "artifacts/source-notices/example/LICENSE"
    notice_bytes = b"Recorded upstream notice\n"
    place(notice, notice_bytes)
    place("data/skills_catalog.json", json.dumps([ENTRY]).encode())
    place(
        "data/source_lock.json",
        json.dumps(
            {
                "sources": [
                    {
                        "repo": ENTRY["source_repo"],
                        "commit_sha": ENTRY["commit_sha"],
                        "selected_ref": ENTRY["selected_ref"],
                        "skills": [ENTRY],
                        "preserved_notice": {
                            "commit_sha": ENTRY["commit_sha"],
                            "path": notice,
                            "sha256": hashlib.sha256(notice_bytes).hexdigest(),
                        },
                    }
                ]
            },
        ).encode(),
    )
    git("add", "--all")
    git("update-index", "--chmod=+x", "--", ENTRY["mirrored_path"] + "/scripts/run.sh")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "package fixture")
    (root / ENTRY["mirrored_path"] / "SKILL.md").write_bytes(b"private draft\n")
    (root / ENTRY["mirrored_path"] / "untracked.txt").write_text("local scratch", encoding="utf-8")
    return root


def test_export_uses_lock_and_resolves_all_delivered_routes(published_source: Path, tmp_path: Path) -> None:
    first, second = tmp_path / "one.zip", tmp_path / "another path.zip"
    report = package_skills.export(published_source, ["example-skill"], first)
    assert package_skills.export(published_source, ["example-skill"], second) == report
    assert first.read_bytes() == second.read_bytes()
    assert package_skills.verify(first) == report
    with zipfile.ZipFile(first) as package:
        manifest = json.loads(package.read("package-manifest.json"))
        [skill] = manifest["skills"]
        assert skill["source_entrypoint"] == "sources/example-skill/SKILL.md"
        assert package.read(skill["source_entrypoint"]).startswith(b"---\n")
        assert not any(name.endswith("untracked.txt") for name in package.namelist())
        assert package.read(skill["source_notice"]) == b"Recorded upstream notice\n"
        script = "sources/example-skill/scripts/run.sh"
        assert package.getinfo(script).external_attr >> 16 == 0o100755
        assert manifest["files"][script]["mode"] == "100755"
        scratch = tmp_path / "detached"
        package.extractall(scratch)
    entry = scratch / skill["entrypoint"]
    text = entry.read_text(encoding="utf-8")
    header = yaml.safe_load(text.split("---\n", 2)[1])
    assert header["name"] == entry.parent.name
    assert (entry.parent / header["metadata"]["source_mirror"]).samefile(scratch / skill["source_entrypoint"])
    assert "../../../docs/agent-tools.md" in text and "../../../docs/benchmark-results.md" in text
    assert (scratch / "docs/agent-tools.md").is_file() and (scratch / "docs/benchmark-results.md").is_file()
    assert list((entry.parent).rglob("SKILL.md")) == [entry]


@pytest.mark.parametrize("defect", ["bad-digest", "missing-runtime"])
def test_verify_requires_exact_contents_and_runtime(published_source: Path, tmp_path: Path, defect: str) -> None:
    clean, changed = tmp_path / "clean.zip", tmp_path / "changed.zip"
    package_skills.export(published_source, ["example-skill"], clean)
    with zipfile.ZipFile(clean) as original, zipfile.ZipFile(changed, "x") as replacement:
        metadata: dict[str, Any] = json.loads(original.read(package_skills.MANIFEST))
        removed = "toolchains/bootstrap/NativeSupervisor.dll" if defect == "missing-runtime" else None
        if removed:
            del metadata["files"][removed]
        for item in original.infolist():
            if item.filename == removed:
                continue
            data = original.read(item)
            if item.filename == package_skills.MANIFEST:
                data = json.dumps(metadata).encode()
            elif defect == "bad-digest" and item.filename == "docs/agent-tools.md":
                data = b"x" + data[1:]
            replacement.writestr(item, data)
    error = "required runtime" if removed else "file digest differs"
    with pytest.raises(ValueError, match=error):
        package_skills.verify(changed)


def test_failed_export_leaves_existing_user_files_untouched(published_source: Path, tmp_path: Path) -> None:
    missing = tmp_path / "missing.zip"
    with pytest.raises(ValueError, match="catalog entry"):
        package_skills.export(published_source, ["unknown"], missing)
    assert not missing.exists() and not list(tmp_path.glob(".skill-package-*"))
    existing = tmp_path / "original.zip"
    existing.write_bytes(b"user content")
    with pytest.raises(ValueError, match="new .zip"):
        package_skills.export(published_source, ["example-skill"], existing)
    assert existing.read_bytes() == b"user content"


@pytest.mark.parametrize("paths", [("Readme", "README"), ("Tools/a", "tools/b"), ("a", "A/b")])
def test_installed_names_preserve_portable_path_identity(paths: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="paths collide|paths overlap"):
        package_skills.portable_inventory(paths)

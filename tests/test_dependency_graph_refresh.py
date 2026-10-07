"""Complete graph publication preserves original skills and rejects tampering."""

from __future__ import annotations

import hashlib
import json
import subprocess

import _catalog_publication as publication
import build_catalog as catalog
import pytest
import refresh_dependency_graph as refresh
from _lib_b import dependency_graphs
from refresh_credential_policy import METADATA


def git(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


@pytest.fixture
def fixture(tmp_path):
    root, sources = tmp_path / "workspace", tmp_path / "sources"
    checkout = sources / "public-source"
    source = checkout / "skill"
    source.mkdir(parents=True)
    git(checkout, "init", "-q")
    git(checkout, "remote", "add", "origin", "https://github.com/example/public-source")
    (source / "SKILL.md").write_text("---\nname: fixture\ndescription: Independent fixture.\n---\n")
    package = {"name": "fixture", "dependencies": {"fixture": "^1.0.0"}}
    lock = {
        "lockfileVersion": 3,
        "packages": {"": {"dependencies": package["dependencies"]}, "node_modules/fixture": {"version": "1.0.0"}},
    }
    catalog.write_json(source / "package.json", package)
    catalog.write_json(source / "package-lock.json", lock)
    git(checkout, "add", ".")
    git(checkout, "-c", "user.name=AI agent", "-c", "user.email=", "commit", "-qm", "Owned source fixture")
    modes = catalog.skill_file_modes(source)
    tree = catalog.sha256_tree(source, file_modes=modes)
    entry = {
        "id": "fixture",
        "source_repo": "example/public-source",
        "commit_sha": git(checkout, "rev-parse", "HEAD"),
        "source_path": "skill/SKILL.md",
        "mirrored_path": "included/skills/fixture",
        "skill_file_sha256": catalog.sha256_file(source / "SKILL.md"),
        "skill_dir_sha256": tree,
        "file_modes": modes,
    }
    catalog.copy_sanitized_tree(source, root / entry["mirrored_path"], file_modes=modes)
    source_record = {
        "repo": entry["source_repo"],
        "local_dir": "public-source",
        "commit_sha": entry["commit_sha"],
        "tree_sha": git(checkout, "rev-parse", "HEAD^{tree}"),
        "skills": [dict(entry)],
    }
    for relative, value in zip(METADATA, [[entry], {"sources": [source_record]}, [entry], [entry]], strict=True):
        catalog.write_json(root / relative, value)
    new_package = {**package, "dependencies": {"fixture": "^1.1.0"}}
    new_lock = {
        "lockfileVersion": 3,
        "packages": {
            "": {"dependencies": new_package["dependencies"]},
            "node_modules/fixture": {"version": "1.1.0", "license": "MIT"},
        },
    }
    files = {}
    for name, value in (("package.json", new_package), ("package-lock.json", new_lock)):
        destination = root / "graphs" / name
        catalog.write_json(destination, value)
        files[name] = {
            "source_sha256": hashlib.sha256((source / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            "replacement_path": destination.relative_to(root).as_posix(),
            "replacement_sha256": hashlib.sha256(destination.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        }
    graph = {
        "id": "fixture-floor",
        "source_repo": entry["source_repo"],
        "source_commit": entry["commit_sha"],
        "source_path": entry["source_path"],
        "source_tree_sha256": tree,
        "previous_mirror_sha256": tree,
        "direct_floors": {"fixture": "^1.1.0"},
        "files": files,
    }
    catalog.write_json(root / "data/dependency_graphs.json", {"graphs": [graph]})
    return root, sources, checkout, source, entry, graph


def test_stage_publish_replay_and_plain_hashing(fixture):
    root, sources, checkout, source, entry, graph = fixture
    original = publication.signature(checkout)
    old_skill = (root / entry["mirrored_path"] / "SKILL.md").read_bytes()
    before = publication.signature(root / entry["mirrored_path"])
    stage, journal, count = refresh.prepare(root, sources, "fixture", "artifacts/refresh.json")
    assert count == 1
    assert publication.signature(root / entry["mirrored_path"]) == before
    publication.publish(root, stage, journal)
    assert publication.signature(checkout) == original
    assert (root / entry["mirrored_path"] / "SKILL.md").read_bytes() == old_skill
    assert catalog.sha256_tree(source, file_modes=entry["file_modes"]) == graph["source_tree_sha256"]
    for relative in METADATA:
        values = json.loads((root / relative).read_bytes())
        records = values["sources"][0]["skills"] if relative == METADATA[1] else values
        assert records[0]["dependency_graph"] == graph["id"]
        assert records[0]["skill_dir_sha256"] == catalog.sha256_tree(
            root / entry["mirrored_path"], file_modes=entry["file_modes"]
        )
        replacements = dependency_graphs.for_entry({**entry, **records[0]}, source, root=root)
        assert records[0]["skill_dir_sha256"] == catalog.sha256_tree(
            source, file_modes=entry["file_modes"], replacements=replacements
        )
    assert refresh.prepare(root, sources, "fixture", "artifacts/refresh.json")[2] == 0


@pytest.mark.parametrize("tamper", ["mirror", "source", "graph", "declaration", "pair", "identity", "receipt", "lock"])
def test_invalid_input_never_publishes(fixture, tamper):
    root, sources, checkout, source, entry, graph = fixture
    if tamper == "mirror":
        (root / entry["mirrored_path"] / "SKILL.md").write_text("changed")
    elif tamper == "source":
        (source / "SKILL.md").write_text("changed")
    elif tamper == "identity":
        git(checkout, "remote", "set-url", "origin", "https://github.com/example/different")
    elif tamper == "receipt":
        catalog.write_json(root / "artifacts/refresh.json", {"preserve": True})
    elif tamper == "lock":
        data = json.loads((root / METADATA[1]).read_bytes())
        data["sources"][0]["skills"][0]["skill_dir_sha256"] = "0" * 64
        catalog.write_json(root / METADATA[1], data)
    else:
        name = "package-lock.json" if tamper == "pair" else "package.json"
        destination = root / "graphs" / name
        value = json.loads(destination.read_bytes())
        if tamper == "pair":
            value["packages"][""]["dependencies"] = {"fixture": "^2.0.0"}
        else:
            value["name"] = "unrelated rename"
        catalog.write_json(destination, value)
        if tamper != "graph":
            graph["files"][name]["replacement_sha256"] = hashlib.sha256(
                destination.read_bytes().replace(b"\r\n", b"\n")
            ).hexdigest()
            catalog.write_json(root / "data/dependency_graphs.json", {"graphs": [graph]})
    before = publication.signature(root)
    with pytest.raises(ValueError):
        refresh.prepare(root, sources, "fixture", "artifacts/refresh.json")
    assert publication.signature(root) == before


def test_unlisted_resources_fail_before_copy(fixture, tmp_path):
    _, _, _, source, _, _ = fixture
    with pytest.raises(ValueError, match="absent"):
        catalog.copy_sanitized_tree(source, tmp_path / "output", replacements={"absent": b"content"})
    assert not (tmp_path / "output").exists()


def test_unknown_graph_metadata_fails(fixture):
    root, _, _, source, entry, _ = fixture
    with pytest.raises(ValueError, match="metadata"):
        dependency_graphs.for_entry({**entry, "dependency_graph": "unknown"}, source, root=root)

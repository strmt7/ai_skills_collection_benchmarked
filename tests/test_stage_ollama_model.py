from __future__ import annotations

import hashlib
import json
import os

import pytest
from stage_ollama_model import stage_model


@pytest.fixture
def upstream_model(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    descriptors = []
    for data in (b"model configuration", b"weight layer"):
        sha = hashlib.sha256(data).hexdigest()
        (source / ("sha256-" + sha)).write_bytes(data)
        descriptors.append({"digest": "sha256:" + sha, "size": len(data)})
    raw = (json.dumps({"schemaVersion": 2, "config": descriptors[0], "layers": [descriptors[1]]}) + "\n").encode()
    manifest = tmp_path / "manifest.json"
    manifest.write_bytes(raw)
    return source, manifest, hashlib.sha256(raw).hexdigest()


def test_stages_exact_content_without_shared_file_identity(tmp_path, upstream_model):
    source, manifest, sha = upstream_model
    output = tmp_path / "staged"
    record = stage_model("qwen3:4b", manifest, sha, source, output)
    assert record["storage"] == "independent_copies"
    assert (output / "manifests/registry.ollama.ai/library/qwen3/4b").read_bytes() == manifest.read_bytes()
    for original in source.iterdir():
        copied = output / "blobs" / original.name
        assert not os.path.samefile(original, copied)
        frozen = original.read_bytes()
        assert copied.read_bytes() == frozen
        copied.write_bytes(b"private rewrite")
        assert original.read_bytes() == frozen


def test_failed_integrity_check_leaves_no_partial_store(tmp_path, upstream_model):
    source, manifest, sha = upstream_model
    output = tmp_path / "staged"
    blob = next(source.iterdir())
    blob.write_bytes(b"x" * blob.stat().st_size)
    with pytest.raises(ValueError, match="frozen identity"):
        stage_model("qwen3:4b", manifest, sha, source, output)
    assert not output.exists()


def test_existing_store_is_preserved(tmp_path, upstream_model):
    source, manifest, sha = upstream_model
    output = tmp_path / "staged"
    output.mkdir()
    sentinel = output / "keep.txt"
    sentinel.write_bytes(b"other existing store")
    with pytest.raises(FileExistsError):
        stage_model("qwen3:4b", manifest, sha, source, output)
    assert list(output.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"other existing store"


@pytest.mark.parametrize("model", ["qwen3", "qwen3:..", "qwen3:nul.txt", "con:4b", "qwen3:4b."])
def test_invalid_windows_model_components_fail_before_staging(tmp_path, upstream_model, model):
    source, manifest, sha = upstream_model
    output = tmp_path / "staged"
    with pytest.raises(ValueError):
        stage_model(model, manifest, sha, source, output)
    assert not output.exists()

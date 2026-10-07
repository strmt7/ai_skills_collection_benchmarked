"""Catalog hashing cannot manufacture dependency security fixes."""

from __future__ import annotations

import hashlib
import json

import build_catalog as catalog
import pytest


@pytest.mark.parametrize("version", ["1.1.12", "2.0.2", "2.1.0", "2.1.7", "5.0.0", "2.2.0-rc.1"])
def test_lockfile_resolutions_and_graph_preserved(tmp_path, version):
    data = {
        "lockfileVersion": 3,
        "packages": {
            "": {"dependencies": {"fixture": "^1.0.0"}},
            "node_modules/brace-expansion": {
                "version": version,
                "resolved": "https://example.invalid/fixture.tgz",
                "integrity": "controlled-fixture-integrity",
                "license": "MIT",
                "dependencies": {"fixture": "^1.0.0"},
            },
            "node_modules/protobufjs": {
                "version": "7.6.6",
                "resolved": "https://example.invalid/protobuf.tgz",
                "integrity": "controlled-other-integrity",
                "license": "BSD-3-Clause",
                "dependencies": {"fixture": "^2.0.0"},
            },
        },
    }
    path = tmp_path / "package-lock.json"
    content = json.dumps(data, indent=2) + "\n"
    path.write_text(content, encoding="utf-8", newline="\n")
    assert catalog.sanitized_file_bytes(path) == content.encode()
    assert catalog.sha256_file(path) == hashlib.sha256(content.encode()).hexdigest()
    copied = tmp_path / "copy"
    source = tmp_path / "source"
    source.mkdir()
    (source / path.name).write_bytes(path.read_bytes())
    catalog.copy_sanitized_tree(source, copied)
    assert json.loads((copied / path.name).read_bytes()) == data


def test_malformed_lockfile_not_repaired_or_hidden(tmp_path):
    path = tmp_path / "package-lock.json"
    path.write_text('{"packages": broken}\n', encoding="utf-8", newline="\n")
    assert catalog.sanitized_file_bytes(path) == path.read_bytes()

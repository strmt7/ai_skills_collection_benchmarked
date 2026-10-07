"""Qualified example transformations cannot rewrite other source bytes."""

from __future__ import annotations

import hashlib

import build_catalog as catalog
import pytest
from _lib_b import credential_neutralizations as examples


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


@pytest.fixture
def fixture():
    value = "runtime-only-" + sha("independent example fixture")[:22]
    text = "# Example\napi_key = '" + value + "'\nretain = 42\n"
    start = text.index(value)
    output = text.replace(value, "<EXAMPLE_CREDENTIAL>")
    record = {
        "spans": [
            {
                "start": start,
                "end": start + len(value),
                "value_sha256": sha(value),
                "replacement": "<EXAMPLE_CREDENTIAL>",
            }
        ],
        "output_sha256": sha(output),
    }
    return text, output, {sha(text): record}


def test_exact_source_unicode_and_idempotent_output(fixture):
    text, expected, rules = fixture
    assert examples.neutralize(text, rules) == expected
    assert examples.neutralize(expected, rules) == expected
    assert examples.neutralize("Unqualified bytes\n" + text, rules) == "Unqualified bytes\n" + text
    assert expected.count("\n") == text.count("\n")


@pytest.mark.parametrize(
    "field,value",
    [
        ("start", -1),
        ("end", 9000),
        ("value_sha256", "0" * 64),
        ("replacement", "bad\nline"),
        ("replacement", "bad\rline"),
        ("replacement", ""),
    ],
)
def test_invalid_span_fails_closed(fixture, field, value):
    text, _, rules = fixture
    rules[sha(text)]["spans"][0][field] = value
    with pytest.raises(ValueError, match="credential span"):
        examples.neutralize(text, rules)


def test_changed_output_and_overlap_fail(fixture):
    text, _, rules = fixture
    rules[sha(text)]["output_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="output hash"):
        examples.neutralize(text, rules)
    rules[sha(text)]["spans"].append(dict(rules[sha(text)]["spans"][0]))
    with pytest.raises(ValueError, match="credential span"):
        examples.neutralize(text, rules)


def test_policy_three_copy_and_hash_agree_without_changing_source(fixture, tmp_path, monkeypatch):
    text, expected, rules = fixture
    monkeypatch.setattr(examples, "policies", lambda: rules)
    source = tmp_path / "source"
    source.mkdir()
    file = source / "example.md"
    file.write_bytes(text.replace("\n", "\r\n").encode())
    before = file.read_bytes()
    assert catalog.sanitized_file_bytes(file, credential_policy=2) == text.encode()
    assert catalog.sanitized_file_bytes(file, credential_policy=3) == expected.encode()
    output = tmp_path / "output"
    catalog.copy_sanitized_tree(source, output, credential_policy=3)
    assert (output / file.name).read_bytes() == expected.encode()
    assert catalog.sha256_tree(source, credential_policy=3) == catalog.sha256_tree(output, credential_policy=3)
    assert file.read_bytes() == before

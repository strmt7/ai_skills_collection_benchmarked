"""Independent hostname controls for the citation repair and its source baseline."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from types import ModuleType

import build_catalog
import check_citation_security_overlay as overlay
import pytest

CASES = (
    (
        "doi_host_suffix",
        "https://doi.org.attacker.example/nope",
        ("doi", "nope"),
        ("url", "https://doi.org.attacker.example/nope"),
    ),
    (
        "doi_userinfo",
        "https://doi.org@attacker.example/nope",
        ("doi", "nope"),
        ("url", "https://doi.org@attacker.example/nope"),
    ),
    (
        "pubmed_host_suffix",
        "https://pubmed.ncbi.nlm.nih.gov.attacker.example/12345678",
        ("pmid", "12345678"),
        ("url", "https://pubmed.ncbi.nlm.nih.gov.attacker.example/12345678"),
    ),
    (
        "pubmed_path_spoof",
        "https://attacker.example/ncbi.nlm.nih.gov/pubmed/12345678",
        ("pmid", "12345678"),
        ("url", "https://attacker.example/ncbi.nlm.nih.gov/pubmed/12345678"),
    ),
    (
        "arxiv_host_suffix",
        "https://arxiv.org.attacker.example/abs/2401.12345",
        ("arxiv", "2401.12345"),
        ("url", "https://arxiv.org.attacker.example/abs/2401.12345"),
    ),
    ("valid_doi", "https://doi.org/10.1234/example", ("doi", "10.1234/example"), ("doi", "10.1234/example")),
    ("valid_pubmed", "https://pubmed.ncbi.nlm.nih.gov/12345678/", ("pmid", "12345678"), ("pmid", "12345678")),
    ("valid_arxiv", "https://arxiv.org/abs/2401.12345", ("arxiv", "2401.12345"), ("arxiv", "2401.12345")),
)


@pytest.fixture
def parsers(monkeypatch):
    # These methods do not use HTTP. A stub prevents the imported skill from
    # opening a network session, and no bytecode is written into the mirrors.
    monkeypatch.setitem(sys.modules, "requests", ModuleType("requests"))
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    instances = []
    for label, path in (("baseline", overlay.ROOT / overlay.MIRROR), ("repair", overlay.ROOT / overlay.OVERLAY)):
        spec = importlib.util.spec_from_file_location(f"citation_{label}", path / overlay.SCRIPT)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        instances.append(module.MetadataExtractor.__new__(module.MetadataExtractor))
    return instances


@pytest.mark.parametrize("name,url,original,expected", CASES)
def test_url_classification_uses_trusted_hostnames(parsers, name, url, original, expected):
    baseline, repaired = parsers
    assert baseline.identify_type(url) == original
    assert repaired.identify_type(url) == expected


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://DX.DOI.ORG/10.1234/example", ("doi", "10.1234/example")),
        ("https://doi.org:8443/10.1234/example", ("doi", "10.1234/example")),
        ("https://www.ncbi.nlm.nih.gov/pubmed/12345678", ("pmid", "12345678")),
        ("http://arxiv.org/abs/2401.12345", ("arxiv", "2401.12345")),
        ("https://www.ncbi.nlm.nih.gov/notpubmed/12345678", ("url", "https://www.ncbi.nlm.nih.gov/notpubmed/12345678")),
        (
            "https://attacker.example/?next=https://doi.org/nope",
            ("url", "https://attacker.example/?next=https://doi.org/nope"),
        ),
    ],
)
def test_repaired_parser_handles_host_case_ports_and_paths(parsers, url, expected):
    _, repaired = parsers
    assert repaired.identify_type(url) == expected


def test_control_artifact_matches_independent_cases(parsers):
    baseline, _ = parsers
    report = json.loads((overlay.ROOT / overlay.CONTROL).read_text(encoding="utf-8"))
    assert report["artifact_kind"] == "runtime_readiness_security_control"
    assert len(report["controls"]) == len(CASES)
    for recorded, (name, url, original, expected) in zip(report["controls"], CASES, strict=True):
        assert recorded["case"] == name
        assert recorded["input"] == url
        assert recorded["expected"] == list(expected)
        assert recorded["actual"]["locked_mirror"] == list(baseline.identify_type(url)) == list(original)
        assert recorded["actual"]["candidate"] == list(expected)
        assert recorded["candidate_pass"] is True
        assert recorded["mirror_pass"] is (original == expected)


def test_overlay_preserves_original_and_rejects_drift(tmp_path):
    expected = overlay.expected_files()
    actual = overlay.ROOT / overlay.OVERLAY
    assert not overlay.check_overlay(actual, expected)
    assert (actual / "provenance/original.SKILL.md").read_bytes() == build_catalog.sanitized_file_bytes(
        overlay.ROOT / overlay.MIRROR / "SKILL.md"
    )
    copied = tmp_path / "overlay"
    shutil.copytree(actual, copied)
    (copied / overlay.SCRIPT).write_text("changed", encoding="utf-8")
    (copied / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    assert set(overlay.check_overlay(copied, expected)) == {
        "changed file: scripts/extract_metadata.py",
        "unexpected or missing file: unexpected.txt",
    }


def test_checker_reports_missing_overlay(tmp_path):
    assert overlay.check_overlay(tmp_path / "missing", overlay.expected_files()) == [
        "repair overlay is missing or is a symlink"
    ]


@pytest.mark.skipif(os.name == "nt", reason="Windows executable modes are recorded in the Git index")
def test_overlay_check_rejects_wrong_executable_mode(tmp_path):
    files = overlay.expected_files()
    target = tmp_path / "mode-check"
    shutil.copytree(overlay.ROOT / overlay.OVERLAY, target)
    (target / overlay.SCRIPT).chmod(0o644)
    assert overlay.check_overlay(target, files) == ["changed executable mode: scripts/extract_metadata.py"]


def test_checker_rejects_control_from_another_candidate(tmp_path, monkeypatch):
    report = json.loads((overlay.ROOT / overlay.CONTROL).read_text(encoding="utf-8"))
    report["upstream_candidate"]["git_blob"] = "0" * 40
    path = tmp_path / "wrong-control.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.setattr(overlay, "CONTROL", path)
    with pytest.raises(ValueError, match="does not match"):
        overlay.expected_files()


@pytest.mark.parametrize("change", ["missing_source", "duplicate_source", "missing_skill", "duplicate_skill"])
def test_source_lock_identity_must_be_unique_before_overlay(tmp_path, change):
    """Missing or ambiguous source identities must fail before mirror processing."""
    lock = json.loads((overlay.ROOT / "data/source_lock.json").read_text(encoding="utf-8"))
    (source,) = [item for item in lock["sources"] if item["repo"] == "K-Dense-AI/scientific-agent-skills"]
    (entry,) = [item for item in source["skills"] if item["id"] == overlay.SKILL_ID]
    source["skills"] = [] if change == "missing_skill" else [entry, entry] if change == "duplicate_skill" else [entry]
    lock["sources"] = (
        [] if change == "missing_source" else [source, source] if change == "duplicate_source" else [source]
    )
    (tmp_path / "data").mkdir()
    (tmp_path / "data/source_lock.json").write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(ValueError, match="one .* record"):
        overlay.expected_files(tmp_path)

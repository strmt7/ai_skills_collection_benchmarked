"""Verify the immutable historical evidence behind the scientific source note."""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts/research/2026-11-02/what-if-oracle-provenance"
PREVIOUS = ROOT / "artifacts/research/2026-10-28/scientific-source-snapshots"


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def tree_entries(data: bytes, expected_tree: str) -> dict[str, dict]:
    tree = json.loads(data)
    assert tree["sha"] == expected_tree
    assert tree["truncated"] is False
    entries = {entry["path"]: entry for entry in tree["tree"]}
    assert len(entries) == len(tree["tree"])
    return entries


def test_author_notice_and_historical_skill_match_source_trees() -> None:
    record = json.loads((EVIDENCE / "record.json").read_bytes())
    origin = record["origin"]
    pinned = record["pinned_source"]
    candidate = record["candidate"]
    assert origin["initial_commit"] == "f4954b1de0cd00a74c8e16d4bc62b74d3d26d238"
    assert origin["initial_tree"] == "e0d0afe3403759d7165823d4a8b8fdecc8c5e738"
    assert origin["license_change_commit"] == "23cebd4aeb8d80c68088b9944b68c559accb4c11"
    assert origin["license_change_tree"] == "564fc8b6cdbd25b00dd4bf075b51d54f485950e0"
    initial_data = (EVIDENCE / "origin-initial-tree.json").read_bytes()
    later_data = (EVIDENCE / "origin-current-tree.json").read_bytes()
    assert hashlib.sha256(initial_data).hexdigest() == origin["initial_tree_capture"]["sha256"]
    assert hashlib.sha256(later_data).hexdigest() == origin["license_change_tree_capture"]["sha256"]
    initial = tree_entries(initial_data, origin["initial_tree"])
    later = tree_entries(later_data, origin["license_change_tree"])

    for item, source_path in (
        (origin["initial_license"], "LICENSE"),
        (origin["initial_skill"], "what-if-oracle/SKILL.md"),
        (origin["initial_reference"], "what-if-oracle/references/scenario-templates.md"),
    ):
        data = (ROOT / item["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
        assert git_blob(data) == item["git_blob"] == initial[source_path]["sha"]
    assert later["LICENSE"]["sha"] == origin["later_license_git_blob"]
    assert later["LICENSE"]["sha"] != initial["LICENSE"]["sha"]

    old_tree = tree_entries(
        gzip.decompress((PREVIOUS / "old-tree.json.gz").read_bytes()), "336d3f82c7139237934026e7ee2ddc1104711a58"
    )
    new_tree = tree_entries(
        gzip.decompress((PREVIOUS / "new-tree.json.gz").read_bytes()), "bd99d572702e6c9aa02be8ea9edd9c11c82523ce"
    )
    original = (ROOT / origin["initial_skill"]["path"]).read_bytes()
    snapshot = (ROOT / pinned["skill"]["path"]).read_bytes()
    assert hashlib.sha256(snapshot).hexdigest() == pinned["skill"]["sha256"]
    assert git_blob(snapshot) == pinned["skill"]["git_blob"]
    assert git_blob(snapshot) == old_tree["scientific-skills/what-if-oracle/SKILL.md"]["sha"]
    assert (
        old_tree["scientific-skills/what-if-oracle/references/scenario-templates.md"]["sha"]
        == (origin["initial_reference"]["git_blob"])
    )
    assert new_tree[candidate["path"]]["sha"] == candidate["git_blob"]
    old_marker = b"\n---\n\n# What-If"
    new_marker = (
        b"\nallowed-tools: Read Write\nlicense: MIT license\nmetadata:\n"
        b"  skill-author: AHK Strategies (ashrafkahoush-ux)\n---\n\n# What-If"
    )
    assert original.count(old_marker) == 1
    assert original.replace(old_marker, new_marker, 1) == snapshot


def test_ledger_references_exact_provenance_record() -> None:
    record = (EVIDENCE / "record.json").read_bytes()
    ledger = json.loads((ROOT / "data/improvement_ledger.json").read_bytes())
    skill = ledger["skills"]["k-dense-ai-scientific-agent-skills-scientific-skills-what-if-oracle-skill-md"]
    references = skill["research"]["evidence"]
    assert any(
        item["path"] == EVIDENCE.relative_to(ROOT).as_posix() + "/record.json"
        and item["sha256"] == hashlib.sha256(record).hexdigest()
        for item in references
    )

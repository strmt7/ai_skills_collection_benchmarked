"""Check the recorded GNU Make repair against its exact sources and observations."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/coding-refactoring-repository-automation/latest-release-devops/makefile-parallelism"
)
EVIDENCE = ROOT / "artifacts/repaired-skill-readiness/makefile-parallelism-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_provenance_and_recorded_controls_bind_exact_files():
    manifest = json.loads((OVERLAY / "repair.json").read_bytes())
    source = ROOT / manifest["source_mirror"] / "SKILL.md"
    canonical_source = source.read_bytes().replace(b"\r\n", b"\n")
    assert (OVERLAY / "provenance/original.SKILL.md").read_bytes() == canonical_source
    assert manifest["original_skill_sha256"] == hashlib.sha256(canonical_source).hexdigest()
    for base, key in ((OVERLAY, "overlay_sha256"), (EVIDENCE, "evidence_sha256")):
        recorded = manifest[key]
        actual = {
            p.relative_to(base).as_posix(): sha(p)
            for p in base.rglob("*")
            if p.is_file() and p.name != "repair.json" and "__pycache__" not in p.parts
        }
        assert recorded == actual
    qualification = json.loads((EVIDENCE / "qualification.json").read_bytes())
    assert qualification["runner_sha256"] == sha(EVIDENCE / "reproduce.py")
    assert not qualification["agent_performance_tested"]
    for name, version in (("linux-make-4.3.json", "GNU Make 4.3"), ("linux-make-4.4.1.json", "GNU Make 4.4.1")):
        path = EVIDENCE / name
        assert qualification["results"][name] == sha(path)
        result = json.loads(path.read_bytes())
        assert result["make"] == version
        assert result["source_sha256"] == manifest["original_skill_sha256"]
        assert all(sha(OVERLAY / "examples" / path) == value for path, value in result["examples_sha256"].items())
        assert all(value["prepare_completed_first"] for value in result["observations"].values())
        assert all(
            not result["observations"][case]["siblings_overlap"]
            for case in ("ordered_all", "ordered_direct", "serial_all", "serial_multiple_goals")
        )
        assert result["observations"]["ordered_direct"]["publish_completed_before_verify"]
        if version == "GNU Make 4.4.1":
            assert result["observations"]["original"]["siblings_overlap"]

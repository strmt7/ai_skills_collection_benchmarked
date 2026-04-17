from helpers import ROOT, load

import check_no_secret_patterns


def test_skill_risk_audit_covers_every_skill():
    audit = load("data/skill_risk_audit.json")
    catalog = load("data/skills_catalog.json")
    assert audit["summary"]["skill_count"] == len(catalog)
    assert {item["skill_id"] for item in audit["skills"]} == {entry["id"] for entry in catalog}
    assert sum(audit["summary"][key] for key in [
        "likely_non_working",
        "subpar_needs_review",
        "usable_with_listing_gaps",
        "no_static_risk_found",
    ]) == len(catalog)
    assert audit["summary"]["subpar_needs_review"] > 0
    text = (ROOT / "docs" / "skill-risk-findings.md").read_text(encoding="utf-8")
    assert "static, source-backed evidence" in text
    assert "| Risk | Skill | Category | Blocking | Warnings | Key findings |" in text


def test_history_secret_scan_rename_parser_uses_existing_commit_paths(monkeypatch):
    def fake_git_bytes(*args):
        assert args == ("diff-tree", "-z", "--no-commit-id", "--name-status", "-r", "-M", "commit")
        return (
            b"R100\0old/path.txt\0new/path.txt\0"
            b"D\0removed/path.txt\0"
            b"M\0kept/path.txt\0"
            b"A\0added/path.txt\0"
        )

    monkeypatch.setattr(check_no_secret_patterns, "git_bytes", fake_git_bytes)
    assert check_no_secret_patterns.commit_changed_names("commit") == [
        "new/path.txt",
        "kept/path.txt",
        "added/path.txt",
    ]

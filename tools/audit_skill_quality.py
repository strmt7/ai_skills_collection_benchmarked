#!/usr/bin/env python3
"""Audit all mirrored skills for likely subpar or non-working conditions."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_catalog

SCRIPT_EXPECTED_CATEGORIES = {
    "DevOps, cloud & operations",
    "Science, research & data analysis",
    "Security, compliance & risk",
    "Testing, QA & benchmarking",
}

SUBAGENT_PATTERNS = [
    re.compile(r"\bsubagents?\b", re.IGNORECASE),
    re.compile(r"\bparallel agents?\b", re.IGNORECASE),
    re.compile(r"\bmulti-agent\b", re.IGNORECASE),
    re.compile(r"\bTask subagents?\b", re.IGNORECASE),
]

MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def table_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def is_external_link(target: str) -> bool:
    parsed = urlparse(target)
    return bool(parsed.scheme) or target.startswith("#") or target.startswith("mailto:")


def missing_markdown_links(skill_dir: Path, text: str) -> list[str]:
    missing: list[str] = []
    for match in MARKDOWN_LINK.finditer(text):
        target = match.group(1).split("#", 1)[0].strip()
        if not target or is_external_link(target):
            continue
        candidate = (skill_dir / target).resolve()
        try:
            candidate.relative_to(skill_dir.resolve())
        except ValueError:
            missing.append(target)
            continue
        if not candidate.exists():
            missing.append(target)
    return sorted(set(missing))


def audit_entry(entry: dict[str, Any], manifest_entry: dict[str, Any]) -> dict[str, Any]:
    mirror = ROOT / entry["mirrored_path"]
    skill_file = mirror / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8") if skill_file.is_file() else ""
    resources = entry.get("resources") or {}
    findings: list[dict[str, Any]] = []

    def add(severity: str, code: str, detail: str) -> None:
        findings.append({"severity": severity, "code": code, "detail": detail})

    if not skill_file.is_file():
        add("blocking", "missing-skill-file", "The mirrored directory has no root SKILL.md.")
    if not entry.get("has_required_frontmatter"):
        add("blocking", "missing-required-frontmatter", "The source SKILL.md lacks required name/description frontmatter.")
    if manifest_entry.get("name_conflict_group"):
        add("warning", "duplicate-skill-name", "This skill name collides with another source; bulk install is unsafe.")
    missing_links = missing_markdown_links(mirror, text) if text else []
    if missing_links:
        add("blocking", "missing-local-link", f"Markdown links point to missing local files: {', '.join(missing_links[:8])}.")
    if entry.get("line_count", 0) > 500:
        add("warning", "oversized-skill", "SKILL.md exceeds 500 lines and may waste context unless split into references.")
    if entry["category"] in SCRIPT_EXPECTED_CATEGORIES and not resources.get("has_scripts"):
        add("warning", "no-executable-validator", "This category benefits from executable validators, but no scripts/ directory was observed.")
    if not resources.get("has_agents_metadata"):
        add("info", "missing-agent-metadata", "No agents/openai.yaml metadata was observed for listing UI compatibility.")
    if any(pattern.search(text) for pattern in SUBAGENT_PATTERNS):
        add("warning", "delegation-conflict-in-source", "Mirrored source mentions delegated AI work; repository AGENTS.md overrides it with single-session execution.")

    blocking = sum(1 for item in findings if item["severity"] == "blocking")
    warnings = sum(1 for item in findings if item["severity"] == "warning")
    infos = sum(1 for item in findings if item["severity"] == "info")
    if blocking:
        risk_level = "likely_non_working"
    elif warnings:
        risk_level = "subpar_needs_review"
    elif infos:
        risk_level = "usable_with_listing_gaps"
    else:
        risk_level = "no_static_risk_found"
    return {
        "skill_id": entry["id"],
        "name": entry["name"],
        "category": entry["category"],
        "source_repo": entry["source_repo"],
        "source_path": entry["source_path"],
        "mirrored_path": entry["mirrored_path"],
        "agent_ready_path": entry["agent_ready_path"],
        "risk_level": risk_level,
        "blocking_count": blocking,
        "warning_count": warnings,
        "info_count": infos,
        "findings": findings,
    }


def render_report(results: dict[str, Any]) -> str:
    summary = results["summary"]
    lines = [
        "# Skill Risk Findings",
        "",
        "This report flags likely subpar or non-working skills from static, source-backed evidence. It does not replace runtime scenario execution; it identifies candidates that need human or benchmark follow-up.",
        "",
        "## Summary",
        "",
        f"- Skills audited: `{summary['skill_count']}`",
        f"- Likely non-working: `{summary['likely_non_working']}`",
        f"- Subpar / needs review: `{summary['subpar_needs_review']}`",
        f"- Usable with listing gaps: `{summary['usable_with_listing_gaps']}`",
        f"- No static risk found: `{summary['no_static_risk_found']}`",
        "",
        "## Findings",
        "",
        "| Risk | Skill | Category | Blocking | Warnings | Key findings |",
        "|---|---|---|---:|---:|---|",
    ]
    for item in results["skills"]:
        if item["risk_level"] == "no_static_risk_found":
            continue
        key_findings = "; ".join(f"{finding['code']}: {finding['detail']}" for finding in item["findings"][:4])
        lines.append(
            f"| `{item['risk_level']}` | `{item['skill_id']}` | {table_cell(item['category'])} | "
            f"{item['blocking_count']} | {item['warning_count']} | {table_cell(key_findings)} |"
        )
    if len(lines) == 18:
        lines.append("| none | none | none | 0 | 0 | none |")
    return "\n".join(lines) + "\n"


def run() -> dict[str, Any]:
    catalog = load_json(ROOT / "data" / "skills_catalog.json")
    manifest = {entry["id"]: entry for entry in load_json(ROOT / "included" / "skills" / "manifest.json")}
    skills = [audit_entry(entry, manifest[entry["id"]]) for entry in catalog]
    summary = {
        "skill_count": len(skills),
        "likely_non_working": sum(1 for item in skills if item["risk_level"] == "likely_non_working"),
        "subpar_needs_review": sum(1 for item in skills if item["risk_level"] == "subpar_needs_review"),
        "usable_with_listing_gaps": sum(1 for item in skills if item["risk_level"] == "usable_with_listing_gaps"),
        "no_static_risk_found": sum(1 for item in skills if item["risk_level"] == "no_static_risk_found"),
    }
    return {
        "audit_version": 1,
        "generated_on": build_catalog.BUILD_DATE,
        "summary": summary,
        "skills": skills,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit mirrored skill quality and likely usability risks.")
    parser.add_argument("--check", action="store_true", help="Fail if generated audit artifacts are stale.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the audit results JSON envelope to stdout instead of the human summary line.",
    )
    parser.add_argument(
        "--severity",
        choices=["blocking", "warning", "info", "any"],
        default="any",
        help="When used with --json, restrict the 'skills' array to entries with a finding at or above this severity.",
    )
    args = parser.parse_args(argv)
    results = run()
    data_path = ROOT / "data" / "skill_risk_audit.json"
    doc_path = ROOT / "docs" / "skill-risk-findings.md"
    rendered = render_report(results)
    if args.check:
        if load_json(data_path) != results:
            raise SystemExit("data/skill_risk_audit.json is stale")
        if doc_path.read_text(encoding="utf-8") != rendered:
            raise SystemExit("docs/skill-risk-findings.md is stale")
    else:
        write_json(data_path, results)
        doc_path.write_text(rendered, encoding="utf-8")

    if args.json:
        if args.severity != "any":
            rank = {"blocking": 0, "warning": 1, "info": 2, "any": 3}
            threshold = rank[args.severity]
            filtered = [
                item
                for item in results["skills"]
                if any(rank[f["severity"]] <= threshold for f in item["findings"])
            ]
            output = {**results, "skills": filtered}
        else:
            output = results
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        print(
            "Skill risk audit: "
            f"{results['summary']['likely_non_working']} likely non-working, "
            f"{results['summary']['subpar_needs_review']} subpar/needs review, "
            f"{results['summary']['skill_count']} audited."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

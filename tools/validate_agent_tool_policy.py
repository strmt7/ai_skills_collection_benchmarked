#!/usr/bin/env python3
"""Check mandatory development-tool routing without executing external providers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import yaml
from search_semantic_corpus import verify_response

ROOT = Path(__file__).resolve().parents[1]
POLICY = "docs/agent-tools.md"
TOOLS = {
    "caveman": ".agents/skills/caveman/SKILL.md",
    "cocoindex-code-search": ".agents/skills/cocoindex-code-search/SKILL.md",
    "crawl4ai-research": ".agents/skills/crawl4ai-research/SKILL.md",
}
TRIGGERS = dict(zip(TOOLS, ("every_task", "broad_navigation", "web_research"), strict=True))
GATE = "python tools/validate_agent_tool_policy.py --check --json"


def policy_link(root: Path, parent: Path) -> str:
    """Return the portable mandatory policy link for an agent entrypoint."""
    relative = os.path.relpath(root / POLICY, parent).replace(os.sep, "/")
    return f"[Mandatory agent tools]({relative})"


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []

    def read(name: str) -> str:
        path = root / name
        try:
            if not path.resolve().is_relative_to(root) or any(
                part.is_symlink() or getattr(part.lstat(), "st_file_attributes", 0) & 0x400
                for part in (path, *path.parents)
                if part != root and part.is_relative_to(root)
            ):
                raise ValueError("external or linked policy resource")
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
            return ""

    policy = read(POLICY)
    agents = read("AGENTS.md")
    if policy_link(root, root) not in agents:
        errors.append("AGENTS.md: mandatory agent-tool policy link missing")
    if "Caveman, CocoIndex Code and Crawl4AI are mandatory" not in agents:
        errors.append("AGENTS.md: mandatory three-tool directive missing")
    for name, path in TOOLS.items():
        if f"]({os.path.relpath(root / path, root / 'docs').replace(os.sep, '/')})" not in policy:
            errors.append(f"{POLICY}: {name} skill link missing")
        text = read(path)
        try:
            parts = text.split("---", 2)
            frontmatter = yaml.safe_load(parts[1]) if parts[0] == "" and len(parts) == 3 else None
            if not isinstance(frontmatter, dict) or frontmatter.get("name") != name:
                errors.append(f"{path}: incorrect or absent skill identity")
            elif not isinstance(frontmatter.get("description"), str) or not frontmatter["description"].strip():
                errors.append(f"{path}: missing skill activation description")
            elif (
                not isinstance(frontmatter.get("metadata"), dict)
                or frontmatter["metadata"].get("mandatory") is not True
                or frontmatter["metadata"].get("trigger") != TRIGGERS[name]
            ):
                errors.append(f"{path}: mandatory activation contract changed")
            if len(parts) != 3 or not parts[2].strip():
                errors.append(f"{path}: empty skill instructions")
        except yaml.YAMLError as exc:
            errors.append(f"{path}: invalid frontmatter: {exc}")
    try:
        workflow = yaml.safe_load(read(".github/workflows/offline-validation.yml"))
        job = workflow["jobs"]["validate"]
        gate_steps = [step for step in job["steps"] if isinstance(step, dict) and step.get("run") == GATE]
        if (
            not gate_steps
            or "if" in job
            or job.get("continue-on-error", False) is not False
            or any("if" in step or step.get("continue-on-error", False) is not False for step in gate_steps)
        ):
            errors.append("offline-validation.yml: mandatory agent-tool gate missing or bypassable")
    except (yaml.YAMLError, KeyError, TypeError) as exc:
        errors.append(f"offline-validation.yml: invalid gate configuration: {exc}")
    checked = 0
    try:
        catalog = json.loads(read("data/skills_catalog.json"))
        if not isinstance(catalog, list) or not catalog:
            raise ValueError("catalog must be a nonempty list")
        seen: set[str] = set()
        for entry in catalog:
            if not isinstance(entry, dict) or not isinstance(entry.get("agent_ready_path"), str):
                errors.append("catalog entry lacks agent_ready_path")
                continue
            name = entry["agent_ready_path"]
            entry_path = Path(name)
            if (
                entry_path.is_absolute()
                or ".." in entry_path.parts
                or "\\" in name
                or ":" in name
                or not name.startswith("included/agent-ready/")
                or entry_path.as_posix() != name
            ):
                errors.append(f"invalid agent-ready path: {name}")
                continue
            if name in seen:
                errors.append(f"duplicate agent-ready path: {name}")
                continue
            seen.add(name)
            checked += 1
            if policy_link(root, (root / name).parent) not in read(name):
                errors.append(f"{name}: mandatory agent-tool policy link missing")
    except (ValueError, TypeError) as exc:
        errors.append(f"data/skills_catalog.json: {exc}")
    if policy_link(root, root / "included/agent-ready") not in read("included/agent-ready/README.md"):
        errors.append("agent-ready README: mandatory agent-tool policy link missing")
    return {"ok": not errors, "required_tools": list(TOOLS), "entrypoints_checked": checked, "errors": errors}


def validate_execution(root: Path, path: Path) -> list[str]:
    """Recheck linked task evidence; an agent declaration is not independent observation."""
    errors: list[str] = []
    try:
        task = json.loads(path.read_text(encoding="utf-8"))
        if (
            type(task["schema_version"]) is not int
            or task["schema_version"] != 1
            or Path(task["source_root"]).resolve() != root
        ):
            raise ValueError("execution receipt has a different schema or repository binding")
        scope = task["task_scope"]
        if (
            not isinstance(scope, dict)
            or set(scope) != {"broad_navigation", "web_research"}
            or any(type(flag) is not bool for flag in scope.values())
        ):
            raise ValueError("task scope must explicitly classify both mandatory execution triggers")
        caveman = task["caveman"]
        if (
            caveman["applied"] is not True
            or caveman["skill_sha256"] != hashlib.sha256((root / TOOLS["caveman"]).read_bytes()).hexdigest()
        ):
            raise ValueError("Caveman application declaration is absent or bound to different instructions")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"execution receipt: {exc}"]

    def linked(name: str) -> tuple[dict[str, Any], Any]:
        record = task[name]
        evidence_path = Path(record["path"])
        if not evidence_path.is_absolute():
            raise ValueError("linked execution evidence requires an explicit absolute path")
        raw = evidence_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ValueError("linked execution evidence digest mismatch")
        return record, json.loads(raw)

    if scope["broad_navigation"]:
        try:
            record, search = linked("cocoindex_code")
            if not isinstance(search, dict):
                raise ValueError("expected a native adapter search receipt")
            base = Path(record["corpus"]).resolve()
            if not base.is_relative_to(root / ".venv"):
                raise ValueError("CocoIndex corpus is outside this repository's isolated workspace")
            raw_manifest = (base / "manifest.json").read_bytes()
            manifest = json.loads(raw_manifest)
            if not isinstance(manifest, dict) or not isinstance(search.get("query"), dict):
                raise ValueError("invalid source manifest or query")
            paths = search["query"]["paths"]
            if paths is not None and (not isinstance(paths, list) or any(not isinstance(item, str) for item in paths)):
                raise ValueError("invalid query path scopes")
            if (
                search.get("ok") is not True
                or not isinstance(search["query"]["query"], str)
                or not search["query"]["query"].strip()
                or not isinstance(search.get("response"), dict)
                or Path(search["query"]["project_root"]).resolve() != base / "tree"
                or Path(manifest["source_root"]).resolve() != root
                or search["manifest_sha256"] != hashlib.sha256(raw_manifest).hexdigest()
            ):
                raise ValueError("CocoIndex execution or source binding is invalid")
            checks = verify_response(search["response"], base, manifest, paths or [], 5)
            if search["source_checks"] != checks:
                raise ValueError("CocoIndex source verification differs from the linked receipt")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"cocoindex_code: {exc}")
    if scope["web_research"]:
        try:
            record, crawl = linked("crawl4ai")
            if not isinstance(crawl, dict):
                raise ValueError("expected one native Crawl4AI result object")
            markdown = crawl.get("markdown", {})
            text = markdown.get("raw_markdown", "") if isinstance(markdown, dict) else markdown
            if (
                not isinstance(record["provider_version"], str)
                or not record["provider_version"].strip()
                or crawl.get("success") is not True
                or crawl.get("status_code") != 200
                or crawl.get("url") != record["url"]
                or not isinstance(text, str)
                or len(text.strip()) < 80
                or record["scope_reviewed"] is not True
            ):
                raise ValueError("crawl failed, content is insufficient, or intended document scope is unreviewed")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"crawl4ai: {exc}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--check", action="store_true", help="Verify the contract without rewriting files")
    parser.add_argument("--json", action="store_true", help="Emit a machine-readable envelope")
    parser.add_argument(
        "--execution-receipt", type=Path, help="Also verify mandatory tool evidence for a classified task"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate(args.root.resolve())
    if args.execution_receipt:
        result["errors"].extend(validate_execution(args.root.resolve(), args.execution_receipt))
        result["ok"] = not result["errors"]
    print(
        json.dumps(result, indent=2)
        if args.json
        else ("OK: mandatory agent-tool routing" if result["ok"] else "\n".join(result["errors"]))
    )
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

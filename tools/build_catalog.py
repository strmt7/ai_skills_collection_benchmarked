#!/usr/bin/env python3
"""Generate an evidence-backed AI skill catalog and benchmark suite.

Refresh inputs are local checkouts of public GitHub repositories. The generated
catalog never counts repo-only guesses as skills: each item must come from an
observed SKILL.md file and carry an immutable commit URL.
"""

from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import subprocess
import argparse
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(os.environ.get("AI_SKILL_SOURCE_ROOT", "/tmp/ai_skill_sources"))
BUILD_DATE = "2026-04-17"
MIN_SCENARIOS = 3
GENERIC_WORKFLOW_REQUIRED = ["inputs", "steps", "outputs", "metrics", "citations_or_paths"]
SOURCE_PROOF_REQUIRED = ["activation_conditions", "required_context", "safe_boundaries", "workflow_steps", "proof_evidence"]
SECRET_PLACEHOLDERS = [
    (re.compile(r"AIza[0-9A-Za-z_-]{35}"), "<GOOGLE_API_KEY>"),
    (re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"), "<AWS_ACCESS_KEY_ID>"),
    (re.compile(r"(?<![A-Za-z0-9_-])sk-(?:proj-)?[A-Za-z0-9_]{20,}(?![A-Za-z0-9_-])"), "<OPENAI_API_KEY>"),
    (re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{20,})"), "<GITHUB_TOKEN>"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_.-]+"), "<GITHUB_TOKEN>"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_.-]+"), "<GITHUB_TOKEN>"),
    (re.compile(r"glpat-[A-Za-z0-9_-]{20,}"), "<GITLAB_TOKEN>"),
    (re.compile(r"\bglpat-[A-Za-z0-9_.-]+"), "<GITLAB_TOKEN>"),
    (re.compile(r"hf_[A-Za-z0-9]{30,}"), "<HUGGINGFACE_TOKEN>"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "<SLACK_TOKEN>"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9_.-]+"), "<SLACK_TOKEN>"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |)?PRIVATE KEY-----"), "<PRIVATE_KEY_HEADER>"),
]


SOURCES: list[dict[str, Any]] = [
    {"repo": "strmt7/simple_ai_bitcoin_trading_binance", "dir": "strmt7__simple_ai_bitcoin_trading_binance", "tier": "priority-user-public-repo", "group": "strmt7 account priority", "policy": "default-branch HEAD; GitHub API reported no latest release", "prefixes": [".agents/skills/"]},
    {"repo": "strmt7/ome-zarr-C", "dir": "strmt7__ome-zarr-C", "tier": "priority-user-public-repo", "group": "strmt7 account priority", "policy": "default-branch HEAD; GitHub API reported no latest release", "prefixes": [".agents/skills/"]},
    {"repo": "strmt7/project_air_defense", "dir": "strmt7__project_air_defense", "tier": "priority-user-public-repo", "group": "strmt7 account priority", "policy": "default-branch HEAD; GitHub API reported no latest release", "prefixes": [".agents/skills/", "skills/"]},
    {"repo": "ZMB-UZH/omero-docker-extended", "dir": "ZMB-UZH__omero-docker-extended", "tier": "priority-requested-public-repo", "group": "requested OMERO repository priority", "policy": "default-branch HEAD; GitHub API reported no latest release", "prefixes": [".agents/skills/", "third_party/"]},
    {"repo": "anthropics/skills", "dir": "anthropics__skills", "tier": "official-reference", "group": "official skill reference", "policy": "default-branch HEAD; GitHub API reported no latest release", "prefixes": ["skills/"], "exclude_prefixes": ["template/"]},
    {"repo": "K-Dense-AI/scientific-agent-skills", "dir": "K-Dense-AI__scientific-agent-skills", "tier": "latest-release-community", "group": "latest release scientific skills", "policy": "latest GitHub release v2.37.1", "tag": "v2.37.1", "release_url": "https://github.com/K-Dense-AI/scientific-agent-skills/releases/tag/v2.37.1", "prefixes": ["scientific-skills/"]},
    {"repo": "microsoft/skills", "dir": "microsoft__skills", "tier": "official-vendor-reference", "group": "Microsoft skills reference", "policy": "default-branch HEAD; GitHub API reported no latest release", "prefixes": [".github/plugins/", ".github/skills/"]},
    {"repo": "trailofbits/skills", "dir": "trailofbits__skills", "tier": "security-reference", "group": "security and audit skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "ahmedasmar/devops-claude-skills", "dir": "ahmedasmar__devops-claude-skills", "tier": "devops-reference", "group": "DevOps skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "akin-ozer/cc-devops-skills", "dir": "akin-ozer__cc-devops-skills", "tier": "latest-release-devops", "group": "latest release DevOps skills", "policy": "latest GitHub release v1.0.0", "tag": "v1.0.0", "release_url": "https://github.com/akin-ozer/cc-devops-skills/releases/tag/v1.0.0"},
    {"repo": "composio-community/support-skills", "dir": "composio-community__support-skills", "tier": "support-reference", "group": "customer support skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "browser-act/skills", "dir": "browser-act__skills", "tier": "browser-automation-reference", "group": "browser and web automation skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "lackeyjb/playwright-skill", "dir": "lackeyjb__playwright-skill", "tier": "latest-release-browser-automation", "group": "latest release browser automation skill", "policy": "latest GitHub release v4.1.0", "tag": "v4.1.0", "release_url": "https://github.com/lackeyjb/playwright-skill/releases/tag/v4.1.0"},
    {"repo": "twwch/comfyui-workflow-skill", "dir": "twwch__comfyui-workflow-skill", "tier": "creative-reference", "group": "creative media skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "EvoLinkAI/video-generation-skill-for-openclaw", "dir": "EvoLinkAI__video-generation-skill-for-openclaw", "tier": "creative-reference", "group": "creative media skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "EvoLinkAI/music-generation-skill-for-openclaw", "dir": "EvoLinkAI__music-generation-skill-for-openclaw", "tier": "creative-reference", "group": "creative media skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "designrique/ai-graphic-design-skill", "dir": "designrique__ai-graphic-design-skill", "tier": "creative-reference", "group": "creative media skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "yuvalsuede/agent-media-skill", "dir": "yuvalsuede__agent-media-skill", "tier": "creative-reference", "group": "creative media skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "Raven7979/ai-video-editing-skill", "dir": "Raven7979__ai-video-editing-skill", "tier": "creative-reference", "group": "creative media skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "ztj7728/gemini-image-generation", "dir": "ztj7728__gemini-image-generation", "tier": "creative-reference", "group": "creative media skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "fruteroclub/marketing-designer", "dir": "fruteroclub__marketing-designer", "tier": "creative-reference", "group": "creative media skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "Bria-AI/bria-skill", "dir": "Bria-AI__bria-skill", "tier": "latest-release-creative", "group": "latest release creative media skills", "policy": "latest GitHub release v1.3.1", "tag": "v1.3.1", "release_url": "https://github.com/Bria-AI/bria-skill/releases/tag/v1.3.1"},
    {"repo": "nextlevelbuilder/ui-ux-pro-max-skill", "dir": "nextlevelbuilder__ui-ux-pro-max-skill", "tier": "latest-release-creative", "group": "latest release UI/UX skills", "policy": "latest GitHub release v2.5.0", "tag": "v2.5.0", "release_url": "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/releases/tag/v2.5.0"},
    {"repo": "guinacio/claude-image-gen", "dir": "guinacio__claude-image-gen", "tier": "latest-release-creative", "group": "latest release image generation skill", "policy": "latest GitHub release 1.0.2", "tag": "1.0.2", "release_url": "https://github.com/guinacio/claude-image-gen/releases/tag/1.0.2"},
    {"repo": "hugohe3/ppt-master", "dir": "hugohe3__ppt-master", "tier": "latest-release-creative", "group": "latest release presentation skill", "policy": "latest GitHub release v2.3.0", "tag": "v2.3.0", "release_url": "https://github.com/hugohe3/ppt-master/releases/tag/v2.3.0"},
    {"repo": "aizzaku/create-infographics", "dir": "aizzaku__create-infographics", "tier": "creative-reference", "group": "creative media skills", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "Varnan-Tech/opendirectory", "dir": "Varnan-Tech__opendirectory", "tier": "reddit-verified-gtm-registry", "group": "Reddit r/codex open-source Codex skills signal; GitHub SKILL.md files verified", "policy": "default-branch HEAD; GitHub API reported no latest release", "prefixes": ["packages/cli/skills/"], "max_path_parts": 5},
    {"repo": "supermemoryai/skills", "dir": "supermemoryai__skills", "tier": "reddit-verified-creative-skill", "group": "Reddit r/codex linked skill; GitHub SKILL.md verified", "policy": "default-branch HEAD; GitHub API reported no latest release", "prefixes": ["svg-animations/"]},
    {"repo": "hardikpandya/stop-slop", "dir": "hardikpandya__stop-slop", "tier": "reddit-verified-writing-skill", "group": "Reddit r/codex linked skill; GitHub SKILL.md verified", "policy": "default-branch HEAD; GitHub API reported no latest release"},
    {"repo": "affaan-m/everything-claude-code", "dir": "affaan-m__everything-claude-code", "tier": "selected-structure-reference", "group": "selected repository structure reference", "policy": "latest GitHub release v1.10.0", "tag": "v1.10.0", "release_url": "https://github.com/affaan-m/everything-claude-code/releases/tag/v1.10.0", "prefixes": [".agents/skills/"]},
]


BEST_PRACTICE_SOURCES = [
    {"id": "anthropic-skill-best-practices", "title": "Anthropic skill authoring best practices", "url": "https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices"},
    {"id": "mdskills-open-ecosystem", "title": "mdskills.ai open skills ecosystem", "url": "https://www.mdskills.ai/"},
    {"id": "github-copilot-instructions", "title": "GitHub Copilot repository custom instructions", "url": "https://docs.github.com/en/copilot/how-tos/use-copilot-agents/request-a-code-review/configure-coding-guidelines"},
    {"id": "skillsbench-paper", "title": "SkillsBench benchmark paper", "url": "https://arxiv.org/abs/2602.12670"},
    {"id": "skill-usage-paper", "title": "Skill usage benchmark code", "url": "https://github.com/UCSB-NLP-Chang/Skill-Usage"},
    {"id": "reddit-agent-skills-worth-installing", "title": "Forum signal: practical skill use", "url": "https://www.reddit.com/r/claude/comments/1s51b5u/the_claude_code_skills_actually_worth_installing/"},
    {"id": "reddit-skills-subagents-patterns", "title": "Forum signal: skills and subagents", "url": "https://www.reddit.com/r/ClaudeAI/comments/1qbc30u/claude_code_skills_subagents_feel_misaligned_what/"},
    {"id": "reddit-codex-open-source-skills", "title": "Forum signal: open-source Codex skills", "url": "https://www.reddit.com/r/codex/comments/1sns7hr/top_10_opensource_codex_skills/"},
    {"id": "opendirectory-gtm-skills", "title": "OpenDirectory GTM skills registry", "url": "https://github.com/Varnan-Tech/opendirectory"},
]


TRACKS = [
    ("source-skill-repository", "Source skill repository proof", "https://github.com/strmt7/ai_skills_collection_benchmarked", "Use the skill source repository itself as the proof fixture: inspect SKILL.md, companion resources, and source path to verify trigger, constraints, and expected artifacts.", ["frontmatter valid", "trigger derivable", "proof artifact schema valid"]),
    ("swe-bench-lite", "SWE-bench Lite", "https://github.com/SWE-bench/SWE-bench", "Patch real GitHub issue tasks and verify with repository tests.", ["patch applies", "test pass rate", "regression count"]),
    ("nyc-tlc-trip-records", "NYC TLC trip records", "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page", "Clean, aggregate, and explain large real trip data.", ["schema correctness", "aggregation accuracy", "runtime budget"]),
    ("sec-edgar-companyfacts", "SEC EDGAR company facts", "https://www.sec.gov/edgar/sec-api-documentation", "Extract and reconcile financial facts from filings.", ["citation coverage", "numeric reconciliation", "filing provenance"]),
    ("common-crawl-warc", "Common Crawl WARC", "https://commoncrawl.org/", "Retrieve, parse, and cite web-scale documents.", ["source precision", "deduplication", "citation traceability"]),
    ("beir-retrieval", "BEIR retrieval benchmark", "https://github.com/beir-cellar/beir", "Evaluate retrieval workflows across datasets.", ["nDCG@10", "recall@100", "query latency"]),
    ("ms-marco", "MS MARCO", "https://microsoft.github.io/msmarco/", "Rank passages and support answer extraction.", ["MRR", "recall", "answer support"]),
    ("enron-email", "CMU Enron email dataset", "https://www.cs.cmu.edu/~enron/", "Classify, summarize, and route real email threads.", ["routing accuracy", "PII handling", "summary faithfulness"]),
    ("stackoverflow-survey", "Stack Overflow Developer Survey", "https://survey.stackoverflow.co/", "Analyze survey data and produce reproducible charts.", ["cleaning correctness", "chart reproducibility", "method clarity"]),
    ("ome-ngff-samples", "OME-NGFF sample data", "https://idr.github.io/ome-ngff-samples/", "Read and validate multiscale microscopy data.", ["metadata validity", "chunk correctness", "shape parity"]),
    ("cellxgene-census", "CZ CELLxGENE Census", "https://chanzuckerberg.github.io/cellxgene-census/", "Query and analyze single-cell expression data.", ["query correctness", "metadata filters", "reproducibility"]),
    ("chembl", "ChEMBL", "https://www.ebi.ac.uk/chembl/", "Retrieve molecular bioactivity records.", ["identifier accuracy", "filter correctness", "citation provenance"]),
    ("owasp-benchmark", "OWASP Benchmark", "https://owasp.org/www-project-benchmark/", "Find and classify vulnerability test cases.", ["true positives", "false positives", "CWE mapping"]),
    ("owasp-juice-shop", "OWASP Juice Shop", "https://owasp.org/www-project-juice-shop/", "Run safe local security workflows against a known vulnerable app.", ["finding reproducibility", "risk classification", "remediation quality"]),
    ("kubernetes-examples", "Kubernetes examples", "https://github.com/kubernetes/examples", "Validate manifests and operational runbooks.", ["schema validity", "least privilege", "rollout success"]),
    ("opentelemetry-demo", "OpenTelemetry demo", "https://github.com/open-telemetry/opentelemetry-demo", "Debug telemetry across microservices.", ["trace completeness", "metric coverage", "diagnostic accuracy"]),
    ("coco-captions", "COCO captions", "https://cocodataset.org/#download", "Evaluate image understanding and visual QA tasks.", ["caption faithfulness", "object coverage", "layout accuracy"]),
    ("local-omero-compose-workflows", "ZMB-UZH OMERO workflows", "https://github.com/ZMB-UZH/omero-docker-extended", "Validate OMERO deployment, plugin, upload/import, and monitoring workflows.", ["compose health", "plugin workflow", "regression count"]),
    ("air-defense-android-benchmarks", "Project Air Defense Android benchmarks", "https://github.com/strmt7/project_air_defense/tree/main/benchmarks", "Run startup, gameplay, and visual QA benchmark scenarios.", ["startup time", "frame stability", "visual regressions"]),
]


SCENARIO_TRACKS = {
    "Coding, refactoring & repository automation": ["swe-bench-lite", "kubernetes-examples", "opentelemetry-demo"],
    "Testing, QA & benchmarking": ["swe-bench-lite", "owasp-benchmark", "local-omero-compose-workflows"],
    "Data, analytics & visualization": ["nyc-tlc-trip-records", "stackoverflow-survey", "sec-edgar-companyfacts"],
    "Science, research & data analysis": ["cellxgene-census", "chembl", "ome-ngff-samples"],
    "Documents, spreadsheets & presentations": ["sec-edgar-companyfacts", "enron-email", "stackoverflow-survey"],
    "Frontend, UI & browser automation": ["owasp-juice-shop", "coco-captions", "air-defense-android-benchmarks"],
    "Creative, media & design": ["coco-captions", "air-defense-android-benchmarks", "nyc-tlc-trip-records"],
    "DevOps, cloud & operations": ["kubernetes-examples", "opentelemetry-demo", "local-omero-compose-workflows"],
    "Cloud, Azure & Microsoft SDKs": ["kubernetes-examples", "opentelemetry-demo", "sec-edgar-companyfacts"],
    "Security, compliance & risk": ["owasp-benchmark", "owasp-juice-shop", "kubernetes-examples"],
    "Search, retrieval & web automation": ["common-crawl-warc", "beir-retrieval", "ms-marco"],
    "Communication, productivity & support": ["enron-email", "ms-marco", "sec-edgar-companyfacts"],
    "Finance, commerce & forecasting": ["sec-edgar-companyfacts", "nyc-tlc-trip-records", "stackoverflow-survey"],
    "Game, mobile & visual QA": ["air-defense-android-benchmarks", "coco-captions", "owasp-juice-shop"],
    "OMERO, Django, Docker & lab infrastructure": ["local-omero-compose-workflows", "ome-ngff-samples", "opentelemetry-demo"],
    "Agent infrastructure & skill creation": ["beir-retrieval", "swe-bench-lite", "common-crawl-warc"],
}


CATEGORY_KEYWORDS = [
    ("OMERO, Django, Docker & lab infrastructure", ["omero", "django", "postgres", "docker-patterns", "env-contract", "plugin-regression"]),
    ("Game, mobile & visual QA", ["ue5", "android", "mobile", "game", "city", "rendering", "visual-qa", "air-defense"]),
    ("Science, research & data analysis", ["scientific", "science", "bio", "chem", "cell", "gene", "rdkit", "zarr", "scanpy", "pydicom", "molecular", "clinical", "lab"]),
    ("Cloud, Azure & Microsoft SDKs", ["azure", "m365", "microsoft", "foundry", "eventhub", "cosmos", "servicebus", "keyvault", "webjobs"]),
    ("Security, compliance & risk", ["security", "compliance", "secret", "rbac", "content-safety", "auth", "vulnerability", "audit", "semgrep", "codeql", "fuzz", "sarif", "sandbox", "risk", "yara", "zeroize"]),
    ("Testing, QA & benchmarking", ["test", "qa", "benchmark", "regression", "playwright", "verification", "tdd", "parity", "mutation", "coverage", "wycheproof"]),
    ("DevOps, cloud & operations", ["deploy", "kubernetes", "k8s", "cloud", "workflow", "supply-chain", "monitor", "monitoring", "observability", "diagnostic", "terraform", "terragrunt", "helm", "ansible", "promql", "logql", "jenkins", "gitlab", "ci", "ci-cd", "gitops", "dockerfile", "pipeline", "bash"]),
    ("Documents, spreadsheets & presentations", ["pdf", "docx", "xlsx", "pptx", "slides", "poster", "document", "spreadsheet", "presentation"]),
    ("Creative, media & design", ["image", "video", "music", "audio", "art", "gif", "podcast", "schematic", "visualization", "infographic", "brand", "designer", "figma", "comfyui", "bria", "ux", "svg", "animation", "logo", "icon", "illustration", "cover", "thumbnail"]),
    ("Communication, productivity & support", ["support", "ticket", "customer", "zendesk", "intercom", "freshdesk", "sla", "refund", "response", "whatsapp", "csat", "nps", "inbox", "handoff", "call-summary", "slack", "internal-comms", "meeting", "writing", "prose", "blog", "newsletter", "linkedin", "twitter", "reddit", "hackernews", "outreach", "standup", "gtm"]),
    ("Search, retrieval & web automation", ["search", "lookup", "retrieval", "web", "parallel-web", "database-lookup", "documentation-lookup", "site-extract", "browser-act", "scraper", "youtube", "google", "maps", "wechat", "zhihu", "seo", "trends", "keyword"]),
    ("Finance, commerce & forecasting", ["finance", "fiscal", "trading", "market", "forecast", "cost", "amazon", "product", "sales", "commerce"]),
    ("Frontend, UI & browser automation", ["frontend", "browser", "ui", "webapp", "canvas", "theme", "react"]),
    ("Agent infrastructure & skill creation", ["agent", "mcp", "context", "source-audit", "creator", "continual-learning"]),
]


def run_git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "item"


def install_name(entry_or_repo: dict[str, Any] | str, source_path: str | None = None) -> str:
    if isinstance(entry_or_repo, dict):
        repo = entry_or_repo["source_repo"]
        source_path = entry_or_repo["source_path"]
    else:
        repo = entry_or_repo
    assert source_path is not None
    return slug(f"{repo} {source_path.removesuffix('/SKILL.md').removesuffix('SKILL.md')}")


def sanitize_secret_like_text(text: str) -> str:
    for pattern, placeholder in SECRET_PLACEHOLDERS:
        text = pattern.sub(placeholder, text)
    return text


def normalize_text_file(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"^ +\t", "\t", line.rstrip(" \t")) for line in text.split("\n")]
    return "\n".join(lines).rstrip("\n") + "\n"


def sanitized_file_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if b"\0" in data:
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return normalize_text_file(sanitize_secret_like_text(text)).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(sanitized_file_bytes(path))
    return digest.hexdigest()


def is_under_nested_skill(root: Path, item: Path) -> bool:
    parent = item.parent
    while parent != root:
        if (parent / "SKILL.md").is_file():
            return True
        parent = parent.parent
    return False


def sha256_tree(path: Path) -> str:
    digest = hashlib.sha256()
    ignored_parts = {".git", "__pycache__"}
    files: list[Path] = []
    root_stat = path.resolve().stat()
    seen_dirs = {(root_stat.st_dev, root_stat.st_ino)}
    for current, dirs, names in os.walk(path, followlinks=True):
        current_path = Path(current)
        kept_dirs: list[str] = []
        for dirname in dirs:
            child = current_path / dirname
            if dirname in ignored_parts or (child != path and (child / "SKILL.md").is_file()):
                continue
            try:
                stat = child.resolve().stat()
            except OSError:
                continue
            key = (stat.st_dev, stat.st_ino)
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs
        for name in names:
            item = current_path / name
            if ignored_parts.intersection(item.parts) or not item.is_file() or is_under_nested_skill(path, item):
                continue
            files.append(item)
    for item in sorted(files, key=lambda p: p.relative_to(path).as_posix()):
        rel = item.relative_to(path).as_posix()
        stat = item.stat()
        data = sanitized_file_bytes(item)
        file_digest = hashlib.sha256(data).hexdigest()
        digest.update(f"file\0{rel}\0{stat.st_mode:o}\0{len(data)}\0".encode())
        digest.update(file_digest.encode())
        digest.update(b"\n")
    return digest.hexdigest()


def ignore_non_root_skill_dirs(root: Path):
    root = root.resolve()

    def ignore(directory: str, names: list[str]) -> set[str]:
        current = Path(directory).resolve()
        ignored = {name for name in names if name in {".git", "__pycache__"}}
        for name in names:
            child = current / name
            if child.is_dir() and child != root and (child / "SKILL.md").is_file():
                ignored.add(name)
        return ignored

    return ignore


def copy_sanitized_tree(src: Path, dst: Path) -> None:
    ignored_parts = {".git", "__pycache__"}
    dst.mkdir(parents=True, exist_ok=True)
    root_stat = src.resolve().stat()
    seen_dirs = {(root_stat.st_dev, root_stat.st_ino)}
    for current, dirs, names in os.walk(src, followlinks=True):
        current_path = Path(current)
        rel_dir = current_path.relative_to(src)
        target_dir = dst / rel_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        kept_dirs: list[str] = []
        for dirname in dirs:
            child = current_path / dirname
            if dirname in ignored_parts or (child != src and (child / "SKILL.md").is_file()):
                continue
            try:
                stat = child.resolve().stat()
            except OSError:
                continue
            key = (stat.st_dev, stat.st_ino)
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs
        for name in names:
            source_file = current_path / name
            if ignored_parts.intersection(source_file.parts) or not source_file.is_file() or is_under_nested_skill(src, source_file):
                continue
            target_file = target_dir / name
            target_file.write_bytes(sanitized_file_bytes(source_file))
            shutil.copymode(source_file, target_file, follow_symlinks=False)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        return {}, text
    if yaml:
        try:
            data = yaml.safe_load(parts[1]) or {}
            return data if isinstance(data, dict) else {}, parts[2]
        except Exception:
            pass
    data: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            data[key.strip()] = val.strip().strip("\"'")
    return data, parts[2]


def compact(text: Any, limit: int = 420) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rsplit(" ", 1)[0] + "."


def headings(body: str) -> list[str]:
    found: list[str] = []
    for line in body.splitlines():
        if line.startswith("#"):
            found.append(re.sub(r"^#+\s*", "", line).strip())
        if len(found) >= 8:
            break
    return [item for item in found if item]


def fallback_description(name: str, rel: str, body: str) -> str:
    found = headings(body)
    if found:
        return f"Use for {name} workflows. Source sections include {', '.join(found[:3])}."
    source_hint = rel.removesuffix("/SKILL.md").replace("/", " / ")
    return f"Use for {name} workflows from `{source_hint}`."


def flags(skill_file: Path) -> dict[str, bool]:
    folder = skill_file.parent
    return {
        "has_agents_metadata": (folder / "agents" / "openai.yaml").exists(),
        "has_scripts": (folder / "scripts").exists(),
        "has_references": (folder / "references").exists(),
        "has_assets": (folder / "assets").exists(),
        "has_examples": (folder / "examples").exists() or (folder / "examples.md").exists(),
    }


def keyword_matches(blob: str, keyword: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", blob.lower())
    normalized_keyword = re.sub(r"[^a-z0-9]+", " ", keyword.lower()).strip()
    if not normalized_keyword:
        return False
    parts = normalized_keyword.split()
    if len(parts) == 1:
        return parts[0] in set(normalized.split())
    return f" {normalized_keyword} " in f" {normalized} "


def category_for(source: dict[str, Any], rel: str, name: str, description: str) -> str:
    blob = f"{source['repo']} {rel} {name} {description}".lower()
    for category, words in CATEGORY_KEYWORDS:
        if any(keyword_matches(blob, word) for word in words):
            return category
    if source["repo"] == "K-Dense-AI/scientific-agent-skills":
        return "Science, research & data analysis"
    if source["repo"] == "microsoft/skills":
        return "Cloud, Azure & Microsoft SDKs"
    return "Coding, refactoring & repository automation"


def scenario_ids(category: str) -> list[str]:
    ids = SCENARIO_TRACKS.get(category, SCENARIO_TRACKS["Coding, refactoring & repository automation"])
    return [category_scenario_id(category, track_id) for track_id in ids]


def category_scenario_id(category: str, track_id: str) -> str:
    return f"{slug(category.replace('&', 'and'))}-{track_id}"


def skill_mirror_path(category: str, source_tier: str, entry_install_name: str) -> str:
    return f"included/skills/by-category/{slug(category)}/{slug(source_tier)}/{entry_install_name}"


def skill_agent_ready_path(category: str, source_tier: str, entry_install_name: str) -> str:
    return f"included/agent-ready/by-category/{slug(category)}/{slug(source_tier)}/{entry_install_name}/SKILL.md"


def collect() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for source in SOURCES:
        repo_dir = SOURCE_ROOT / source["dir"]
        if not repo_dir.exists():
            raise FileNotFoundError(
                f"missing source checkout for {source['repo']}: expected {repo_dir}. "
                "Clone the source repo there or rerun with --source-root /path/to/checkouts."
            )
        commit = run_git(repo_dir, "rev-parse", "HEAD")
        if source.get("tag"):
            tag_commit = run_git(repo_dir, "rev-parse", f"{source['tag']}^{{commit}}")
            if tag_commit != commit:
                raise ValueError(f"{source['repo']} checkout HEAD {commit} does not match tag {source['tag']} commit {tag_commit}")
        selected_ref = source.get("tag") or "default-branch HEAD"
        ref_url = source.get("tag") or commit
        skill_files = sorted(repo_dir.rglob("SKILL.md"))
        for skill_file in skill_files:
            rel = skill_file.relative_to(repo_dir).as_posix()
            prefixes = source.get("prefixes") or []
            excludes = source.get("exclude_prefixes") or []
            if prefixes and not any(rel.startswith(prefix) for prefix in prefixes):
                continue
            if excludes and any(rel.startswith(prefix) for prefix in excludes):
                continue
            if source.get("max_path_parts") and len(rel.split("/")) > source["max_path_parts"]:
                continue
            text = skill_file.read_text(encoding="utf-8", errors="replace")
            skill_dir = skill_file.parent
            meta, body = parse_frontmatter(text)
            name = str(meta.get("name") or skill_file.parent.name)
            description = compact(meta.get("description") or fallback_description(name, rel, body))
            category = category_for(source, rel, name, description)
            resource_flags = flags(skill_file)
            has_required_frontmatter = all(key in meta for key in ("name", "description"))
            entry_install_name = install_name(source["repo"], rel)
            item = {
                "id": slug(f"{source['repo']} {rel}"),
                "name": name,
                "description": description,
                "category": category,
                "subcategory": source["tier"],
                "install_name": entry_install_name,
                "mirrored_path": skill_mirror_path(category, source["tier"], entry_install_name),
                "agent_ready_path": skill_agent_ready_path(category, source["tier"], entry_install_name),
                "source_repo": source["repo"],
                "source_group": source["group"],
                "source_tier": source["tier"],
                "source_path": rel,
                "source_url": f"https://github.com/{source['repo']}/blob/{ref_url}/{rel}",
                "immutable_source_url": f"https://github.com/{source['repo']}/blob/{commit}/{rel}",
                "selected_ref": selected_ref,
                "selection_policy": source["policy"],
                "latest_release_tag": source.get("tag"),
                "latest_release_url": source.get("release_url"),
                "commit_sha": commit,
                "skill_file_sha256": sha256_file(skill_file),
                "skill_dir_sha256": sha256_tree(skill_dir),
                "line_count": text.count("\n") + 1,
                "frontmatter_keys": sorted(meta.keys()),
                "has_required_frontmatter": has_required_frontmatter,
                "headings": headings(body),
                "resources": resource_flags,
                "scenario_covered_candidate": True,
                "benchmark_status": "artifact_gated",
                "runtime_artifacts_recorded": False,
                "readiness_basis": "Actual SKILL.md found at selected release tag or default HEAD; deployment still requires running assigned scenarios in the target agent runtime.",
                "benchmark_scenarios": [],
                "best_practice_basis": [item["id"] for item in BEST_PRACTICE_SOURCES[:4]],
            }
            notes = [
                "Keep provenance and selected ref visible so agents can verify the source before use.",
                f"Maintain at least {MIN_SCENARIOS} real workflow benchmark scenarios before treating the skill as deployable.",
            ]
            if not resource_flags["has_agents_metadata"]:
                notes.append("Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.")
            if not resource_flags["has_scripts"] and category in {"Testing, QA & benchmarking", "Security, compliance & risk", "Science, research & data analysis", "DevOps, cloud & operations"}:
                notes.append("Add an executable validator or helper script so the workflow has objective checks.")
            if item["line_count"] > 500:
                notes.append("Move long background material into references/ to keep SKILL.md concise.")
            item["improvement_notes"] = notes[:5]
            item["explanation"] = {
                "what_it_covers": f"Source description: {description}",
                "how_an_agent_should_use_it": "Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.",
                "observed_structure": f"Headings: {', '.join(item['headings'][:5]) or 'none observed'}. Resources: {', '.join(k for k, v in resource_flags.items() if v) or 'none observed'}.",
                "notability": "Selected priority source." if source["tier"].startswith("priority") else f"Included from {source['group']} with explicit GitHub provenance.",
            }
            item["benchmark_scenarios"] = [f"skill-proof-{item['id']}"] + scenario_ids(category)
            entries.append(item)
    entries.sort(key=lambda e: (0 if e["source_tier"].startswith("priority") else 1, e["category"], e["source_repo"], e["source_path"]))
    return entries


def build_scenarios(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    track_lookup = {track[0]: track for track in TRACKS}
    scenarios: list[dict[str, Any]] = []
    present_categories = sorted({entry["category"] for entry in entries})
    for category in present_categories:
        track_ids = SCENARIO_TRACKS.get(category, SCENARIO_TRACKS["Coding, refactoring & repository automation"])
        for index, track_id in enumerate(track_ids, 1):
            _, title, _, problem, metrics = track_lookup[track_id]
            scenarios.append({
                "id": category_scenario_id(category, track_id),
                "category": category,
                "dataset_track_id": track_id,
                "title": f"{category} scenario {index}: {title}",
                "workflow": problem,
                "agent_task": "Load the skill in a fresh agent session, solve the workflow using the cited dataset/repository, capture commands and files consulted, and produce machine-checkable output.",
                "dataset_snapshot_policy": "Runner must record dataset release, crawl ID, tag, file date, or repository commit before scoring.",
                "input_selector": {"mode": "runner-selected-real-instance", "selection_rule": "choose a non-trivial instance from the cited dataset or workflow and record its immutable identifier"},
                "expected_output_schema": {"type": "object", "required": GENERIC_WORKFLOW_REQUIRED},
                "environment_requirements": ["fresh agent session", "read-only source checkout unless task requires patching", "network only when dataset retrieval requires it"],
                "evaluator_path": "evaluators/generic_workflow_result.schema.json",
                "required_artifacts": ["agent transcript or command log", "dataset/version reference", "output artifact", "objective evaluator result"],
                "objective_checks": metrics,
                "real_data_or_workflow": True,
            })
    for entry in entries:
        scenarios.append({
            "id": f"skill-proof-{entry['id']}",
            "category": entry["category"],
            "dataset_track_id": "source-skill-repository",
            "title": f"{entry['name']} source-grounded functionality proof",
            "workflow": f"Use the immutable source file {entry['immutable_source_url']} as the fixture and prove the agent can understand when and how to use the skill.",
            "agent_task": "In a fresh agent session, read only the recorded SKILL.md and directly referenced local resources, then produce an activation proof, misuse boundaries, required inputs, expected outputs, and one realistic task plan.",
            "dataset_snapshot_policy": "Pinned by the catalog entry commit_sha and immutable_source_url.",
            "input_selector": {"source_repo": entry["source_repo"], "source_path": entry["source_path"], "commit_sha": entry["commit_sha"]},
            "expected_output_schema": {"type": "object", "required": SOURCE_PROOF_REQUIRED},
            "environment_requirements": ["fresh agent session", "read-only access to mirrored or source skill directory", "no private credentials"],
            "evaluator_path": "evaluators/source_grounded_skill_proof.schema.json",
            "required_artifacts": ["source-grounded proof JSON", "source line/path citations", "agent transcript"],
                "objective_checks": ["frontmatter or fallback source structure used", "source citations present", "no unsupported capability claims"],
            "real_data_or_workflow": True,
        })
    return scenarios


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def esc(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def skill_manifest_entry(entry: dict[str, Any], name_conflict_group: str | None) -> dict[str, Any]:
    return {k: entry[k] for k in [
        "id",
        "name",
        "category",
        "subcategory",
        "install_name",
        "mirrored_path",
        "agent_ready_path",
        "source_repo",
        "source_path",
        "immutable_source_url",
        "selected_ref",
        "commit_sha",
        "benchmark_scenarios",
        "has_required_frontmatter",
        "skill_file_sha256",
        "skill_dir_sha256",
    ]} | {
        "name_conflict_group": name_conflict_group,
        "standalone_installable": bool(entry["has_required_frontmatter"]),
        "bulk_install_safe": bool(entry["has_required_frontmatter"] and name_conflict_group is None),
    }


def name_conflict_groups(entries: list[dict[str, Any]]) -> dict[str, str | None]:
    name_counts: dict[str, int] = {}
    for entry in entries:
        name_counts[entry["name"]] = name_counts.get(entry["name"], 0) + 1
    return {entry["id"]: entry["name"] if name_counts[entry["name"]] > 1 else None for entry in entries}


def mirror_all_skills(entries: list[dict[str, Any]]) -> None:
    target = ROOT / "included" / "skills"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    source_by_repo = {source["repo"]: source for source in SOURCES}
    conflicts = name_conflict_groups(entries)
    manifest = []
    for entry in entries:
        source = source_by_repo[entry["source_repo"]]
        repo_dir = SOURCE_ROOT / source["dir"]
        src_dir = (repo_dir / entry["source_path"]).parent
        dst_dir = ROOT / entry["mirrored_path"]
        dst_dir.parent.mkdir(parents=True, exist_ok=True)
        copy_sanitized_tree(src_dir, dst_dir)
        manifest.append(skill_manifest_entry(entry, conflicts[entry["id"]]) | {
            "source_group": entry["source_group"],
            "source_tier": entry["source_tier"],
        })
    write_json(target / "manifest.json", manifest)
    (target / "README.md").write_text(
        f"# Included Skills\n\n"
        f"This directory contains one physical mirror for each of the `{len(entries)}` cataloged source-backed skills.\n\n"
        "Skill mirrors are grouped by category and source tier, then isolated in a stable repository-and-path `install_name` directory so duplicate upstream skill names do not overwrite each other. "
        "Use `manifest.json` to trace every mirror back to its immutable source URL, commit, source path, and SHA-256 hashes.\n\n"
        "Do not bulk-install entries where `bulk_install_safe` is false.\n",
        encoding="utf-8",
    )


def write_agent_ready_skills(entries: list[dict[str, Any]]) -> None:
    target = ROOT / "included" / "agent-ready"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    manifest = []
    for entry in entries:
        path = ROOT / entry["agent_ready_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        rel_source = os.path.relpath(ROOT / entry["mirrored_path"] / "SKILL.md", path.parent).replace(os.sep, "/")
        body = f"""---
name: {json.dumps(entry["name"])}
description: {json.dumps(entry["description"])}
source_skill_id: {json.dumps(entry["id"])}
category: {json.dumps(entry["category"])}
source_mirror: {json.dumps(rel_source)}
benchmark_status: "artifact_gated"
---

# {entry["name"]}

Use this skill when the task matches the description above or the source path clearly applies. Start with this concise entrypoint; open `{rel_source}` only when implementation details, commands, assets, or references are needed.

## Workflow

1. Confirm the task matches this skill's scope.
2. Read the local source mirror if more detail is required.
3. Follow repository-level `AGENTS.md`; use one AI session only.
4. Keep claims tied to files, commands, citations, or benchmark artifacts.

## Verification

- Source mirror: `{rel_source}`
- Source commit: `{entry["commit_sha"]}`
- Static benchmark results: see `docs/benchmark-results.md`
- Runtime artifacts recorded by this entrypoint: `0`
- Assigned scenarios: {", ".join(f"`{scenario_id}`" for scenario_id in entry["benchmark_scenarios"])}

Do not claim this skill passed a runtime benchmark until a validated artifact exists.
"""
        path.write_text(body, encoding="utf-8")
        manifest.append({
            "id": entry["id"],
            "name": entry["name"],
            "category": entry["category"],
            "subcategory": entry["subcategory"],
            "install_name": entry["install_name"],
            "agent_ready_path": entry["agent_ready_path"],
            "source_mirrored_path": entry["mirrored_path"],
            "benchmark_status": entry["benchmark_status"],
        })
    write_json(target / "manifest.json", manifest)
    (target / "README.md").write_text(
        f"# Agent-Ready Skills\n\n"
        f"This directory contains `{len(entries)}` compact skill entrypoints, grouped by category and source tier. Each entrypoint is a separate `SKILL.md` file with frontmatter and a local pointer to the audited source mirror under `included/skills/`.\n\n"
        "Use these files when an agent needs a concise starting point. Use the source mirrors when full upstream detail is required.\n",
        encoding="utf-8",
    )


def write_priority_manifest(entries: list[dict[str, Any]]) -> None:
    target = ROOT / "included" / "priority"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    priority_entries = [entry for entry in entries if entry["source_tier"].startswith("priority")]
    conflicts = name_conflict_groups(entries)
    manifest = [skill_manifest_entry(entry, conflicts[entry["id"]]) for entry in priority_entries]
    write_json(target / "manifest.json", manifest)
    (target / "README.md").write_text(
        "# Priority Skills\n\n"
        "This directory is a priority subset manifest only. The actual skill directories are physically written once under `included/skills/` and are referenced by each entry's `mirrored_path`.\n\n"
        "Use `manifest.json` to trace priority entries back to immutable source URLs and unique `install_name` values. Do not bulk-install entries where `bulk_install_safe` is false.\n",
        encoding="utf-8",
    )


def build_source_lock(entries: list[dict[str, Any]]) -> dict[str, Any]:
    entries_by_repo: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        entries_by_repo.setdefault(entry["source_repo"], []).append(entry)
    declared_dirs = {source["dir"] for source in SOURCES}
    staged_dirs = {path.name for path in SOURCE_ROOT.iterdir() if path.is_dir()} if SOURCE_ROOT.exists() else set()
    sources = []
    for source in SOURCES:
        repo_dir = SOURCE_ROOT / source["dir"]
        repo_entries = sorted(entries_by_repo.get(source["repo"], []), key=lambda item: item["source_path"])
        if not repo_entries:
            continue
        commit = run_git(repo_dir, "rev-parse", "HEAD")
        origin_url = run_git(repo_dir, "config", "--get", "remote.origin.url")
        sources.append({
            "repo": source["repo"],
            "local_dir": source["dir"],
            "origin_url": origin_url,
            "selected_ref": source.get("tag") or "default-branch HEAD",
            "selection_policy": source["policy"],
            "commit_sha": commit,
            "tree_sha": run_git(repo_dir, "rev-parse", "HEAD^{tree}"),
            "skill_count": len(repo_entries),
            "skills": [
                {
                    "id": entry["id"],
                    "source_path": entry["source_path"],
                    "install_name": entry["install_name"],
                    "skill_file_sha256": entry["skill_file_sha256"],
                    "skill_dir_sha256": entry["skill_dir_sha256"],
                }
                for entry in repo_entries
            ],
        })
    return {
        "lock_version": 1,
        "hash_algorithm": "sha256",
        "generated_on": BUILD_DATE,
        "source_root": SOURCE_ROOT.as_posix(),
        "sources": sources,
        "unused_staged_source_dirs": sorted(staged_dirs - declared_dirs),
        "best_practice_sources": [
            source | {"offline_verification": "url recorded for review; not hashed into source skill catalog"}
            for source in BEST_PRACTICE_SOURCES
        ],
    }


def write_docs(entries: list[dict[str, Any]], scenarios: list[dict[str, Any]]) -> None:
    docs = ROOT / "docs"
    cat_dir = docs / "catalog" / "by-category"
    if cat_dir.exists():
        shutil.rmtree(cat_dir)
    skill_doc_root = docs / "catalog" / "skills"
    if skill_doc_root.exists():
        shutil.rmtree(skill_doc_root)
    cat_dir.mkdir(parents=True, exist_ok=True)
    skill_doc_dir = skill_doc_root / "by-category"
    skill_doc_dir.mkdir(parents=True, exist_ok=True)
    categories = sorted({e["category"] for e in entries})
    priority = [e for e in entries if e["source_tier"].startswith("priority")]

    (ROOT / "README.md").write_text(f"""# AI Skills Collection Benchmarked

> Early alpha: this repository is experimental. Many entries may be incomplete, incompatible, stale, or unsuitable for a given environment. Use it at your own risk; the maintainers accept no responsibility for results, failures, or downstream use.

Evidence-backed catalog of AI agent skills, with benchmark scenarios tied to real datasets and real repository workflows.

Repository scope:

- Catalog entries come from observed `SKILL.md` files in public GitHub repositories.
- Each entry records source repo, path, selected ref, immutable commit URL, category, and readiness caveat.
- Source discovery used a broad web and repository search, then offline verification against local checkouts.
- Priority ordering follows the source policy and lock files, not README-only claims.
- Scenario-covered candidates must have multiple benchmark scenarios before any runtime claim is considered.
- The benchmark suite defines realistic workflows and datasets; it does not claim a skill passed until a run artifact is recorded.

Current snapshot:

- `{len(entries)}` source-backed skill entries.
- `{len(entries)}` written skill mirrors under `included/skills/`.
- `{len(entries)}` compact agent-ready skill entrypoints under `included/agent-ready/`.
- `{len(priority)}` priority entries from selected repositories.
- `{len(categories)}` categories.
- `{len(scenarios)}` real-data scenario templates.
- Minimum `{MIN_SCENARIOS}` benchmark scenarios assigned per scenario-covered candidate.

Start here:

- [Methodology](docs/methodology.md)
- [Source policy](docs/source-policy.md)
- [Included skill mirrors](included/skills/README.md)
- [Agent-ready skills](included/agent-ready/README.md)
- [Priority skills](docs/priority-skills.md)
- [Catalog index](docs/catalog/index.md)
- [Benchmark suite](docs/benchmarks.md)
- [Benchmark results](docs/benchmark-results.md)
- [Skill quality findings](docs/skill-quality-findings.md)
- [Benchmark runner requirements](docs/benchmark-runner-requirements.md)
- [Host-agnostic installation](docs/installation.md)
- [Agent consumability checklist](docs/agent-consumability.md)

Validation:

```bash
python3 tools/validate_catalog.py
python3 -m pytest
```
""", encoding="utf-8")

    (docs / "methodology.md").write_text(f"""# Methodology

Snapshot date: `{BUILD_DATE}`. Inputs are local checkouts of public GitHub repositories.

Rules:

1. A broad web and repository search identifies candidate public skill sources.
2. GitHub sources with a latest release use that release tag.
3. GitHub sources without releases use current default branch HEAD and record the commit SHA.
4. Only observed `SKILL.md` files count as catalog skills.
5. Adjacent `AGENTS.md`, Copilot instructions, Cursor rules, commands, hooks, and benchmark folders are context, not counted skills.
6. Every scenario-covered candidate must have at least `{MIN_SCENARIOS}` real dataset or real workflow scenarios.
7. Every cataloged skill is physically mirrored under `included/skills/` and validated against recorded SHA-256 hashes.
8. Every cataloged skill also gets a compact agent-ready entrypoint under `included/agent-ready/`.

The repository provides catalog and benchmark definitions. A skill is not marked as having passed until an external run artifact is recorded.
""", encoding="utf-8")

    source_doc = "# Source Policy\n\n## Skill Sources\n\n"
    for source in SOURCES:
        source_doc += f"- `{source['repo']}`: {source['policy']}"
        if source.get("release_url"):
            source_doc += f" ([release]({source['release_url']}))"
        source_doc += "\n"
    source_doc += "\n## Best-Practice Sources Reviewed\n\n"
    for source in BEST_PRACTICE_SOURCES:
        source_doc += f"- [{source['title']}]({source['url']})\n"
    (docs / "source-policy.md").write_text(source_doc, encoding="utf-8")

    (docs / "installation.md").write_text("""# Host-Agnostic Installation

Validation does not require the original source checkouts:

```bash
python3 -m pip install -e '.[test]'
python3 tools/validate_catalog.py
python3 -m pytest
```

Catalog refresh does require source repositories. Put checkouts anywhere and point `AI_SKILL_SOURCE_ROOT` at that directory:

```bash
python3 tools/fetch_sources.py --source-root /path/to/ai_skill_sources
python3 tools/build_catalog.py --source-root /path/to/ai_skill_sources
```

Validation does not depend on `/tmp`, a local username, a private absolute path, or a specific host. Network-heavy benchmark execution should be performed by a separate runner that records dataset versions and artifacts.
""", encoding="utf-8")

    priority_doc = f"# Priority Skills\n\nPriority entries: `{len(priority)}`.\n\n| Skill | Category | Source | Ref | Scenarios |\n|---|---|---|---|---:|\n"
    for entry in priority:
        priority_doc += f"| `{esc(entry['name'])}` | {esc(entry['category'])} | [{esc(entry['source_repo'])}]({entry['immutable_source_url']}) | {esc(entry['selected_ref'])} | {len(entry['benchmark_scenarios'])} |\n"
    priority_doc += "\nPriority entries are a subset of the physical mirrors under `included/skills/`; `included/priority/manifest.json` points to the exact mirrored directory for each one. Adjacent agent instruction files and benchmark folders are documented as context in the source policy, not counted as skills.\n"
    (docs / "priority-skills.md").write_text(priority_doc, encoding="utf-8")

    index = f"# Catalog Index\n\nTotal entries: `{len(entries)}`. Every skill also has its own compact page under `docs/catalog/skills/by-category/`.\n\n| Category | Count | Category document |\n|---|---:|---|\n"
    for category in categories:
        filename = f"{slug(category)}.md"
        count = sum(e["category"] == category for e in entries)
        index += f"| {esc(category)} | {count} | [Open](by-category/{filename}) |\n"
    (docs / "catalog" / "index.md").write_text(index, encoding="utf-8")

    scenario_lookup = {s["id"]: s for s in scenarios}
    for category in categories:
        doc = f"# {category}\n\n"
        for entry in [e for e in entries if e["category"] == category]:
            skill_doc_rel = f"../skills/by-category/{slug(entry['category'])}/{slug(entry['subcategory'])}/{entry['install_name']}.md"
            doc += f"## {entry['name']} - {entry['source_repo']} `{entry['source_path']}`\n\n"
            doc += f"- Skill page: [{entry['install_name']}]({skill_doc_rel})\n"
            doc += f"- Mirrored skill: `{entry['mirrored_path']}`\n"
            doc += f"- Agent-ready entrypoint: `{entry['agent_ready_path']}`\n"
            doc += f"- Source: [{entry['source_repo']} `{entry['source_path']}`]({entry['immutable_source_url']})\n"
            doc += f"- Selected ref: `{entry['selected_ref']}`; commit `{entry['commit_sha'][:12]}`\n"
            doc += f"- What it covers: {entry['explanation']['what_it_covers']}\n"
            doc += f"- Agent use: {entry['explanation']['how_an_agent_should_use_it']}\n"
            doc += f"- Observed structure: {entry['explanation']['observed_structure']}\n"
            doc += f"- Notability: {entry['explanation']['notability']}\n"
            doc += "- Improvement and correction plan:\n"
            for note in entry["improvement_notes"]:
                doc += f"  - {note}\n"
            doc += "- Assigned benchmark scenarios:\n"
            for sid in entry["benchmark_scenarios"]:
                doc += f"  - `{sid}`: {scenario_lookup[sid]['workflow']}\n"
            doc += "\n"
            per_skill = f"""# {entry['name']}

Category: {entry['category']}

Mirrored skill: `{entry['mirrored_path']}`

Agent-ready entrypoint: `{entry['agent_ready_path']}`

Source: [{entry['source_repo']} `{entry['source_path']}`]({entry['immutable_source_url']})

Selected ref: `{entry['selected_ref']}`; commit `{entry['commit_sha'][:12]}`

## Use

{entry['explanation']['how_an_agent_should_use_it']}

## Scope

{entry['explanation']['what_it_covers']}

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

"""
            for sid in entry["benchmark_scenarios"]:
                per_skill += f"- `{sid}`: {scenario_lookup[sid]['workflow']}\n"
            per_skill += "\nImprovement notes:\n\n"
            for note in entry["improvement_notes"]:
                per_skill += f"- {note}\n"
            skill_path = skill_doc_dir / slug(entry["category"]) / slug(entry["subcategory"]) / f"{entry['install_name']}.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(per_skill.rstrip() + "\n", encoding="utf-8")
        (cat_dir / f"{slug(category)}.md").write_text(doc.rstrip() + "\n", encoding="utf-8")

    benchmark_doc = "# Benchmark Suite\n\nScenario definitions live in `data/benchmark_scenarios.json`; per-skill assignments live in `data/benchmark_assignments.json`.\n\n"
    category_template_count = len(scenarios) - len(entries)
    benchmark_doc += f"The current suite contains `{len(entries)}` source-grounded skill-proof scenarios and `{category_template_count}` category workflow templates. A scenario is only a template until a runner records artifacts under the rules in [Benchmark runner requirements](benchmark-runner-requirements.md).\n\n"
    benchmark_doc += "## Scoring Rules\n\nA benchmark run must record the skill ID, scenario ID, source commit, dataset or website snapshot, environment, commands or transcript, output artifact, objective metrics, and evaluator result. Synthetic fixtures may supplement coverage, but they do not replace a real source repository, real dataset, real website, or recorded runtime workflow when the scenario calls for one.\n\n"
    for track_id, title, url, problem, metrics in TRACKS:
        benchmark_doc += f"## {title}\n\n- ID: `{track_id}`\n- URL: {url}\n- Workflow: {problem}\n- Metrics: {', '.join(metrics)}\n\n"
    (docs / "benchmarks.md").write_text(benchmark_doc.rstrip() + "\n", encoding="utf-8")

    (docs / "benchmark-runner-requirements.md").write_text("""# Benchmark Runner Requirements

This repository defines benchmark scenarios. It does not mark a skill as passed until a separate runner records real artifacts for that skill and scenario.

Required for every benchmark run:

- Record `skill_id`, `scenario_id`, catalog commit, source repository commit, selected ref, runner version, model/runtime identifier, environment, and timestamp.
- Record the immutable dataset, website, source checkout, or workflow snapshot used for scoring.
- Save the agent transcript or command log, files read, files written, output artifact, metric values, and evaluator result.
- Keep synthetic fixtures as supplemental probes only. A synthetic fixture cannot replace the real dataset, website, source checkout, or workflow required by the scenario.
- Mark a runtime claim as passed only when objective checks pass and artifacts are available for review.

Visual parsing and browser skills:

- Test against actual websites or a recorded local mirror of an actual website, plus synthetic pages with known ground truth when useful.
- Save viewport size, screenshot or video evidence, DOM snapshot when available, interaction log, and expected-vs-observed extraction results.
- Include at least one layout change, dynamic state, or adverse condition such as lazy loading, modals, responsive breakpoints, or occluded content.

Context, memory, and retrieval skills:

- Use a long multi-step task with distractor material and delayed recall probes.
- Measure recall precision, missed facts, unsupported facts, and citation/path coverage.
- Record token usage before and after applying the skill. A memory or context-efficiency claim fails if token use increases without a documented quality gain.

Code, DevOps, and security skills:

- Run on real repositories, manifests, logs, or vulnerable fixtures with pinned commits or versions.
- Record commands, exit codes, patches, test results, scanner findings, and regression checks.
- Separate read-only audit results from changes that were actually applied and verified.

Data, science, and document skills:

- Use real public datasets, filings, papers, documents, or spreadsheets with immutable identifiers.
- Record schema assumptions, cleaning decisions, row counts, units, citations, and reproducible analysis commands.
- Validate numeric outputs against an independent calculation or dataset-provided ground truth where possible.
""", encoding="utf-8")

    (docs / "agent-consumability.md").write_text(f"""# Agent Consumability Checklist

Mechanical checks:

- `SKILL.md` exists at the recorded source path.
- `name`, description, source URL, immutable URL, selected ref, and commit SHA are recorded.
- Selected ref is latest release tag where available, otherwise default branch HEAD with explicit no-release policy.
- At least `{MIN_SCENARIOS}` real workflow scenarios are assigned to every scenario-covered candidate.
- Improvement notes are derived from observed file structure.

Runtime proof requires running the scenario in the target agent environment and saving artifacts.
""", encoding="utf-8")


def write_evaluators() -> None:
    directory = ROOT / "evaluators"
    directory.mkdir(exist_ok=True)
    generic = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Generic workflow benchmark result",
        "type": "object",
        "required": GENERIC_WORKFLOW_REQUIRED,
        "properties": {
            "inputs": {"type": "object"},
            "steps": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "outputs": {"type": "object"},
            "metrics": {"type": "object"},
            "citations_or_paths": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "runner_environment": {"type": "object"},
        },
        "additionalProperties": True,
    }
    proof = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Source-grounded skill proof",
        "type": "object",
        "required": SOURCE_PROOF_REQUIRED,
        "properties": {
            "activation_conditions": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "required_context": {"type": "array", "items": {"type": "string"}},
            "safe_boundaries": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "workflow_steps": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "proof_evidence": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["source_path", "line_or_section", "claim"],
                    "properties": {
                        "source_path": {"type": "string"},
                        "line_or_section": {"type": "string"},
                        "claim": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "minItems": 1,
            },
        },
        "additionalProperties": True,
    }
    benchmark_run = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Benchmark run artifact",
        "type": "object",
        "required": [
            "artifact_version",
            "skill_id",
            "scenario_id",
            "catalog_commit",
            "source_commit",
            "source_repo",
            "source_path",
            "runner",
            "scenario_requirements",
            "input_snapshot",
            "execution",
            "outputs",
            "metrics",
            "evidence",
            "objective_checks",
        ],
        "properties": {
            "artifact_version": {"type": "string", "pattern": "^1\\."},
            "skill_id": {"type": "string"},
            "scenario_id": {"type": "string"},
            "catalog_commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "source_commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "source_repo": {"type": "string"},
            "source_path": {"type": "string"},
            "runner": {
                "type": "object",
                "required": ["timestamp_utc", "tool", "model_or_runtime"],
                "properties": {
                    "timestamp_utc": {"type": "string"},
                    "tool": {"type": "string"},
                    "model_or_runtime": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "scenario_requirements": {
                "type": "object",
                "properties": {
                    "visual_or_browser": {"type": "boolean"},
                    "context_memory": {"type": "boolean"},
                    "token_efficiency_claim": {"type": "boolean"},
                },
                "additionalProperties": True,
            },
            "input_snapshot": {
                "type": "object",
                "required": ["kind", "identifier", "is_real"],
                "properties": {
                    "kind": {"type": "string"},
                    "identifier": {"type": "string"},
                    "is_real": {"type": "boolean"},
                },
                "additionalProperties": True,
            },
            "execution": {
                "type": "object",
                "required": ["fresh_session", "commands_or_transcript_path"],
                "properties": {
                    "fresh_session": {"type": "boolean"},
                    "commands_or_transcript_path": {"type": "string"},
                },
                "additionalProperties": True,
            },
            "outputs": {"type": "object"},
            "metrics": {"type": "object"},
            "evidence": {
                "type": "object",
                "required": ["artifact_paths", "citations_or_paths"],
                "properties": {
                    "artifact_paths": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "citations_or_paths": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "visual": {"type": "object"},
                    "context_memory": {"type": "object"},
                },
                "additionalProperties": True,
            },
            "objective_checks": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        },
        "additionalProperties": True,
    }
    write_json(directory / "generic_workflow_result.schema.json", generic)
    write_json(directory / "source_grounded_skill_proof.schema.json", proof)
    write_json(directory / "benchmark_run_artifact.schema.json", benchmark_run)


def main() -> None:
    global SOURCE_ROOT
    parser = argparse.ArgumentParser(description="Build the AI skill catalog from local source checkouts.")
    parser.add_argument("--source-root", default=str(SOURCE_ROOT), help="Directory containing source repo checkouts. Defaults to AI_SKILL_SOURCE_ROOT or /tmp/ai_skill_sources.")
    args = parser.parse_args()
    SOURCE_ROOT = Path(args.source_root).expanduser().resolve()
    entries = collect()
    scenarios = build_scenarios(entries)
    tracks = [{"id": t[0], "title": t[1], "url": t[2], "kind": "real dataset or repository workflow", "problem": t[3], "metrics": t[4]} for t in TRACKS]
    write_json(ROOT / "data" / "skills_catalog.json", entries)
    write_json(ROOT / "data" / "best_practice_sources.json", BEST_PRACTICE_SOURCES)
    write_json(ROOT / "data" / "benchmark_tracks.json", tracks)
    write_json(ROOT / "data" / "benchmark_scenarios.json", scenarios)
    write_json(ROOT / "data" / "benchmark_assignments.json", [{"skill_id": e["id"], "scenario_ids": e["benchmark_scenarios"]} for e in entries])
    write_json(ROOT / "data" / "source_lock.json", build_source_lock(entries))
    mirror_all_skills(entries)
    write_agent_ready_skills(entries)
    write_priority_manifest(entries)
    write_docs(entries, scenarios)
    write_evaluators()
    # Tests and validation are hand-maintained so they can check generated
    # outputs independently instead of being overwritten by the generator.
    print(f"Generated {len(entries)} skills and {len(scenarios)} scenarios.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate an evidence-backed AI skill catalog and benchmark suite.

Refresh inputs are local checkouts of public GitHub repositories. The generated
catalog never counts repo-only guesses as skills: each item must come from an
observed SKILL.md file and carry an immutable commit URL.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

import _catalog_publication as publication
import update_readme_badges
from _lib_b import credential_neutralizations, dependency_graphs
from _lib_b.credential_patterns import V2_NEUTRALIZATIONS
from _lib_b.determinism import existing_field, git_latest_commit_epoch_for, resolve_timestamp

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = Path(os.environ.get("AI_SKILL_SOURCE_ROOT", "/tmp/ai_skill_sources"))
BUILD_DATE = "2026-04-17"
CREDENTIAL_POLICY_VERSION = 1
MIN_SCENARIOS = 3
GENERIC_WORKFLOW_REQUIRED = ["inputs", "steps", "outputs", "metrics", "citations_or_paths"]
SOURCE_PROOF_REQUIRED = [
    "activation_conditions",
    "required_context",
    "safe_boundaries",
    "workflow_steps",
    "proof_evidence",
]
SECRET_PLACEHOLDERS = [
    (re.compile(r"AIza[0-9A-Za-z_-]{35}"), "<GOOGLE_API_KEY>"),
    (re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"), "<AWS_ACCESS_KEY_ID>"),
    (re.compile(r"(?<![A-Za-z0-9_-])sk-(?:proj-)?[A-Za-z0-9_]{20,}(?![A-Za-z0-9_-])"), "<OPENAI_API_KEY>"),
    (
        re.compile(
            r"(?<![A-Za-z0-9_-])sk-(?:proj-)?(?:[xX][xX-]{2,}|\.{3}|[A-Za-z0-9][A-Za-z0-9_.-]*\.{3})(?![A-Za-z0-9_-])"
        ),
        "<API_KEY>",
    ),
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
    {
        "repo": "strmt7/simple_ai_bitcoin_trading_binance",
        "dir": "strmt7__simple_ai_bitcoin_trading_binance",
        "tier": "selected-project-reference",
        "group": "selected project repository",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
        "prefixes": [".agents/skills/"],
        "selected_subset": True,
    },
    {
        "repo": "strmt7/ome-zarr-C",
        "dir": "strmt7__ome-zarr-C",
        "tier": "selected-project-reference",
        "group": "selected project repository",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
        "prefixes": [".agents/skills/"],
        "selected_subset": True,
    },
    {
        "repo": "strmt7/project_air_defense",
        "dir": "strmt7__project_air_defense",
        "tier": "selected-project-reference",
        "group": "selected project repository",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
        "prefixes": [".agents/skills/", "skills/"],
        "selected_subset": True,
    },
    {
        "repo": "ZMB-UZH/omero-docker-extended",
        "dir": "ZMB-UZH__omero-docker-extended",
        "tier": "selected-omero-reference",
        "group": "selected OMERO repository",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
        "prefixes": [".agents/skills/", "third_party/"],
        "selected_subset": True,
    },
    {
        "repo": "anthropics/skills",
        "dir": "anthropics__skills",
        "tier": "official-reference",
        "group": "official skill reference",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
        "prefixes": ["skills/"],
        "exclude_prefixes": ["template/"],
    },
    {
        "repo": "K-Dense-AI/scientific-agent-skills",
        "dir": "K-Dense-AI__scientific-agent-skills",
        "tier": "latest-release-community",
        "group": "latest release scientific skills",
        "policy": "latest GitHub release v2.37.1",
        "tag": "v2.37.1",
        "release_url": "https://github.com/K-Dense-AI/scientific-agent-skills/releases/tag/v2.37.1",
        "prefixes": ["scientific-skills/"],
    },
    {
        "repo": "microsoft/skills",
        "dir": "microsoft__skills",
        "tier": "official-vendor-reference",
        "group": "Microsoft skills reference",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
        "prefixes": [".github/plugins/", ".github/skills/"],
    },
    {
        "repo": "trailofbits/skills",
        "dir": "trailofbits__skills",
        "tier": "security-reference",
        "group": "security and audit skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "ahmedasmar/devops-claude-skills",
        "dir": "ahmedasmar__devops-claude-skills",
        "tier": "devops-reference",
        "group": "DevOps skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "akin-ozer/cc-devops-skills",
        "dir": "akin-ozer__cc-devops-skills",
        "tier": "latest-release-devops",
        "group": "latest release DevOps skills",
        "policy": "latest GitHub release v1.0.0",
        "tag": "v1.0.0",
        "release_url": "https://github.com/akin-ozer/cc-devops-skills/releases/tag/v1.0.0",
    },
    {
        "repo": "composio-community/support-skills",
        "dir": "composio-community__support-skills",
        "tier": "support-reference",
        "group": "customer support skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "browser-act/skills",
        "dir": "browser-act__skills",
        "tier": "browser-automation-reference",
        "group": "browser and web automation skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "lackeyjb/playwright-skill",
        "dir": "lackeyjb__playwright-skill",
        "tier": "latest-release-browser-automation",
        "group": "latest release browser automation skill",
        "policy": "latest GitHub release v4.1.0",
        "tag": "v4.1.0",
        "release_url": "https://github.com/lackeyjb/playwright-skill/releases/tag/v4.1.0",
    },
    {
        "repo": "twwch/comfyui-workflow-skill",
        "dir": "twwch__comfyui-workflow-skill",
        "tier": "creative-reference",
        "group": "creative media skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "EvoLinkAI/video-generation-skill-for-openclaw",
        "dir": "EvoLinkAI__video-generation-skill-for-openclaw",
        "tier": "creative-reference",
        "group": "creative media skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "EvoLinkAI/music-generation-skill-for-openclaw",
        "dir": "EvoLinkAI__music-generation-skill-for-openclaw",
        "tier": "creative-reference",
        "group": "creative media skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "designrique/ai-graphic-design-skill",
        "dir": "designrique__ai-graphic-design-skill",
        "tier": "creative-reference",
        "group": "creative media skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "yuvalsuede/agent-media-skill",
        "dir": "yuvalsuede__agent-media-skill",
        "tier": "creative-reference",
        "group": "creative media skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "Raven7979/ai-video-editing-skill",
        "dir": "Raven7979__ai-video-editing-skill",
        "tier": "creative-reference",
        "group": "creative media skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "ztj7728/gemini-image-generation",
        "dir": "ztj7728__gemini-image-generation",
        "tier": "creative-reference",
        "group": "creative media skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "fruteroclub/marketing-designer",
        "dir": "fruteroclub__marketing-designer",
        "tier": "creative-reference",
        "group": "creative media skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "Bria-AI/bria-skill",
        "dir": "Bria-AI__bria-skill",
        "tier": "latest-release-creative",
        "group": "latest release creative media skills",
        "policy": "latest GitHub release v1.3.1",
        "tag": "v1.3.1",
        "release_url": "https://github.com/Bria-AI/bria-skill/releases/tag/v1.3.1",
    },
    {
        "repo": "nextlevelbuilder/ui-ux-pro-max-skill",
        "dir": "nextlevelbuilder__ui-ux-pro-max-skill",
        "tier": "latest-release-creative",
        "group": "latest release UI/UX skills",
        "policy": "latest GitHub release v2.5.0",
        "tag": "v2.5.0",
        "release_url": "https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/releases/tag/v2.5.0",
    },
    {
        "repo": "guinacio/claude-image-gen",
        "dir": "guinacio__claude-image-gen",
        "tier": "latest-release-creative",
        "group": "latest release image generation skill",
        "policy": "latest GitHub release 1.0.2",
        "tag": "1.0.2",
        "release_url": "https://github.com/guinacio/claude-image-gen/releases/tag/1.0.2",
    },
    {
        "repo": "hugohe3/ppt-master",
        "dir": "hugohe3__ppt-master",
        "category": "Documents, spreadsheets & presentations",
        "tier": "latest-release-creative",
        "group": "latest release presentation skill",
        "policy": "latest GitHub release v6.6.0",
        "tag": "v6.6.0",
        "release_url": "https://github.com/hugohe3/ppt-master/releases/tag/v6.6.0",
    },
    {
        "repo": "aizzaku/create-infographics",
        "dir": "aizzaku__create-infographics",
        "tier": "creative-reference",
        "group": "creative media skills",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "Varnan-Tech/opendirectory",
        "dir": "Varnan-Tech__opendirectory",
        "tier": "reddit-verified-gtm-registry",
        "group": "Reddit r/codex open-source Codex skills signal; GitHub SKILL.md files verified",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
        "prefixes": ["packages/cli/skills/"],
        "max_path_parts": 5,
    },
    {
        "repo": "supermemoryai/skills",
        "dir": "supermemoryai__skills",
        "tier": "reddit-verified-creative-skill",
        "group": "Reddit r/codex linked skill; GitHub SKILL.md verified",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
        "prefixes": ["svg-animations/"],
    },
    {
        "repo": "hardikpandya/stop-slop",
        "dir": "hardikpandya__stop-slop",
        "tier": "reddit-verified-writing-skill",
        "group": "Reddit r/codex linked skill; GitHub SKILL.md verified",
        "policy": "default-branch HEAD; GitHub API reported no latest release",
    },
    {
        "repo": "affaan-m/everything-claude-code",
        "dir": "affaan-m__everything-claude-code",
        "tier": "selected-structure-reference",
        "group": "selected repository structure reference",
        "policy": "latest GitHub release v1.10.0",
        "tag": "v1.10.0",
        "release_url": "https://github.com/affaan-m/everything-claude-code/releases/tag/v1.10.0",
        "prefixes": [".agents/skills/"],
    },
]


BEST_PRACTICE_SOURCES = [
    {
        "id": "anthropic-skill-best-practices",
        "title": "Anthropic skill authoring best practices",
        "url": "https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices",
    },
    {"id": "mdskills-open-ecosystem", "title": "mdskills.ai open skills ecosystem", "url": "https://www.mdskills.ai/"},
    {
        "id": "github-copilot-instructions",
        "title": "GitHub Copilot repository custom instructions",
        "url": "https://docs.github.com/en/copilot/how-tos/use-copilot-agents/request-a-code-review/configure-coding-guidelines",
    },
    {"id": "skillsbench-paper", "title": "SkillsBench benchmark paper", "url": "https://arxiv.org/abs/2602.12670"},
    {
        "id": "skill-usage-paper",
        "title": "Skill usage benchmark code",
        "url": "https://github.com/UCSB-NLP-Chang/Skill-Usage",
    },
    {
        "id": "reddit-agent-skills-worth-installing",
        "title": "Forum signal: practical skill use",
        "url": "https://www.reddit.com/r/claude/comments/1s51b5u/the_claude_code_skills_actually_worth_installing/",
    },
    {
        "id": "reddit-skills-subagents-patterns",
        "title": "Forum signal: skills and subagents",
        "url": "https://www.reddit.com/r/ClaudeAI/comments/1qbc30u/claude_code_skills_subagents_feel_misaligned_what/",
    },
    {
        "id": "reddit-codex-open-source-skills",
        "title": "Forum signal: open-source Codex skills",
        "url": "https://www.reddit.com/r/codex/comments/1sns7hr/top_10_opensource_codex_skills/",
    },
    {
        "id": "opendirectory-gtm-skills",
        "title": "OpenDirectory GTM skills registry",
        "url": "https://github.com/Varnan-Tech/opendirectory",
    },
]


TRACKS = [
    (
        "source-skill-repository",
        "Source skill repository proof",
        "https://github.com/strmt7/ai_skills_collection_benchmarked",
        "Use the skill source repository itself as the proof fixture: inspect SKILL.md, companion resources, and source path to verify trigger, constraints, and expected artifacts.",
        ["frontmatter valid", "trigger derivable", "proof artifact schema valid"],
    ),
    (
        "swe-bench-lite",
        "SWE-bench Lite",
        "https://github.com/SWE-bench/SWE-bench",
        "Patch real GitHub issue tasks and verify with repository tests.",
        ["patch applies", "test pass rate", "regression count"],
    ),
    (
        "nyc-tlc-trip-records",
        "NYC TLC trip records",
        "https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page",
        "Clean, aggregate, and explain large real trip data.",
        ["schema correctness", "aggregation accuracy", "runtime budget"],
    ),
    (
        "sec-edgar-companyfacts",
        "SEC EDGAR company facts",
        "https://www.sec.gov/edgar/sec-api-documentation",
        "Extract and reconcile financial facts from filings.",
        ["citation coverage", "numeric reconciliation", "filing provenance"],
    ),
    (
        "common-crawl-warc",
        "Common Crawl WARC",
        "https://commoncrawl.org/",
        "Retrieve, parse, and cite web-scale documents.",
        ["source precision", "deduplication", "citation traceability"],
    ),
    (
        "beir-retrieval",
        "BEIR retrieval benchmark",
        "https://github.com/beir-cellar/beir",
        "Evaluate retrieval workflows across datasets.",
        ["nDCG@10", "recall@100", "query latency"],
    ),
    (
        "ms-marco",
        "MS MARCO",
        "https://microsoft.github.io/msmarco/",
        "Rank passages and support answer extraction.",
        ["MRR", "recall", "answer support"],
    ),
    (
        "enron-email",
        "CMU Enron email dataset",
        "https://www.cs.cmu.edu/~enron/",
        "Classify, summarize, and route real email threads.",
        ["routing accuracy", "PII handling", "summary faithfulness"],
    ),
    (
        "stackoverflow-survey",
        "Stack Overflow Developer Survey",
        "https://survey.stackoverflow.co/",
        "Analyze survey data and produce reproducible charts.",
        ["cleaning correctness", "chart reproducibility", "method clarity"],
    ),
    (
        "ome-ngff-samples",
        "OME-NGFF sample data",
        "https://idr.github.io/ome-ngff-samples/",
        "Read and validate multiscale microscopy data.",
        ["metadata validity", "chunk correctness", "shape parity"],
    ),
    (
        "cellxgene-census",
        "CZ CELLxGENE Census",
        "https://chanzuckerberg.github.io/cellxgene-census/",
        "Query and analyze single-cell expression data.",
        ["query correctness", "metadata filters", "reproducibility"],
    ),
    (
        "chembl",
        "ChEMBL",
        "https://www.ebi.ac.uk/chembl/",
        "Retrieve molecular bioactivity records.",
        ["identifier accuracy", "filter correctness", "citation provenance"],
    ),
    (
        "owasp-benchmark",
        "OWASP Benchmark",
        "https://owasp.org/www-project-benchmark/",
        "Find and classify vulnerability test cases.",
        ["true positives", "false positives", "CWE mapping"],
    ),
    (
        "owasp-juice-shop",
        "OWASP Juice Shop",
        "https://owasp.org/www-project-juice-shop/",
        "Run safe local security workflows against a known vulnerable app.",
        ["finding reproducibility", "risk classification", "remediation quality"],
    ),
    (
        "kubernetes-examples",
        "Kubernetes examples",
        "https://github.com/kubernetes/examples",
        "Validate manifests and operational runbooks.",
        ["schema validity", "least privilege", "rollout success"],
    ),
    (
        "opentelemetry-demo",
        "OpenTelemetry demo",
        "https://github.com/open-telemetry/opentelemetry-demo",
        "Debug telemetry across microservices.",
        ["trace completeness", "metric coverage", "diagnostic accuracy"],
    ),
    (
        "coco-captions",
        "COCO captions",
        "https://cocodataset.org/#download",
        "Evaluate image understanding and visual QA tasks.",
        ["caption faithfulness", "object coverage", "layout accuracy"],
    ),
    (
        "local-omero-compose-workflows",
        "ZMB-UZH OMERO workflows",
        "https://github.com/ZMB-UZH/omero-docker-extended",
        "Validate OMERO deployment, plugin, upload/import, and monitoring workflows.",
        ["compose health", "plugin workflow", "regression count"],
    ),
    (
        "air-defense-android-benchmarks",
        "Project Air Defense Android benchmarks",
        "https://github.com/strmt7/project_air_defense/tree/main/benchmarks",
        "Run startup, gameplay, and visual QA benchmark scenarios.",
        ["startup time", "frame stability", "visual regressions"],
    ),
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
    "OMERO, Django, Docker & lab infrastructure": [
        "local-omero-compose-workflows",
        "ome-ngff-samples",
        "opentelemetry-demo",
    ],
    "Agent infrastructure & skill creation": ["beir-retrieval", "swe-bench-lite", "common-crawl-warc"],
}


CATEGORY_KEYWORDS = [
    (
        "OMERO, Django, Docker & lab infrastructure",
        ["omero", "django", "postgres", "docker-patterns", "env-contract", "plugin-regression"],
    ),
    ("Game, mobile & visual QA", ["ue5", "android", "mobile", "game", "city", "rendering", "visual-qa", "air-defense"]),
    (
        "Science, research & data analysis",
        [
            "scientific",
            "science",
            "bio",
            "chem",
            "cell",
            "gene",
            "rdkit",
            "zarr",
            "scanpy",
            "pydicom",
            "molecular",
            "clinical",
            "lab",
        ],
    ),
    (
        "Cloud, Azure & Microsoft SDKs",
        ["azure", "m365", "microsoft", "foundry", "eventhub", "cosmos", "servicebus", "keyvault", "webjobs"],
    ),
    (
        "Security, compliance & risk",
        [
            "security",
            "compliance",
            "secret",
            "rbac",
            "content-safety",
            "auth",
            "vulnerability",
            "audit",
            "semgrep",
            "codeql",
            "fuzz",
            "sarif",
            "sandbox",
            "risk",
            "yara",
            "zeroize",
        ],
    ),
    (
        "Testing, QA & benchmarking",
        [
            "test",
            "qa",
            "benchmark",
            "regression",
            "playwright",
            "verification",
            "tdd",
            "parity",
            "mutation",
            "coverage",
            "wycheproof",
        ],
    ),
    (
        "DevOps, cloud & operations",
        [
            "deploy",
            "kubernetes",
            "k8s",
            "cloud",
            "workflow",
            "supply-chain",
            "monitor",
            "monitoring",
            "observability",
            "diagnostic",
            "terraform",
            "terragrunt",
            "helm",
            "ansible",
            "promql",
            "logql",
            "jenkins",
            "gitlab",
            "ci",
            "ci-cd",
            "gitops",
            "dockerfile",
            "pipeline",
            "bash",
        ],
    ),
    (
        "Documents, spreadsheets & presentations",
        ["pdf", "docx", "xlsx", "pptx", "slides", "poster", "document", "spreadsheet", "presentation"],
    ),
    (
        "Creative, media & design",
        [
            "image",
            "video",
            "music",
            "audio",
            "art",
            "gif",
            "podcast",
            "schematic",
            "visualization",
            "infographic",
            "brand",
            "designer",
            "figma",
            "comfyui",
            "bria",
            "ux",
            "svg",
            "animation",
            "logo",
            "icon",
            "illustration",
            "cover",
            "thumbnail",
        ],
    ),
    (
        "Communication, productivity & support",
        [
            "support",
            "ticket",
            "customer",
            "zendesk",
            "intercom",
            "freshdesk",
            "sla",
            "refund",
            "response",
            "whatsapp",
            "csat",
            "nps",
            "inbox",
            "handoff",
            "call-summary",
            "slack",
            "internal-comms",
            "meeting",
            "writing",
            "prose",
            "blog",
            "newsletter",
            "linkedin",
            "twitter",
            "reddit",
            "hackernews",
            "outreach",
            "standup",
            "gtm",
        ],
    ),
    (
        "Search, retrieval & web automation",
        [
            "search",
            "lookup",
            "retrieval",
            "web",
            "parallel-web",
            "database-lookup",
            "documentation-lookup",
            "site-extract",
            "browser-act",
            "scraper",
            "youtube",
            "google",
            "maps",
            "wechat",
            "zhihu",
            "seo",
            "trends",
            "keyword",
        ],
    ),
    (
        "Finance, commerce & forecasting",
        ["finance", "fiscal", "trading", "market", "forecast", "cost", "amazon", "product", "sales", "commerce"],
    ),
    ("Frontend, UI & browser automation", ["frontend", "browser", "ui", "webapp", "canvas", "theme", "react"]),
    (
        "Agent infrastructure & skill creation",
        ["agent", "mcp", "context", "source-audit", "creator", "continual-learning"],
    ),
]


def run_git(path: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "item"


GENERIC_SKILL_PATH_PARTS = {
    ".agents",
    ".claude",
    ".cursor",
    ".github",
    ".kiro",
    "agents",
    "claude-skills",
    "docs",
    "plugins",
    "skill",
    "skills",
}
GENERIC_REPO_NAMES = {"skill", "skills"}


def repo_identity_slug(source_repo: str) -> str:
    owner, _, repo = source_repo.partition("/")
    repo_value = slug(repo or source_repo)
    if repo_value in GENERIC_REPO_NAMES:
        return slug(owner)
    return repo_value


def source_path_slug(source_path: str) -> str:
    parts = [slug(part) for part in Path(source_path).parts[:-1]]
    meaningful = [part for part in parts if part and part not in GENERIC_SKILL_PATH_PARTS]
    return slug("-".join(meaningful[-3:] or parts[-1:] or ["skill"]))


def base_install_name(skill_name: str, source_path: str) -> str:
    name_slug = slug(skill_name)
    if name_slug != "item" and name_slug not in GENERIC_SKILL_PATH_PARTS:
        return name_slug
    return source_path_slug(source_path)


def unique_install_name(entry: dict[str, Any], used_names: set[str], base_counts: dict[str, int]) -> str:
    base = base_install_name(entry["name"], entry["source_path"])
    source_identity = repo_identity_slug(entry["source_repo"])
    path_identity = source_path_slug(entry["source_path"])
    full_source_identity = slug(
        f"{entry['source_repo']} {entry['source_path'].removesuffix('/SKILL.md').removesuffix('SKILL.md')}"
    )

    if base_counts[base] == 1:
        candidates = [base, f"{base}--{source_identity}", f"{base}--{path_identity}"]
    else:
        candidates = [
            f"{base}--{source_identity}",
            f"{base}--{path_identity}",
            f"{base}--{source_identity}-{path_identity}",
        ]
    candidates.append(f"{base}--{full_source_identity}")

    for candidate in candidates:
        value = slug(candidate)
        if value not in used_names:
            used_names.add(value)
            return value
    raise ValueError(f"could not allocate unique install_name for {entry['id']}")


def assign_install_names(entries: list[dict[str, Any]]) -> None:
    base_counts: dict[str, int] = {}
    for entry in entries:
        base = base_install_name(entry["name"], entry["source_path"])
        base_counts[base] = base_counts.get(base, 0) + 1

    used_names: set[str] = set()
    for entry in sorted(entries, key=lambda item: item["id"]):
        entry_install_name = unique_install_name(entry, used_names, base_counts)
        entry["install_name"] = entry_install_name
        entry["mirrored_path"] = skill_mirror_path(entry["category"], entry["subcategory"], entry_install_name)
        entry["agent_ready_path"] = skill_agent_ready_path(entry["category"], entry["subcategory"], entry_install_name)


def install_name(
    entry_or_repo: dict[str, Any] | str, source_path: str | None = None, skill_name: str | None = None
) -> str:
    if isinstance(entry_or_repo, dict):
        return base_install_name(entry_or_repo["name"], entry_or_repo["source_path"])
    assert source_path is not None
    return base_install_name(skill_name or Path(source_path).parent.name, source_path)


def validate_credential_policy(credential_policy: int) -> None:
    if type(credential_policy) is not int or credential_policy not in {1, 2, 3}:
        raise ValueError("unknown credential neutralization policy")


def sanitize_secret_like_text(text: str, *, credential_policy: int = 1) -> str:
    validate_credential_policy(credential_policy)
    for pattern, placeholder in SECRET_PLACEHOLDERS:
        text = pattern.sub(placeholder, text)
    if credential_policy >= 2:
        for pattern, placeholder in V2_NEUTRALIZATIONS:
            text = pattern.sub(placeholder, text)
    return text


def normalize_text_file(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"^ +\t", "\t", line.rstrip(" \t")) for line in text.split("\n")]
    return "\n".join(lines).rstrip("\n") + "\n"


def sanitized_file_bytes(path: Path, *, credential_policy: int = 1) -> bytes:
    validate_credential_policy(credential_policy)
    data = path.read_bytes()
    if b"\0" in data:
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    # Dependency remediation must replace a qualified complete graph in an
    # explicit repair/source refresh. Never synthesize package resolutions while
    # hashing or copying: doing so can downgrade versions and conceal real bytes.
    text = normalize_text_file(sanitize_secret_like_text(text, credential_policy=credential_policy))
    if credential_policy == 3:
        text = credential_neutralizations.neutralize(text)
    return text.encode("utf-8")


def sha256_file(path: Path, *, credential_policy: int = 1) -> str:
    digest = hashlib.sha256()
    digest.update(sanitized_file_bytes(path, credential_policy=credential_policy))
    return digest.hexdigest()


def is_under_nested_skill(root: Path, item: Path) -> bool:
    parent = item.parent
    while parent != root:
        if (parent / "SKILL.md").is_file():
            return True
        parent = parent.parent
    return False


def _portable_mode(st_mode: int) -> int:
    # Host-portable file mode (git-style): regular file is 0o100644; if any
    # execute bit is set we record 0o100755. Umask and per-checkout permission
    # drift (e.g. different clones on different systems) must not change the
    # tree hash, so we never record the raw st_mode.
    executable = bool(st_mode & 0o111)
    return 0o100755 if executable else 0o100644


@lru_cache(maxsize=8)
def _indexed_modes(root: Path, index_stamp: tuple[int, int]) -> dict[Path, int]:
    """Git preserves executable bits that NTFS file stats cannot represent."""
    output = subprocess.check_output(["git", "-C", str(root), "ls-files", "--stage", "-z"])
    modes = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, filename = record.split(b"\t", 1)
        mode, _, stage = metadata.split()
        if stage != b"0":
            raise ValueError(f"cannot hash an unmerged Git index in {root}")
        if mode in {b"100644", b"100755"}:
            modes[root / os.fsdecode(filename)] = int(mode, 8)
    return modes


def _git_modes(path: Path) -> dict[Path, int]:
    root = path.resolve()
    while root != root.parent and not (root / ".git").exists():
        root = root.parent
    git_path = root / ".git"
    if not git_path.exists():
        return {}
    if git_path.is_file():
        location = git_path.read_text(encoding="utf-8").strip()
        if not location.startswith("gitdir: "):
            raise ValueError(f"invalid Git directory pointer in {root}")
        git_path = (root / location.removeprefix("gitdir: ")).resolve()
    index = git_path / "index"
    if not index.is_file():
        return {}
    info = index.stat()
    return _indexed_modes(root, (info.st_mtime_ns, info.st_size))


def skill_tree_files(path: Path) -> list[Path]:
    """Enumerate the same resource boundary for hashing and copying; fail on I/O errors."""
    ignored_parts = {".git", "__pycache__"}
    files: list[Path] = []
    root_stat = path.resolve().stat()
    seen_dirs = {(root_stat.st_dev, root_stat.st_ino)}

    def raise_walk_error(error: OSError) -> None:
        raise error

    for current, dirs, names in os.walk(path, followlinks=True, onerror=raise_walk_error):
        current_path = Path(current)
        kept_dirs: list[str] = []
        for dirname in dirs:
            child = current_path / dirname
            if dirname in ignored_parts or (child != path and (child / "SKILL.md").is_file()):
                continue
            child_stat = child.resolve().stat()
            key = (child_stat.st_dev, child_stat.st_ino)
            if key in seen_dirs:
                continue
            seen_dirs.add(key)
            kept_dirs.append(dirname)
        dirs[:] = kept_dirs
        for name in names:
            item = current_path / name
            if ignored_parts.intersection(item.parts) or is_under_nested_skill(path, item):
                continue
            if not stat.S_ISREG(item.stat().st_mode):
                raise ValueError(f"unsupported nonregular skill resource: {item.relative_to(path)}")
            files.append(item)
    return sorted(files, key=lambda p: p.relative_to(path).as_posix())


def skill_file_modes(path: Path) -> dict[str, str]:
    """Persist source Git modes, including executable files copied onto NTFS."""
    indexed_modes = _git_modes(path)
    return {
        item.relative_to(path).as_posix(): f"{indexed_modes.get(item.resolve(), _portable_mode(item.stat().st_mode)):o}"
        for item in skill_tree_files(path)
    }


def checked_file_modes(path: Path, files: list[Path], file_modes: dict[str, str]) -> dict[str, int]:
    observed = {item.relative_to(path).as_posix() for item in files}
    if not isinstance(file_modes, dict) or set(file_modes) != observed:
        raise ValueError("file mode manifest must cover exactly the enumerated skill resources")
    if any(mode not in ("100644", "100755") for mode in file_modes.values()):
        raise ValueError("file modes must be Git regular-file modes 100644 or 100755")
    modes = {relative: int(mode, 8) for relative, mode in file_modes.items()}
    if os.name != "nt":
        for item in files:
            relative = item.relative_to(path).as_posix()
            if _portable_mode(item.stat().st_mode) != modes[relative]:
                raise ValueError(f"filesystem executable mode differs from manifest: {relative}")
    return modes


def sha256_tree(
    path: Path,
    *,
    file_modes: dict[str, str] | None = None,
    credential_policy: int = 1,
    replacements: dict[str, bytes] | None = None,
) -> str:
    validate_credential_policy(credential_policy)
    digest = hashlib.sha256()
    files = skill_tree_files(path)
    if replacements and not set(replacements) <= {file.relative_to(path).as_posix() for file in files}:
        raise ValueError("dependency replacements contain absent source resources")
    declared_modes = checked_file_modes(path, files, file_modes) if file_modes is not None else None
    indexed_modes = _git_modes(path) if os.name == "nt" and declared_modes is None else {}
    for item in files:
        rel = item.relative_to(path).as_posix()
        file_stat = item.stat()
        data = sanitized_file_bytes(item, credential_policy=credential_policy)
        if replacements and rel in replacements:
            data = replacements[rel]
        file_digest = hashlib.sha256(data).hexdigest()
        mode = (
            declared_modes[rel]
            if declared_modes is not None
            else indexed_modes.get(item.resolve(), _portable_mode(file_stat.st_mode))
        )
        digest.update(f"file\0{rel}\0{mode:o}\0{len(data)}\0".encode())
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


def copy_sanitized_tree(
    src: Path,
    dst: Path,
    *,
    file_modes: dict[str, str] | None = None,
    credential_policy: int = 1,
    replacements: dict[str, bytes] | None = None,
) -> None:
    validate_credential_policy(credential_policy)
    files = skill_tree_files(src)
    if replacements and not set(replacements) <= {file.relative_to(src).as_posix() for file in files}:
        raise ValueError("dependency replacements contain absent source resources")
    modes = checked_file_modes(src, files, file_modes) if file_modes is not None else None
    dst.mkdir(parents=True, exist_ok=True)
    for source_file in files:
        relative = source_file.relative_to(src).as_posix()
        target_file = dst / relative
        target_file.parent.mkdir(parents=True, exist_ok=True)
        content = sanitized_file_bytes(source_file, credential_policy=credential_policy)
        target_file.write_bytes(replacements[relative] if replacements and relative in replacements else content)
        if modes is None:
            shutil.copymode(source_file, target_file, follow_symlinks=False)
        else:
            target_file.chmod(modes[relative] & 0o777)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) != 3:
        return {}, text
    if yaml:
        try:
            parsed = yaml.safe_load(parts[1]) or {}
            return parsed if isinstance(parsed, dict) else {}, parts[2]
        except Exception:
            pass
    fallback: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            fallback[key.strip()] = val.strip().strip("\"'")
    return fallback, parts[2]


def compact(text: Any, limit: int = 420) -> str:
    value = " ".join(str(text or "").split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rsplit(" ", 1)[0] + "."


def single_session_summary(text: str) -> str:
    """Keep generated, agent-facing summaries compatible with AGENTS.md."""
    replacements = [
        (r"\busing parallel subagents\b", "using single-session review passes"),
        (r"\bvia Task subagents\b", "within one session"),
        (r"\bsubagent delegation\b", "explicit workflow routing"),
        (r"\bparallel subagents\b", "single-session review passes"),
        (r"\bsubagents\b", "single-session review steps"),
        (r"\bsubagent\b", "single-session review step"),
        (r"\bSpawns? parallel workers?[^.]*\.", "Uses one-session workflow coordination."),
        (r"\bSpawn all scan Tasks[^.]*\.", "Plan scan tasks inside one session."),
        (r"\bparallel agent workflows\b", "single-session workflow coordination"),
        (r"\bagents?\s+in\s+parallel\b", "one AI session"),
        (r"\bmultiple agent sessions in parallel\b", "one AI session"),
        (r"\bcoordinating multi-agent development workflows\b", "coordinating single-session development workflows"),
        (r"\bparallel agents\b", "single-session review steps"),
        (r"\bmulti-agent orchestration\b", "single-session workflow coordination"),
        (r"\bmulti-agent\b", "single-session"),
    ]
    value = text
    for pattern, replacement in replacements:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    summary = compact(value)
    return summary[:1].upper() + summary[1:] if summary else summary


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
    # A reviewed, single-purpose source must not move categories because its
    # release description gains a generic word such as "workflow".
    if "category" in source:
        category = str(source["category"])
        if category not in {label for label, _ in CATEGORY_KEYWORDS}:
            raise ValueError(f"unknown declared source category: {category}")
        return category
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
        if run_git(repo_dir, "status", "--porcelain=v1", "--untracked-files=all"):
            raise ValueError(f"source checkout contains uncommitted changes: {source['repo']}")
        commit = run_git(repo_dir, "rev-parse", "HEAD")
        if source.get("tag"):
            tag_commit = run_git(repo_dir, "rev-parse", f"{source['tag']}^{{commit}}")
            if tag_commit != commit:
                raise ValueError(
                    f"{source['repo']} checkout HEAD {commit} does not match tag {source['tag']} commit {tag_commit}"
                )
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
            if CREDENTIAL_POLICY_VERSION >= 2:
                text = sanitize_secret_like_text(text, credential_policy=2)
            skill_dir = skill_file.parent
            meta, body = parse_frontmatter(text)
            name = str(meta.get("name") or skill_file.parent.name)
            source_description = compact(meta.get("description") or fallback_description(name, rel, body))
            description = single_session_summary(source_description)
            category = category_for(source, rel, name, source_description)
            resource_flags = flags(skill_file)
            has_required_frontmatter = all(key in meta for key in ("name", "description"))
            entry_install_name = install_name(source["repo"], rel, name)
            file_modes = skill_file_modes(skill_dir)
            graph = dependency_graphs.graph_for(source["repo"], commit, rel, root=ROOT)
            graph_files = dependency_graphs.replacements(skill_dir, graph, root=ROOT) if graph else {}
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
                "selected_subset": bool(source.get("selected_subset")),
                "source_path": rel,
                "source_url": f"https://github.com/{source['repo']}/blob/{ref_url}/{rel}",
                "immutable_source_url": f"https://github.com/{source['repo']}/blob/{commit}/{rel}",
                "selected_ref": selected_ref,
                "selection_policy": source["policy"],
                "latest_release_tag": source.get("tag"),
                "latest_release_url": source.get("release_url"),
                "commit_sha": commit,
                "skill_file_sha256": sha256_file(skill_file, credential_policy=CREDENTIAL_POLICY_VERSION),
                "skill_dir_sha256": sha256_tree(
                    skill_dir,
                    file_modes=file_modes,
                    credential_policy=CREDENTIAL_POLICY_VERSION,
                    replacements=graph_files,
                ),
                "file_modes": file_modes,
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
            if CREDENTIAL_POLICY_VERSION != 1:
                item["credential_policy_version"] = CREDENTIAL_POLICY_VERSION
            if graph:
                item["dependency_graph"] = graph["id"]
            notes = [
                "Keep provenance and selected ref visible so agents can verify the source before use.",
                f"Maintain at least {MIN_SCENARIOS} real workflow benchmark scenarios before treating the skill as deployable.",
            ]
            if not resource_flags["has_agents_metadata"]:
                notes.append(
                    "Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings."
                )
            if not resource_flags["has_scripts"] and category in {
                "Testing, QA & benchmarking",
                "Security, compliance & risk",
                "Science, research & data analysis",
                "DevOps, cloud & operations",
            }:
                notes.append("Add an executable validator or helper script so the workflow has objective checks.")
            if item["line_count"] > 500:
                notes.append("Move long background material into references/ to keep SKILL.md concise.")
            item["improvement_notes"] = notes[:5]
            item["explanation"] = {
                "what_it_covers": f"Catalog summary: {description}",
                "how_an_agent_should_use_it": "Load this skill only when the task matches the catalog summary or source path; read SKILL.md first and then load referenced resources on demand.",
                "observed_structure": f"Headings: {', '.join(item['headings'][:5]) or 'none observed'}. Resources: {', '.join(k for k, v in resource_flags.items() if v) or 'none observed'}.",
                "notability": "Selected source."
                if source.get("selected_subset")
                else f"Included from {source['group']} with explicit GitHub provenance.",
            }
            item["benchmark_scenarios"] = [f"skill-proof-{item['id']}"] + scenario_ids(category)
            entries.append(item)
    entries.sort(key=lambda e: (0 if e["selected_subset"] else 1, e["category"], e["source_repo"], e["source_path"]))
    assign_install_names(entries)
    return entries


def build_scenarios(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    track_lookup = {track[0]: track for track in TRACKS}
    scenarios: list[dict[str, Any]] = []
    present_categories = sorted({entry["category"] for entry in entries})
    for category in present_categories:
        track_ids = SCENARIO_TRACKS.get(category, SCENARIO_TRACKS["Coding, refactoring & repository automation"])
        for index, track_id in enumerate(track_ids, 1):
            _, title, _, problem, metrics = track_lookup[track_id]
            scenarios.append(
                {
                    "id": category_scenario_id(category, track_id),
                    "category": category,
                    "dataset_track_id": track_id,
                    "title": f"{category} scenario {index}: {title}",
                    "workflow": problem,
                    "agent_task": "Load the skill in a fresh agent session, solve the workflow using the cited dataset/repository, capture commands and files consulted, and produce machine-checkable output.",
                    "dataset_snapshot_policy": "Runner must record dataset release, crawl ID, tag, file date, or repository commit before scoring.",
                    "input_selector": {
                        "mode": "runner-selected-real-instance",
                        "selection_rule": "choose a non-trivial instance from the cited dataset or workflow and record its immutable identifier",
                    },
                    "expected_output_schema": {"type": "object", "required": GENERIC_WORKFLOW_REQUIRED},
                    "environment_requirements": [
                        "fresh agent session",
                        "read-only source checkout unless task requires patching",
                        "network only when dataset retrieval requires it",
                    ],
                    "evaluator_path": "evaluators/generic_workflow_result.schema.json",
                    "required_artifacts": [
                        "agent transcript or command log",
                        "dataset/version reference",
                        "output artifact",
                        "objective evaluator result",
                    ],
                    "objective_checks": metrics,
                    "real_data_or_workflow": True,
                }
            )
    for entry in entries:
        scenarios.append(
            {
                "id": f"skill-proof-{entry['id']}",
                "category": entry["category"],
                "dataset_track_id": "source-skill-repository",
                "title": f"{entry['name']} source-grounded functionality proof",
                "workflow": f"Use the immutable source file {entry['immutable_source_url']} as the fixture and prove the agent can understand when and how to use the skill.",
                "agent_task": "In a fresh agent session, read only the recorded SKILL.md and directly referenced local resources, then produce an activation proof, misuse boundaries, required inputs, expected outputs, and one realistic task plan.",
                "dataset_snapshot_policy": "Pinned by the catalog entry commit_sha and immutable_source_url.",
                "input_selector": {
                    "source_repo": entry["source_repo"],
                    "source_path": entry["source_path"],
                    "commit_sha": entry["commit_sha"],
                },
                "expected_output_schema": {"type": "object", "required": SOURCE_PROOF_REQUIRED},
                "environment_requirements": [
                    "fresh agent session",
                    "read-only access to mirrored or source skill directory",
                    "no private credentials",
                ],
                "evaluator_path": "evaluators/source_grounded_skill_proof.schema.json",
                "required_artifacts": ["source-grounded proof JSON", "source line/path citations", "agent transcript"],
                "objective_checks": [
                    "frontmatter or fallback source structure used",
                    "source citations present",
                    "no unsupported capability claims",
                ],
                "real_data_or_workflow": True,
            }
        )
    return scenarios


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def esc(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def skill_manifest_entry(entry: dict[str, Any], name_conflict_group: str | None) -> dict[str, Any]:
    return (
        {
            k: entry[k]
            for k in [
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
            ]
        }
        | ({"file_modes": entry["file_modes"]} if "file_modes" in entry else {})
        | ({"dependency_graph": entry["dependency_graph"]} if "dependency_graph" in entry else {})
        | (
            {"credential_policy_version": entry["credential_policy_version"]}
            if "credential_policy_version" in entry
            else {}
        )
        | {
            "name_conflict_group": name_conflict_group,
            "standalone_installable": bool(entry["has_required_frontmatter"]),
            "bulk_install_safe": bool(entry["has_required_frontmatter"] and name_conflict_group is None),
        }
    )


def name_conflict_groups(entries: list[dict[str, Any]]) -> dict[str, str | None]:
    name_counts: dict[str, int] = {}
    for entry in entries:
        name_counts[entry["name"]] = name_counts.get(entry["name"], 0) + 1
    return {entry["id"]: entry["name"] if name_counts[entry["name"]] > 1 else None for entry in entries}


def mirror_all_skills(
    entries: list[dict[str, Any]], *, retained_root: Path | None = None, refreshed_repos: set[str] | None = None
) -> None:
    """Stage and verify a complete replacement; retain the previous tree for recovery.

    Directory publication uses two renames, not an atomic multi-file transaction.
    A failed build leaves the current tree untouched. A failed second rename rolls
    back; a process crash leaves uniquely named staging/backup directories.
    """
    root = ROOT.resolve()
    if not entries:
        raise ValueError("refusing to publish an empty mirror collection")
    target = root / "included" / "skills"
    if target.resolve() != target or not target.resolve().is_relative_to(root):
        raise ValueError("mirror publication target must be a real directory within the workspace")
    relative_targets: list[Path] = []
    for entry in entries:
        destination = root / entry["mirrored_path"]
        if "\\" in entry["mirrored_path"] or not destination.resolve().is_relative_to(target):
            raise ValueError(f"mirror path escapes included/skills: {entry['mirrored_path']}")
        if destination.resolve().relative_to(root).as_posix() != entry["mirrored_path"]:
            raise ValueError(f"mirror path must be canonical and relative: {entry['mirrored_path']}")
        relative = destination.resolve().relative_to(target)
        if not relative.parts or relative.parts[0] != "by-category":
            raise ValueError(f"invalid mirror directory: {relative}")
        if any(
            relative == other or relative in other.parents or other in relative.parents for other in relative_targets
        ):
            raise ValueError(f"overlapping mirror directories: {relative}")
        relative_targets.append(relative)
    staging_parent = root / ".venv" / "generation-staging"
    if not staging_parent.resolve().is_relative_to(root):
        raise ValueError("generation staging directory escapes the workspace")
    staging_parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix="skill-mirrors-", dir=staging_parent))
    source_by_repo = {source["repo"]: source for source in SOURCES}
    conflicts = name_conflict_groups(entries)
    manifest = []
    for entry, relative in zip(entries, relative_targets, strict=True):
        if retained_root is not None and entry["source_repo"] not in (refreshed_repos or set()):
            src_dir = publication.checked_path(retained_root, entry["mirrored_path"])
            dst_dir = staged / relative
            publication.signature(src_dir)  # Reject links and nonregular resources before hashing/copying.
            if sha256_tree(src_dir, file_modes=entry.get("file_modes")) != entry["skill_dir_sha256"]:
                raise ValueError(f"retained mirror differs from locked catalog: {entry['id']}")
            for path in skill_tree_files(src_dir):
                destination = dst_dir / path.relative_to(src_dir)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination)
            if sha256_tree(dst_dir, file_modes=entry.get("file_modes")) != entry["skill_dir_sha256"]:
                raise ValueError(f"retained mirror changed while copying: {entry['id']}")
            manifest.append(
                skill_manifest_entry(entry, conflicts[entry["id"]])
                | {
                    "source_group": entry["source_group"],
                    "source_tier": entry["source_tier"],
                }
            )
            continue
        source = source_by_repo[entry["source_repo"]]
        repo_dir = SOURCE_ROOT / source["dir"]
        src_dir = (repo_dir / entry["source_path"]).parent
        if not src_dir.resolve().is_relative_to(repo_dir.resolve()):
            raise ValueError(f"source path escapes checkout: {entry['source_path']}")
        dst_dir = staged / relative
        dst_dir.parent.mkdir(parents=True, exist_ok=True)
        copy_sanitized_tree(
            src_dir,
            dst_dir,
            file_modes=entry.get("file_modes"),
            credential_policy=entry.get("credential_policy_version", 1),
            replacements=dependency_graphs.for_entry(entry, src_dir, root=ROOT),
        )
        if sha256_tree(dst_dir, file_modes=entry.get("file_modes")) != entry["skill_dir_sha256"]:
            raise ValueError(f"staged mirror hash differs from catalog: {entry['id']}")
        manifest.append(
            skill_manifest_entry(entry, conflicts[entry["id"]])
            | {
                "source_group": entry["source_group"],
                "source_tier": entry["source_tier"],
            }
        )
    write_json(staged / "manifest.json", manifest)
    (staged / "README.md").write_text(
        f"# Included Skills\n\n"
        f"This directory contains one physical mirror for each of the `{len(entries)}` cataloged source-backed skills.\n\n"
        "Skill mirrors are grouped by category and source tier, then isolated in a stable `install_name` directory. "
        "The install name is the skill name when unique, with exact source-derived qualifiers only when needed to prevent collisions. "
        "Use `manifest.json` to trace every mirror back to its full immutable source URL, commit, source path, and SHA-256 hashes.\n\n"
        "Do not bulk-install entries where `bulk_install_safe` is false.\n",
        encoding="utf-8",
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = staged.with_name(staged.name + "-previous")
    if target.exists():
        target.rename(backup)
    try:
        staged.rename(target)
    except OSError:
        if backup.exists():
            backup.rename(target)
        raise


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
        manifest.append(
            {
                "id": entry["id"],
                "name": entry["name"],
                "category": entry["category"],
                "subcategory": entry["subcategory"],
                "install_name": entry["install_name"],
                "agent_ready_path": entry["agent_ready_path"],
                "source_mirrored_path": entry["mirrored_path"],
                "benchmark_status": entry["benchmark_status"],
            }
        )
    write_json(target / "manifest.json", manifest)
    (target / "README.md").write_text(
        f"# Agent-Ready Skills\n\n"
        f"This directory contains `{len(entries)}` compact skill entrypoints, grouped by category and source tier. Each entrypoint is a separate `SKILL.md` file with frontmatter and a local pointer to the audited source mirror under `included/skills/`.\n\n"
        "Use these files when an agent needs a concise starting point. Use the source mirrors when full upstream detail is required.\n",
        encoding="utf-8",
    )


def write_selected_manifest(entries: list[dict[str, Any]]) -> None:
    legacy_target = ROOT / "included" / "priority"
    if legacy_target.exists():
        shutil.rmtree(legacy_target)
    target = ROOT / "included" / "selected"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    selected_entries = [entry for entry in entries if entry["selected_subset"]]
    conflicts = name_conflict_groups(entries)
    manifest = [skill_manifest_entry(entry, conflicts[entry["id"]]) for entry in selected_entries]
    write_json(target / "manifest.json", manifest)
    (target / "README.md").write_text(
        "# Selected Skills\n\n"
        "This directory is a selected subset manifest only. The actual skill directories are physically written once under `included/skills/` and are referenced by each entry's `mirrored_path`.\n\n"
        "Use `manifest.json` to trace selected entries back to full immutable source URLs and unique `install_name` values. Do not bulk-install entries where `bulk_install_safe` is false.\n",
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
        if run_git(repo_dir, "status", "--porcelain=v1", "--untracked-files=all"):
            raise ValueError(f"source checkout changed during collection: {source['repo']}")
        if any(entry["commit_sha"] != commit for entry in repo_entries):
            raise ValueError(f"source HEAD changed after collection: {source['repo']}")
        sources.append(
            {
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
                    | ({"file_modes": entry["file_modes"]} if "file_modes" in entry else {})
                    | ({"dependency_graph": entry["dependency_graph"]} if "dependency_graph" in entry else {})
                    | (
                        {"credential_policy_version": entry["credential_policy_version"]}
                        if "credential_policy_version" in entry
                        else {}
                    )
                    for entry in repo_entries
                ],
            }
        )
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


def write_docs(
    entries: list[dict[str, Any]], scenarios: list[dict[str, Any]], *, context_root: Path | None = None
) -> None:
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
    selected = [e for e in entries if e["selected_subset"]]
    # Read independent artifact inventories before staging, without regenerating
    # them or turning their packaging/smoke counts into efficacy claims.
    context = ROOT if context_root is None else context_root
    supplemental_counts = []
    repair_manifest = context / "included/repaired/skills/manifest.json"
    if repair_manifest.exists():
        repairs = json.loads(repair_manifest.read_text(encoding="utf-8"))["repairs"]
        supplemental_counts.append(
            f"- `{len(repairs)}` repaired skill overlays under `included/repaired/skills/` "
            "for currently observed runtime-readiness packaging failures."
        )
    adapter_registry = context / "data/external_benchmark_methods.json"
    if adapter_registry.exists():
        methods = json.loads(adapter_registry.read_text(encoding="utf-8"))["methods"]
        supplemental_counts.append(
            f"- `{len(methods)}` selected external benchmark method adapters with smoke artifacts."
        )
    supplemental_snapshot = "".join(f"{line}\n" for line in supplemental_counts)
    legacy_priority_doc = docs / "priority-skills.md"
    if legacy_priority_doc.exists():
        legacy_priority_doc.unlink()

    (ROOT / "README.md").write_text(
        f"""# AI Skills Collection Benchmarked

> Early alpha: this repository is experimental. Many entries may be incomplete, incompatible, stale, or unsuitable for a given environment. Use it at your own risk; the maintainers accept no responsibility for results, failures, or downstream use.

Evidence-backed catalog of AI agent skills, with benchmark scenarios tied to real datasets and real repository workflows.

Repository scope:

- Catalog entries come from observed `SKILL.md` files in public GitHub repositories.
- Each entry records source repo, path, selected ref, immutable commit URL, category, and readiness caveat.
- Source discovery used a broad web and repository search, then offline verification against local checkouts.
- Selected-entry ordering follows the source policy and lock files, not README-only claims.
- Scenario-covered candidates must have multiple benchmark scenarios before any runtime claim is considered.
- The benchmark suite defines realistic workflows and datasets; it does not claim a skill passed until a run artifact is recorded.

Current snapshot:

- `{len(entries)}` source-backed skill entries.
- `{len(entries)}` written skill mirrors under `included/skills/`.
- `{len(entries)}` compact agent-ready skill entrypoints under `included/agent-ready/`.
{supplemental_snapshot}- `{len(selected)}` selected repository entries.
- `{len(categories)}` categories.
- `{len(scenarios)}` real-data scenario templates.
- Minimum `{MIN_SCENARIOS}` benchmark scenarios assigned per scenario-covered candidate.

Start here:

- [Methodology](docs/methodology.md)
- [Source policy](docs/source-policy.md)
- [Included skill mirrors](included/skills/README.md)
- [Agent-ready skills](included/agent-ready/README.md)
- [Selected skills](docs/selected-skills.md)
- [Catalog index](docs/catalog/index.md)
- [Benchmark suite](docs/benchmarks.md)
- [Benchmark results](docs/benchmark-results.md)
- [Runtime benchmark batch 01](docs/runtime-benchmark-batch-01.md)
- [Runtime benchmark batch 02](docs/runtime-benchmark-batch-02.md)
- [Runtime benchmark batch 03](docs/runtime-benchmark-batch-03.md)
- [Local Markdown link failures](docs/local-markdown-link-failures.md)
- [Repaired skill readiness](docs/repaired-skill-readiness.md)
- [Objective benchmark methods](docs/objective-benchmark-methods.md)
- [External benchmark adapter smoke](docs/external-benchmark-adapter-smoke.md)
- [Skill quality findings](docs/skill-quality-findings.md)
- [Skill risk findings](docs/skill-risk-findings.md)
- [Immutable audit model](docs/immutable-audit-model.md)
- [Benchmark runner requirements](docs/benchmark-runner-requirements.md)
- [Host-agnostic installation](docs/installation.md)
- [Agent consumability checklist](docs/agent-consumability.md)
- [Contributing guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

Validation (offline; no source checkouts required):

```bash
python3 -m pip install -e '.[test,lint]'
python3 tools/validate_catalog.py            # cross-reference + mirror integrity
python3 tools/validate_source_lock.py        # offline structural + mirror-hash check
python3 tools/run_static_benchmarks.py --check
python3 tools/audit_skill_quality.py --check
python3 tools/check_no_secret_patterns.py --history
ruff check tools tests
ruff format --check tools tests
mypy tools tests
python3 -m pytest -q -n auto
python3 -m compileall -q tools tests
```

The same gates run in [GitHub Actions](.github/workflows/) on every push, on
weekly cron, and on `workflow_dispatch`. See [docs/installation.md](docs/installation.md)
for the full reproducible / `SOURCE_DATE_EPOCH`-anchored regeneration flow.
""",
        encoding="utf-8",
    )

    (docs / "methodology.md").write_text(
        f"""# Methodology

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
""",
        encoding="utf-8",
    )

    (docs / "immutable-audit-model.md").write_text(
        """# Immutable Audit Model

This repository keeps skill mirroring and benchmark evaluation as separate loops.

## Skill Mirror Loop

The mirror loop imports source-locked skill folders from pinned public commits and writes catalog metadata, source mirrors, agent-ready entrypoints, and documentation. It does not rewrite upstream `SKILL.md` content to remove findings or improve benchmark results.

Allowed mirror transformations are deterministic and auditable:

- Secret-shaped text is neutralized before it can enter the repository.
- Declared dependency advisory floors may be applied by the generator.
- Stable generated paths, category labels, and metadata are derived from catalog rules.

## Artifact And Test Loop

The artifact loop works from the generated catalog, mirrored source files, benchmark scenarios, and real run evidence. It records benchmark artifacts, static benchmark tables, risk reports, and validation checks.

Benchmark tasks, fixtures, expected results, and evaluators must be defined independently from the exact text of the skill being evaluated. Skill text may be used for activation and operating context, but it must not define the expected answer used to score that same skill.

Source-grounded skill-proof artifacts are provenance checks. They are useful for confirming that a source file can be located and interpreted, but they are not runtime benchmark passes.

A counted runtime benchmark artifact must record that its task, evaluator, and expected result were created outside the skill content.
""",
        encoding="utf-8",
    )

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

    selected_doc = f"# Selected Skills\n\nSelected entries: `{len(selected)}`.\n\n| Skill | Category | Source | Ref | Scenarios |\n|---|---|---|---|---:|\n"
    for entry in selected:
        selected_doc += f"| `{esc(entry['name'])}` | {esc(entry['category'])} | [{esc(entry['source_repo'])}]({entry['immutable_source_url']}) | {esc(entry['selected_ref'])} | {len(entry['benchmark_scenarios'])} |\n"
    selected_doc += "\nSelected entries are a subset of the physical mirrors under `included/skills/`; `included/selected/manifest.json` points to the exact mirrored directory for each one. Adjacent agent instruction files and benchmark folders are documented as context in the source policy, not counted as skills.\n"
    (docs / "selected-skills.md").write_text(selected_doc, encoding="utf-8")

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
            per_skill = f"""# {entry["name"]}

Category: {entry["category"]}

Mirrored skill: `{entry["mirrored_path"]}`

Agent-ready entrypoint: `{entry["agent_ready_path"]}`

Source: [{entry["source_repo"]} `{entry["source_path"]}`]({entry["immutable_source_url"]})

Selected ref: `{entry["selected_ref"]}`; commit `{entry["commit_sha"][:12]}`

## Use

{entry["explanation"]["how_an_agent_should_use_it"]}

## Scope

{entry["explanation"]["what_it_covers"]}

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

"""
            for sid in entry["benchmark_scenarios"]:
                per_skill += f"- `{sid}`: {scenario_lookup[sid]['workflow']}\n"
            per_skill += "\nImprovement notes:\n\n"
            for note in entry["improvement_notes"]:
                per_skill += f"- {note}\n"
            skill_path = (
                skill_doc_dir / slug(entry["category"]) / slug(entry["subcategory"]) / f"{entry['install_name']}.md"
            )
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(per_skill.rstrip() + "\n", encoding="utf-8")
        (cat_dir / f"{slug(category)}.md").write_text(doc.rstrip() + "\n", encoding="utf-8")

    benchmark_doc = "# Benchmark Suite\n\nScenario definitions live in `data/benchmark_scenarios.json`; per-skill assignments live in `data/benchmark_assignments.json`.\n\n"
    category_template_count = len(scenarios) - len(entries)
    benchmark_doc += f"The current suite contains `{len(entries)}` source-grounded skill-proof scenarios and `{category_template_count}` category workflow templates. A scenario is only a template until a runner records artifacts under the rules in [Benchmark runner requirements](benchmark-runner-requirements.md). Current measured outputs are summarized in [Benchmark results](benchmark-results.md), with independent runtime-readiness batches in [Runtime benchmark batch 01](runtime-benchmark-batch-01.md), [Runtime benchmark batch 02](runtime-benchmark-batch-02.md), and [Runtime benchmark batch 03](runtime-benchmark-batch-03.md). Exact unresolved local Markdown targets are grouped in [Local Markdown link failures](local-markdown-link-failures.md).\n\n"
    benchmark_doc += "## Scoring Rules\n\nA benchmark run must record the skill ID, scenario ID, source commit, dataset or website snapshot, environment, commands or transcript, output artifact, objective metrics, and evaluator result. Synthetic fixtures may supplement coverage, but they do not replace a real source repository, real dataset, real website, or recorded runtime workflow when the scenario calls for one.\n\n"
    for track_id, title, url, problem, metrics in TRACKS:
        benchmark_doc += f"## {title}\n\n- ID: `{track_id}`\n- URL: {url}\n- Workflow: {problem}\n- Metrics: {', '.join(metrics)}\n\n"
    (docs / "benchmarks.md").write_text(benchmark_doc.rstrip() + "\n", encoding="utf-8")

    (docs / "benchmark-runner-requirements.md").write_text(
        """# Benchmark Runner Requirements

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
""",
        encoding="utf-8",
    )

    (docs / "agent-consumability.md").write_text(
        f"""# Agent Consumability Checklist

Mechanical checks:

- `SKILL.md` exists at the recorded source path.
- `name`, description, source URL, immutable URL, selected ref, and commit SHA are recorded.
- Selected ref is latest release tag where available, otherwise default branch HEAD with explicit no-release policy.
- At least `{MIN_SCENARIOS}` real workflow scenarios are assigned to every scenario-covered candidate.
- Improvement notes are derived from observed file structure.

Runtime proof requires running the scenario in the target agent environment and saving artifacts.
""",
        encoding="utf-8",
    )


GENERATED_OUTPUTS = (
    "README.md",
    "data/skills_catalog.json",
    "data/best_practice_sources.json",
    "data/benchmark_tracks.json",
    "data/benchmark_scenarios.json",
    "data/benchmark_assignments.json",
    "data/source_lock.json",
    "included/skills",
    "included/agent-ready",
    "included/selected",
    "included/priority",  # retired output: retain its old contents in recovery storage
    "docs/priority-skills.md",
    "docs/methodology.md",
    "docs/immutable-audit-model.md",
    "docs/source-policy.md",
    "docs/selected-skills.md",
    "docs/catalog/index.md",
    "docs/catalog/by-category",
    "docs/catalog/skills",
    "docs/benchmarks.md",
    "docs/benchmark-runner-requirements.md",
    "docs/agent-consumability.md",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build the AI skill catalog from local source checkouts.")
    parser.add_argument(
        "--source-root",
        default=str(SOURCE_ROOT),
        help="Directory containing source repo checkouts. Defaults to AI_SKILL_SOURCE_ROOT or /tmp/ai_skill_sources.",
    )
    parser.add_argument("--check", action="store_true", help="Stage and compare all outputs without publishing")
    parser.add_argument("--json", action="store_true", help="Emit publication or freshness results as JSON")
    parser.add_argument(
        "--refresh-source",
        action="append",
        default=[],
        metavar="OWNER/REPO",
        help="Refresh a declared, already cataloged source; verify and retain all other locked mirrors",
    )
    parser.add_argument(
        "--credential-policy",
        type=int,
        choices=(1, 2, 3),
        default=1,
        help="Declared credential neutralization policy: 1 replays old locks; 2 adds Stripe shapes; 3 adds hash-qualified examples",
    )
    return parser


def write_catalog_outputs(
    entries: list[dict[str, Any]],
    scenarios: list[dict[str, Any]],
    source_lock: dict[str, Any],
    *,
    retained_root: Path | None = None,
    refreshed_repos: set[str] | None = None,
    context_root: Path | None = None,
) -> None:
    tracks = [
        {
            "id": t[0],
            "title": t[1],
            "url": t[2],
            "kind": "real dataset or repository workflow",
            "problem": t[3],
            "metrics": t[4],
        }
        for t in TRACKS
    ]
    write_json(ROOT / "data" / "skills_catalog.json", entries)
    write_json(ROOT / "data" / "best_practice_sources.json", BEST_PRACTICE_SOURCES)
    write_json(ROOT / "data" / "benchmark_tracks.json", tracks)
    write_json(ROOT / "data" / "benchmark_scenarios.json", scenarios)
    write_json(
        ROOT / "data" / "benchmark_assignments.json",
        [{"skill_id": e["id"], "scenario_ids": e["benchmark_scenarios"]} for e in entries],
    )
    write_json(ROOT / "data" / "source_lock.json", source_lock)
    mirror_all_skills(entries, retained_root=retained_root, refreshed_repos=refreshed_repos)
    write_agent_ready_skills(entries)
    write_selected_manifest(entries)
    write_docs(entries, scenarios, context_root=context_root)
    # Evaluator schemas, tests, and validation belong to the independent artifact
    # loop. Catalog generation never rewrites those maintained scoring inputs.


def verify_generated_outputs(root: Path, entries: list[dict[str, Any]], source_lock: dict[str, Any]) -> None:
    """Validate newly generated cross-references independently of publication."""
    load = lambda relative: json.loads((root / relative).read_text(encoding="utf-8"))  # noqa: E731
    if load("data/skills_catalog.json") != entries or load("data/source_lock.json") != source_lock:
        raise ValueError("staged catalog/source lock differs from collected inputs")
    expected = {entry["id"] for entry in entries}
    if len(expected) != len(entries) or not expected:
        raise ValueError("staged catalog must have unique nonempty IDs")
    retired_outputs = {"included/priority", "docs/priority-skills.md"}
    for relative in set(GENERATED_OUTPUTS) - retired_outputs:
        if not publication.checked_path(root, relative).exists():
            raise ValueError(f"required generated output is missing: {relative}")
    for relative in ("included/skills/manifest.json", "included/agent-ready/manifest.json"):
        items = load(relative)
        if len(items) != len(entries) or {item["id"] for item in items} != expected:
            raise ValueError(f"staged manifest differs from catalog: {relative}")
    if {item["id"] for item in load("included/selected/manifest.json")} != {
        entry["id"] for entry in entries if entry["selected_subset"]
    }:
        raise ValueError("staged selected manifest differs from catalog")
    for entry in entries:
        mirror = publication.checked_path(root, entry["mirrored_path"])
        if sha256_tree(mirror, file_modes=entry.get("file_modes")) != entry["skill_dir_sha256"]:
            raise ValueError(f"staged mirror changed during generation: {entry['id']}")
        if sha256_file(mirror / "SKILL.md") != entry["skill_file_sha256"]:
            raise ValueError(f"staged entrypoint differs from catalog: {entry['id']}")
        if not publication.checked_path(root, entry["agent_ready_path"]).is_file():
            raise ValueError(f"staged agent entrypoint is missing: {entry['id']}")


def scoped_refresh_inputs(root: Path, repos: set[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Resolve selected sources while preserving independently verified locked inputs."""
    global SOURCES
    old_entries = json.loads((root / "data/skills_catalog.json").read_text(encoding="utf-8"))
    old_lock = json.loads((root / "data/source_lock.json").read_text(encoding="utf-8"))
    for entry in old_entries:
        publication.signature(publication.checked_path(root, entry["mirrored_path"]))
    verify_generated_outputs(root, old_entries, old_lock)
    declared = {source["repo"] for source in SOURCES}
    existing = {source["repo"] for source in old_lock["sources"]}
    if not repos or repos - declared or repos - existing:
        raise ValueError("scoped refresh requires declared, already locked source repositories")
    by_id = {entry["id"]: entry for entry in old_entries}
    locked_ids = []
    for source in old_lock["sources"]:
        if source["skill_count"] != len(source["skills"]):
            raise ValueError(f"source lock count differs from skill inventory: {source['repo']}")
        for skill in source["skills"]:
            locked_ids.append(skill["id"])
            entry = by_id.get(skill["id"])
            if (
                entry is None
                or entry["source_repo"] != source["repo"]
                or entry["commit_sha"] != source["commit_sha"]
                or any(
                    entry.get(key) != skill.get(key)
                    for key in (
                        "source_path",
                        "install_name",
                        "skill_file_sha256",
                        "skill_dir_sha256",
                        "file_modes",
                        "credential_policy_version",
                        "dependency_graph",
                    )
                )
            ):
                raise ValueError(f"source lock differs from catalog: {skill['id']}")
    if len(locked_ids) != len(set(locked_ids)) or set(locked_ids) != set(by_id):
        raise ValueError("source lock and catalog IDs differ")
    original_sources = SOURCES
    try:
        SOURCES = [source for source in original_sources if source["repo"] in repos]
        updated = collect()
        if {entry["source_repo"] for entry in updated} != repos:
            raise ValueError("a selected source no longer contains catalogable skills")
        entries = [copy.deepcopy(entry) for entry in old_entries if entry["source_repo"] not in repos] + updated
        # Legacy catalogs infer executable bits from the repository Git index.
        # Staging has no such index: retain these exact input modes explicitly
        # so the replacement remains portable on NTFS and fresh Linux clones.
        for entry in entries:
            if entry["source_repo"] not in repos and "file_modes" not in entry:
                entry["file_modes"] = skill_file_modes(publication.checked_path(root, entry["mirrored_path"]))
        entries.sort(
            key=lambda entry: (
                0 if entry["selected_subset"] else 1,
                entry["category"],
                entry["source_repo"],
                entry["source_path"],
            )
        )
        assign_install_names(entries)
        if any(
            {key: value for key, value in entry.items() if key != "file_modes"}
            != {key: value for key, value in by_id[entry["id"]].items() if key != "file_modes"}
            for entry in entries
            if entry["source_repo"] not in repos
        ):
            raise ValueError("scoped refresh would rename retained skills; use a complete source build")
        new_lock = build_source_lock(updated)
    finally:
        SOURCES = original_sources
    lock = copy.deepcopy(old_lock)
    replacements = {source["repo"]: source for source in new_lock["sources"]}
    lock["sources"] = [replacements.get(source["repo"], source) for source in lock["sources"]]
    refreshed_entries = {entry["id"]: entry for entry in entries}
    for source in lock["sources"]:
        for skill in source["skills"]:
            skill["file_modes"] = refreshed_entries[skill["id"]]["file_modes"]
    lock["generated_on"] = BUILD_DATE
    return entries, lock


def main(argv: list[str] | None = None) -> int:
    global ROOT, SOURCE_ROOT, BUILD_DATE, CREDENTIAL_POLICY_VERSION
    args = build_parser().parse_args(argv)
    original_root, original_source, original_date = ROOT, SOURCE_ROOT, BUILD_DATE
    original_policy = CREDENTIAL_POLICY_VERSION
    root = ROOT.resolve()
    try:
        SOURCE_ROOT = Path(args.source_root).expanduser().resolve()
        CREDENTIAL_POLICY_VERSION = args.credential_policy
        BUILD_DATE = resolve_timestamp(
            existing_manifest_value=existing_field(root / "data/source_lock.json", "generated_on"),
            fallback_epoch=git_latest_commit_epoch_for(root, [root / "tools/build_catalog.py"]),
        )[:10]
        refreshed_repos = set(args.refresh_source)
        retained_root = root if refreshed_repos else None
        if refreshed_repos:
            entries, source_lock = scoped_refresh_inputs(root, refreshed_repos)
        else:
            entries = collect()
            source_lock = build_source_lock(entries)
        scenarios = build_scenarios(entries)
        badge_block = update_readme_badges.render_badge_block(update_readme_badges.load_metadata(root))

        def build(staged: Path) -> None:
            global ROOT
            ROOT = staged
            try:
                write_catalog_outputs(
                    entries,
                    scenarios,
                    source_lock,
                    retained_root=retained_root,
                    refreshed_repos=refreshed_repos,
                    context_root=root,
                )
                readme_path = staged / "README.md"
                heading, body = readme_path.read_text(encoding="utf-8").split("\n", 1)
                readme_path.write_text(f"{heading}\n\n{badge_block}\n{body}", encoding="utf-8", newline="\n")
                verify_generated_outputs(staged, entries, source_lock)
            finally:
                ROOT = original_root

        transaction, journal = publication.prepare(root, GENERATED_OUTPUTS, build)
        drift = publication.differences(root, transaction, journal)
        if not args.check:
            publication.publish(root, transaction, journal)
        result = {
            "ok": not drift if args.check else True,
            "mode": "check" if args.check else "publish",
            "skills": len(entries),
            "scenarios": len(scenarios),
            "different_outputs": drift,
            "refreshed_sources": sorted(refreshed_repos),
            "retained_skills": sum(entry["source_repo"] not in refreshed_repos for entry in entries)
            if refreshed_repos
            else 0,
            "recovery_directory": str(transaction),
        }
        print(json.dumps(result, indent=2) if args.json else result)
        return int(args.check and bool(drift))
    finally:
        ROOT, SOURCE_ROOT, BUILD_DATE = original_root, original_source, original_date
        CREDENTIAL_POLICY_VERSION = original_policy


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Record objective external benchmark method integration probes.

The probes here do not run full benchmark suites and do not claim agent task
success. They verify that every selected external method has a concrete adapter
definition, a resolvable upstream repository, declared objective metrics, and a
recorded integration artifact that can be reviewed later.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNNER_ID = "tools/evaluate_external_benchmark_methods.py"
RUN_NAME = "2026-04-19-external-benchmark-method-smoke"


EXTERNAL_METHODS: list[dict[str, Any]] = [
    {
        "id": "swe-skills-bench",
        "title": "SWE-Skills-Bench",
        "scope": "Measures skill utility on real software-engineering tasks by comparing paired runs with and without the skill.",
        "repo_url": "https://github.com/GeniusHTX/SWE-Skills-Bench",
        "source_url": "https://arxiv.org/abs/2603.15401",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["with-skill pass rate", "without-skill pass rate", "pass-rate delta", "token overhead"],
        "category_fit": ["Coding, refactoring & repository automation", "Agent infrastructure & skill creation"],
        "integration_requirements": ["pinned task repository", "with-skill run", "without-skill run", "deterministic acceptance tests"],
    },
    {
        "id": "skillsbench",
        "title": "SkillsBench",
        "scope": "Evaluates agent skill use across diverse verifiable real-world tasks and deterministic verifiers.",
        "repo_url": "https://github.com/benchflow-ai/skillsbench",
        "source_url": "https://www.skillsbench.ai/",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["task pass rate", "skill gain", "steps", "token usage"],
        "category_fit": ["Agent infrastructure & skill creation", "Testing, QA & benchmarking"],
        "integration_requirements": ["task package", "skill package", "deterministic verifier", "agent trajectory"],
    },
    {
        "id": "skill-bench",
        "title": "Skill Bench",
        "scope": "Runs evidence-graded skill eval cases in CI and reports regression-oriented skill scores.",
        "repo_url": "https://github.com/skill-bench/skill-eval-action",
        "source_url": "https://skill-bench.dev/",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["criterion score", "evidence coverage", "pass/fail", "regression delta"],
        "category_fit": ["Agent infrastructure & skill creation", "Testing, QA & benchmarking"],
        "integration_requirements": ["eval case YAML", "grader criteria", "skill path", "agent response transcript"],
    },
    {
        "id": "swe-bench",
        "title": "SWE-bench",
        "scope": "Evaluates repository issue resolution by applying patches and running project tests.",
        "repo_url": "https://github.com/SWE-bench/SWE-bench",
        "source_url": "https://github.com/SWE-bench/SWE-bench",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["resolved instances", "patch applies", "test pass rate", "regression count"],
        "category_fit": ["Coding, refactoring & repository automation", "Testing, QA & benchmarking"],
        "integration_requirements": ["Docker-capable host", "instance id", "prediction patch", "test harness output"],
    },
    {
        "id": "terminal-bench",
        "title": "Terminal-Bench",
        "scope": "Evaluates terminal-native agent tasks with reproducible task containers and verifiers.",
        "repo_url": "https://github.com/laude-institute/terminal-bench",
        "source_url": "https://github.com/laude-institute/terminal-bench",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["task success", "command log completeness", "execution time", "resource use"],
        "category_fit": ["DevOps, cloud & operations", "Testing, QA & benchmarking"],
        "integration_requirements": ["task definition", "container environment", "command transcript", "verifier result"],
    },
    {
        "id": "browsergym",
        "title": "BrowserGym",
        "scope": "Provides a unified browser-agent environment across MiniWoB, WebArena, VisualWebArena, WorkArena, and related suites.",
        "repo_url": "https://github.com/ServiceNow/BrowserGym",
        "source_url": "https://github.com/ServiceNow/BrowserGym",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["task success", "trace completeness", "browser actions", "wall time"],
        "category_fit": ["Frontend, UI & browser automation", "Search, retrieval & web automation"],
        "integration_requirements": ["Playwright browser", "environment id", "browser trace", "task evaluator"],
    },
    {
        "id": "webarena",
        "title": "WebArena",
        "scope": "Measures realistic self-hosted web tasks with end-to-end web-agent success criteria.",
        "repo_url": "https://github.com/web-arena-x/webarena",
        "source_url": "https://arxiv.org/abs/2307.13854",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["end-to-end task success", "site state correctness", "action trace", "human-baseline comparison"],
        "category_fit": ["Frontend, UI & browser automation", "Search, retrieval & web automation"],
        "integration_requirements": ["self-hosted sites", "task id", "browser trace", "state evaluator"],
    },
    {
        "id": "webarena-verified",
        "title": "WebArena-Verified",
        "scope": "Adds version-controlled verified web tasks and deterministic evaluators on top of WebArena-style environments.",
        "repo_url": "https://github.com/ServiceNow/webarena-verified",
        "source_url": "https://github.com/ServiceNow/webarena-verified",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["verified task success", "network trace evidence", "response evaluator result", "state evaluator result"],
        "category_fit": ["Frontend, UI & browser automation", "Search, retrieval & web automation"],
        "integration_requirements": ["verified task set", "captured browser/network trace", "deterministic evaluator", "site snapshot"],
    },
    {
        "id": "st-webagentbench",
        "title": "ST-WebAgentBench",
        "scope": "Evaluates safety and trustworthiness for enterprise-oriented web agents.",
        "repo_url": "https://github.com/segev-shlomov/ST-WebAgentBench",
        "source_url": "https://github.com/segev-shlomov/ST-WebAgentBench",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["task success", "safety violation rate", "trustworthiness score", "modality challenge score"],
        "category_fit": ["Security, compliance & risk", "Frontend, UI & browser automation"],
        "integration_requirements": ["web task instance", "browser trace", "safety policy", "evaluator result"],
    },
    {
        "id": "osworld",
        "title": "OSWorld",
        "scope": "Evaluates multimodal computer-use agents across real desktop applications and operating-system workflows.",
        "repo_url": "https://github.com/xlang-ai/OSWorld",
        "source_url": "https://os-world.github.io/",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["task success", "execution evaluator result", "screen trace", "application state correctness"],
        "category_fit": ["Frontend, UI & browser automation", "Documents, spreadsheets & presentations"],
        "integration_requirements": ["desktop environment", "task config", "screen/action trace", "execution evaluator"],
    },
    {
        "id": "bfcl",
        "title": "Berkeley Function Calling Leaderboard",
        "scope": "Evaluates executable tool/function calling, including relevance detection and multi-turn/tool-call scenarios.",
        "repo_url": "https://github.com/ShishirPatil/gorilla",
        "repo_subpath": "berkeley-function-call-leaderboard",
        "source_url": "https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["AST match", "execution accuracy", "function relevance", "multi-turn correctness"],
        "category_fit": ["Agent infrastructure & skill creation", "Search, retrieval & web automation"],
        "integration_requirements": ["function schema", "model/tool-call output", "checker output", "test split identifier"],
    },
    {
        "id": "mle-bench",
        "title": "MLE-bench",
        "scope": "Evaluates machine-learning engineering agents on Kaggle-style competitions with local grading scripts.",
        "repo_url": "https://github.com/openai/mle-bench",
        "source_url": "https://github.com/openai/mle-bench",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["competition score", "medal threshold", "valid submission rate", "runtime budget"],
        "category_fit": ["Science, research & data analysis", "Data, analytics & visualization"],
        "integration_requirements": ["Kaggle credentials when needed", "competition data", "submission artifact", "grading script output"],
    },
    {
        "id": "ml-dev-bench",
        "title": "ML-Dev-Bench",
        "scope": "Evaluates real-world ML development tasks such as dataset handling, debugging, training, and implementation.",
        "repo_url": "https://github.com/ml-dev-bench/ml-dev-bench",
        "source_url": "https://github.com/ml-dev-bench/ml-dev-bench",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["task success", "model score", "debugging correctness", "implementation correctness"],
        "category_fit": ["Science, research & data analysis", "Data, analytics & visualization"],
        "integration_requirements": ["task repository", "agent patch or outputs", "training/evaluation logs", "scoring script"],
    },
    {
        "id": "gittaskbench",
        "title": "GitTaskBench",
        "scope": "Evaluates code agents on real repository tasks from setup through delivery with cost-aware metrics.",
        "repo_url": "https://github.com/QuantaAlpha/GitTaskBench",
        "source_url": "https://github.com/QuantaAlpha/GitTaskBench",
        "adapter_stage": "implemented-smoke-adapter",
        "primary_metrics": ["task success", "setup success", "cost-aware alpha", "test result"],
        "category_fit": ["Coding, refactoring & repository automation", "DevOps, cloud & operations"],
        "integration_requirements": ["repository task", "environment setup log", "agent patch", "test/evaluator result"],
    },
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "item"


def git_head(repo_url: str) -> dict[str, Any]:
    completed = subprocess.run(["git", "ls-remote", repo_url, "HEAD"], text=True, capture_output=True, check=False)
    stdout = completed.stdout.strip()
    head_sha = stdout.split()[0] if completed.returncode == 0 and stdout else ""
    return {
        "command": ["git", "ls-remote", repo_url, "HEAD"],
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": completed.stderr.strip(),
        "head_sha": head_sha,
        "resolved": bool(head_sha),
    }


def github_tree_paths(repo_url: str, head_sha: str) -> list[str]:
    match = re.fullmatch(r"https://github\.com/([^/]+)/([^/]+)", repo_url.rstrip("/"))
    if not match or not head_sha:
        return []
    owner, repo = match.groups()
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{head_sha}?recursive=1"
    request = urllib.request.Request(api_url, headers={"User-Agent": "ai-skills-external-benchmark-smoke/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        return sorted(item["path"] for item in data.get("tree", []) if item.get("path"))
    except Exception:
        with tempfile.TemporaryDirectory(prefix="external-benchmark-tree-") as tmp:
            clone = subprocess.run(
                ["git", "clone", "--filter=blob:none", "--no-checkout", "--depth", "1", repo_url, tmp],
                text=True,
                capture_output=True,
                check=False,
                timeout=180,
            )
            if clone.returncode != 0:
                raise RuntimeError(clone.stderr.strip() or "git clone tree fallback failed")
            tree = subprocess.run(
                ["git", "-C", tmp, "ls-tree", "-r", "--name-only", "HEAD"],
                text=True,
                capture_output=True,
                check=False,
                timeout=60,
            )
            if tree.returncode != 0:
                raise RuntimeError(tree.stderr.strip() or "git ls-tree fallback failed")
            return sorted(path for path in tree.stdout.splitlines() if path)


def registry() -> dict[str, Any]:
    return {
        "registry_version": 1,
        "generated_on": "2026-04-19",
        "method_count": len(EXTERNAL_METHODS),
        "methods": EXTERNAL_METHODS,
    }


def adapter_complete(method: dict[str, Any]) -> bool:
    return all(
        [
            method.get("id"),
            method.get("title"),
            method.get("scope"),
            method.get("repo_url", "").startswith("https://github.com/"),
            method.get("source_url", "").startswith("https://"),
            method.get("primary_metrics"),
            method.get("category_fit"),
            method.get("integration_requirements"),
        ]
    )


def smoke_probe(method: dict[str, Any], timestamp: str) -> dict[str, Any]:
    head = git_head(method["repo_url"])
    subpath = method.get("repo_subpath")
    sampled_paths: list[str] = []
    subpath_present: bool | None = None
    tree_path_count = 0
    tree_error = ""
    if head["resolved"]:
        try:
            paths = github_tree_paths(method["repo_url"], head["head_sha"])
            tree_path_count = len(paths)
            sampled_paths = paths[:20]
            if subpath:
                prefix = subpath.rstrip("/") + "/"
                subpath_present = any(path == subpath or path.startswith(prefix) for path in paths)
        except Exception as exc:
            tree_error = str(exc)
    if subpath is None:
        subpath_present = True
    checks = [
        {"name": "adapter_spec_complete", "passed": adapter_complete(method), "evidence": "data/external_benchmark_methods.json"},
        {"name": "repository_head_resolves", "passed": head["resolved"], "evidence": method["repo_url"]},
        {"name": "repo_tree_sampled", "passed": tree_path_count > 0, "evidence": tree_path_count},
        {"name": "declares_objective_metrics", "passed": len(method.get("primary_metrics", [])) >= 3, "evidence": method.get("primary_metrics", [])},
        {"name": "declares_integration_requirements", "passed": len(method.get("integration_requirements", [])) >= 3, "evidence": method.get("integration_requirements", [])},
        {"name": "declares_category_fit", "passed": bool(method.get("category_fit")), "evidence": method.get("category_fit", [])},
        {"name": "required_subpath_resolves", "passed": subpath_present is True, "evidence": subpath or "repository root"},
    ]
    passed = sum(1 for check in checks if check["passed"])
    total = len(checks)
    failures = [check["name"] for check in checks if not check["passed"]]
    return {
        "artifact_version": "1.0",
        "artifact_kind": "external_benchmark_method_smoke",
        "method_id": method["id"],
        "method_title": method["title"],
        "runner": {
            "timestamp_utc": timestamp,
            "tool": RUNNER_ID,
            "model_or_runtime": "local-deterministic-integration-smoke",
            "run_name": RUN_NAME,
        },
        "input_snapshot": {
            "kind": "real-github-repository-tree",
            "repo_url": method["repo_url"],
            "source_url": method["source_url"],
            "head_sha": head["head_sha"],
            "tree_path_count": tree_path_count,
            "sampled_paths": sampled_paths,
            "repo_subpath": subpath,
            "repo_subpath_present": subpath_present,
            "tree_error": tree_error,
            "is_real": True,
        },
        "execution": {
            "fresh_session": True,
            "commands": [
                {
                    "command": head["command"],
                    "returncode": head["returncode"],
                    "stdout": head["stdout"],
                    "stderr": head["stderr"],
                }
            ],
        },
        "outputs": {
            "schema": "evaluators/external_benchmark_method_smoke.schema.json",
        },
        "method": method,
        "checks": checks,
        "metrics": {
            "checks_passed": passed,
            "checks_total": total,
            "score_percent": round((passed / total) * 100, 2),
            "integration_status": "adapter_ready" if not failures else "adapter_incomplete",
            "blocking_failures": failures,
        },
        "evidence": {
            "citations_or_paths": [
                method["repo_url"],
                method["source_url"],
                "data/external_benchmark_methods.json",
            ],
        },
    }


def render_methods_doc(data: dict[str, Any]) -> str:
    lines = [
        "# Objective Benchmark Methods",
        "",
        "This registry maps selected external benchmark methods to the skill catalog without claiming benchmark scores. A method is usable here only after it has a concrete adapter definition, objective metrics, integration requirements, and a recorded repository-resolution artifact.",
        "",
        "Full-suite execution remains separate from adapter smoke checks. Any future score must include task inputs, environment details, command logs, output artifacts, and evaluator results.",
        "",
        "## Methods",
        "",
        "| Method | Scope | Metrics | Requirements | Adapter |",
        "|---|---|---|---|---|",
    ]
    for method in data["methods"]:
        metrics = ", ".join(method["primary_metrics"])
        requirements = ", ".join(method["integration_requirements"])
        lines.append(
            f"| `{method['id']}` | {method['scope']} | {metrics} | {requirements} | `{method['adapter_stage']}` |"
        )
    lines.extend(
        [
            "",
            "## Adapter Rule",
            "",
            "A smoke adapter proves only that the external method can be addressed objectively from this repository. It is not a task pass, not a model score, and not a substitute for running the external suite.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_smoke_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# External Benchmark Adapter Smoke Results",
        "",
        "These are real repository-resolution probes for the registered external benchmark methods. They verify adapter readiness only; no full benchmark suite score is claimed here.",
        "",
        "## Summary",
        "",
        f"- Run: `{manifest['run_name']}`",
        f"- Methods checked: `{manifest['summary']['method_count']}`",
        f"- Adapter-ready methods: `{manifest['summary']['adapter_ready']}`",
        f"- Incomplete adapters: `{manifest['summary']['adapter_incomplete']}`",
        "",
        "## Results",
        "",
        "| Method | Status | Score | Upstream HEAD | Artifact |",
        "|---|---|---:|---|---|",
    ]
    for item in manifest["artifacts"]:
        lines.append(
            f"| `{item['method_id']}` | `{item['integration_status']}` | {item['score_percent']} | "
            f"`{item['head_sha']}` | `{item['artifact_path']}` |"
        )
    return "\n".join(lines) + "\n"


def write_registry_outputs() -> dict[str, Any]:
    data = registry()
    write_json(ROOT / "data" / "external_benchmark_methods.json", data)
    (ROOT / "docs" / "objective-benchmark-methods.md").write_text(render_methods_doc(data), encoding="utf-8")
    return data


def run_smoke() -> dict[str, Any]:
    data = write_registry_outputs()
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    output_root = ROOT / "artifacts" / "external-benchmark-integrations" / RUN_NAME
    output_root.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, Any]] = []
    for method in data["methods"]:
        artifact = smoke_probe(method, timestamp)
        method_dir = output_root / slug(method["id"])
        method_dir.mkdir(parents=True, exist_ok=True)
        write_json(method_dir / "artifact.json", artifact)
        summaries.append(
            {
                "method_id": method["id"],
                "artifact_path": (method_dir / "artifact.json").relative_to(ROOT).as_posix(),
                "integration_status": artifact["metrics"]["integration_status"],
                "score_percent": artifact["metrics"]["score_percent"],
                "head_sha": artifact["input_snapshot"]["head_sha"],
                "blocking_failures": artifact["metrics"]["blocking_failures"],
            }
        )
    ready = sum(1 for item in summaries if item["integration_status"] == "adapter_ready")
    manifest = {
        "run_name": RUN_NAME,
        "artifact_kind": "external_benchmark_method_smoke",
        "runner": RUNNER_ID,
        "generated_at_utc": timestamp,
        "registry_path": "data/external_benchmark_methods.json",
        "summary": {
            "method_count": len(summaries),
            "adapter_ready": ready,
            "adapter_incomplete": len(summaries) - ready,
        },
        "artifacts": summaries,
    }
    write_json(output_root / "manifest.json", manifest)
    (ROOT / "docs" / "external-benchmark-adapter-smoke.md").write_text(render_smoke_report(manifest), encoding="utf-8")
    return manifest


def check_outputs() -> None:
    expected = registry()
    data_path = ROOT / "data" / "external_benchmark_methods.json"
    doc_path = ROOT / "docs" / "objective-benchmark-methods.md"
    report_path = ROOT / "docs" / "external-benchmark-adapter-smoke.md"
    manifest_path = ROOT / "artifacts" / "external-benchmark-integrations" / RUN_NAME / "manifest.json"
    if load_json(data_path) != expected:
        raise SystemExit("data/external_benchmark_methods.json is stale")
    if doc_path.read_text(encoding="utf-8") != render_methods_doc(expected):
        raise SystemExit("docs/objective-benchmark-methods.md is stale")
    manifest = load_json(manifest_path)
    if report_path.read_text(encoding="utf-8") != render_smoke_report(manifest):
        raise SystemExit("docs/external-benchmark-adapter-smoke.md is stale")
    expected_ids = {method["id"] for method in expected["methods"]}
    artifact_ids = {item["method_id"] for item in manifest["artifacts"]}
    if artifact_ids != expected_ids:
        raise SystemExit("external benchmark smoke manifest does not cover every method")
    for item in manifest["artifacts"]:
        artifact_path = ROOT / item["artifact_path"]
        artifact = load_json(artifact_path)
        if artifact["metrics"]["integration_status"] != item["integration_status"]:
            raise SystemExit(f"stale external smoke summary for {item['method_id']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate external benchmark method adapter readiness.")
    parser.add_argument("--check", action="store_true", help="Validate generated registry and smoke outputs without network probes.")
    parser.add_argument("--registry-only", action="store_true", help="Write only the method registry and registry documentation.")
    args = parser.parse_args()
    if args.check:
        check_outputs()
        print("External benchmark method outputs are current.")
        return 0
    if args.registry_only:
        data = write_registry_outputs()
        print(f"External benchmark methods registered: {data['method_count']}")
        return 0
    manifest = run_smoke()
    print(
        "External benchmark adapter smoke: "
        f"{manifest['summary']['adapter_ready']}/{manifest['summary']['method_count']} adapter-ready."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

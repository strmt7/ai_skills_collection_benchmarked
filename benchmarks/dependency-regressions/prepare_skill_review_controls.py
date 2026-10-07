#!/usr/bin/env python3
"""Prepare owned browser fixtures with the unchanged upstream HTML generator."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "included/skills/by-category/testing-qa-benchmarking/official-reference/skill-creator-anthropics"


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", required=True, type=Path, help="New owned fixture directory")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    sys.dont_write_bytecode = True
    args.output_directory.mkdir(parents=True, exist_ok=False)
    spec = importlib.util.spec_from_file_location("original_review", PACKAGE / "eval-viewer/generate_review.py")
    assert spec is not None and spec.loader is not None
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    run = {
        "id": "eval-0-with_skill",
        "eval_id": 0,
        "prompt": "Owned normal prompt",
        "outputs": [{"name": "owned.txt", "type": "text", "content": "Owned text with <tag> characters"}],
        "grading": {
            "summary": {"passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0},
            "expectations": [{"text": "Owned content", "passed": True, "evidence": "Owned evidence"}],
        },
    }
    benchmark = {
        "metadata": {"skill_name": "Owned fixture", "timestamp": "2026-10-02T00:00:00Z"},
        "run_summary": {},
        "runs": [
            {
                "eval_id": 0,
                "configuration": "with_skill",
                "run_number": 1,
                "result": {"pass_rate": 1.0},
                "expectations": run["grading"]["expectations"],
            }
        ],
    }
    cases = {}
    for name in ["normal", "script-boundary", "metadata", "grading-count", "evidence-attribute", "two-runs"]:
        current = json.loads(json.dumps(run))
        current_benchmark = json.loads(json.dumps(benchmark))
        marker = f"globalThis.__OWNED_REVIEW_CONTROL__='{name}'"
        if name == "script-boundary":
            current["prompt"] = f"</script><script>{marker}</script><script>"
        elif name == "metadata":
            current_benchmark["metadata"]["timestamp"] = f'<img src="/owned-missing" onerror="{marker}">'
        elif name == "grading-count":
            current["grading"]["summary"]["total"] = f'<img src="/owned-missing" onerror="{marker}">'
        elif name == "evidence-attribute":
            current_benchmark["runs"][0]["expectations"][0]["evidence"] = f'" onpointerenter="{marker}" data-owned="'
        runs = [current]
        if name == "two-runs":
            second = json.loads(json.dumps(run))
            second["id"], second["eval_id"] = "eval-1-without_skill", 1
            runs.append(second)
        data = original.generate_html(runs, "Owned fixture", benchmark=current_benchmark)
        file = args.output_directory / f"{name}.html"
        file.write_text(data, encoding="utf-8", newline="\n")
        cases[file.name] = hashlib.sha256(file.read_bytes()).hexdigest()
    safe_spec = importlib.util.spec_from_file_location("safe_review", ROOT / "tools/build_skill_review.py")
    assert safe_spec is not None and safe_spec.loader is not None
    safe_review = importlib.util.module_from_spec(safe_spec)
    safe_spec.loader.exec_module(safe_review)
    injection = '</script><img src="/owned-missing" onerror="globalThis.__OWNED_REVIEW_CONTROL__=1"><script>'
    safe_runs = [
        {"id": 'owned" data-extra="changed', "prompt": injection, "output_text": injection},
        {"id": "owned-second", "prompt": "Second prompt", "output_text": "Second output"},
    ]
    safe_file = args.output_directory / "safe-offline.html"
    safe_file.write_text(safe_review.render(safe_runs), encoding="utf-8", newline="\n")
    cases[safe_file.name] = hashlib.sha256(safe_file.read_bytes()).hexdigest()
    inputs = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [
            PACKAGE / "eval-viewer/generate_review.py",
            PACKAGE / "eval-viewer/viewer.html",
            ROOT / "tools/build_skill_review.py",
            Path(__file__),
        ]
    }
    receipt = {
        "schema_version": 1,
        "scope": "Owned fixtures only; no viewer server or port-killing helper invoked",
        "original_input_sha256": inputs,
        "fixture_sha256": cases,
        "ai_processes_launched": 0,
    }
    (args.output_directory / "manifest.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"fixtures": len(cases), "output_directory": str(args.output_directory)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

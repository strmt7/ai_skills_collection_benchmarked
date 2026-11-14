#!/usr/bin/env python3
"""Check official CLI account/quota/model metadata without starting a model trial."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _lib_b.io_utils import write_json
from _native_trial_plan import ROOT, archive_sources, execution_sources, load_plan
from _trial_account_readiness import probe
from _trial_context import create_context
from _trial_provider import validate_provider
from _trial_signin import home_identity
from _windows_appcontainer import checked_path


def run(plan_path: Path, output: Path) -> dict[str, Any]:
    """Admit frozen inputs, run one model-free check and retain sanitized evidence."""
    admitted = load_plan(plan_path)
    plan, runtime = admitted["plan"], admitted["runtime"]
    provider = validate_provider(plan["provider"])
    if provider.get("authentication") != "codex_signin":
        raise ValueError("This readiness check requires official CLI sign-in")
    output = checked_path(output)
    home = checked_path(Path(provider["codex_home"]))
    protected = [home, *runtime["roots"], plan_path.resolve(), *[ROOT / name for name in execution_sources()]]
    if output.exists() or any(output.is_relative_to(path) or path.is_relative_to(output) for path in protected):
        raise ValueError("Readiness evidence must be new and separate from protected inputs")
    if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT / ".venv"):
        raise ValueError("Review readiness evidence outside tracked source before publication")
    if home_identity(str(home)) != home_identity(provider["codex_home"]):
        raise ValueError("The selected sign-in home changed during path admission")
    output.mkdir(parents=True)
    archive_sources(output / "sources", plan["execution_source_sha256"])
    workspace = output / "workspace"
    workspace.mkdir()
    context = create_context(output / "controller", workspace, runtime["cli"], runtime["python"], runtime["roots"])
    report = probe(context, provider, plan["model"], plan["reasoning_effort"])
    if plan["execution_source_sha256"] != execution_sources():
        report.update(status="harness_error", eligible=False, error_type="SourceChanged")
    report.update(plan_sha256=admitted["plan_sha256"], execution_source_sha256=plan["execution_source_sha256"])
    write_json(output / "readiness.json", report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run(args.plan, args.output)
    except (OSError, ValueError, RuntimeError) as error:
        report = {
            "schema_version": 1,
            "status": "harness_error",
            "eligible": False,
            "error_type": type(error).__name__,
            "model_inferences": 0,
            "error_code": "readiness_setup_failed",
            "hint": "Use an admitted runtime and a fresh source-bound native plan; see docs/native-benchmark-controller.md.",
        }
    print(json.dumps(report, sort_keys=True))
    return {"eligible": 0, "ineligible": 1, "harness_error": 2}[report["status"]]


if __name__ == "__main__":
    raise SystemExit(main())

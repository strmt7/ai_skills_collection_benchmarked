"""Verify a declared multi-task plan and publish descriptive outcome summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from _trial_declarations import declared_task_signatures
from _trial_summary import aggregate, project_condition_pair, summarize_planned_order
from _trial_transcript import strict_json
from summarize_agent_trials import summarize


def run_plan(path: Path) -> dict[str, Any]:
    """Verify every declared single-task report and condition before aggregation."""
    raw = path.read_bytes()
    plan = strict_json(raw.decode("utf-8"))
    if (
        not isinstance(plan, dict)
        or set(plan) != {"schema_version", "tasks"}
        or type(plan["schema_version"]) is not int
        or plan["schema_version"] != 1
    ):
        raise ValueError("Invalid multi-task plan")
    if not isinstance(plan["tasks"], list) or not plan["tasks"]:
        raise ValueError("Plan must list at least one task")
    reports = []
    definitions = []
    configs = []
    hashes = set()
    for item in plan["tasks"]:
        if not isinstance(item, dict) or set(item) != {"id", "protocol", "protocol_sha256", "trials"}:
            raise ValueError("Invalid task plan entry")
        if any(not isinstance(item[key], str) or not item[key] for key in item):
            raise ValueError("Task plan values must be nonempty strings")
        protocol = path.parent / item["protocol"]
        trials = path.parent / item["trials"]
        source = protocol.read_bytes()
        digest = hashlib.sha256(source).hexdigest()
        if digest != item["protocol_sha256"] or digest in hashes:
            raise ValueError("Protocol hash differs or occurs more than once")
        hashes.add(digest)
        config = strict_json(source.decode("utf-8"))
        report = summarize(protocol, trials)
        if report["protocol_sha256"] != digest or report["task_id"] != item["id"]:
            raise ValueError("Verified task identity does not match the plan")
        reports.append(report)
        definitions.append(config["conditions"])
        configs.append(config)
    if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(raw).digest():
        raise ValueError("Multi-task plan changed during verification")
    signatures = [declared_task_signatures(config) for config in configs]
    task_signatures = [task for task, _ in signatures]
    if len(set(task_signatures)) != len(task_signatures):
        raise ValueError("Plan contains a duplicate declared task prompt and workspace")
    result = aggregate(reports, definitions)
    result["plan_sha256"] = hashlib.sha256(raw).hexdigest()
    result["planned_order_outcomes"] = {
        condition: summarize_planned_order(reports, configs, condition)
        for condition in sorted(set(definitions[0]) - {"default"})
    }
    for baseline, candidates in result["non_default_comparisons"].items():
        for candidate, comparison in candidates.items():
            projected = project_condition_pair(reports, baseline, candidate)
            projected_configs = [
                {
                    "conditions": {
                        "default": config["conditions"][baseline],
                        "candidate": config["conditions"][candidate],
                    },
                    "planned_order": [
                        {
                            "repetition": block["repetition"],
                            "conditions": [
                                "default" if name == baseline else "candidate"
                                for name in block["conditions"]
                                if name in {baseline, candidate}
                            ],
                        }
                        for block in config["planned_order"]
                    ],
                }
                for config in configs
            ]
            comparison["planned_order_outcomes"] = summarize_planned_order(projected, projected_configs, "candidate")
    result["limitations"].append(
        "Order groups describe planned relative positions, not verified execution order or an order effect; "
        "pooled blocks can be dependent and tasks may have unequal repetition counts."
    )
    result["declared_task_signatures"] = [
        {"task_id": report["task_id"], "sha256": task, "workspace_sha256": workspace}
        for report, (task, workspace) in zip(reports, signatures, strict=True)
    ]
    workspaces: dict[str, list[str]] = {}
    for report, (_, workspace) in zip(reports, signatures, strict=True):
        workspaces.setdefault(workspace, []).append(report["task_id"])
    result["declared_shared_workspaces"] = [
        {"workspace_sha256": key, "task_ids": sorted(ids)} for key, ids in sorted(workspaces.items()) if len(ids) > 1
    ]
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = run_plan(args.plan)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"ok": True, **result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

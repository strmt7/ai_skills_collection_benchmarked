"""Check example metrics against independent finite subset enumeration."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from fractions import Fraction
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))
from summarize_best_of_k import subset_success  # noqa: E402


def mean(values: list[Fraction]) -> Fraction:
    return sum(values, Fraction()) / len(values)


def verify() -> dict[str, str | int]:
    checked = 0
    for n in range(1, 9):
        for successes in range(n + 1):
            observations = [True] * successes + [False] * (n - successes)
            for k in range(1, n + 1):
                subsets = list(combinations(observations, k))
                for rule, condition in (("any", any), ("all", all)):
                    expected = Fraction(sum(condition(subset) for subset in subsets), len(subsets))
                    if subset_success(n, successes, k, rule=rule) != expected:
                        raise ValueError("Subset estimator disagrees with enumeration")
                    checked += 1

    unequal = [(2, 2), (8, 0)]
    sample = [(5, 5), (5, 3), (5, 1), (5, 0)]
    results: dict[str, str | int] = {
        "subsets_checked": checked,
        "unequal_attempts_equal_task_pass1": str(mean([subset_success(n, c, 1) for n, c in unequal])),
        "unequal_attempts_pooled_pass1": str(subset_success(10, 2, 1)),
        "four_tasks_pass1": str(mean([subset_success(n, c, 1) for n, c in sample])),
        "four_tasks_any5": str(mean([subset_success(n, c, 5) for n, c in sample])),
        "four_tasks_all5": str(mean([subset_success(n, c, 5, rule="all") for n, c in sample])),
    }
    reference_outputs: dict[str, str | int] = {
        "subsets_checked": 480,
        "unequal_attempts_equal_task_pass1": "1/2",
        "unequal_attempts_pooled_pass1": "1/5",
        "four_tasks_pass1": "9/20",
        "four_tasks_any5": "3/4",
        "four_tasks_all5": "1/4",
    }
    if results != reference_outputs:
        raise ValueError(f"Unexpected numerical result: {results}")
    return results


def build_report() -> dict[str, object]:
    inputs = (
        "included/improved/skills/eval-harness-current/SKILL.md",
        "tools/summarize_best_of_k.py",
        "artifacts/research/2026-11-03/eval-harness-sampling-v1/check_metrics.py",
    )
    return {
        "schema_version": 1,
        "scope": "Synthetic finite-subset controls; not an agent trial or skill-effectiveness result.",
        "input_sha256": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in inputs},
        "results": verify(),
        "agent_performance_tested": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--result", type=Path, default=Path(__file__).with_name("result.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = build_report()
        if args.check and json.loads(args.result.read_text(encoding="utf-8")) != report:
            raise ValueError("Sampling-control evidence is stale")
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Check selected Vaex statistics against independent synthetic expectations."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
import vaex
from vaex.promise import Promise

ROOT = Path(__file__).resolve().parents[3]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/vaex-delayed-statistics"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run() -> dict[str, Any]:
    require(version("vaex-core") == "4.19.0", "The control requires vaex-core 4.19.0")
    skill = (OVERLAY / "SKILL.md").read_text(encoding="utf-8")
    snippets = [part.split("```", 1)[0] for part in skill.split("```python\n")[1:]]
    require(len(snippets) == 1, "Expected one maintained example")
    original = (OVERLAY / "provenance/original.performance.md").read_text(encoding="utf-8")
    require(
        "mean_expr = df.total.mean()" in original and "result = mean_expr" in original,
        "The original immediate-mean example changed",
    )

    # The original example executes at the mean call, not at the assignment.
    control = vaex.from_arrays(price=np.array([2, 3, 4]), quantity=np.array([4, 2, 3]))
    context: dict[str, Any] = {"df": control}
    initial_passes = control.executor.passes
    exec("df['total'] = df.price * df.quantity\nmean_expr = df.total.mean()", context)
    require(control.executor.passes == initial_passes + 1, "The ordinary mean did not execute as expected")
    require(math.isclose(float(context["mean_expr"]), 26 / 3), "Unexpected ordinary mean")
    exec("result = mean_expr", context)
    require(control.executor.passes == initial_passes + 1, "Assignment unexpectedly executed another pass")
    mean_job = control.total.mean(delay=True)
    sum_job = control.total.sum(delay=True)
    require(isinstance(mean_job, Promise) and isinstance(sum_job, Promise), "Delayed controls are not promises")
    require(control.executor.passes == initial_passes + 1, "Scheduling unexpectedly executed a pass")
    control.execute()
    require(control.executor.passes == initial_passes + 2, "Delayed controls did not share one observed pass")
    require(
        math.isclose(float(mean_job.get()), 26 / 3) and math.isclose(float(sum_job.get()), 26),
        "Delayed controls returned unexpected values",
    )

    with tempfile.TemporaryDirectory(prefix="vaex-statistics-control-") as directory:
        input_csv = Path(directory) / "input.csv"
        input_csv.write_text("category,value\na,50\na,150\nb,100\nb,300\nc,250\n", encoding="utf-8")
        example: dict[str, Any] = {"input_csv": input_csv}
        exec(compile(snippets[0], str(OVERLAY / "SKILL.md"), "exec"), example)
        require(type(example["df"].dataset).__name__ == "DatasetCsvLazy", "Unexpected CSV dataset type")
        require(
            isinstance(example["mean_job"], Promise) and isinstance(example["sum_job"], Promise),
            "Delayed results are not promises",
        )
        require(math.isclose(example["mean_value"], 170.0), "Incorrect delayed mean")
        require(math.isclose(example["sum_value"], 850.0), "Incorrect delayed sum")
    return {
        "schema_version": 1,
        "platform": platform.system(),
        "python": platform.python_version(),
        "vaex_core": version("vaex-core"),
        "dask": version("dask"),
        "skill_sha256": hashlib.sha256((OVERLAY / "SKILL.md").read_bytes()).hexdigest(),
        "checks": [
            "original_mean_executes_at_call",
            "assignment_does_not_trigger_execution",
            "csv_uses_lazy_dataset",
            "delayed_statistics_resolve_correctly",
            "delayed_statistics_share_observed_pass",
        ],
        "agent_performance_tested": False,
        "full_skill_reviewed": False,
    }


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

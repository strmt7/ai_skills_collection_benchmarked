"""Exercise the Dask index overlay against independently specified fixtures."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path
from typing import Any

import dask
import dask.dataframe as dd
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/dask-index-queries"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run() -> dict[str, Any]:
    require(dask.__version__ == "2026.8.0" and pd.__version__ == "3.1.0", "Unexpected package versions")
    skill = (OVERLAY / "SKILL.md").read_text(encoding="utf-8")
    snippets = [part.split("```", 1)[0] for part in skill.split("```python\n")[1:]]
    require(len(snippets) == 1, "Expected one maintained example")
    original = (OVERLAY / "provenance/original.dataframes.md").read_text(encoding="utf-8")
    require("ddf.set_index('timestamp', sorted=True)" in original, "The original example changed")

    fixtures = (
        ("overlapping_unsorted", [1, 3, 2, 4], [10, 30, 20, 40], 2, 3, [(2, 20), (3, 30)]),
        ("already_sorted", [1, 2, 3, 4], [10, 20, 30, 40], 2, 3, [(2, 20), (3, 30)]),
        ("duplicate_labels", [3, 1, 3, 2], [30, 10, 31, 20], 2, 3, [(2, 20), (3, 30), (3, 31)]),
        ("empty_range", [1, 3, 2, 4], [10, 30, 20, 40], 8, 9, []),
    )
    checked = []
    for name, labels, values, lower, upper, expected in fixtures:
        data = pd.DataFrame({"timestamp": labels, "value": values})
        ddf = dd.from_pandas(data, npartitions=2, sort=False)
        context: dict[str, Any] = {"ddf": ddf, "lower": lower, "upper": upper}
        exec(compile(snippets[0], str(OVERLAY / "SKILL.md"), "exec"), context)
        result = context["result"]
        rows = sorted(zip(result.index.tolist(), result["value"].tolist(), strict=True))
        require(rows == expected, f"Incorrect selected rows for {name}")
        checked.append(name)

    # The original presorted assertion is invalid for this overlapping input.
    input_frame = pd.DataFrame({"timestamp": [1, 3, 2, 4], "value": [10, 30, 20, 40]})
    input_ddf = dd.from_pandas(input_frame, npartitions=2, sort=False)
    try:
        input_ddf.set_index("timestamp", sorted=True).loc[3].compute()
    except ValueError as exc:
        require("Missing dependency" in str(exc), "Unexpected presorted control failure")
    else:
        raise ValueError("Invalid presorted control unexpectedly succeeded")
    return {
        "schema_version": 1,
        "platform": platform.system(),
        "python": platform.python_version(),
        "dask": dask.__version__,
        "pandas": pd.__version__,
        "skill_sha256": hashlib.sha256((OVERLAY / "SKILL.md").read_bytes()).hexdigest(),
        "checks": checked + ["invalid_presorted_input_rejected_by_lookup"],
        "agent_performance_tested": False,
        "full_skill_reviewed": False,
    }


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

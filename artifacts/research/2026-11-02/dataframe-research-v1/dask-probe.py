"""Check a Dask index precondition with a fixed independent fixture."""

from __future__ import annotations

import json
import platform
from pathlib import Path

import dask
import dask.dataframe as dd
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
SOURCE = (
    ROOT
    / "included/skills/by-category/science-research-data-analysis/latest-release-community/dask/references/dataframes.md"
)


def run():
    if dask.__version__ != "2026.8.0":
        raise ValueError("This observation requires Dask 2026.8.0")
    if "ddf.set_index('timestamp', sorted=True)" not in SOURCE.read_text(encoding="utf-8"):
        raise ValueError("The source example changed")
    frame = pd.DataFrame({"timestamp": [1, 3, 2, 4], "value": [10, 30, 20, 40]})
    ddf = dd.from_pandas(frame, npartitions=2, sort=False)
    incorrect = ddf.set_index("timestamp", sorted=True)
    try:
        incorrect.loc[3].compute()
    except ValueError as exc:
        if "Missing dependency" not in str(exc):
            raise
        observed = type(exc).__name__
    else:
        raise ValueError("The overlapping-partition lookup unexpectedly succeeded")
    actual = ddf.set_index("timestamp").loc[3].compute()
    if actual.index.tolist() != [3] or actual["value"].tolist() != [30]:
        raise ValueError("The normal index construction did not preserve the expected row")
    return {
        "schema_version": 1,
        "platform": platform.system(),
        "python": platform.python_version(),
        "dask": dask.__version__,
        "pandas": pd.__version__,
        "incorrect_presorted_lookup_error": observed,
        "default_index_lookup": {"timestamp": 3, "value": 30},
        "agent_performance_tested": False,
        "full_skill_reviewed": False,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))

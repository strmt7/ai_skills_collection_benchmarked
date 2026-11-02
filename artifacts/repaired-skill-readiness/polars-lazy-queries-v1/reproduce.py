"""Test selected Polars instructions against independent synthetic expectations."""

from __future__ import annotations

import hashlib
import io
import json
import platform
import tempfile
from pathlib import Path
from typing import Any

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
OVERLAY = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/polars-lazy-queries"
)
SOURCE = ROOT / "included/skills/by-category/science-research-data-analysis/latest-release-community/polars"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def run() -> dict[str, Any]:
    require(pl.__version__ == "2.1.0", "The control requires Polars 2.1.0")
    skill = (OVERLAY / "SKILL.md").read_text(encoding="utf-8")
    snippets = [part.split("```", 1)[0] for part in skill.split("```python\n")[1:]]
    require(len(snippets) == 2, "Expected two maintained Python snippets")
    original = (SOURCE / "SKILL.md").read_text(encoding="utf-8")
    practices = (SOURCE / "references/best_practices.md").read_text(encoding="utf-8")
    io_guide = (SOURCE / "references/io_guide.md").read_text(encoding="utf-8")
    require("lf.collect(streaming=True)" in original, "Original streaming example changed")
    require("dtypes={" in io_guide, "Original CSV schema example changed")
    require('.filter(pl.col("value") > 100)' in practices, "Original filter example changed")
    removed = {}
    lazy = pl.LazyFrame({"value": [1, 2, 3]})
    for name, operation in (
        ("streaming", lambda: lazy.collect(streaming=True)),
        ("dtypes", lambda: pl.read_csv(io.BytesIO(b"id\n1\n"), dtypes={"id": pl.Int64})),
    ):
        try:
            operation()
        except pl.exceptions.ArgumentRemovedError as exc:
            removed[name] = type(exc).__name__
        else:
            raise ValueError(f"The original {name} argument unexpectedly succeeded")

    # The independent question is which group means over all rows exceed 100.
    # Group a has mean 100, b has mean 200, and c has mean 250.
    with tempfile.TemporaryDirectory(prefix="polars-lazy-control-") as directory:
        root = Path(directory)
        input_csv = root / "input.csv"
        input_csv.write_text("category,value\na,50\na,150\nb,100\nb,300\nc,250\n", encoding="utf-8")
        output_parquet = root / "result.parquet"
        context: dict[str, Any] = {"input_csv": input_csv, "output_parquet": output_parquet}
        exec(compile(snippets[0], str(OVERLAY / "SKILL.md"), "exec"), context)
        result = context["result"]
        expected = {"category": ["b", "c"], "mean_value": [200.0, 250.0]}
        require(result.to_dict(as_series=False) == expected, "Aggregate-first result differs from fixture")
        require(result.schema == {"category": pl.String, "mean_value": pl.Float64}, "Unexpected output schema")
        exec(compile(snippets[1], str(OVERLAY / "SKILL.md"), "exec"), context)
        restored = pl.read_parquet(output_parquet)
        require(restored.equals(result), "Parquet sink did not preserve result and schema")

        # Reproduce the original filter-before-mean choice on the same inputs.
        early = (
            pl.scan_csv(input_csv, schema_overrides={"category": pl.String, "value": pl.Float64})
            .filter(pl.col("value") > 100)
            .group_by("category")
            .agg(pl.col("value").mean().alias("mean_value"))
            .sort("category")
            .collect(engine="streaming")
        )
        require(
            early.to_dict(as_series=False) == {"category": ["a", "b", "c"], "mean_value": [150.0, 300.0, 250.0]},
            "Filter-before-aggregation counterexample did not reproduce",
        )
        require(not early.equals(result), "The two different questions unexpectedly produced equal data")
    return {
        "schema_version": 1,
        "platform": platform.system(),
        "python": platform.python_version(),
        "polars": pl.__version__,
        "skill_sha256": hashlib.sha256((OVERLAY / "SKILL.md").read_bytes()).hexdigest(),
        "checks": [
            "original_streaming_argument_removed",
            "original_dtypes_argument_removed",
            "aggregate_first_fixture_and_schema",
            "parquet_sink_round_trip",
            "filter_before_mean_changes_answer",
        ],
        "removed_argument_errors": removed,
        "agent_performance_tested": False,
        "full_skill_reviewed": False,
    }


def main() -> int:
    print(json.dumps(run(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

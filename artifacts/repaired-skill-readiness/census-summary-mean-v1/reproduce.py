"""Run focused Census examples against local native SOMA tables."""

import argparse
import json
import math
import platform
import re
import tempfile
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pyarrow as pa
import tiledbsoma as soma

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / (
    "included/repaired/skills/by-category/science-research-data-analysis/"
    "latest-release-community/cellxgene-census-summary-and-mean/SKILL.md"
)
ORIGINAL = SKILL.parent / "provenance/original.SKILL.md"


def examples():
    text = SKILL.read_text(encoding="utf-8")
    result = [part.split("```", 1)[0] for part in text.split("```python\n")[1:]]
    if len(result) != 2:
        raise RuntimeError("Expected summary and matrix examples")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary_code, mean_code = examples()
    source = ORIGINAL.read_text(encoding="utf-8")
    summary_original = re.search(r"summary\['total_cell_count'\]\[0\]", source)
    mean_original = re.search(r"n_observations = 0\n.*?mean_expression = sum_values / n_observations", source, re.S)
    if not summary_original or not mean_original:
        raise RuntimeError("Expected pinned examples have changed")

    with tempfile.TemporaryDirectory(prefix="census-native-control-") as temp:
        root = Path(temp)
        with soma.Collection.create(str(root / "census")) as census:
            info = census.add_new_collection("census_info")
            schema = pa.schema([("soma_joinid", pa.int64()), ("label", pa.string()), ("value", pa.string())])
            table = info.add_new_dataframe("summary", schema=schema, domain=((0, 1),))
            table.write(
                pa.table(
                    {
                        "soma_joinid": pa.array([0, 1], pa.int64()),
                        "label": ["census_build_date", "total_cell_count"],
                        "value": ["2025-11-08", "10000"],
                    }
                )
            )
        with soma.Collection.open(str(root / "census")) as census:
            scope = {"census": census}
            exec(compile(summary_code, str(SKILL), "exec"), scope)
            if scope["total_cell_count"] != 10000:
                raise AssertionError("Summary count differs from the native fixture")
            try:
                eval(compile(summary_original.group(), str(ORIGINAL), "eval"), scope)
            except KeyError:
                pass
            else:
                raise AssertionError("Pinned summary unexpectedly succeeded")

        uri = str(root / "experiment")
        schema = pa.schema([("soma_joinid", pa.int64())])
        with soma.Experiment.create(uri) as experiment:
            obs = experiment.add_new_dataframe("obs", schema=schema, domain=((0, 9),))
            obs.write(pa.table({"soma_joinid": pa.array([1, 4, 9], pa.int64())}))
            ms = experiment.add_new_collection("ms")
            rna = ms.add_new_collection("RNA", kind=soma.Measurement)
            var = rna.add_new_dataframe("var", schema=schema, domain=((0, 15),))
            var.write(pa.table({"soma_joinid": pa.array([2, 7, 15], pa.int64())}))
            x = rna.add_new_collection("X")
            raw = x.add_new_sparse_ndarray("raw", type=pa.float32(), shape=(10, 16))
            raw.write(
                pa.table(
                    {
                        "soma_dim_0": pa.array([1, 4], pa.int64()),
                        "soma_dim_1": pa.array([7, 2], pa.int64()),
                        "soma_data": pa.array([2, 4], pa.float32()),
                    }
                )
            )

        matrix = np.array([[0, 2, 0], [4, 0, 0], [0, 0, 0]], dtype=np.float32)
        cases = ((None, None, matrix), ([1, 9], [7, 15], matrix[np.ix_([0, 2], [1, 2])]), ([9], None, matrix[[2], :]))
        observed = []
        with soma.Experiment.open(uri) as experiment:
            for rows, cols, dense in cases:
                obs_query = soma.AxisQuery(coords=(rows,)) if rows is not None else None
                var_query = soma.AxisQuery(coords=(cols,)) if cols is not None else None
                with experiment.axis_query("RNA", obs_query=obs_query, var_query=var_query) as query:
                    scope = {"query": query}
                    exec(compile(mean_code, str(SKILL), "exec"), scope)
                    expected = float(dense.astype(np.float64).mean())
                    if not math.isclose(scope["mean_expression"], expected, rel_tol=1e-12, abs_tol=1e-12):
                        raise AssertionError("Sparse result differs from the dense fixture")
                    observed.append(scope["mean_expression"])
                    if rows is None:
                        old = {"query": query}
                        exec(compile(mean_original.group(), str(ORIGINAL), "exec"), old)
                        if float(old["mean_expression"]) != 3.0:
                            raise AssertionError("Pinned stored-entry mean changed")
            for kwargs in (
                {"obs_query": soma.AxisQuery(value_filter="soma_joinid == 99")},
                {"var_query": soma.AxisQuery(value_filter="soma_joinid == 99")},
            ):
                with experiment.axis_query("RNA", **kwargs) as query:
                    try:
                        exec(compile(mean_code, str(SKILL), "exec"), {"query": query})
                    except ValueError as error:
                        if str(error) != "Cannot average an empty cell-by-feature selection":
                            raise
                    else:
                        raise AssertionError("An empty selection was accepted")

        schema = pa.schema(
            [
                ("soma_joinid", pa.int64()),
                ("cell_type", pa.string()),
                ("tissue_general", pa.string()),
                ("is_primary_data", pa.bool_()),
            ]
        )
        projection_uri = str(root / "projection")
        with soma.DataFrame.create(projection_uri, schema=schema, domain=((0, 2),)) as frame:
            frame.write(
                pa.table(
                    {
                        "soma_joinid": pa.array([0, 1, 2], pa.int64()),
                        "cell_type": ["neuron", "glia", "other"],
                        "tissue_general": ["brain", "brain", "lung"],
                        "is_primary_data": [True, False, True],
                    }
                )
            )
        with soma.DataFrame.open(projection_uri) as frame:
            selected = (
                frame.read(
                    value_filter="tissue_general == 'brain' and is_primary_data == True",
                    column_names=["cell_type"],
                )
                .concat()
                .to_pandas()
            )
        if selected.groupby("tissue_general").size().to_dict() != {"brain": 1}:
            raise AssertionError("Filter-column projection behavior changed")

    result = {
        "schema_version": 1,
        "python": platform.python_version(),
        "packages": {name: version(name) for name in ("tiledbsoma", "numpy", "pyarrow", "pandas")},
        "summary_count": 10000,
        "means": observed,
        "pinned_stored_entry_mean": 3.0,
        "empty_cell_and_feature_selections_rejected": True,
        "filter_column_projection_checked": True,
        "live_census_tested": False,
        "biological_validity_tested": False,
        "agent_performance_tested": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

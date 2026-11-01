"""Exercise the Census ML streaming example on a synthetic native experiment."""

import argparse
import json
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pyarrow as pa
import tiledbsoma as soma
import torch
from tiledbsoma_ml import experiment_dataloader

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / (
    "included/repaired/skills/by-category/science-research-data-analysis/"
    "latest-release-community/cellxgene-census-ml-streaming/SKILL.md"
)
ORIGINAL = SKILL.parent / "provenance/original.SKILL.md"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    original = ORIGINAL.read_text(encoding="utf-8")
    if "from cellxgene_census.experimental.ml import experiment_dataloader" not in original:
        raise RuntimeError("The pinned source import changed")
    try:
        from cellxgene_census.experimental.ml import experiment_dataloader as old_loader
    except ModuleNotFoundError as error:
        if error.name != "cellxgene_census.experimental.ml":
            raise
    else:
        raise AssertionError(f"The pinned loader unexpectedly imported: {old_loader}")
    examples = [part.split("```", 1)[0] for part in SKILL.read_text(encoding="utf-8").split("```python\n")[1:]]
    if len(examples) != 1:
        raise RuntimeError("Expected one streaming example")
    code = compile(examples[0], str(SKILL), "exec")

    ids = [1, 3, 5, 7, 9, 11, 13, 15]
    genes = [1, 3, 5]
    matrix = np.arange(24, dtype=np.float32).reshape(8, 3)
    matrix[matrix % 4 == 0] = 0
    with tempfile.TemporaryDirectory(prefix="census-ml-control-") as temporary:
        uri = str(Path(temporary) / "experiment")
        schema = pa.schema([("soma_joinid", pa.int64()), ("class_id", pa.int64())])
        with soma.Experiment.create(uri) as experiment:
            obs = experiment.add_new_dataframe("obs", schema=schema, domain=((0, 15),))
            obs.write(
                pa.table(
                    {
                        "soma_joinid": pa.array(ids, pa.int64()),
                        "class_id": pa.array([i % 2 for i in range(8)], pa.int64()),
                    }
                )
            )
            measurements = experiment.add_new_collection("ms")
            rna = measurements.add_new_collection("RNA", kind=soma.Measurement)
            var = rna.add_new_dataframe("var", schema=pa.schema([("soma_joinid", pa.int64())]), domain=((0, 5),))
            var.write(pa.table({"soma_joinid": pa.array(genes, pa.int64())}))
            raw = rna.add_new_collection("X").add_new_sparse_ndarray("raw", type=pa.float32(), shape=(16, 6))
            rows, cols = np.nonzero(matrix)
            raw.write(
                pa.table(
                    {
                        "soma_dim_0": pa.array([ids[i] for i in rows], pa.int64()),
                        "soma_dim_1": pa.array([genes[i] for i in cols], pa.int64()),
                        "soma_data": pa.array(matrix[rows, cols], pa.float32()),
                    }
                )
            )

        with soma.Experiment.open(uri) as experiment:
            torch.manual_seed(71)
            model = torch.nn.Linear(3, 2)
            optimizer = torch.optim.SGD(model.parameters(), lr=0.001)
            before = model.weight.detach().clone()
            seen = []

            def consume(features, obs):
                for j, obs_id in enumerate(obs["soma_joinid"]):
                    row = ids.index(obs_id)
                    np.testing.assert_array_equal(features[j], matrix[row])
                    if obs["class_id"].iloc[j] != row % 2:
                        raise AssertionError("Labels are not aligned with join IDs")
                    seen.append(obs_id)
                inputs = torch.from_numpy(features).float()
                targets = torch.as_tensor(obs["class_id"].to_numpy(), dtype=torch.long)
                optimizer.zero_grad()
                torch.nn.functional.cross_entropy(model(inputs), targets).backward()
                optimizer.step()

            scope = {
                "experiment": experiment,
                "obs_query": None,
                "var_query": None,
                "seed": 71,
                "batch_size": 2,
                "process_train_batch": consume,
            }
            exec(code, scope)
            train, test = scope["train"], scope["test"]
            train_ids, test_ids = set(train.query_ids.obs_joinids.tolist()), set(test.query_ids.obs_joinids.tolist())
            if len(train_ids) != 6 or len(test_ids) != 2 or train_ids & test_ids or train_ids | test_ids != set(ids):
                raise AssertionError("Split did not partition the selected cells")
            train2, test2 = scope["dataset"].random_split(0.75, 0.25, seed=71)
            if (
                set(train2.query_ids.obs_joinids.tolist()) != train_ids
                or set(test2.query_ids.obs_joinids.tolist()) != test_ids
            ):
                raise AssertionError("Split was not reproducible for the fixed seed")
            if set(seen) != train_ids or len(seen) != len(train_ids) or torch.equal(before, model.weight.detach()):
                raise AssertionError("Training did not consume each training cell and update the model")
            evaluated = []
            for features, obs in experiment_dataloader(test, num_workers=0):
                for j, obs_id in enumerate(obs["soma_joinid"]):
                    row = ids.index(obs_id)
                    np.testing.assert_array_equal(features[j], matrix[row])
                    if obs["class_id"].iloc[j] != row % 2:
                        raise AssertionError("Test labels are not aligned")
                    evaluated.append(obs_id)
            if set(evaluated) != test_ids or len(evaluated) != len(test_ids):
                raise AssertionError("Test loader omitted or duplicated cells")

            small = {
                "experiment": experiment,
                "obs_query": soma.AxisQuery(value_filter="soma_joinid == 1"),
                "var_query": None,
                "seed": 71,
                "batch_size": 2,
                "process_train_batch": consume,
            }
            try:
                exec(code, small)
            except ValueError as error:
                if str(error) != "Both training and test selections must contain cells":
                    raise
            else:
                raise AssertionError("A one-cell split was accepted")

            filtered = []

            def consume_subset(features, obs):
                for j, obs_id in enumerate(obs["soma_joinid"]):
                    row = ids.index(obs_id)
                    np.testing.assert_array_equal(features[j], matrix[row, [0, 2]])
                    filtered.append(obs_id)

            subset = {
                "experiment": experiment,
                "obs_query": None,
                "var_query": soma.AxisQuery(coords=([1, 5],)),
                "seed": 71,
                "batch_size": 2,
                "process_train_batch": consume_subset,
            }
            exec(code, subset)
            if set(filtered) != set(subset["train"].query_ids.obs_joinids.tolist()) or len(filtered) != 6:
                raise AssertionError("Filtered feature selection lost training cells")

    result = {
        "schema_version": 1,
        "python": platform.python_version(),
        "packages": {
            name: version(name) for name in ("cellxgene-census", "tiledbsoma", "tiledbsoma-ml", "torch", "numpy")
        },
        "old_import_missing": True,
        "train_cells": 6,
        "test_cells": 2,
        "split_disjoint_and_repeatable": True,
        "features_and_labels_aligned": True,
        "filtered_features_checked": True,
        "small_selection_rejected": True,
        "cpu_training_updated_weights": True,
        "live_census_tested": False,
        "biological_validity_tested": False,
        "agent_performance_tested": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

---
name: cellxgene-census-ml-streaming
description: Stream a selected SOMA expression matrix into a PyTorch-compatible training workflow with TileDB-SOMA-ML.
license: MIT
---

# CELLxGENE Census ML streaming

For every task, apply Caveman. Before broad repository navigation, use
CocoIndex Code; for web-page research, use Crawl4AI. Read and follow the
repository-root `docs/agent-tools.md` and its linked skills, and retain the
required execution evidence.

The pinned Census skill imports loaders from `cellxgene_census.experimental.ml`;
that module is absent in Census 1.18.0. Use the current TileDB-SOMA-ML API
for a qualified dependency set. This focused guidance covers the local streaming
interface, not the entire source skill or the validity of a trained model.

## Stream a query

Given an open SOMA `experiment`, `obs_query` and `var_query` selections (or
`None`), integer `seed`, positive `batch_size`, and a caller-supplied
`process_train_batch(features, obs)` function:

```python
from tiledbsoma_ml import ExperimentDataset, experiment_dataloader

with experiment.axis_query("RNA", obs_query=obs_query, var_query=var_query) as query:
    dataset = ExperimentDataset(
        query,
        layer_name="raw",
        obs_column_names=["soma_joinid", "class_id"],
        batch_size=batch_size,
        shuffle=True,
        seed=seed,
    )
    train, test = dataset.random_split(0.75, 0.25, seed=seed)
    if not len(train.query_ids.obs_joinids) or not len(test.query_ids.obs_joinids):
        raise ValueError("Both training and test selections must contain cells")
    for features, obs in experiment_dataloader(train, num_workers=0):
        process_train_batch(features, obs)
```

Replace `class_id` with an actual observation column appropriate to the task.
The loader yields a NumPy feature batch and a pandas metadata batch, not a
mapping with `"X"` and `"obs"` keys. Preserve the join IDs and feature ordering;
encode labels and convert batches to tensors in the consumer. Record the Census
build, query, input layer, split and seed. Keep the experiment open while reading.

The example splits individual observations for demonstration. For estimates of
generalization across donors, samples or datasets, create appropriate grouped
training and test queries instead; a random cell split can leak related data.
Check class representation, fit preprocessing and label encoders on training
data only, and handle unseen labels explicitly. A split or one training step does
not validate the biology.

See the official [Census PyTorch tutorial](https://chanzuckerberg.github.io/cellxgene-census/notebooks/experimental/pytorch.html).

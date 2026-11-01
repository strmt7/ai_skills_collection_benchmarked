---
name: scvi-model-inputs
description: Register appropriate input data for scVI or SysVI and run a configurable model fit without treating every scvi-tools model as count-based.
license: MIT
---

# scvi-tools model inputs

For every task, apply Caveman. Before broad repository navigation, use
CocoIndex Code; for web-page research, use Crawl4AI. Read and follow the
repository-root `docs/agent-tools.md` and its linked skills, and retain the
required execution evidence.

The pinned skill says that all scvi-tools models require raw counts. Input
requirements are model-specific: SCVI uses count data, while SysVI is designed
for approximately normal data. Confirm the model's current documentation and
the data's provenance before registration. This focused overlay does not
review the other models or validate biological conclusions.

## SCVI: registered counts

Choose a count layer that contains the intended measured counts and, if needed,
a technical `batch_key` that exists in `adata.obs`. `None` uses no batch key.
Do not automatically register donor, condition or other biological variables as
nuisance covariates. Complete filtering and feature selection before setup.
Supply a chosen integer `seed`, latent dimension `n_latent` and dictionary of
`training_options` appropriate to the data and available hardware:

```python
import scvi

if "counts" not in adata.layers:
    raise ValueError("Provide the intended count layer before SCVI setup")
scvi.settings.seed = seed
scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key=batch_key)
model = scvi.model.SCVI(adata, n_latent=n_latent)
model.train(**training_options)
latent = model.get_latent_representation()
```

Count-like values alone do not establish provenance. Setup registers the given
fields; it does not create a missing count layer or normalize data. If the
training object or its feature ordering changes, use the model's documented
registration and query-mapping procedures instead of assuming the old registry
is still valid.

## SysVI: approximately normal input

SysVI's intended input is approximately normally distributed; its documentation
uses normalized, `log1p`-transformed RNA data as an example. Prepare the data
appropriate to the experiment, preserve its provenance, and select an existing
technical `batch_key`. The caller supplies `seed`, `n_latent`, `prior` and
`training_options`:

```python
import scvi

scvi.settings.seed = seed
scvi.external.SysVI.setup_anndata(adata, batch_key=batch_key)
model = scvi.external.SysVI(adata, n_latent=n_latent, prior=prior)
model.train(**training_options)
latent = model.get_latent_representation()
```

The examples are API starting points, not prescribed hyperparameters. Check
training and validation behavior, sensitivity to seeds and model choices, and
retention of relevant biology. A short synthetic fit does not establish model
convergence or biological validity. Normalized expression can be dense and
large; request only what the task needs.

See the [SCVI API](https://docs.scvi-tools.org/en/stable/api/reference/scvi.model.SCVI.html),
[SysVI model guide](https://docs.scvi-tools.org/en/stable/user_guide/models/sysvi.html)
and [scvi-tools overview](https://docs.scvi-tools.org/en/latest/tutorials/notebooks/quick_start/api_overview.html).
The preserved source entrypoint is in `provenance/`; the control is not an agent
benchmark.

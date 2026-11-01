# scvi-tools model input review

This review concerns a model-input claim in the pinned scvi-tools skill from
`K-Dense-AI/scientific-agent-skills` at commit
`eb20fb0dcb0b1dadaa3db2737188f0755bbc4770`. The upstream mirror is unchanged.

The pinned skill says all models require raw counts. The current
[SCVI API](https://docs.scvi-tools.org/en/stable/api/reference/scvi.model.SCVI.html)
describes its selected layer as count data, while the model-specific
[SysVI guide](https://docs.scvi-tools.org/en/stable/user_guide/models/sysvi.html)
describes approximately normally distributed inputs, with normalized and
log-transformed RNA as an example. The
[overview tutorial](https://docs.scvi-tools.org/en/latest/tutorials/notebooks/quick_start/api_overview.html)
also qualifies the count rule with model-specific exceptions. The generic
[user API page](https://docs.scvi-tools.org/en/stable/api/user.html) still states the broader rule, so consult the specific model's
documentation when sources differ.

The [maintained overlay](../included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/scvi-model-inputs/SKILL.md)
shows separate SCVI and SysVI setup patterns. The
[component control](../artifacts/repaired-skill-readiness/scvi-model-inputs-v1/reproduce.py)
executes both examples on dense and sparse synthetic inputs for one CPU epoch,
checks missing fields, verifies the models report a fit and compares their
returned latent arrays with the models' own results. The
[qualification record](../artifacts/repaired-skill-readiness/scvi-model-inputs-v1/qualification.json)
states the tested versions and limits. A one-epoch fit does not demonstrate
convergence, biological validity or agent effectiveness.

The pinned workflow loads a heart-cell example and requests a `counts` layer and
several covariates. A HEAD request for the documented dataset returned HTTP 403;
the dataset was not fetched or inspected, so this review does not claim those
fields are missing or that its normal loader fails. A separate synthetic test
confirmed that SCVI rejects a requested count layer when that layer is absent.

The newer upstream `v2.72.0` candidate at commit
`526ebce143bc326f44471554e33d66a19c840360` distinguishes model-specific input
requirements and creates a count layer in its illustrative SCVI example. This
observation does not validate the full upstream skill or its migration.

For the Windows control, scvi-tools 1.5.2 resolves `docrep` 0.3.2, which has
no published wheel. The control builds that source distribution inside a
dedicated environment using pinned build dependencies and checks the resulting
runtime graph. This is a reproducible installation recipe, not a claim of
byte-for-byte reproducible wheel builds or support for other platforms.

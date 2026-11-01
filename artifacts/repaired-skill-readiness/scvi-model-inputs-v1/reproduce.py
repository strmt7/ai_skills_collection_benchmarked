"""Exercise SCVI and SysVI input examples on small synthetic datasets."""

import argparse
import json
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import scanpy as sc
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / (
    "included/repaired/skills/by-category/science-research-data-analysis/"
    "latest-release-community/scvi-model-inputs/SKILL.md"
)
SOURCE = SKILL.parent / "provenance/original.SKILL.md"


def dense(value):
    return value.toarray() if hasattr(value, "toarray") else np.asarray(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    text = SKILL.read_text(encoding="utf-8")
    examples = [part.split("```", 1)[0] for part in text.split("```python\n")[1:]]
    if len(examples) != 2:
        raise RuntimeError("Expected focused SCVI and SysVI examples")
    original = SOURCE.read_text(encoding="utf-8")
    if "**Raw counts required**: Models expect unnormalized count data" not in original:
        raise RuntimeError("Pinned source claim has changed")

    counts = np.random.default_rng(71).poisson(3, size=(80, 32)).astype(np.float32)
    obs = pd.DataFrame({"batch": ["a", "b"] * 40}, index=[f"cell_{i}" for i in range(80)])
    absent = ad.AnnData(counts.copy(), obs=obs.copy())
    try:
        exec(compile(examples[0], str(SKILL), "exec"), {"adata": absent})
    except ValueError as exc:
        if str(exc) != "Provide the intended count layer before SCVI setup":
            raise
    else:
        raise RuntimeError("SCVI example unexpectedly accepted a missing layer")

    missing_batch = ad.AnnData(counts.copy())
    missing_batch.layers["counts"] = missing_batch.X.copy()
    try:
        exec(compile(examples[0], str(SKILL), "exec"), {"adata": missing_batch, "batch_key": "batch", "seed": 71})
    except (ValueError, KeyError):
        pass
    else:
        raise RuntimeError("SCVI example unexpectedly accepted a missing batch column")

    results = {}
    with tempfile.TemporaryDirectory(prefix="scvi-model-controls-") as temporary:
        options = {
            "max_epochs": 1,
            "train_size": 0.8,
            "batch_size": 16,
            "accelerator": "cpu",
            "devices": 1,
            "enable_progress_bar": False,
            "logger": False,
            "enable_model_summary": False,
            "enable_checkpointing": False,
            "default_root_dir": temporary,
        }
        for kind, matrix in (("dense", counts.copy()), ("sparse", csr_matrix(counts))):
            adata = ad.AnnData(matrix.copy(), obs=obs.copy())
            adata.layers["counts"] = adata.X.copy()
            context = {
                "adata": adata,
                "batch_key": "batch",
                "seed": 71,
                "n_latent": 4,
                "training_options": options,
            }
            exec(compile(examples[0], str(SKILL), "exec"), context)
            if not context["model"].is_trained:
                raise RuntimeError("SCVI did not complete a fit")
            if context["latent"].shape != (80, 4) or not np.isfinite(context["latent"]).all():
                raise RuntimeError("SCVI returned invalid latent output")
            np.testing.assert_allclose(context["latent"], context["model"].get_latent_representation())
            np.testing.assert_array_equal(dense(adata.layers["counts"]), counts)

            adata = ad.AnnData(matrix.copy(), obs=obs.copy())
            sc.pp.normalize_total(adata, target_sum=1e4)
            sc.pp.log1p(adata)
            transformed = dense(adata.X).copy()
            if np.allclose(transformed, np.rint(transformed)):
                raise RuntimeError("SysVI synthetic input was not transformed")
            context = {
                "adata": adata,
                "batch_key": "batch",
                "seed": 71,
                "n_latent": 4,
                "prior": "standard_normal",
                "training_options": options,
            }
            exec(compile(examples[1], str(SKILL), "exec"), context)
            if not context["model"].is_trained:
                raise RuntimeError("SysVI did not complete a fit")
            if context["latent"].shape != (80, 4) or not np.isfinite(context["latent"]).all():
                raise RuntimeError("SysVI returned invalid latent output")
            np.testing.assert_allclose(context["latent"], context["model"].get_latent_representation())
            np.testing.assert_allclose(dense(adata.X), transformed)
            results[kind] = {
                "scvi_counts_preserved": True,
                "scvi_latent_finite": True,
                "sysvi_transformed_input": True,
                "sysvi_latent_finite": True,
            }

    result = {
        "python": platform.python_version(),
        "platform": platform.system(),
        "packages": {n: version(n) for n in ("scvi-tools", "scanpy", "anndata", "torch")},
        "missing_counts_rejected": True,
        "missing_batch_rejected": True,
        "cases": results,
        "cpu_epochs_per_fit": 1,
        "synthetic": True,
        "source_dataset_inspected": False,
        "biological_validity_tested": False,
        "agent_performance_tested": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

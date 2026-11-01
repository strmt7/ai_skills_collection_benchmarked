"""Run the pinned Scanpy failure and maintained examples on synthetic data."""

import json
import tempfile
from importlib.metadata import version
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import anndata as ad
import numpy as np
import scanpy as sc
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / (
    "included/repaired/skills/by-category/science-research-data-analysis/"
    "latest-release-community/scanpy-counts-clustering/SKILL.md"
)
SOURCE = SKILL.parent / "provenance/original.SKILL.md"


def dense(value):
    return value.toarray() if hasattr(value, "toarray") else np.asarray(value)


def main():
    text = SKILL.read_text(encoding="utf-8")
    examples = [block.split("```", 1)[0] for block in text.split("```python\n")[1:]]
    if len(examples) != 2:
        raise RuntimeError("Expected two focused Scanpy examples")
    source = SOURCE.read_text(encoding="utf-8").split("## Standard Analysis Workflow", 1)[1]
    section = source.split("### 2. Normalization and Preprocessing", 1)[1].split("### 3.", 1)[0]
    commands = ["sc.pp.normalize_total(adata, target_sum=1e4)", "sc.pp.log1p(adata)", "adata.raw = adata"]
    positions = [section.index(command) for command in commands]
    if positions != sorted(positions) or "# Save raw counts for later" not in section:
        raise RuntimeError("Source normalization example has changed")
    plot = "sc.pl.umap(adata, color='leiden')"
    if source.index(plot) >= source.index("sc.tl.leiden(adata, resolution=0.5)"):
        raise RuntimeError("Source plot no longer precedes Leiden")

    counts = np.random.default_rng(8765).poisson(3, size=(48, 20)).astype(np.float32)
    results = {}
    for kind, matrix in (("dense", counts.copy()), ("sparse", csr_matrix(counts))):
        original = ad.AnnData(matrix.copy())
        original_context = {"sc": sc, "adata": original}
        for command in commands:
            exec(command, original_context)
        if np.array_equal(dense(original.raw.X), counts):
            raise RuntimeError("Source snapshot unexpectedly contains input counts")
        original.obsm["X_umap"] = np.zeros((len(counts), 2))
        try:
            exec(plot, original_context)
        except KeyError as exc:
            if exc.args != ("leiden",):
                raise
        else:
            raise RuntimeError("Source plot unexpectedly accepted missing labels")

        adata = ad.AnnData(matrix.copy())
        context = {"adata": adata, "n_pcs": 5, "n_neighbors": 6, "resolution": 0.5}
        exec(compile(examples[0], str(SKILL), "exec"), context)
        np.testing.assert_array_equal(dense(adata.layers["counts"]), counts)
        normalized = dense(adata.raw.X).copy()
        exec(compile(examples[1], str(SKILL), "exec"), context)
        if len(adata.obs["leiden"]) != len(counts) or adata.obs["leiden"].isna().any():
            raise RuntimeError("Clustering did not assign every observation")
        if not np.isfinite(adata.obsm["X_umap"]).all():
            raise RuntimeError("UMAP returned non-finite coordinates")
        adata.X = adata.X.copy()
        adata.X[0, 0] = 0
        np.testing.assert_allclose(dense(adata.raw.X), normalized)
        np.testing.assert_array_equal(dense(adata.layers["counts"]), counts)
        with tempfile.TemporaryDirectory(prefix="scanpy-cluster-") as tmp:
            output = Path(tmp) / "analysis.h5ad"
            adata.write_h5ad(output)
            saved = ad.io.read_h5ad(output)
            np.testing.assert_array_equal(dense(saved.layers["counts"]), counts)
            np.testing.assert_allclose(dense(saved.raw.X), normalized)
            if len(saved.obs) != len(counts) or saved.obs["leiden"].isna().any():
                raise RuntimeError("Round trip lost cluster labels")
        results[kind] = {
            "source_errors_reproduced": True,
            "counts_preserved": True,
            "raw_independent": True,
            "leiden_and_plot": True,
            "round_trip": True,
        }
        matplotlib.pyplot.close("all")

    occupied = ad.AnnData(counts.copy())
    occupied.layers["counts"] = np.zeros_like(counts)
    try:
        exec(compile(examples[0], str(SKILL), "exec"), {"adata": occupied})
    except ValueError as exc:
        if "counts already exists" not in str(exc):
            raise
    else:
        raise RuntimeError("Existing counts layer was unexpectedly replaced")
    np.testing.assert_array_equal(occupied.layers["counts"], np.zeros_like(counts))
    np.testing.assert_array_equal(occupied.X, counts)
    print(
        json.dumps(
            {
                "cases": results,
                "existing_counts_preserved": True,
                "packages": {n: version(n) for n in ("anndata", "scanpy", "igraph", "leidenalg")},
                "synthetic": True,
                "biological_validity_tested": False,
                "agent_performance_tested": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

"""Control the AnnData and Scanpy 10x reader calls with a tiny synthetic file."""

import json
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import scanpy as sc


def main():
    with tempfile.TemporaryDirectory(prefix="anndata-10x-control-") as tmp:
        path = Path(tmp) / "synthetic.h5"
        with h5py.File(path, "w") as out:
            matrix = out.create_group("matrix")
            matrix.create_dataset("data", data=np.array([2, 1, 3], dtype=np.int32))
            matrix.create_dataset("indices", data=np.array([0, 1, 0], dtype=np.int32))
            matrix.create_dataset("indptr", data=np.array([0, 1, 2, 3], dtype=np.int32))
            matrix.create_dataset("shape", data=np.array([2, 3], dtype=np.int64))
            matrix.create_dataset("barcodes", data=np.array([b"cell1", b"cell2", b"cell3"]))
            features = matrix.create_group("features")
            features.create_dataset("id", data=np.array([b"id1", b"id2"]))
            features.create_dataset("name", data=np.array([b"gene1", b"gene2"]))
            features.create_dataset("feature_type", data=np.array([b"Gene Expression", b"Gene Expression"]))
            features.create_dataset("genome", data=np.array([b"GRCh38", b"GRCh38"]))
        try:
            ad.read_10x_h5(path)
        except AttributeError as exc:
            missing = str(exc)
        else:
            raise RuntimeError("AnnData unexpectedly provides read_10x_h5")
        result = sc.read_10x_h5(path)
        observed = result.X.toarray().tolist()
        expected = [[2, 0], [0, 1], [3, 0]]
        cells = result.obs_names.tolist()
        genes = result.var_names.tolist()
        gene_ids = result.var["gene_ids"].tolist()
        if (
            list(result.shape) != [3, 2]
            or observed != expected
            or cells != ["cell1", "cell2", "cell3"]
            or genes != ["gene1", "gene2"]
            or gene_ids != ["id1", "id2"]
        ):
            raise RuntimeError("Scanpy did not preserve the known synthetic matrix")
        print(
            json.dumps(
                {
                    "anndata": version("anndata"),
                    "scanpy": version("scanpy"),
                    "python": platform.python_version(),
                    "platform": platform.system(),
                    "numpy": version("numpy"),
                    "h5py": version("h5py"),
                    "wrapt": version("wrapt"),
                    "ann_data_call_error": missing,
                    "scanpy_shape": list(result.shape),
                    "scanpy_matrix": observed,
                    "cells": cells,
                    "genes": genes,
                    "gene_ids": gene_ids,
                    "synthetic_fixture": True,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()

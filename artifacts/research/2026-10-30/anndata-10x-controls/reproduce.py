"""Control the AnnData and Scanpy 10x reader calls with a tiny synthetic file."""

import gzip
import json
import platform
import tempfile
import warnings
from importlib.metadata import version
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import openpyxl
import pandas as pd
import scanpy as sc
from anndata.experimental import AnnCollection


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
            if "read_10x_h5" not in missing:
                raise
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
        mtx_dir = Path(tmp) / "matrix"
        mtx_dir.mkdir()
        files = {
            "matrix.mtx.gz": "%%MatrixMarket matrix coordinate integer general\n2 3 3\n1 1 2\n2 2 1\n1 3 3\n",
            "features.tsv.gz": "id1\tgene1\tGene Expression\nid2\tgene2\tGene Expression\n",
            "barcodes.tsv.gz": "cell1\ncell2\ncell3\n",
        }
        for name, content in files.items():
            with gzip.open(mtx_dir / name, "wt", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
        try:
            ad.read_10x_mtx(mtx_dir)
        except AttributeError as exc:
            missing_mtx = str(exc)
            if "read_10x_mtx" not in missing_mtx:
                raise
        else:
            raise RuntimeError("AnnData unexpectedly provides read_10x_mtx")
        mtx = sc.read_10x_mtx(mtx_dir)
        if (
            list(mtx.shape) != [3, 2]
            or mtx.X.toarray().tolist() != expected
            or mtx.obs_names.tolist() != cells
            or mtx.var_names.tolist() != genes
            or mtx.var["gene_ids"].tolist() != gene_ids
        ):
            raise RuntimeError("Scanpy did not preserve the synthetic Matrix Market data")
        plain_mtx = Path(tmp) / "matrix.mtx"
        plain_mtx.write_text(files["matrix.mtx.gz"], encoding="utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            try:
                ad.read_mtx(plain_mtx, var_names="features.tsv", obs_names="barcodes.tsv")
            except TypeError as exc:
                bad_mtx_args = str(exc)
                if "var_names" not in bad_mtx_args:
                    raise
            else:
                raise RuntimeError("Unexpected acceptance of unsupported read_mtx arguments")
        generic = ad.io.read_mtx(plain_mtx).T
        features_table = pd.read_csv(mtx_dir / "features.tsv.gz", sep="\t", header=None, dtype=str)
        barcodes_table = pd.read_csv(mtx_dir / "barcodes.tsv.gz", sep="\t", header=None, dtype=str)
        generic.obs_names = barcodes_table[0].tolist()
        generic.var_names = features_table[1].tolist()
        if (
            generic.X.toarray().tolist() != expected
            or generic.obs_names.tolist() != cells
            or generic.var_names.tolist() != genes
        ):
            raise RuntimeError("Generic Matrix Market control did not preserve data and labels")
        excel_path = Path(tmp) / "synthetic.xlsx"
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Data"
        for row in (["cell", "gene1", "gene2"], ["cell1", 2, 0], ["cell2", 0, 1], ["cell3", 3, 0]):
            sheet.append(row)
        workbook.save(excel_path)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", FutureWarning)
            try:
                ad.read_excel(excel_path)
            except TypeError as exc:
                missing_sheet = str(exc)
                if "sheet" not in missing_sheet:
                    raise
            else:
                raise RuntimeError("Unexpected acceptance of read_excel without a sheet")
        excel = ad.io.read_excel(excel_path, sheet="Data")
        if excel.X.tolist() != expected or excel.obs_names.tolist() != cells or excel.var_names.tolist() != genes:
            raise RuntimeError("Excel control did not preserve data and labels")
        missing_element_exports = [name for name in ("read_elem", "write_elem") if not hasattr(ad, name)]
        if missing_element_exports != ["read_elem", "write_elem"]:
            raise RuntimeError("unexpected top-level element exports")
        elem_path = Path(tmp) / "elements.h5"
        with h5py.File(elem_path, "w") as store:
            ad.io.write_elem(store, "values", np.array([2, 1, 3], dtype=np.int32))
        with h5py.File(elem_path, "r") as store:
            element_values = ad.io.read_elem(store["values"]).tolist()
        if element_values != [2, 1, 3]:
            raise RuntimeError("stored element did not round-trip")
        try:
            ad.io.read_elem(str(elem_path) + "/values")
        except (AttributeError, TypeError, NotImplementedError) as exc:
            string_element_error = f"{type(exc).__name__}: {exc}"
        else:
            raise RuntimeError("unexpected acceptance of a path string as a storage element")
        backed_path = Path(tmp) / "backed.h5ad"
        ad.AnnData(np.array([[1, 2], [3, 4]], dtype=np.float32)).write_h5ad(backed_path)
        backed = ad.read_h5ad(backed_path, backed="r+")
        try:
            backed.obs["new_column"] = [10, 20]
            backed.X[0, 0] = 77
        finally:
            backed.file.close()
        reopened = ad.read_h5ad(backed_path)
        obs_persisted = "new_column" in reopened.obs
        x_value = float(reopened.X[0, 0])
        if obs_persisted or x_value != 77:
            raise RuntimeError("backed update control did not match expected persistence")
        new_path = Path(tmp) / "explicit-write.h5ad"
        backed = ad.read_h5ad(backed_path, backed="r+")
        try:
            backed.obs["new_column"] = [10, 20]
            backed.write_h5ad(new_path)
        finally:
            backed.file.close()
        rewritten = ad.read_h5ad(new_path)
        saved_obs = rewritten.obs["new_column"].tolist()
        if saved_obs != [10, 20]:
            raise RuntimeError("explicit write did not preserve observation metadata")
        paths = [backed_path, new_path]
        try:
            AnnCollection([str(item) for item in paths], join_obs="inner", join_vars="inner")
        except AttributeError as exc:
            collection_paths_error = str(exc)
            if "var_names" not in collection_paths_error:
                raise
        else:
            raise RuntimeError("unexpected acceptance of file paths in AnnCollection")
        datasets = [ad.read_h5ad(item, backed="r") for item in paths]
        try:
            collection = AnnCollection(datasets, join_obs="inner", join_vars="inner", index_unique="-")
            collection_shape = list(collection.shape)
            collection_cells = collection.obs_names.tolist()
            collection_values = np.asarray(collection[:].X).tolist()
            if (
                collection_shape != [4, 2]
                or len(set(collection_cells)) != 4
                or collection_values != [[77, 2], [3, 4], [77, 2], [3, 4]]
            ):
                raise RuntimeError("backed AnnCollection did not preserve both datasets")
        finally:
            for dataset in datasets:
                dataset.file.close()
        deprecations = {}
        for name in ("read_csv", "read_mtx"):
            with warnings.catch_warnings(record=True) as captured:
                warnings.simplefilter("always")
                legacy = getattr(ad, name)
            messages = [str(item.message) for item in captured if issubclass(item.category, FutureWarning)]
            if (
                not callable(legacy)
                or not callable(getattr(ad.io, name))
                or not any("deprecated" in m for m in messages)
            ):
                raise RuntimeError(f"unexpected deprecation behavior for {name}")
            deprecations[name] = messages
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
                    "openpyxl": version("openpyxl"),
                    "ann_data_call_error": missing,
                    "ann_data_mtx_call_error": missing_mtx,
                    "scanpy_shape": list(result.shape),
                    "scanpy_matrix": observed,
                    "scanpy_mtx_shape": list(mtx.shape),
                    "scanpy_mtx_matrix": mtx.X.toarray().tolist(),
                    "read_mtx_bad_arguments_error": bad_mtx_args,
                    "generic_mtx_shape": list(generic.shape),
                    "read_excel_missing_sheet_error": missing_sheet,
                    "excel_shape": list(excel.shape),
                    "missing_top_level_element_exports": missing_element_exports,
                    "string_element_error": string_element_error,
                    "stored_element_values": element_values,
                    "backed_obs_persisted_without_write": obs_persisted,
                    "backed_x_value_after_reopen": x_value,
                    "explicit_write_obs_values": saved_obs,
                    "anncollection_paths_error": collection_paths_error,
                    "anncollection_backed_shape": collection_shape,
                    "anncollection_backed_values": collection_values,
                    "deprecated_top_level_imports": deprecations,
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

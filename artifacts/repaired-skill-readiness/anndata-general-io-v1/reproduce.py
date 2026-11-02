"""Exercise the maintained AnnData examples using synthetic local data."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import tempfile
from contextlib import ExitStack
from importlib.metadata import version
from pathlib import Path
from typing import Any

import anndata as ad
import numpy as np
import openpyxl
import pandas as pd
from scipy.io import mmwrite
from scipy.sparse import coo_matrix, csr_matrix

ROOT = Path(__file__).resolve().parents[3]
SKILL = (
    ROOT
    / "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/anndata-general-io/SKILL.md"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict[str, Any]:
    text = SKILL.read_text(encoding="utf-8")
    snippets = [part.split("```", 1)[0] for part in text.split("```python\n")[1:]]
    if len(snippets) != 4:
        raise ValueError("Expected four maintained Python examples")
    with tempfile.TemporaryDirectory(prefix="anndata-general-io-") as temporary:
        root = Path(temporary)
        matrix = root / "matrix.mtx"
        mmwrite(matrix, coo_matrix([[2, 0, 3], [0, 1, 0]]))
        obs, var = root / "obs.tsv", root / "var.tsv"
        obs.write_text("cell-a\nNA\ncell-c\n", encoding="utf-8")
        var.write_text("gene-a\ngene-b\n", encoding="utf-8")
        context: dict[str, Any] = {"matrix_path": matrix, "observation_ids_path": obs, "feature_ids_path": var}
        exec(compile(snippets[0], str(SKILL), "exec"), context)
        data = context["data"]
        np.testing.assert_array_equal(data.X.toarray(), [[2, 0], [0, 1], [3, 0]])
        if data.obs_names.tolist() != ["cell-a", "NA", "cell-c"] or data.var_names.tolist() != ["gene-a", "gene-b"]:
            raise AssertionError("Matrix labels do not match the supplied axes")
        for invalid in ("cell-a\ncell-a\ncell-c\n", "cell-a\n\ncell-c\n", "cell-a\ncell-b\n"):
            obs.write_text(invalid, encoding="utf-8")
            try:
                exec(compile(snippets[0], str(SKILL), "exec"), dict(context))
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid observation IDs were accepted")

        excel = root / "matrix.xlsx"
        book = openpyxl.Workbook()
        book.active.title = "Unused"
        sheet = book.create_sheet("Selected")
        for row in (["cell", "gene-a", "gene-b"], ["cell-a", 2, 0], ["cell-b", 0, 1]):
            sheet.append(row)
        book.save(excel)
        context = {"workbook_path": excel, "sheet_name": "Selected"}
        exec(compile(snippets[1], str(SKILL), "exec"), context)
        data = context["data"]
        np.testing.assert_array_equal(data.X, [[2, 0], [0, 1]])
        if data.obs_names.tolist() != ["cell-a", "cell-b"] or data.var_names.tolist() != ["gene-a", "gene-b"]:
            raise AssertionError("Excel labels do not match the selected sheet")
        try:
            exec(compile(snippets[1], str(SKILL), "exec"), {"workbook_path": excel, "sheet_name": "Missing"})
        except (KeyError, ValueError):
            pass
        else:
            raise AssertionError("An absent workbook sheet was accepted")

        element = root / "element.h5"
        context = {"element_path": element, "values": np.array([2, 1, 3], dtype=np.int32)}
        exec(compile(snippets[2], str(SKILL), "exec"), context)
        np.testing.assert_array_equal(context["restored"], [2, 1, 3])
        original = digest(element)
        try:
            exec(compile(snippets[2], str(SKILL), "exec"), dict(context))
        except FileExistsError:
            pass
        else:
            raise AssertionError("An existing HDF5 destination was overwritten")
        if digest(element) != original:
            raise AssertionError("An existing HDF5 destination changed")

        first, second = root / "first.h5ad", root / "second.h5ad"
        ad.AnnData(
            np.array([[1, 2], [3, 4]]),
            obs=pd.DataFrame({"batch": ["A", "A"], "left_only": [1, 2]}, index=["a", "b"]),
            var=pd.DataFrame(index=["g1", "g2"]),
        ).write_h5ad(first)
        ad.AnnData(
            np.array([[20, 10], [40, 30]]),
            obs=pd.DataFrame({"batch": ["B", "B"], "right_only": [3, 4]}, index=["a", "c"]),
            var=pd.DataFrame(index=["g2", "g1"]),
        ).write_h5ad(second)
        input_hashes = [digest(first), digest(second)]
        context = {"input_paths": [first, second]}
        exec(compile(snippets[3], str(SKILL), "exec"), context)
        combined, observations, variables = context["matrix"], context["observations"], context["variables"]
        if combined.shape != (4, 2) or variables.tolist() != ["g1", "g2"]:
            raise AssertionError("Collection axes do not match the expected feature alignment")
        if observations.index.tolist() != ["a-0", "b-0", "a-1", "c-1"] or list(observations) != ["batch"]:
            raise AssertionError("Collection observation IDs or shared metadata differ")
        np.testing.assert_array_equal(combined, [[1, 2], [3, 4], [10, 20], [30, 40]])
        if (
            any(dataset.file.is_open for dataset in context["datasets"])
            or [digest(first), digest(second)] != input_hashes
        ):
            raise AssertionError("Collection input changed or a backed handle remained open")
        # Record the observed full-materialization failure for both feature orders.
        same_order = root / "same-order.h5ad"
        ad.AnnData(
            np.array([[10, 20]]), obs=pd.DataFrame(index=["a"]), var=pd.DataFrame(index=["g1", "g2"])
        ).write_h5ad(same_order)
        materialization_failures = {}
        for case, path in (("same_order", same_order), ("reordered", second)):
            with ExitStack() as stack:
                from anndata.experimental import AnnCollection

                left = ad.io.read_h5ad(first, backed="r")
                stack.callback(left.file.close)
                right = ad.io.read_h5ad(path, backed="r")
                stack.callback(right.file.close)
                try:
                    AnnCollection([left, right], join_obs="inner", join_vars="inner", index_unique="-")[:].to_adata()
                except (TypeError, ValueError) as exc:
                    materialization_failures[case] = f"{type(exc).__name__}: {exc}"
                else:
                    raise AssertionError(f"Expected full materialization failure was not reproduced: {case}")
        sparse_first, sparse_second = root / "sparse-first.h5ad", root / "sparse-second.h5ad"
        for path, values, genes in (
            (sparse_first, [[1, 2]], ["g1", "g2"]),
            (sparse_second, [[20, 10]], ["g2", "g1"]),
        ):
            ad.AnnData(csr_matrix(values), obs=pd.DataFrame(index=["a"]), var=pd.DataFrame(index=genes)).write_h5ad(
                path
            )
        sparse_context: dict[str, Any] = {"input_paths": [sparse_first, sparse_second]}
        exec(compile(snippets[3], str(SKILL), "exec"), sparse_context)
        np.testing.assert_array_equal(sparse_context["matrix"].toarray(), [[1, 2], [10, 20]])
        if any(dataset.file.is_open for dataset in sparse_context["datasets"]):
            raise AssertionError("Sparse collection left a backed handle open")
        failed: dict[str, Any] = {"input_paths": [first, root / "missing.h5ad"]}
        try:
            exec(compile(snippets[3], str(SKILL), "exec"), failed)
        except FileNotFoundError as exc:
            if len(failed["datasets"]) != 1 or failed["datasets"][0].file.is_open:
                raise AssertionError("Earlier backed input was not closed after a later failure") from exc
        else:
            raise AssertionError("An absent backed file was accepted")

    return {
        "schema_version": 1,
        "platform": platform.system(),
        "python": platform.python_version(),
        "anndata": version("anndata"),
        "openpyxl": version("openpyxl"),
        "h5py": version("h5py"),
        "skill_sha256": digest(SKILL),
        "checks": [
            "matrix-values-and-axis-labels",
            "matrix-rejects-empty-duplicate-and-mismatched-ids",
            "excel-selected-and-missing-sheet",
            "hdf5-element-roundtrip-and-no-overwrite",
            "collection-feature-alignment-and-shared-metadata",
            "collection-reads-matrix-without-materializing-other-fields",
            "sparse-collection-feature-alignment",
            "collection-inputs-unchanged-and-handles-closed",
            "collection-closes-prior-input-after-failure",
        ],
        "synthetic_fixture": True,
        "full_collection_materialization_failures": materialization_failures,
        "agent_performance_tested": False,
    }


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description=__doc__)


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    print(json.dumps(run(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

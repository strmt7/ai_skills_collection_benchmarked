"""Compare native AnnData-to-SOMA ingestion across two pinned dependency sets."""

import argparse
import hashlib
import json
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
import tiledbsoma as soma
import tiledbsoma.io
from scipy import sparse


def dense(value):
    return value.toarray() if sparse.issparse(value) else np.asarray(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect", choices=("compatible", "known-error"), required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    versions = {name: version(name) for name in ("anndata", "tiledbsoma", "numpy", "pandas", "pyarrow")}
    expected_anndata = "0.12.19" if args.expect == "compatible" else "0.13.4"
    if versions["anndata"] != expected_anndata or versions["tiledbsoma"] != "2.3.0":
        raise RuntimeError(f"Unexpected test versions: {versions}")

    values = np.array([[0, 2, 3], [4, 0, 5]], dtype=np.float32)
    observations = []
    for layout in ("dense", "sparse"):
        for transport in ("anndata", "h5ad"):
            x = values.copy() if layout == "dense" else sparse.csr_matrix(values)
            data = ad.AnnData(
                X=x,
                obs=pd.DataFrame({"cell_type": ["a", "b"]}, index=["cellA", "cellB"]),
                var=pd.DataFrame({"feature": ["u", "v", "w"]}, index=["geneA", "geneB", "geneC"]),
            )
            data.layers["counts"] = sparse.csr_matrix(values * 2)
            obs_before, var_before = data.obs.copy(deep=True), data.var.copy(deep=True)
            none_layer = None in data.layers
            if none_layer != (args.expect == "known-error"):
                raise AssertionError("Unexpected AnnData layer-key behavior")

            with tempfile.TemporaryDirectory(prefix="soma-anndata-control-") as temp:
                temp = Path(temp)
                destination = temp / "experiment"
                source = temp / "input.h5ad"
                source_hash = None
                if transport == "h5ad":
                    data.write_h5ad(source)
                    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
                try:
                    if transport == "h5ad":
                        soma.io.from_h5ad(str(destination), str(source), "RNA", X_layer_name="raw")
                    else:
                        soma.io.from_anndata(str(destination), data, "RNA", X_layer_name="raw")
                except TypeError as error:
                    if args.expect != "known-error" or str(error) != "quote_from_bytes() expected bytes":
                        raise
                    if not destination.exists():
                        raise AssertionError("Expected partial destination was absent") from error
                    outcome = "known_type_error"
                else:
                    if args.expect != "compatible":
                        raise AssertionError("Known-incompatible pair unexpectedly ingested data")
                    with soma.Experiment.open(str(destination)) as experiment:
                        output = soma.io.to_anndata(
                            experiment, "RNA", X_layer_name="raw", extra_X_layer_names=["counts"]
                        )
                    np.testing.assert_array_equal(dense(output.X), values)
                    np.testing.assert_array_equal(dense(output.layers["counts"]), values * 2)
                    pd.testing.assert_frame_equal(output.obs, obs_before)
                    pd.testing.assert_frame_equal(output.var, var_before)
                    outcome = "round_trip_equal"

                np.testing.assert_array_equal(dense(data.X), values)
                np.testing.assert_array_equal(dense(data.layers["counts"]), values * 2)
                pd.testing.assert_frame_equal(data.obs, obs_before)
                pd.testing.assert_frame_equal(data.var, var_before)
                if source_hash is not None and source_hash != hashlib.sha256(source.read_bytes()).hexdigest():
                    raise AssertionError("H5AD input changed during ingestion")
                observations.append({"layout": layout, "transport": transport, "outcome": outcome})

    result = {
        "schema_version": 1,
        "python": platform.python_version(),
        "versions": versions,
        "expected_condition": args.expect,
        "observations": observations,
        "partial_destination_observed_on_failure": args.expect == "known-error",
        "input_data_preserved": True,
        "full_dataset_compatibility_tested": False,
        "agent_performance_tested": False,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

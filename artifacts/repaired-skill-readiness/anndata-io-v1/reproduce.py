"""Exercise the maintained AnnData I/O examples on synthetic fixtures."""

import gzip
import json
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / (
    "included/repaired/skills/by-category/science-research-data-analysis/latest-release-community/anndata-io/SKILL.md"
)


def main():
    text = SKILL.read_text(encoding="utf-8")
    examples = [block.split("```", 1)[0] for block in text.split("```python\n")[1:]]
    if len(examples) != 3:
        raise RuntimeError("Expected the three scoped I/O examples")
    with tempfile.TemporaryDirectory(prefix="anndata-io-overlay-") as temporary:
        root = Path(temporary)
        h5_path = root / "matrix.h5"
        with h5py.File(h5_path, "w") as out:
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
        mtx_dir = root / "matrix"
        mtx_dir.mkdir()
        files = {
            "matrix.mtx.gz": "%%MatrixMarket matrix coordinate integer general\n2 3 3\n1 1 2\n2 2 1\n1 3 3\n",
            "features.tsv.gz": "id1\tgene1\tGene Expression\nid2\tgene2\tGene Expression\n",
            "barcodes.tsv.gz": "cell1\ncell2\ncell3\n",
        }
        for name, content in files.items():
            with gzip.open(mtx_dir / name, "wt", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
        context = {"h5_path": h5_path, "mtx_dir": mtx_dir}
        exec(compile(examples[0], str(SKILL), "exec"), context)
        exec(compile(examples[1], str(SKILL), "exec"), context)
        for name in ("counts_h5", "counts_mtx"):
            actual = context[name]
            assert actual.shape == (3, 2)
            assert actual.obs_names.tolist() == ["cell1", "cell2", "cell3"]
            assert actual.var_names.tolist() == ["gene1", "gene2"]
            assert actual.var["gene_ids"].tolist() == ["id1", "id2"]
            np.testing.assert_array_equal(actual.X.toarray(), [[2, 0], [0, 1], [3, 0]])

        for kind, matrix in (
            ("dense", np.array([[1, 2], [3, 4], [5, 6]])),
            ("sparse", csr_matrix([[1, 2], [3, 4], [5, 6]])),
        ):
            input_path, output_path = root / f"{kind}-input.h5ad", root / f"{kind}-output.h5ad"
            data = ad.AnnData(matrix, obs=pd.DataFrame(index=["a", "b", "c"]))
            data.write_h5ad(input_path)
            before = input_path.read_bytes()
            context = {
                "input_path": input_path,
                "output_path": output_path,
                "obs_selection": [True, False, True],
                "sample_label": "sample-A",
            }
            exec(compile(examples[2], str(SKILL), "exec"), context)
            assert input_path.read_bytes() == before
            assert not context["backed"].file.is_open
            output = ad.io.read_h5ad(output_path)
            assert output.obs_names.tolist() == ["a", "c"]
            assert output.obs["sample"].tolist() == ["sample-A", "sample-A"]
            result = output.X.toarray() if hasattr(output.X, "toarray") else output.X
            np.testing.assert_array_equal(result, [[1, 2], [5, 6]])
            assert "sample" not in ad.io.read_h5ad(input_path).obs
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "platform": platform.system(),
                "anndata": version("anndata"),
                "scanpy": version("scanpy"),
                "numpy": version("numpy"),
                "h5py": version("h5py"),
                "scipy": version("scipy"),
                "synthetic_fixture": True,
                "checks": [
                    "10x-h5",
                    "10x-mtx",
                    "dense-backed-subset",
                    "sparse-backed-subset",
                    "input-unchanged",
                    "reopened-output",
                ],
                "agent_performance_tested": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

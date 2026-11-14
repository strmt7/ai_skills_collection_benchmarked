from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from validate_native_qualification_index import INDEX, validate


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def qualified_history(tmp_path: Path) -> Path:
    (tmp_path / "module.py").write_bytes(b"new qualified implementation")
    (tmp_path / "stable.py").write_bytes(b"unchanged implementation")
    old = {
        "module.py": hashlib.sha256(b"old qualified implementation").hexdigest(),
        "stable.py": digest(tmp_path / "stable.py"),
    }
    current = {"module.py": digest(tmp_path / "module.py")}
    references = []
    for name, sources in (("old", old), ("current", current)):
        folder = tmp_path / name
        folder.mkdir()
        (folder / "native.txt").write_bytes(b"retained native control evidence")
        path = folder / "review.json"
        write(path, {"artifacts": {"native.txt": digest(folder / "native.txt")}, "source_sha256": sources})
        references.append({"path": path.relative_to(tmp_path).as_posix(), "sha256": digest(path)})
    write(
        tmp_path / INDEX,
        {
            "schema_version": 2,
            "components": [{"id": "runtime", "review": references[1], "sources": ["module.py"]}],
            "historical_reviews": [{"review": references[0], "superseded_sources": ["module.py"]}],
        },
    )
    return tmp_path


def test_explicit_fresh_source_proof_preserves_historical_review_bytes(qualified_history: Path) -> None:
    before = (qualified_history / "old/review.json").read_bytes()
    assert validate(qualified_history)["ok"]
    assert (qualified_history / "old/review.json").read_bytes() == before


@pytest.mark.parametrize(
    "change",
    [
        "current-source",
        "stable-source",
        "old-evidence",
        "current-evidence",
        "review",
        "missing-supersession",
        "extra-supersession",
        "duplicate-review",
        "duplicate-source",
        "duplicate-current-review",
        "conflicting-current-review",
    ],
)
def test_unproven_changes_and_inconsistent_supersessions_fail(qualified_history: Path, change: str) -> None:
    index_path = qualified_history / INDEX
    index = json.loads(index_path.read_bytes())
    if change in {"current-source", "stable-source"}:
        (qualified_history / ("module.py" if change == "current-source" else "stable.py")).write_bytes(
            b"unqualified change"
        )
    elif change in {"old-evidence", "current-evidence"}:
        (qualified_history / ("old" if change == "old-evidence" else "current") / "native.txt").write_bytes(
            b"changed evidence"
        )
    elif change == "review":
        (qualified_history / "old/review.json").write_bytes(b"{}")
    elif change == "missing-supersession":
        index["historical_reviews"][0]["superseded_sources"] = []
    elif change == "extra-supersession":
        index["historical_reviews"][0]["superseded_sources"].append("stable.py")
    elif change == "duplicate-review":
        index["historical_reviews"].append(index["historical_reviews"][0])
    elif change == "duplicate-current-review":
        index["components"].append(index["components"][0])
    elif change == "conflicting-current-review":
        path = qualified_history / "conflict/review.json"
        write(path, {"artifacts": {}, "source_sha256": {"module.py": "a" * 64}})
        index["components"].append(
            {
                "id": "conflict",
                "review": {"path": "conflict/review.json", "sha256": digest(path)},
                "sources": ["module.py"],
            }
        )
    else:
        index["historical_reviews"][0]["superseded_sources"].append("module.py")
    write(index_path, index)
    result = validate(qualified_history)
    assert not result["ok"] and result["errors"]


def test_components_can_reuse_unchanged_scopes_from_an_older_review(qualified_history: Path) -> None:
    path = qualified_history / INDEX
    index = json.loads(path.read_bytes())
    index["components"].append(
        {"id": "stable-component", "review": index["historical_reviews"][0]["review"], "sources": ["stable.py"]}
    )
    write(path, index)
    assert validate(qualified_history)["ok"]

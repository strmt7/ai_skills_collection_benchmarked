"""Independent known-good/bad structure controls for TF-IDF grading."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import compare_tfidf_outputs as grader
import pytest


def expected_output() -> dict[str, Any]:
    return {
        "index": {
            "num_documents": 2,
            "vocabulary": ["alpha", "beta"],
            "document_frequencies": {"alpha": 2, "beta": 1},
            "idf": {"alpha": 1.0, "beta": 1.6931471805599454},
            "inverted_index": {"alpha": [[7, 1.0], [42, 0.5]], "beta": [[42, 0.8465735902799727]]},
            "doc_vectors": {"7": {"alpha": 1.0}, "42": {"alpha": 0.5, "beta": 0.8465735902799727}},
            "doc_norms": {"7": 1.0, "42": 0.9835132204727984},
        },
        "search_results": [[{"doc_id": 7, "score": 1.0, "title": "Alpha"}], []],
    }


def test_complete_correct_output_passes() -> None:
    expected = expected_output()
    assert grader.compare(expected, copy.deepcopy(expected)) == []


def test_empty_query_results_fail_without_zip_acceptance() -> None:
    actual = expected_output()
    actual["search_results"] = []
    assert grader.compare(expected_output(), actual) == ["$.search_results: list length differs (2 expected, 0 actual)"]


@pytest.mark.parametrize("field", sorted(grader.REQUIRED_INDEX_FIELDS))
def test_missing_index_fields_fail(field: str) -> None:
    actual = expected_output()
    del actual["index"][field]
    assert grader.compare(expected_output(), actual)


def test_changed_vectors_postings_and_norms_fail() -> None:
    expected = expected_output()
    actual = copy.deepcopy(expected)
    actual["index"]["doc_vectors"]["7"]["alpha"] = 0.0
    actual["index"]["inverted_index"]["alpha"].reverse()
    actual["index"]["doc_norms"]["42"] = 1.5
    errors = grader.compare(expected, actual)
    assert any("doc_vectors" in error for error in errors)
    assert any("inverted_index" in error for error in errors)
    assert any("doc_norms" in error for error in errors)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf"), True, "1.0", 10**400])
def test_nonfinite_or_wrong_score_types_fail(value: Any) -> None:
    actual = expected_output()
    actual["search_results"][0][0]["score"] = value
    assert grader.compare(expected_output(), actual)


def test_float_roundoff_passes_without_relaxing_ids() -> None:
    actual = expected_output()
    actual["index"]["idf"]["beta"] += 1e-14
    assert grader.compare(expected_output(), actual) == []
    actual["search_results"][0][0]["doc_id"] = 7.0
    assert grader.compare(expected_output(), actual)


def test_missing_or_additional_queries_fail() -> None:
    actual = expected_output()
    actual["search_results"].append([])
    assert grader.compare(expected_output(), actual)
    actual = expected_output()
    actual["search_results"][0] = []
    assert grader.compare(expected_output(), actual)


def test_incomplete_reference_fails_before_candidate_scoring() -> None:
    with pytest.raises(ValueError, match="trusted reference"):
        grader.compare({"index": {}, "search_results": []}, {})


def test_command_line_wrong_type_is_failure(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    expected = tmp_path / "expected.json"
    actual = tmp_path / "actual.json"
    expected.write_text(json.dumps(expected_output()), encoding="utf-8")
    actual.write_text("[]", encoding="utf-8")
    assert grader.main(["--expected", str(expected), "--actual", str(actual), "--json"]) == 1
    assert '"performance_scored": false' in capsys.readouterr().out


@pytest.mark.parametrize("raw", ['{"key":1,"key":2}', '{"score":NaN}', '{"score":Infinity}'])
def test_file_protocol_rejects_ambiguous_json(tmp_path: Path, raw: str) -> None:
    path = tmp_path / "response.json"
    path.write_text(raw, encoding="utf-8")
    with pytest.raises(ValueError):
        grader.load_bounded(path)

"""Compare complete TF-IDF structures and query outputs outside candidate code.

Expected data comes from a reviewed reference and independent fixture inputs,
never from skill text. This comparator does not score performance.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

REQUIRED_INDEX_FIELDS = {
    "num_documents",
    "vocabulary",
    "document_frequencies",
    "idf",
    "inverted_index",
    "doc_vectors",
    "doc_norms",
}


def compare(expected: dict[str, Any], actual: Any) -> list[str]:
    """Check full cardinality, keys, ordering, types and finite numeric values."""
    if set(expected) != {"index", "search_results"} or not isinstance(expected["index"], dict):
        raise ValueError("invalid trusted reference envelope")
    if set(expected["index"]) != REQUIRED_INDEX_FIELDS or not isinstance(expected["search_results"], list):
        raise ValueError("incomplete trusted reference structure")
    errors: list[str] = []

    def visit(left: Any, right: Any, path: str, depth: int) -> None:
        if len(errors) >= 100:
            return
        if depth > 32:
            errors.append(f"{path}: nesting limit exceeded")
        elif isinstance(left, dict):
            if not isinstance(right, dict):
                errors.append(f"{path}: expected object")
                return
            if set(left) != set(right):
                errors.append(f"{path}: object keys differ")
            for key, value in left.items():
                if key in right:
                    visit(value, right[key], f"{path}.{key}", depth + 1)
        elif isinstance(left, list):
            if not isinstance(right, list):
                errors.append(f"{path}: expected list")
                return
            if len(left) != len(right):
                errors.append(f"{path}: list length differs ({len(left)} expected, {len(right)} actual)")
            for index in range(min(len(left), len(right))):
                visit(left[index], right[index], f"{path}[{index}]", depth + 1)
        elif type(left) is float:
            try:
                matches = (
                    type(right) in {int, float}
                    and math.isfinite(right)
                    and math.isclose(left, right, rel_tol=1e-8, abs_tol=1e-10)
                )
            except OverflowError:
                matches = False
            if not matches:
                errors.append(f"{path}: finite numeric value differs")
        elif type(left) is not type(right) or left != right:
            errors.append(f"{path}: value or type differs")

    visit(expected, actual, "$", 0)
    return errors


def load_bounded(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate comparison key")
            result[key] = value
        return result

    def constant(value: str) -> Any:
        raise ValueError(f"nonfinite comparison number: {value}")

    with path.open("rb") as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("comparison input exceeds 16 MiB")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected", type=Path, required=True)
    parser.add_argument("--actual", type=Path, required=True)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        expected = load_bounded(args.expected)
        if not isinstance(expected, dict):
            raise ValueError("trusted reference must be an object")
        errors = compare(expected, load_bounded(args.actual))
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        errors = [str(exc)]
    report = {"passed": not errors, "errors": errors, "performance_scored": False}
    print(json.dumps(report, indent=2) if args.json else f"{len(errors)} differences")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

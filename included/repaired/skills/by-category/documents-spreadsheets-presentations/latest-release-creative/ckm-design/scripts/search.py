"""Search bundled design data with explicit errors and bounded query expansion."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, NoReturn

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
DOMAINS = {
    ("logo", "style"): ("styles.csv", ("Style Name", "Category", "Keywords", "Best For")),
    ("logo", "color"): ("colors.csv", ("Palette Name", "Category", "Keywords", "Psychology", "Best For")),
    ("logo", "industry"): ("industries.csv", ("Industry", "Keywords", "Recommended Styles", "Mood")),
    ("cip", "deliverable"): (
        "deliverables.csv",
        ("Deliverable", "Category", "Keywords", "Description", "Mockup Context"),
    ),
    ("cip", "style"): ("styles.csv", ("Style Name", "Category", "Keywords", "Description", "Mood")),
    ("cip", "industry"): ("industries.csv", ("Industry", "Keywords", "CIP Style", "Mood")),
    ("cip", "mockup"): ("mockup-contexts.csv", ("Context Name", "Category", "Keywords", "Scene Description")),
}


def tokens(value: str) -> list[str]:
    """Keep Unicode letters and digits, including meaningful short terms."""
    return [
        token
        for token in re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", value).casefold())
        if len(token) > 1 or token.isdigit()
    ]


def stem(token: str, engine: Any) -> str:
    """Apply English stemming only to ASCII words longer than two characters."""
    return engine.stemWord(token) if token.isascii() and token.isalpha() and len(token) > 2 else token


def load_rows(path: Path, columns: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames or []
        if not headers or len(headers) != len(set(headers)) or not set(columns).issubset(headers):
            raise ValueError("dataset headers do not match the selected domain")
        rows = list(reader)
    if not rows:
        raise ValueError("dataset contains no records")
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError("dataset contains malformed records")
    return rows


def load_stemmer() -> Any:
    import importlib
    import importlib.metadata

    try:
        version = importlib.metadata.version("snowballstemmer")
        if version != "3.1.1":
            raise ValueError(f"snowballstemmer 3.1.1 is required; found {version}")
        return importlib.import_module("snowballstemmer.english_stemmer").EnglishStemmer()
    except (importlib.metadata.PackageNotFoundError, ModuleNotFoundError) as exc:
        raise ValueError("Install the pinned snowballstemmer dependency from requirements.txt") from exc


def rank_once(
    rows: list[dict[str, str]], columns: tuple[str, ...], query_tokens: list[str], limit: int, expand: bool
) -> tuple[list[dict[str, Any]], bool]:
    docs = [Counter(tokens(" ".join(row[column] for column in columns))) for row in rows]
    lengths = [sum(doc.values()) for doc in docs]
    average = sum(lengths) / len(lengths)
    if average == 0:
        raise ValueError("dataset contains no searchable content")
    exact_frequency = Counter(term for doc in docs for term in doc)
    engine = load_stemmer() if expand else None
    stems: list[Counter[str]] = [Counter() for _ in docs]
    if engine is not None:
        for index, doc in enumerate(docs):
            for word, count in doc.items():
                stems[index][stem(word, engine)] += count
    stem_frequency = Counter(term for doc in stems for term in doc)
    scored = []
    for index, doc in enumerate(docs):
        score = 0.0
        used_stemming = False
        matched_terms = 0
        for token in query_tokens:
            count = doc.get(token, 0)
            frequency = exact_frequency[token]
            weight = 1.0
            if not count and engine is not None:
                root = stem(token, engine)
                count = stems[index].get(root, 0)
                frequency = stem_frequency[root]
                weight = 0.65
                used_stemming = used_stemming or bool(count)
            if count:
                matched_terms += 1
                inverse = math.log1p((len(docs) - frequency + 0.5) / (frequency + 0.5))
                denominator = count + 1.5 * (1 - 0.75 + 0.75 * lengths[index] / average)
                score += weight * inverse * (count * 2.5) / denominator
        if score > 0:
            scored.append((score, index, used_stemming, matched_terms))
    scored.sort(key=lambda item: (-item[0], item[1]))
    complete = any(matched == len(query_tokens) for _, _, _, matched in scored)
    return (
        [
            {"fields": rows[index], "used_stemming": used, "matched_terms": matched, "query_terms": len(query_tokens)}
            for _, index, used, matched in scored[:limit]
        ],
        complete,
    )


def rank(
    rows: list[dict[str, str]], columns: tuple[str, ...], query: str, limit: int, mode: str
) -> tuple[list[dict[str, Any]], str]:
    query_tokens = list(dict.fromkeys(tokens(query)))
    if not query_tokens:
        raise ValueError("query must contain a searchable term")
    if limit < 1 or limit > 50:
        raise ValueError("max-results must be between 1 and 50")
    if mode not in {"auto", "exact", "expanded"}:
        raise ValueError("unsupported matching mode")
    if mode != "expanded":
        exact, complete = rank_once(rows, columns, query_tokens, limit, False)
        if mode == "exact" or complete:
            return exact, "exact"
    expanded, _ = rank_once(rows, columns, query_tokens, limit, True)
    return expanded, "expanded"


def search(data_dir: Path, collection: str, domain: str, query: str, limit: int, mode: str) -> dict[str, Any]:
    try:
        filename, columns = DOMAINS[collection, domain]
    except KeyError as exc:
        raise ValueError("unsupported collection and domain combination") from exc
    rows = load_rows(data_dir / collection / filename, columns)
    results, selected = rank(rows, columns, query, limit, mode)
    return {
        "ok": True,
        "collection": collection,
        "domain": domain,
        "query": query,
        "matching": selected,
        "count": len(results),
        "results": results,
    }


class JsonArgumentParser(argparse.ArgumentParser):
    """Keep command-line errors in the same machine-readable envelope."""

    def error(self, message: str) -> NoReturn:
        print(json.dumps({"ok": False, "error": message}))
        self.exit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_ROOT)
    parser.add_argument("--collection", required=True, choices=("logo", "cip"))
    parser.add_argument("--domain", required=True)
    parser.add_argument("--max-results", type=int, default=3)
    parser.add_argument("--match", choices=("auto", "exact", "expanded"), default="auto")
    parser.add_argument("query")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = search(args.data_dir, args.collection, args.domain, args.query, args.max_results, args.match)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

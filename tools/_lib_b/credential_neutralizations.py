"""Qualified credential examples, identified by whole-file bytes and span hashes."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def policies() -> dict:
    path = ROOT / "data/credential_neutralizations.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["schema_version"] != 1:
        raise ValueError("unsupported credential neutralization registry")
    indexed: dict[str, dict[str, Any]] = {}
    for item in data["files"]:
        digest = item["input_sha256"]
        bound = {"spans": item["spans"], "output_sha256": item["output_sha256"]}
        if digest in indexed and indexed[digest] != bound:
            raise ValueError("conflicting credential neutralization source bytes")
        indexed[digest] = bound
    return indexed


def neutralize(text: str, rules: dict | None = None) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    record = (policies() if rules is None else rules).get(digest)
    if record is None:
        return text
    spans = record["spans"]
    previous = 0
    parts: list[str] = []
    for item in spans:
        start, end = item["start"], item["end"]
        replacement = item["replacement"]
        if (
            type(start) is not int
            or type(end) is not int
            or not previous <= start < end <= len(text)
            or not isinstance(replacement, str)
            or not replacement
            or "\n" in replacement
            or "\r" in replacement
            or hashlib.sha256(text[start:end].encode("utf-8")).hexdigest() != item["value_sha256"]
        ):
            raise ValueError("invalid or changed qualified credential span")
        parts.extend((text[previous:start], replacement))
        previous = end
    parts.append(text[previous:])
    output = "".join(parts)
    if hashlib.sha256(output.encode("utf-8")).hexdigest() != record["output_sha256"]:
        raise ValueError("qualified credential output hash mismatch")
    return output

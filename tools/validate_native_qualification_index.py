"""Bind current native-source qualifications without rewriting historical reviews."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from _catalog_publication import checked_path
from _trial_transcript import strict_json

ROOT = Path(__file__).resolve().parents[1]
INDEX = "data/native_qualification_index.json"


def validate(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []

    def read(path: Path) -> dict[str, Any]:
        raw = path.read_bytes()
        if len(raw) > 16 * 1024**2:
            raise ValueError("Qualification document exceeds its byte budget")
        value = strict_json(raw.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Qualification document must be an object")
        return value

    def check_digest(path: Path, digest: Any) -> None:
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid qualification digest: " + path.name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append("Qualification bytes differ: " + str(path.relative_to(root)))

    def review(reference: Any) -> tuple[Path, dict[str, Any]]:
        if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
            raise ValueError("A review requires its exact path and digest")
        path = checked_path(root, reference["path"])
        check_digest(path, reference["sha256"])
        value = read(path)
        if not isinstance(value.get("artifacts"), dict) or not isinstance(value.get("source_sha256"), dict):
            raise ValueError("A review requires artifact and source inventories")
        for name, digest in value["artifacts"].items():
            check_digest(checked_path(path.parent, name), digest)
        return path, value

    try:
        index = read(checked_path(root, INDEX))
        if (
            set(index) != {"schema_version", "components", "historical_reviews"}
            or type(index["schema_version"]) is not int
            or index["schema_version"] != 2
            or not isinstance(index["components"], list)
            or not index["components"]
            or not isinstance(index["historical_reviews"], list)
        ):
            raise ValueError("Expected a versioned current/historical qualification index")
        sources = {}
        component_ids = set()
        for component in index["components"]:
            if (
                not isinstance(component, dict)
                or set(component) != {"id", "review", "sources"}
                or not isinstance(component["id"], str)
                or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", component["id"])
                or component["id"] in component_ids
            ):
                raise ValueError("Current components require distinct IDs, review references and source scopes")
            component_ids.add(component["id"])
            _, current = review(component["review"])
            selected = component["sources"]
            if not isinstance(selected, list) or not selected or any(not isinstance(name, str) for name in selected):
                raise ValueError("Each component must select qualified source paths")
            for name in selected:
                if name in sources or name not in current["source_sha256"]:
                    raise ValueError("Source ownership overlaps or lacks qualification: " + name)
                sources[name] = current["source_sha256"][name]
        for name, digest in sources.items():
            check_digest(checked_path(root, name), digest)
        seen = set()
        for entry in index["historical_reviews"]:
            if not isinstance(entry, dict) or set(entry) != {"review", "superseded_sources"}:
                raise ValueError("Historical entries must declare their source supersessions")
            path, historical = review(entry["review"])
            if path in seen:
                raise ValueError("Historical review is repeated")
            seen.add(path)
            declared = entry["superseded_sources"]
            if not isinstance(declared, list) or any(not isinstance(name, str) for name in declared):
                raise ValueError("Superseded sources must be distinct paths")
            if len(set(declared)) != len(declared):
                raise ValueError("Superseded source is repeated")
            previous = historical["source_sha256"]
            changed = {name for name in previous.keys() & sources.keys() if previous[name] != sources[name]}
            if set(declared) != changed:
                errors.append("Source supersessions differ: " + str(path.relative_to(root)))
            for name, digest in previous.items():
                check_digest(checked_path(root, name), sources[name] if name in changed else digest)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError) as error:
        errors.append(str(error))
    return {"ok": not errors, "errors": errors, "scope": "Source and artifact binding; not proof of model efficacy"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Validate without modifying any record")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate()
    print(json.dumps(result, indent=2) if args.json else ("OK" if result["ok"] else "\n".join(result["errors"])))
    return int(not result["ok"])


if __name__ == "__main__":
    raise SystemExit(main())

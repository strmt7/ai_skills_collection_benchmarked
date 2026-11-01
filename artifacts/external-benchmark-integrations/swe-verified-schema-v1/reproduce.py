"""Check SWE-bench Verified API rows with an installed SWE-bench test-spec builder.

This reads previously downloaded dataset-server responses; it does not run
benchmark scripts, build images, submit patches, or evaluate an agent.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
from collections import Counter
from pathlib import Path
from typing import Any

EXPECTED_ROWS = 500
PAGE_SIZE = 100


def load_pages(directory: Path, label: str) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Read all untruncated response pages, rejecting gaps or duplicate IDs."""
    rows: list[dict[str, Any]] = []
    hashes = {}
    identifiers = set()
    for offset in range(0, EXPECTED_ROWS, PAGE_SIZE):
        raw = (directory / f"{label}-{offset}.json").read_bytes()
        page = json.loads(raw)
        if page.get("num_rows_total") != EXPECTED_ROWS or page.get("partial") is not False:
            raise ValueError(f"Incomplete {label} page at {offset}")
        page_rows = page.get("rows")
        if not isinstance(page_rows, list) or len(page_rows) != PAGE_SIZE:
            raise ValueError(f"Unexpected {label} page length at {offset}")
        hashes[str(offset)] = hashlib.sha256(raw).hexdigest()
        for position, item in enumerate(page_rows, offset):
            if item.get("row_idx") != position or item.get("truncated_cells") != []:
                raise ValueError(f"Missing, reordered or truncated {label} row at {position}")
            row = item["row"]
            identity = row["instance_id"]
            if not isinstance(identity, str) or not identity or identity in identifiers:
                raise ValueError(f"Invalid or duplicate {label} instance ID at {position}")
            identifiers.add(identity)
            rows.append(row)
    return rows, hashes


def observe(directory: Path) -> dict[str, Any]:
    version = importlib.metadata.version("swebench")
    if version != "5.0.2":
        raise ValueError(f"Expected SWE-bench 5.0.2; found {version}")
    # Keep the optional harness import offline and prevent implicit .env loading.
    os.environ["PYTHON_DOTENV_DISABLED"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    from swebench.harness.utils import make_test_spec

    observations: dict[str, Any] = {}
    identities: dict[str, dict[str, tuple[str, str]]] = {}
    for label in ("legacy", "current"):
        rows, hashes = load_pages(directory, label)
        counts: Counter[str] = Counter()
        commits = {}
        for row in rows:
            identity = row["instance_id"]
            base, repo = row["base_commit"], row["repo"]
            if (
                not isinstance(base, str)
                or len(base) != 40
                or any(char not in "0123456789abcdef" for char in base)
                or not isinstance(repo, str)
                or not repo
            ):
                raise ValueError(f"Invalid source identity for {identity}")
            commits[identity] = (repo, base)
            try:
                spec = make_test_spec(row)
                if spec.instance_id != identity:
                    raise ValueError("test-spec instance does not match source")
                counts["accepted"] += 1
            except Exception as exc:
                counts[f"{type(exc).__name__}: {exc}"] += 1
        identities[label] = commits
        observations[label] = {"rows": len(rows), "counts": dict(sorted(counts.items())), "page_sha256": hashes}
    same = identities["legacy"] == identities["current"]
    matches = (
        same
        and observations["legacy"]["counts"] == {"KeyError: 'image'": EXPECTED_ROWS}
        and observations["current"]["counts"] == {"accepted": EXPECTED_ROWS}
    )
    return {
        "swebench_version": version,
        "python_version": platform.python_version(),
        "cases": observations,
        "same_instance_ids_repositories_and_base_commits": same,
        "matches_recorded_observation": matches,
        "executes_evaluation_scripts": False,
        "agent_efficacy_scored": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pages", type=Path, required=True, help="Directory containing the ten captured API pages")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = observe(args.pages)
    except (ImportError, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1
    print(json.dumps({"ok": result["matches_recorded_observation"], **result}, indent=2))
    return 0 if result["matches_recorded_observation"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

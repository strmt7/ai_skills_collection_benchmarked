#!/usr/bin/env python3
"""Report exact local Markdown link failures from runtime artifacts.

This tool reads every independent-runtime benchmark ``artifact.json`` and its
associated ``result.json`` to find the ``local_markdown_links_resolve`` check
evidence. Each unresolved target is grouped with the skill, batch and artifact
path that recorded it so human reviewers can repair mirrored SKILL.md files in
a targeted way.

Public helpers (used by tests and other tools):

- ``extract_local_links(text)`` -- returns the list of inline Markdown link
  targets in a text buffer, excluding images and autolinks. Anchor fragments
  and query strings are stripped so a caller can compare against real file
  paths.
- ``iter_runtime_results()`` -- yields ``(artifact_path, artifact, result)``
  tuples for every independent-benchmark artifact on disk.
- ``render_report()`` -- returns the exact Markdown body that ``main()``
  writes to ``docs/local-markdown-link-failures.md``.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "local-markdown-link-failures.md"

# Inline Markdown link pattern. We deliberately stay with a pragmatic regex
# instead of pulling in markdown-it-py or mistune as a dependency: the
# documentation files in this repo are CommonMark-compatible and never embed
# links inside code spans, so the simpler approach is both faster and
# sufficient for the contract tested elsewhere.
#
# ``(?<!!)`` excludes image syntax (``![alt](url)``) so cover-image URLs are
# not reported.
INLINE_LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def table_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


# ---------------------------------------------------------------------------
# Link extraction helpers (reusable)
# ---------------------------------------------------------------------------


def extract_local_links(text: str) -> list[str]:
    """Return Markdown inline link targets that look local (not URLs).

    Fragments (``#anchor``) and query strings (``?x=y``) are stripped to leave
    just the path portion, matching the behaviour of the existing
    documentation-contract test in ``tests/test_documentation_contracts.py``.
    """
    links: list[str] = []
    for raw_target in INLINE_LINK_PATTERN.findall(text):
        target = raw_target.strip().split("#", 1)[0].split("?", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        links.append(target)
    return links


# ---------------------------------------------------------------------------
# Artifact iteration
# ---------------------------------------------------------------------------


def iter_runtime_results() -> list[tuple[Path, dict[str, Any], dict[str, Any]]]:
    rows = []
    for artifact_path in sorted((ROOT / "artifacts" / "benchmark-runs").rglob("artifact.json")):
        artifact = load_json(artifact_path)
        if artifact.get("artifact_kind") != "independent_benchmark":
            continue
        result_path = artifact_path.parent / artifact["outputs"]["path"]
        rows.append((artifact_path, artifact, load_json(result_path)))
    return rows


def local_link_failures(result: dict[str, Any]) -> list[str]:
    for check in result.get("outputs", {}).get("checks", []):
        if check.get("name") == "local_markdown_links_resolve" and check.get("passed") is False:
            return [str(item) for item in check.get("evidence", [])]
    return []


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def render_report() -> str:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    runtime_results = iter_runtime_results()
    for artifact_path, artifact, result in runtime_results:
        for target in local_link_failures(result):
            groups[target].append({
                "skill_id": artifact["skill_id"],
                "batch_name": artifact["runner"]["batch_name"],
                "artifact_path": artifact_path.relative_to(ROOT).as_posix(),
            })

    failing_artifacts = {
        item["artifact_path"]
        for entries in groups.values()
        for item in entries
    }

    lines = [
        "# Local Markdown Link Failures",
        "",
        "This report groups exact unresolved local Markdown targets recorded by the `local_markdown_links_resolve` check in independent runtime benchmark artifacts. It is generated from artifact `result.json` files and does not edit mirrored skills.",
        "",
        "## Summary",
        "",
        f"- Runtime artifacts scanned: `{len(runtime_results)}`",
        f"- Runtime artifacts with local-link failures: `{len(failing_artifacts)}`",
        f"- Unique missing targets: `{len(groups)}`",
        "",
        "## Missing Targets",
        "",
        "| Missing target | Occurrences | Batches | Skills | Artifacts |",
        "|---|---:|---|---|---|",
    ]

    for target, entries in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0].lower())):
        batches = ", ".join(sorted({entry["batch_name"] for entry in entries}))
        skills = "<br>".join(sorted({f"`{entry['skill_id']}`" for entry in entries}))
        artifacts = "<br>".join(
            f"`{entry['artifact_path']}`"
            for entry in sorted(entries, key=lambda entry: entry["artifact_path"])
        )
        lines.append(
            f"| `{table_cell(target)}` | {len(entries)} | {table_cell(batches)} | {skills} | {artifacts} |"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    REPORT_PATH.write_text(render_report(), encoding="utf-8")
    print(f"Wrote {REPORT_PATH.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()

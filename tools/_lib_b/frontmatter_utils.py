"""YAML frontmatter parser with line-aware error reporting.

This delegates to PyYAML for parsing but wraps ``yaml.YAMLError`` so callers
get a ``FrontmatterError`` with line/column info and a friendly message,
regardless of which YAML error variant was raised.

We avoid pulling in ``python-frontmatter`` as a dependency: the contract of
Batch B tools is a single fenced ``---`` block at the very top of a Markdown
file, matching the existing ``build_catalog.parse_frontmatter`` behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:  # pragma: no cover - exercised implicitly by any YAML parse
    import yaml
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "PyYAML is required for frontmatter parsing; install 'PyYAML'."
    ) from exc


@dataclass(frozen=True)
class FrontmatterError(ValueError):
    """Raised when a Markdown file's YAML frontmatter cannot be parsed."""

    message: str
    line: int | None
    column: int | None

    def __str__(self) -> str:  # pragma: no cover - cosmetic
        loc = ""
        if self.line is not None:
            loc = f" (line {self.line}"
            if self.column is not None:
                loc += f", col {self.column}"
            loc += ")"
        return f"frontmatter parse error{loc}: {self.message}"


def parse(text: str) -> tuple[dict[str, Any], str]:
    """Split off a ``---``-delimited YAML block at the top of *text*.

    Returns (metadata, body). If there is no frontmatter, returns ({}, text).
    Raises ``FrontmatterError`` with line/column info on malformed YAML.
    """
    if not text.startswith("---\n"):
        return {}, text
    try:
        end = text.index("\n---", 4)
    except ValueError:
        # Malformed: opening fence but no closing fence.
        return {}, text
    raw = text[4:end]
    try:
        meta = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        line = None
        col = None
        mark = getattr(exc, "problem_mark", None) or getattr(exc, "context_mark", None)
        if mark is not None:
            # PyYAML marks are 0-indexed; humans expect 1-indexed.
            # The frontmatter starts at line 2 of the source (after '---\n').
            line = mark.line + 2
            col = mark.column + 1
        raise FrontmatterError(message=str(exc), line=line, column=col) from exc
    if not isinstance(meta, dict):
        raise FrontmatterError(
            message=f"frontmatter must be a mapping, got {type(meta).__name__}",
            line=2,
            column=1,
        )
    body_start = end + len("\n---")
    if text[body_start : body_start + 1] == "\n":
        body_start += 1
    return meta, text[body_start:]

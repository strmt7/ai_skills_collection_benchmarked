"""Shared helpers for Batch B generators (runtime/repaired/source-proof).

This namespace is intentionally distinct from any Batch A shared library to
avoid cross-branch merge conflicts. It may be consolidated later.

Modules:
    io_utils      - atomic JSON/text writers with deterministic formatting
    hashing       - SHA-256 helpers for files, text, and sorted trees
    determinism   - stable timestamp and catalog-commit resolvers
    logging_utils - structured stdlib logging configuration for CLI tools
    frontmatter_utils - YAML frontmatter parser with line-aware errors
"""

from . import determinism, frontmatter_utils, hashing, io_utils, logging_utils

__all__ = [
    "determinism",
    "frontmatter_utils",
    "hashing",
    "io_utils",
    "logging_utils",
]

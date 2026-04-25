"""Shared pytest setup.

Inserts ``<repo>/tools`` onto ``sys.path`` so test modules can import the
top-level tool scripts (e.g. ``import build_catalog``) without each module
having to maintain its own ``sys.path`` shim. Centralising this also keeps
ruff's import sorter happy: tests can declare normal third-party-style
imports, and the ordering invariant ``sys.path``-insert-before-import is
enforced once, at collection time.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

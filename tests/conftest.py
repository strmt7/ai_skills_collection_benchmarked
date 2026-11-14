"""Shared pytest setup.

Inserts ``<repo>/tools`` onto ``sys.path`` so test modules can import the
top-level tool scripts (e.g. ``import build_catalog``) without each module
having to maintain its own ``sys.path`` shim. Centralising this also keeps
ruff's import sorter happy: tests can declare normal third-party-style
imports, and the ordering invariant ``sys.path``-insert-before-import is
enforced once, at collection time.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path, PureWindowsPath

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))


@pytest.fixture
def native_catalog_pin():
    """Build public pin metadata for pure command/evidence tests, without host I/O."""
    from _trial_catalog import NativeCatalog

    def build(cli):
        windows = PureWindowsPath(str(cli))
        name = windows.name if windows.is_absolute() else cli.name
        commit = "c" * 40
        return NativeCatalog(
            json.dumps(
                {
                    "executable": name,
                    "source_commit": commit,
                    "files": {name: {"bytes": 1, "sha256": "0" * 64}},
                    "resources": {
                        "models.json": {
                            "bytes": 1,
                            "sha256": "0" * 64,
                            "url": f"https://raw.githubusercontent.com/openai/codex/{commit}/codex-rs/models-manager/models.json",
                        }
                    },
                }
            )
        )

    return build

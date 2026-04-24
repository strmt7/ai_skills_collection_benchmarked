"""Lightweight structured logging for Batch B CLI tools.

We prefer stdlib `logging` configured once at the CLI entry point, per the
guidance in docs.python.org's "Logging HOWTO" and Real Python's logging best
practices. No third-party dependency is pulled in.
"""

from __future__ import annotations

import logging
import os
import sys

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_cli_logging(tool_name: str, *, verbose: bool = False) -> logging.Logger:
    """Configure root logging for a CLI tool and return a named logger.

    Level resolution:
        - verbose=True           -> DEBUG
        - LOG_LEVEL env var      -> that level (case-insensitive)
        - default                -> INFO
    """
    level = logging.INFO
    if verbose:
        level = logging.DEBUG
    else:
        env_level = os.environ.get("LOG_LEVEL")
        if env_level:
            level = logging.getLevelName(env_level.upper())
            if not isinstance(level, int):
                level = logging.INFO

    root = logging.getLogger()
    # Only install a handler if none is configured yet; tests install their own.
    if not root.handlers:
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT))
        root.addHandler(handler)
    root.setLevel(level)
    return logging.getLogger(tool_name)

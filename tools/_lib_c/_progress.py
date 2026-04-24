"""Rich-free progress helpers.

Batch-C tools run in CI where progress bars are either invisible or actively
corrupt machine-consumer output. These helpers emit progress to **stderr**
only so JSON/markdown on stdout remains clean.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Iterable, Iterator, TypeVar

T = TypeVar("T")


def _is_tty() -> bool:
    return sys.stderr.isatty() and os.environ.get("CI") != "true"


def log_progress(message: str) -> None:
    """Write a single progress line to stderr."""

    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def progress_iter(
    items: Iterable[T],
    *,
    label: str,
    total: int | None = None,
    step: int = 25,
) -> Iterator[T]:
    """Yield items from ``items`` while emitting paced progress on stderr.

    The implementation is deliberately stdlib-only and TTY-aware: in CI we
    emit one line every ``step`` items (defaulting to 25) to avoid log spam,
    and in interactive TTYs we refresh in place.
    """

    items = list(items) if total is None else items
    if total is None:
        total = len(items)  # type: ignore[arg-type]
    tty = _is_tty()
    start = time.monotonic()
    for index, item in enumerate(items, start=1):
        yield item
        if total and (index == total or index % step == 0):
            elapsed = time.monotonic() - start
            msg = f"[{label}] {index}/{total} ({elapsed:0.1f}s)"
            if tty:
                sys.stderr.write("\r" + msg + "  ")
            else:
                sys.stderr.write(msg + "\n")
            sys.stderr.flush()
    if tty:
        sys.stderr.write("\n")
        sys.stderr.flush()

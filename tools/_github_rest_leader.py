"""Hold an isolated POSIX process group until the parent collects worker status."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

WORKER_TIMEOUT = 45
CLEANUP_TIMEOUT = 50


if sys.platform != "win32":
    from os import getpgrp, getsid, killpg
    from signal import SIGKILL


def main(argv: list[str] | None = None) -> int:
    """Run the worker in a verified private session with a bounded lifetime."""
    args = sys.argv[1:] if argv is None else argv
    if sys.platform != "win32":
        if len(args) != 1 or os.getpid() != getpgrp() or os.getpid() != getsid(0):
            return 2
        deadline = time.monotonic() + CLEANUP_TIMEOUT
        worker = Path(__file__).resolve().with_name("_github_rest_worker.py")
        child = subprocess.Popen([sys.executable, "-I", "-S", str(worker), args[0]], stdin=subprocess.DEVNULL)
        try:
            status = child.wait(timeout=WORKER_TIMEOUT)
        except subprocess.TimeoutExpired:
            killpg(getpgrp(), SIGKILL)
            return 2
        sys.stdout.flush()
        with open(os.devnull, "w", encoding="utf8") as sink:
            os.dup2(sink.fileno(), sys.stdout.fileno())
        sys.stderr.buffer.write(f"\n__GH_WORKER_EXIT__:{status}\n".encode("ascii"))
        sys.stderr.buffer.flush()
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)
        killpg(getpgrp(), SIGKILL)
        return 2

    return 2


if __name__ == "__main__":
    raise SystemExit(main())

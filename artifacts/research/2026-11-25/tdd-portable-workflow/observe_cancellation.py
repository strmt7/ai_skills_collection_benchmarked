"""Qualify cancellation and cleanup through the same observable behavior."""
from __future__ import annotations

import asyncio
import hashlib
import json
import platform
import sys
from pathlib import Path

CHECK = "worker_finishes_after_cancellation"
DEADLINE = 0.1


async def observe(acknowledge: bool) -> dict[str, object]:
    started = asyncio.Event()
    waiting_after_cancel = asyncio.Event()
    release = asyncio.Event()

    async def worker() -> None:
        started.set()
        try:
            await release.wait()
        except asyncio.CancelledError:
            if acknowledge:
                raise
            waiting_after_cancel.set()
            await release.wait()

    task = asyncio.create_task(worker())
    state: dict[str, object] = {}
    try:
        await asyncio.wait_for(started.wait(), timeout=5)
        state["started_before_cancel"] = started.is_set()
        task.cancel()
        done, pending = await asyncio.wait({task}, timeout=DEADLINE)
        state["finished_before_release"] = task in done
        state["pending_before_release"] = task in pending
        state["observed_ignored_cancel"] = waiting_after_cancel.is_set()
        state["cancelled_before_release"] = task.cancelled()
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)

    state["joined_after_cleanup"] = task.done()
    state["other_pending_tasks"] = len(asyncio.all_tasks() - {asyncio.current_task()})
    return state


async def main() -> dict[str, object]:
    before = await observe(acknowledge=False)
    after = await observe(acknowledge=True)
    if before != {
        "started_before_cancel": True,
        "finished_before_release": False,
        "pending_before_release": True,
        "observed_ignored_cancel": True,
        "cancelled_before_release": False,
        "joined_after_cleanup": True,
        "other_pending_tasks": 0,
    }:
        raise ValueError(f"The defect sentinel did not reach its intended failure: {before}")
    if after != {
        "started_before_cancel": True,
        "finished_before_release": True,
        "pending_before_release": False,
        "observed_ignored_cancel": False,
        "cancelled_before_release": True,
        "joined_after_cleanup": True,
        "other_pending_tasks": 0,
    }:
        raise ValueError(f"The implementation correction did not satisfy the same check: {after}")
    return {
        "case_id": CHECK,
        "before": before,
        "after": after,
        "python": platform.python_version(),
        "platform": sys.platform,
        "machine": platform.machine(),
        "test_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "model_attempts": 0,
    }


if __name__ == "__main__":
    print(json.dumps(asyncio.run(main()), indent=2))

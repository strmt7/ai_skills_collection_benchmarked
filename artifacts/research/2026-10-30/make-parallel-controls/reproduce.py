"""Observe GNU Make parallel target behavior without running Docker targets."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

MARKER = """
import json, pathlib, sys, time
start = time.monotonic_ns()
time.sleep(1.0)
end = time.monotonic_ns()
pathlib.Path(sys.argv[1] + ".json").write_text(json.dumps([start, end]), encoding="utf-8")
"""


def run(command, directory, env):
    return subprocess.run(
        command, cwd=directory, env=env, capture_output=True, text=True, timeout=30, check=True
    ).stdout


def control(directory, env, directive):
    directory.mkdir()
    (directory / "marker.py").write_text(MARKER, encoding="utf-8")
    (directory / "Makefile").write_text(
        ".PHONY: all docker-build docker-push docker-run\n"
        "all: docker-push docker-run\n"
        f"{directive}\n"
        "docker-push docker-run: docker-build\n"
        "docker-build docker-push docker-run:\n\t@python3 marker.py $@\n",
        encoding="utf-8",
    )
    run(["make", "-j2", "--no-print-directory", "all"], directory, env)
    build = json.loads((directory / "docker-build.json").read_text(encoding="utf-8"))
    push = json.loads((directory / "docker-push.json").read_text(encoding="utf-8"))
    run_target = json.loads((directory / "docker-run.json").read_text(encoding="utf-8"))
    return {
        "build_ns": build,
        "push_ns": push,
        "run_ns": run_target,
        "build_before_dependents": build[1] <= min(push[0], run_target[0]),
        "dependents_overlap": max(push[0], run_target[0]) < min(push[1], run_target[1]),
    }


def main():
    env = os.environ.copy()
    for name in ("MAKEFLAGS", "GNUMAKEFLAGS", "MAKEFILES", "CC"):
        env.pop(name, None)
    with tempfile.TemporaryDirectory(prefix="gnu-make-control-") as tmp:
        root = Path(tmp)
        selective = control(root / "selective", env, ".NOTPARALLEL: docker-build docker-push docker-run")
        global_serial = control(root / "global", env, ".NOTPARALLEL:")
        if (
            not selective["build_before_dependents"]
            or not global_serial["build_before_dependents"]
            or not selective["dependents_overlap"]
            or global_serial["dependents_overlap"]
        ):
            raise RuntimeError("parallel control did not show the expected overlap distinction")
        print(
            json.dumps(
                {
                    "make": run(["make", "--version"], root, env).splitlines()[0],
                    "selective_notparallel": selective,
                    "global_notparallel": global_serial,
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()

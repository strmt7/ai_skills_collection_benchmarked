"""Controlled POSIX probes of the unchanged webapp-testing server helper."""

import os
import signal
import socket
import subprocess
import sys
import tempfile
from contextlib import suppress
from pathlib import Path


def invoke(directory, port, server, client):
    process = subprocess.Popen(
        [
            sys.executable,
            "/submission/with_server.py",
            "--server",
            server,
            "--port",
            str(port),
            "--timeout",
            "1",
            "--",
            sys.executable,
            "-c",
            client,
        ],
        cwd=directory,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=9)
        return {"returncode": process.returncode, "stdout": stdout.decode(), "stderr": stderr.decode()}, process.pid
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=2)


def group_cleanup(group):
    with suppress(ProcessLookupError):
        os.killpg(group, signal.SIGKILL)


def run(request):
    results = []
    with tempfile.TemporaryDirectory(prefix="server-control-") as temporary:
        directory = Path(temporary)
        # A listening socket belongs to this fixture, not the launched server.
        with socket.socket() as existing:
            existing.bind(("127.0.0.1", 0))
            existing.listen()
            port = existing.getsockname()[1]
            outcome, group = invoke(directory, port, "exit 7", "from pathlib import Path; Path('client-ran').touch()")
            group_cleanup(group)
            results.append(
                {
                    "control": "unrelated_open_port_accepts_failed_server",
                    "passed": outcome["returncode"] == 0 and (directory / "client-ran").exists(),
                    "outcome": outcome,
                }
            )
            outcome, group = invoke(directory, port, "exit 7", "raise SystemExit(11)")
            group_cleanup(group)
            results.append(
                {
                    "control": "client_failure_status_is_preserved",
                    "passed": outcome["returncode"] == 11,
                    "outcome": outcome,
                }
            )

        # Readiness waits while the child's undrained stdout pipe fills.
        with socket.socket() as reservation:
            reservation.bind(("127.0.0.1", 0))
            port = reservation.getsockname()[1]
        noisy = directory / "noisy.py"
        noisy.write_text(
            "import os, socket, sys, time\nfrom pathlib import Path\n"
            "Path('server-pid').write_text(str(os.getpid()))\n"
            "sys.stdout.write('x' * 1048576); sys.stdout.flush()\n"
            f"s=socket.socket(); s.bind(('127.0.0.1', {port})); s.listen()\n"
            "Path('listening').touch(); time.sleep(60)\n",
            encoding="utf-8",
        )
        outcome, group = invoke(directory, port, f"{sys.executable} {noisy}", "raise SystemExit(0)")
        pid_path = directory / "server-pid"
        child_survived = False
        child_state = None
        if pid_path.exists():
            try:
                child_pid = int(pid_path.read_text())
                os.kill(child_pid, 0)
                child_state = Path(f"/proc/{child_pid}/stat").read_text().split(") ", 1)[1].split()[0]
                child_survived = child_state not in {"Z", "X"}
            except ProcessLookupError:
                pass
        group_cleanup(group)
        results.append(
            {
                "control": "undrained_server_output_blocks_readiness",
                "passed": outcome["returncode"] != 0
                and pid_path.exists()
                and not (directory / "listening").exists()
                and "Server failed to start" in outcome["stderr"],
                "outcome": outcome,
            }
        )
        results.append(
            {
                "control": "shell_child_survives_helper_cleanup",
                "passed": child_survived,
                "observed_child_process_state": child_state,
                "fixture_process_group_killed_after_observation": True,
            }
        )
    return {
        "platform": sys.platform,
        "uid": os.getuid(),
        "controls": results,
        "scope": "Actual bounded processes and sockets in an owned network-isolated Linux container; negative findings are not repaired behavior",
    }

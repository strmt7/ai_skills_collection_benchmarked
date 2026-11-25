"""Independent Linux contract controls for the Playwright-managed server example."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import shlex
import signal
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

READY_PATH = "/health/ready"
TEST_EVENT_REPORTER = """const fs = require('node:fs');
module.exports = class TestEventReporter {
  onTestBegin() {
    fs.writeFileSync(process.env.SERVICE_TEST_STARTED, 'test started', { flag: 'wx' });
  }
};
"""


def read(path: Path) -> dict:
    return json.loads(path.read_bytes())


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def serve() -> None:
    origin = urlsplit(os.environ["APP_TEST_ORIGIN"])
    case = os.environ["SERVICE_CONTROL_CASE"]
    started = Path("service.pid")
    started.write_text(str(os.getpid()), encoding="ascii")
    if case == "early-exit":
        raise SystemExit(7)
    if case == "noisy":
        total = 2 * 1024**2
        sys.stdout.buffer.write(b"." * total)
        sys.stdout.flush()
        Path("startup-log-size").write_text(str(total), encoding="ascii")
    application = PreviewService(("127.0.0.1", origin.port), HealthHandler)
    with application:
        application.serve_forever()


class PreviewService(HTTPServer):
    """The listener can accept requests while the application is still starting."""

    def __init__(self, address: tuple[str, int], handler: type[BaseHTTPRequestHandler]) -> None:
        self.samples = 0
        super().__init__(address, handler)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != READY_PATH:
            self.send_error(404)
            return
        case = os.environ["SERVICE_CONTROL_CASE"]
        self.server.samples += 1
        ready = case != "never-ready" and (case != "slow-readiness" or self.server.samples > 1)
        status = 200 if ready else 503
        with Path("statuses.jsonl").open("a", encoding="ascii") as stream:
            stream.write(str(status) + "\n")
        if case == "interrupted" and Path(os.environ["SERVICE_TEST_STARTED"]).exists():
            time.sleep(3)
        instance = os.environ["APP_TEST_INSTANCE"]
        if case == "wrong-instance":
            instance = "different-preview-instance"
        payload = json.dumps({"application": "preview", "ready": ready, "instance": instance}).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args: object) -> None:
        pass


class OccupantHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        payload = b"unrelated service"
        self.send_response(200)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args: object) -> None:
        pass


def open_port(port: int) -> bool:
    with socket.socket() as connection:
        connection.settimeout(0.2)
        return connection.connect_ex(("127.0.0.1", port)) == 0


def select_port() -> int:
    with socket.socket() as socket_reservation:
        socket_reservation.bind(("127.0.0.1", 0))
        return socket_reservation.getsockname()[1]


def extract_dependencies(inputs: Path, output: Path) -> dict:
    graph = read(inputs / "admission.json")
    expected_names = {"@playwright/test", "playwright", "playwright-core"}
    if {package["name"] for package in graph["packages"]} != expected_names or len(graph["packages"]) != 3:
        raise ValueError("The fixture requires the three admitted Playwright packages")
    for package in graph["packages"]:
        data = inputs / package["archive"]
        if data.parent != inputs or data.name != package["name"].replace("@", "").replace("/", "-") + ".package.tgz":
            raise ValueError("Unrecognized Playwright package archive")
        if sha256(data.read_bytes()) != package["sha256"]:
            raise ValueError("A locked npm archive differs from its admission receipt")
        destination = output / package["name"]
        destination.mkdir(parents=True)
        total = 0
        with tarfile.open(data, "r:gz") as archive:
            for member in archive:
                path = PurePosixPath(member.name)
                if path.is_absolute() or path.parts[:1] != ("package",) or ".." in path.parts:
                    raise ValueError("An npm archive member left its package root")
                target = destination.joinpath(*path.parts[1:])
                total += member.size
                if total > 32 * 1024**2 or not (member.isreg() or member.isdir()):
                    raise ValueError("An npm archive member exceeded the fixture contract")
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as stream:
                        stream.write(archive.extractfile(member).read())
        installed = read(destination / "package.json")
        if installed["name"] != package["name"] or installed["version"] != package["version"]:
            raise ValueError("Extracted npm metadata differs from the locked graph")
    return graph


def capture_run(
    case: str, root: Path, node: str, cli: Path, port: int, test_started: Path
) -> tuple[int, bool, bytes, bytes]:
    environment = {
        **os.environ,
        "APP_TEST_ORIGIN": f"http://127.0.0.1:{port}",
        "APP_TEST_INSTANCE": uuid.uuid4().hex,
        "SERVICE_CONTROL_CASE": case,
        "SERVICE_TEST_STARTED": str(test_started),
        "NPM_CONFIG_CACHE": str(root / "npm-cache"),
        "NPM_CONFIG_OFFLINE": "true",
        "NPM_CONFIG_UPDATE_NOTIFIER": "false",
    }
    stdout = root / "runner.stdout.native"
    stderr = root / "runner.stderr.native"
    delivered_interrupt = False
    with stdout.open("xb") as standard, stderr.open("xb") as errors:
        process = subprocess.Popen(
            [
                node,
                str(cli),
                "test",
                "--config",
                "playwright.config.cjs",
                "--retries",
                "0",
                "--reporter",
                "json,./test-event.cjs",
            ],
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=standard,
            stderr=errors,
        )
        try:
            if case == "interrupted":
                deadline = time.monotonic() + 8
                while process.poll() is None and time.monotonic() < deadline:
                    if test_started.is_file():
                        process.send_signal(signal.SIGINT)
                        delivered_interrupt = True
                        break
                    time.sleep(0.025)
            return_code = process.wait(timeout=18)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=4)
    return return_code, delivered_interrupt, stdout.read_bytes(), stderr.read_bytes()


def observed_outcome(code: int, report: dict, interrupted: bool) -> str:
    counts = report.get("stats", {})
    messages = " ".join(error["message"] for error in report.get("errors", []))
    if interrupted and code != 0:
        return "interrupted"
    if code == 0 and counts.get("expected") == 1:
        return "pass"
    if code != 0:
        if counts.get("unexpected") == 1:
            return "test-failure"
        if "already used" in messages:
            return "port-conflict"
        if "Exit code: 7" in messages:
            return "startup-failure"
        if "Timed out waiting" in messages:
            return "startup-timeout"
    return "unclassified"


def project_workers(project: Path) -> int:
    workers = 0
    for process in Path("/proc").iterdir():
        if process.name.isdecimal():
            try:
                cwd = Path(os.readlink(process / "cwd"))
            except OSError:
                continue
            if cwd.is_relative_to(project):
                workers += 1
    return workers


def control(inputs: Path, project: Path, node: str, cli: Path, case: dict) -> dict:
    name = case["id"]
    project.mkdir()
    for source in ("playwright.config.cjs", "preview-health.spec.cjs"):
        (project / source).write_bytes((inputs / source).read_bytes())
    (project / "test-event.cjs").write_text(TEST_EVENT_REPORTER, encoding="utf-8")
    npm_command = shlex.join([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--serve"])
    metadata = {"name": "preview-lifecycle-fixture", "private": True, "scripts": {"test:serve": npm_command}}
    (project / "package.json").write_text(json.dumps(metadata), encoding="utf-8")
    test_marker = project / "test-started"
    if name == "occupied":
        with HTTPServer(("127.0.0.1", 0), OccupantHandler) as existing:
            serving = threading.Thread(target=existing.serve_forever)
            serving.start()
            port = existing.server_port
            try:
                code, interrupted, stdout, stderr = capture_run(name, project, node, cli, port, test_marker)
                occupant_intact = open_port(port)
            finally:
                existing.shutdown()
                serving.join()
    else:
        port = select_port()
        code, interrupted, stdout, stderr = capture_run(name, project, node, cli, port, test_marker)
        occupant_intact = None
    if len(stdout) + len(stderr) > 128 * 1024:
        raise ValueError("The runner exceeded this control's retained output budget")
    report = json.loads(stdout) if stdout else {}
    outcome = observed_outcome(code, report, interrupted)
    pid_file = project / "service.pid"
    spawned = pid_file.is_file()
    process_present = spawned and (Path("/proc") / pid_file.read_text(encoding="ascii")).exists()
    listening = open_port(port)
    remaining_workers = project_workers(project)
    status_file = project / "statuses.jsonl"
    statuses = list(map(int, status_file.read_text().splitlines())) if status_file.exists() else []
    log_file = project / "startup-log-size"
    startup_log_size = int(log_file.read_text()) if log_file.is_file() else 0
    passed = (
        case["outcome"] == outcome
        and case["owned_service_started"] == spawned
        and case["test_started"] == test_marker.is_file()
        and not process_present
        and not listening
        and remaining_workers == 0
        and (name != "occupied" or occupant_intact)
        and (name != "never-ready" or (statuses and set(statuses) == {503}))
        and (name != "slow-readiness" or (statuses and statuses[0] == 503 and statuses[-1] == 200))
        and (name != "noisy" or startup_log_size == 2 * 1024**2)
        and (name != "interrupted" or interrupted)
    )
    return {
        "id": name,
        "passed": bool(passed),
        "outcome": outcome,
        "exit_code": code,
        "runner_stats": report.get("stats"),
        "owned_service_started": spawned,
        "test_started": test_marker.is_file(),
        "service_process_present_after": process_present,
        "remaining_project_processes": remaining_workers,
        "listener_present_after": listening,
        "independent_occupant_preserved": occupant_intact,
        "statuses": statuses,
        "startup_stdout_bytes": startup_log_size,
        "interrupt_delivered": interrupted,
        "streams": {
            "stdout": base64.b64encode(stdout).decode("ascii"),
            "stderr": base64.b64encode(stderr).decode("ascii"),
        },
    }


def main() -> None:
    if sys.argv[1:] == ["--serve"]:
        serve()
        return
    if len(sys.argv) != 4:
        raise SystemExit("usage: webapp_managed_service_fixture.py INPUTS NODE forward|reverse")
    inputs, node, order = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    contract = read(inputs / "service-lifecycle-contract.json")
    if order not in {"forward", "reverse"}:
        raise SystemExit("Invalid control order")
    with tempfile.TemporaryDirectory(prefix="preview control ") as directory:
        root = Path(directory)
        packages = root / "node_modules"
        graph = extract_dependencies(inputs, packages)
        cli = packages / "@playwright/test/cli.js"
        cases = contract["cases"]
        if order == "reverse":
            cases = list(reversed(cases))
        results = [control(inputs, root / case["id"], node, cli, case) for case in cases]
        version = subprocess.check_output([node, "--version"], text=True, timeout=5).strip()
    print(json.dumps({"playwright": graph["stable_version"], "node": version, "order": order, "cases": results}))


if __name__ == "__main__":
    main()

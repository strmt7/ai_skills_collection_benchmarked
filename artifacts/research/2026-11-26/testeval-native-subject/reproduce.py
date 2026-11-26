"""Replay the native Codex-to-TestEval boundary with a deterministic local peer."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, Thread
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))

from _native_benchmark_runtime import write_json  # noqa: E402
from _scripted_tool_control import successful_commands  # noqa: E402
from _testeval_subject import finish_subject, prepare_subject  # noqa: E402
from _trial_context import command, create_context  # noqa: E402
from _trial_transcript import parse_events  # noqa: E402
from collect_testeval_submission import collect_handoff  # noqa: E402
from qualify_trial_context import check as check_context  # noqa: E402
from run_agent_trial import execute_agent  # noqa: E402

MODEL = "scripted-testeval-boundary"
MARKER = "TESTEVAL_SUBMISSION_WRITTEN"
PRIVATE_MARKER = b"TESTEVAL_GRADER_PRIVATE_CANARY"
CALL_ID = "call_testeval_control"
CONTROLS = {
    "sealed": "sealed",
    "unchanged": "missing_submission",
    "tool-failed": "missing_submission",
    "extra-edit": "submission_scope_changed",
    "empty-tests": "submission_invalid",
    "truncated": "execution_incomplete",
    "timeout": "execution_incomplete",
}
SOURCES = (
    "tools/_scripted_tool_control.py",
    "tools/_testeval_subject.py",
    "tools/_trial_collection.py",
    "tools/_trial_context.py",
    "tools/_windows_trial_process.py",
    "tools/collect_testeval_submission.py",
    "tools/grade_testeval_submission.py",
    "tools/qualify_trial_context.py",
    "tools/run_agent_trial.py",
    "tools/transfer_benchmark_submission.py",
)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def protocol_events(index: int, tool: dict[str, Any] | None, *, truncated: bool) -> bytes:
    response = {
        "id": f"resp_testeval_{index}",
        "object": "response",
        "model": MODEL,
        "created_at": 0,
        "status": "in_progress",
        "output": [],
        "usage": None,
    }
    events: list[dict[str, Any]] = []

    def event(kind: str, **fields: Any) -> None:
        events.append({"type": kind, "sequence_number": len(events), **fields})

    event("response.created", response=response)
    if not truncated:
        if tool is None:
            content = {"type": "output_text", "text": "Scripted control complete.", "annotations": [], "logprobs": []}
            item = {
                "id": f"msg_testeval_{index}",
                "type": "message",
                "role": "assistant",
                "status": "completed",
                "content": [content],
            }
            event("response.output_item.added", output_index=0, item={**item, "content": [], "status": "in_progress"})
            fields = {"item_id": item["id"], "output_index": 0, "content_index": 0}
            event("response.content_part.added", **fields, part={**content, "text": ""})
            event("response.output_text.delta", **fields, delta=content["text"], logprobs=[])
            event("response.output_text.done", **fields, text=content["text"], logprobs=[])
            event("response.content_part.done", **fields, part=content)
        else:
            item = tool
            event("response.output_item.added", output_index=0, item={**item, "arguments": "", "status": "in_progress"})
            fields = {"item_id": item["id"], "output_index": 0}
            event("response.function_call_arguments.delta", **fields, delta=item["arguments"])
            event("response.function_call_arguments.done", **fields, arguments=item["arguments"], name=item["name"])
        event("response.output_item.done", output_index=0, item=item)
        usage = {
            "input_tokens": 1,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens": 1,
            "output_tokens_details": {"reasoning_tokens": 0},
            "total_tokens": 2,
        }
        event("response.completed", response={**response, "status": "completed", "output": [item], "usage": usage})
    return "".join(f"event: {row['type']}\ndata: {json.dumps(row)}\n\n" for row in events).encode()


def quote_powershell(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def tool_script(case: str, secret: Path, payload: bytes) -> str | None:
    if case in {"unchanged", "truncated", "timeout"}:
        return None
    if case == "tool-failed":
        return "throw 'Intentional failed native tool control'"
    if case == "empty-tests":
        payload = b"[]"
    statements = [
        "$ErrorActionPreference='Stop'",
        f"$private={quote_powershell(str(secret))}",
        "$denied=$false",
        "try { $null=Get-Content -LiteralPath $private -Raw -ErrorAction Stop } "
        "catch { $denied=$_.CategoryInfo.Category -eq 'PermissionDenied' }",
        "if (!$denied) { throw 'Expected the grading canary to be denied' }",
        "Set-Content -LiteralPath 'tests.json' -Encoding Ascii -NoNewline -Value "
        + quote_powershell(payload.decode("ascii")),
    ]
    if case == "extra-edit":
        statements.append("Set-Content -LiteralPath 'unexpected.txt' -Value 'deliberate scope control'")
    statements.append(f"Write-Output '{MARKER}'")
    return "; ".join(statements)


class ScriptedPeer(HTTPServer):
    def __init__(self, output: Path, case: str, script: str | None) -> None:
        super().__init__(("127.0.0.1", 0), ScriptedHandler)
        self.output, self.case, self.script = output, case, script
        self.release = Event()
        self.requests: list[dict[str, Any]] = []
        self.errors: list[str] = []

    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(5)
        return connection, address


class ScriptedHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def do_POST(self) -> None:
        peer = self.server
        assert isinstance(peer, ScriptedPeer)
        try:
            index = len(peer.requests) + 1
            if (
                self.path != "/v1/responses"
                or self.headers.get("Authorization") is not None
                or self.headers.get("Content-Encoding") not in (None, "identity")
                or self.headers.get("Transfer-Encoding")
                or index > (2 if peer.script else 1)
            ):
                raise ValueError("Unexpected anonymous scripted request")
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 1024**2:
                raise ValueError("Scripted request exceeds its byte budget")
            raw = self.rfile.read(size)
            request = json.loads(raw)
            if (
                len(raw) != size
                or PRIVATE_MARKER in raw
                or request.get("model") != MODEL
                or request.get("stream") is not True
            ):
                raise ValueError("Unexpected native request body or context marker")
            (peer.output / f"request-{index}.native.json").write_bytes(raw)
            peer.requests.append({"route": self.path, "anonymous": True, "model": request["model"]})
            item = None
            if peer.script is not None and index == 1:
                tools = {
                    value.get("name"): value for value in request.get("tools", []) if value.get("type") == "function"
                }
                if "shell_command" in tools and "command" in tools["shell_command"]["parameters"]["properties"]:
                    name, arguments = "shell_command", {"command": peer.script, "timeout_ms": 15000}
                elif "exec_command" in tools and "cmd" in tools["exec_command"]["parameters"]["properties"]:
                    name, arguments = "exec_command", {"cmd": peer.script, "yield_time_ms": 10000}
                else:
                    raise ValueError("Native Codex did not expose an admitted ordinary shell tool")
                item = {
                    "id": "fc_testeval",
                    "type": "function_call",
                    "call_id": CALL_ID,
                    "name": name,
                    "arguments": json.dumps(arguments),
                    "status": "completed",
                }
            elif index == 2:
                outputs = [
                    row
                    for row in request["input"]
                    if row.get("type") == "function_call_output" and row.get("call_id") == CALL_ID
                ]
                if len(outputs) != 1:
                    raise ValueError("Native tool output differs from its originating call")
            truncated = peer.case in {"truncated", "timeout"}
            data = protocol_events(index, item, truncated=truncated)
            (peer.output / f"response-{index}.native.sse").write_bytes(data)
            if peer.case == "timeout":
                peer.release.wait(12)
                return
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)
        except (OSError, KeyError, TypeError, ValueError) as error:
            peer.errors.append(type(error).__name__ + ": " + str(error))
            self.send_error(400, "Scripted transport rejected the request")


def run_case(args: argparse.Namespace, setup: dict[str, Any], case: str, payload: bytes) -> dict[str, Any]:
    out = args.output / case
    cli, python = Path(setup["cli"]), Path(setup["python"])
    with TemporaryDirectory(prefix="native-testeval-") as temporary:
        scratch = Path(temporary).resolve(strict=True)
        prepared = prepare_subject(args.task_plan, args.baseline, scratch / "subject", out, python)
        control = out / "grader-only.txt"
        control.write_bytes(PRIVATE_MARKER)
        context = create_context(scratch / "controller", prepared.workspace, cli, python, (cli.parent, python.parent))
        execution = out / "execution"
        execution.mkdir()
        with ScriptedPeer(execution, case, tool_script(case, control, payload)) as peer:
            provider = {"base_url": f"http://127.0.0.1:{peer.server_port}/v1", "authentication": "none"}
            argv = command(context, MODEL, "high", provider=provider)
            thread = Thread(target=peer.serve_forever, kwargs={"poll_interval": 0.05})
            thread.start()
            try:
                code, timed_out, _ = execute_agent(
                    argv,
                    (prepared.workspace / "task.txt").read_bytes().decode("utf-8"),
                    execution,
                    6 if case == "timeout" else 45,
                    context=context,
                )
            finally:
                peer.release.set()
                peer.shutdown()
                thread.join(6)
            if thread.is_alive() or peer.errors or len(peer.requests) != (2 if peer.script else 1):
                raise ValueError(f"Scripted peer did not finish the expected request frame for {case}")
            write_json(execution / "peer-observations.json", {"requests": peer.requests, "closed": True})
        observed = finish_subject(prepared)
        process = json.loads((execution / "process.json").read_bytes())
        assert process["job_active_processes_after_cleanup"] == 0
        assert observed["status"] == CONTROLS[case]
        transcript = (execution / "transcript.jsonl").read_bytes()
        if case in {"sealed", "extra-edit", "empty-tests"}:
            [executed] = successful_commands(transcript, expected_count=1)
            assert executed["aggregated_output"].strip() == MARKER
        if case == "tool-failed":
            failures = [
                row["item"]
                for row in parse_events(transcript)
                if row["type"] == "item.completed" and row["item"].get("type") == "command_execution"
            ]
            assert len(failures) == 1 and failures[0]["status"] == "failed" and failures[0]["exit_code"] != 0
            assert code == 0
        grading = None
        if case == "sealed":
            captured = (out / "submission/tests.json").read_bytes()
            assert captured == payload
            grading = collect_handoff(
                prepared.task_plan,
                prepared.handoff,
                observed["archive_sha256"],
                args.defects,
                args.assets,
                args.runtime,
                out / "grading",
            )
            assert grading["native_test_eval"]["status"] == "measured" and grading["reference"]["status"] == "passed"
            assert grading["sensitivity"] == {"detected": 2, "survived": 0, "inconclusive": 0, "planned": 2}
            leases = [json.loads(item.read_bytes()) for item in (out / "grading").glob("*.lease.json")]
            assert len(leases) == 4 and all(item["stage"] == "closed" for item in leases)
        else:
            assert not (prepared.handoff / "submission.tar").exists() and not (out / "grading").exists()
        if case in {"truncated", "timeout"}:
            assert not (out / "collection").exists()
            assert timed_out == (case == "timeout")
        assert control.read_bytes() == PRIVATE_MARKER
    return {
        "status": observed["status"],
        "cli_exit": code,
        "timed_out": timed_out,
        "native_processes_remaining": process["job_active_processes_after_cleanup"],
        "archive_sha256": observed["archive_sha256"],
        "grade": grading,
        "evidence_sha256": {
            name: digest(out / name)
            for name in (
                "subject-result.json",
                "execution/process.json",
                "execution/transcript.jsonl",
                "execution/peer-observations.json",
            )
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("context-proof", "task-plan", "baseline", "accepted-suite", "defects", "assets", "runtime", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    if not args.output.is_relative_to(ROOT / ".venv") or args.output == ROOT / ".venv":
        parser.error("Use a new private directory inside the checkout's .venv")
    proof = args.context_proof.resolve(strict=True)
    context_check = check_context(proof)
    if not context_check["ok"]:
        raise ValueError("Native context revalidation failed. " + ". ".join(context_check["errors"]))
    setup = json.loads((proof / "qualification.json").read_bytes())
    task = json.loads(args.task_plan.read_bytes())
    if task["task_id"] != 685 or set(task["programs"]) != {"reference", "repeat-last", "reverse-order"}:
        raise ValueError("This control requires the reviewed public TestEval task 685 and its two prepared defects")
    payload = (json.dumps([args.accepted_suite.read_text(encoding="utf-8")], ensure_ascii=True) + "\n").encode("ascii")
    sources = {name: digest(ROOT / name) for name in SOURCES}
    args.output.mkdir()
    write_json(
        args.output / "specification.json",
        {
            "expected_statuses": CONTROLS,
            "model_attempts": 0,
            "task_plan_sha256": digest(args.task_plan),
            "cli_sha256": setup["cli_sha256"],
            "context_proof_sha256": digest(proof / "qualification.json"),
            "execution_sources_sha256": sources,
        },
    )
    rows = {}
    for case in CONTROLS:
        rows[case] = run_case(args, setup, case, payload)
        write_json(args.output / "progress.json", rows)
        print(json.dumps({"control": case, "status": rows[case]["status"]}), flush=True)
    if sources != {name: digest(ROOT / name) for name in SOURCES} or not check_context(proof)["ok"]:
        raise ValueError("Native execution or context sources changed during the controls")
    write_json(
        args.output / "summary.json",
        {
            "model_attempts": 0,
            "official_cli": True,
            "graded_controls": 1,
            "native_grader_stages_closed": 4,
            "controls": rows,
            "source_sha256": digest(Path(__file__)),
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

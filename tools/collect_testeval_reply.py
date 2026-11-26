"""Send an exact native final message to the sealed public TestEval grader."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from _native_benchmark_runtime import write_json
from _testeval_subject import prepare_subject, stopped_execution
from _trial_collection import capture_owned
from _trial_transcript import parse_events
from _windows_appcontainer import checked_path
from collect_testeval_submission import ROOT, capture_directory, collect_handoff, object_from, read_asset
from grade_testeval_submission import TEST_SUBMISSION, load_test_snippets, sha256
from transfer_benchmark_submission import plan_handoff, seal
from validate_testeval_calibration import read_evidence

TRANSCRIPT_LIMIT = 8 * 1024**2


def extract_reply(execution: Path, prompt_sha256: str) -> tuple[bytes, dict[str, Any]]:
    """Bind the official export to one complete native turn and its frozen prompt."""
    process = read_evidence(execution / "process.json")
    if not stopped_execution(object_from(process)):
        raise ValueError("The owned native subject did not finish successfully")
    if sha256(read_evidence(execution / "input.native")) != prompt_sha256:
        raise ValueError("The native request differs from the frozen prompt")

    with checked_path(execution / "transcript.jsonl").open("rb") as stream:
        transcript = stream.read(TRANSCRIPT_LIMIT + 1)
    if len(transcript) > TRANSCRIPT_LIMIT:
        raise ValueError("The native transcript exceeds the TestEval limit")
    events = parse_events(transcript)
    types = [event["type"] for event in events]
    if (
        types.count("thread.started") != 1
        or types.count("turn.started") != 1
        or types.count("turn.completed") != 1
        or types[0] != "thread.started"
        or types[-1] != "turn.completed"
        or "turn.failed" in types
    ):
        raise ValueError("One complete native client turn is required")
    items = [
        event["item"] for event in events[types.index("turn.started") + 1 : -1] if event["type"] == "item.completed"
    ]
    reply = items[-1] if items else {}
    identifier, message = reply.get("id"), reply.get("text")
    if (
        reply.get("type") != "agent_message"
        or not isinstance(identifier, str)
        or not identifier
        or sum(item.get("id") == identifier for item in items) != 1
        or not isinstance(message, str)
        or not message.strip()
    ):
        raise ValueError("The completed native turn has no final assistant message")
    exported = read_evidence(execution / "last-message.native")
    if exported != message.encode("utf-8"):
        raise ValueError("The native last-message export differs from the completed transcript")
    return exported, {
        "delivery": "native_final_message",
        "message_item_id": identifier,
        "message_sha256": sha256(exported),
        "native_process_sha256": sha256(process),
        "native_transcript_sha256": sha256(transcript),
        "prompt_sha256": prompt_sha256,
    }


def collect_reply(
    plan: Path,
    baseline: Path,
    execution: Path,
    prompt_sha256: str,
    defects: Path,
    assets: Path,
    runtime: Path,
    output: Path,
) -> dict[str, Any]:
    """Build a controller envelope and grade its single exact publisher test string."""
    execution, output = checked_path(execution), capture_directory(output)
    if not execution.is_relative_to(ROOT / ".venv") or output.is_relative_to(execution):
        raise ValueError("Native execution and grading evidence require disjoint controller-owned paths")
    reply, evidence = extract_reply(execution, prompt_sha256)
    snippet = reply.decode("utf-8")
    tests = (json.dumps([snippet], ensure_ascii=False) + "\n").encode("utf-8")
    load_test_snippets(tests)
    output.mkdir()
    write_json(output / "reply-evidence.json", evidence)

    with TemporaryDirectory(prefix="testeval-reply-") as temporary:
        workspace = Path(temporary) / "envelope"
        prepared = prepare_subject(plan, baseline, workspace, output / "envelope", Path(sys.executable))
        (workspace / TEST_SUBMISSION).write_bytes(tests)
        captured, observation = output / "captured-envelope", output / "envelope-collection"
        initial = plan_handoff(prepared.baseline_bytes, prepared.baseline_bytes)
        report = capture_owned(workspace, captured, observation, prepared.python, initial.baseline["policy"])
        if report["status"] != "collected":
            raise ValueError("The native collector could not attest the reply envelope")

    submission = read_asset(observation / "stdout.native")
    transfer = plan_handoff(prepared.baseline_bytes, submission)
    (prepared.handoff / "submission.collection.json").write_bytes(submission)
    archive = seal(transfer, captured, prepared.handoff / "submission.tar")
    if read_asset(captured / TEST_SUBMISSION) != tests:
        raise ValueError("The sealed reply envelope differs from the verified export")
    write_json(output / "delivery.json", {**evidence, "archive_sha256": archive["archive_sha256"]})
    return collect_handoff(
        prepared.task_plan, prepared.handoff, archive["archive_sha256"], defects, assets, runtime, output / "grade"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True, help="Frozen TestEval task plan")
    parser.add_argument("--baseline", type=Path, required=True, help="Sealed starting workspace")
    parser.add_argument("--execution", type=Path, required=True, help="Owned native CLI execution records")
    parser.add_argument("--prompt-sha256", required=True, help="Frozen request digest")
    parser.add_argument("--defects", type=Path, required=True)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = collect_reply(
            args.plan,
            args.baseline,
            args.execution,
            args.prompt_sha256,
            args.defects,
            args.assets,
            args.runtime,
            args.output,
        )
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 1
    print(json.dumps({"ok": True, "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Offline helper regression probes; use the qualified current SDK environment."""

import argparse
import asyncio
import hashlib
import importlib.metadata
import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path


def qualify(root):
    from mcp.types import TextContent

    package = (
        root
        / "included/skills/by-category/agent-infrastructure-skill-creation/official-reference/mcp-builder-anthropics"
    )
    records = []

    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    try:
        load("original_connections", package / "scripts/connections.py")
    except ImportError as exc:
        records.append(
            {
                "probe": "unchanged_helper_import_on_latest_stable_mcp",
                "outcome": "compatibility_failure",
                "error_type": type(exc).__name__,
                "detail": str(exc).split(" (")[0],
            }
        )
    else:
        records.append({"probe": "unchanged_helper_import_on_latest_stable_mcp", "outcome": "imports"})

    # A clearly labeled import shim lets us test additional, independent agent-loop
    # defects without editing the baseline or claiming its connection helper works.
    shim = types.ModuleType("connections")

    def no_connection(*args, **kwargs):
        raise AssertionError("provider or external MCP connection forbidden in this probe")

    shim.create_connection = no_connection
    sys.modules["connections"] = shim
    evaluation = load("original_evaluation", package / "scripts/evaluation.py")

    class FixtureProtocolError(Exception):
        pass

    class FixtureMessages:
        def __init__(self, count):
            self.count = count
            self.calls = 0
            self.observed_ids = []
            self.returned_tool_text = None

        def create(self, **kwargs):
            self.calls += 1
            if self.calls == 1:
                blocks = [
                    types.SimpleNamespace(type="tool_use", id="call_" + str(i), name="lookup_" + str(i), input={})
                    for i in range(self.count)
                ]
                return types.SimpleNamespace(stop_reason="tool_use", content=blocks)
            content = kwargs["messages"][-1]["content"]
            self.observed_ids = [item["tool_use_id"] for item in content]
            self.returned_tool_text = content[0]["content"]
            if set(self.observed_ids) != {"call_" + str(i) for i in range(self.count)}:
                raise FixtureProtocolError("tool results must cover every preceding assistant tool call")
            return types.SimpleNamespace(
                stop_reason="end_turn", content=[types.SimpleNamespace(type="text", text="<response>ok</response>")]
            )

    class FixtureConnection:
        def __init__(self, result):
            self.result = result
            self.called = []

        async def call_tool(self, name, arguments):
            self.called.append(name)
            return self.result

    async def run():
        messages = FixtureMessages(2)
        connection = FixtureConnection("ok")
        try:
            await evaluation.agent_loop(
                types.SimpleNamespace(messages=messages), "offline-fixture", "lookup both items", [], connection
            )
        except FixtureProtocolError as exc:
            records.append(
                {
                    "probe": "multiple_tool_call_result_matching",
                    "outcome": "reproduced_failure",
                    "calls_requested": 2,
                    "calls_executed": len(connection.called),
                    "result_ids_sent": messages.observed_ids,
                    "detail": str(exc),
                }
            )
        else:
            raise AssertionError("expected incomplete multi-call behavior was not reproduced")
        messages = FixtureMessages(1)
        connection = FixtureConnection([TextContent(type="text", text="successful fixture result")])
        await evaluation.agent_loop(
            types.SimpleNamespace(messages=messages), "offline-fixture", "lookup item", [], connection
        )
        failed = (
            messages.returned_tool_text.startswith("Error executing tool")
            and "not JSON serializable" in messages.returned_tool_text
        )
        records.append(
            {
                "probe": "actual_mcp_text_content_serialization",
                "outcome": "reproduced_failure" if failed else "not_reproduced",
                "mcp_content_type": "mcp.types.TextContent",
                "successful_result_converted_to_error": failed,
            }
        )
        if not failed:
            raise AssertionError("expected real SDK content serialization defect was not reproduced")

    asyncio.run(run())
    try:
        evaluation.extract_xml_content(None, "response")
    except TypeError:
        records.append({"probe": "missing_text_response", "outcome": "reproduced_failure", "error_type": "TypeError"})
    else:
        raise AssertionError("None handling differs from reviewed behavior")
    with tempfile.TemporaryDirectory(prefix="mcp-xml-probe-") as directory:
        path = Path(directory) / "evaluation.xml"
        path.write_text("<evaluation>", encoding="utf-8")
        result = evaluation.parse_evaluation_file(path)
        records.append({"probe": "malformed_xml", "outcome": "reproduced_empty_task_list", "task_count": len(result)})
    report = {
        "schema_version": 1,
        "evidence_class": "offline_helper_contract_probe",
        "python_version": sys.version.split()[0],
        "anthropic_version": importlib.metadata.version("anthropic"),
        "mcp_version": importlib.metadata.version("mcp"),
        "input_sha256": {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (package / "scripts/connections.py", package / "scripts/evaluation.py")
        },
        "provider_requests": 0,
        "external_mcp_connections": 0,
        "additional_agent_probes_used_connection_import_shim": True,
        "probes": records,
        "scope": "Reproduced packaging/contract defects; not a model benchmark or completed skill repair",
    }
    report["reproducer_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return report


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.output.exists():
        raise ValueError("receipt already exists; select a new output path")
    root = Path(__file__).resolve().parents[2]
    report = qualify(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "probes": len(report["probes"]),
                "provider_requests": report["provider_requests"],
                "external_mcp_connections": report["external_mcp_connections"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

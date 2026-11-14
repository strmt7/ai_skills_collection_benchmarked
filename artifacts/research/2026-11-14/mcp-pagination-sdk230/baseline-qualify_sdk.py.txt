"""Actual local stdio and typed pagination controls for Python MCP 2.x.

Run with the qualified MCP SDK environment. No provider requests or external
MCP endpoints are used. This does not qualify remote HTTP/session security.
"""

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TypedDict

from mcp import ClientSession, MCPError, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.mcpserver import Context, MCPServer
from mcp.types import REQUEST_TIMEOUT, ListToolsResult, PaginatedRequestParams, Tool, ToolAnnotations


class EchoResult(TypedDict):
    values: list[int]
    sum: int
    lifespan_ready: bool


def serve(lifecycle: Path):
    @asynccontextmanager
    async def lifespan(server):
        lifecycle.write_text("started\n", encoding="utf-8")
        try:
            yield {"fixture_ready": True}
        finally:
            with lifecycle.open("a", encoding="utf-8") as stream:
                stream.write("closed\n")

    server = MCPServer("current-sdk-fixture", lifespan=lifespan)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
    async def echo(values: list[int], ctx: Context) -> EchoResult:
        await ctx.info("local fixture")
        await ctx.report_progress(0.25, total=1.0, message="fixture started")
        return {
            "values": values,
            "sum": sum(values),
            "lifespan_ready": ctx.request_context.lifespan_context["fixture_ready"],
        }

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
    def fail() -> str:
        raise ValueError("controlled fixture failure")

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False))
    async def wait() -> str:
        await asyncio.sleep(300)
        return "unexpected completion"

    server.run(transport="stdio")


async def all_tools(session, max_pages=100):
    """Use current typed request/result fields and reject cursor cycles."""
    cursor = None
    seen = set()
    tools = []
    names = set()
    for _ in range(max_pages):
        response = await session.list_tools(params=PaginatedRequestParams(cursor=cursor))
        for tool in response.tools:
            if tool.name in names:
                raise ValueError("duplicate tool name across pages")
            names.add(tool.name)
            tools.append(tool)
        if not response.next_cursor:
            return tools
        if response.next_cursor in seen:
            raise ValueError("tool pagination cursor cycle")
        seen.add(response.next_cursor)
        cursor = response.next_cursor
    raise ValueError("tool pagination page limit exceeded")


class TypedPages:
    def __init__(self, cycle=False):
        self.observed = []
        self.cycle = cycle

    async def list_tools(self, *, params):
        self.observed.append(params.cursor)
        if params.cursor is None:
            return ListToolsResult(tools=[Tool(name="page_one", inputSchema={"type": "object"})], nextCursor="second")
        name = "page_cycle" if self.cycle else "page_two"
        return ListToolsResult(
            tools=[Tool(name=name, inputSchema={"type": "object"})], nextCursor="second" if self.cycle else None
        )


async def qualify(protocol="modern"):
    progress = []

    async def on_progress(value, total, message):
        progress.append({"progress": value, "total": total, "message": message})

    pages = TypedPages()
    names = [tool.name for tool in await all_tools(pages)]
    cycle_rejected = False
    try:
        await all_tools(TypedPages(cycle=True))
    except ValueError as exc:
        cycle_rejected = "cursor cycle" in str(exc)
    with tempfile.TemporaryDirectory(prefix="mcp-roundtrip-") as temporary:
        lifecycle = Path(temporary) / "lifecycle.txt"
        stderr = Path(temporary) / "server.log"
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(Path(__file__).resolve()), "--server", "--lifecycle", str(lifecycle)],
        )
        timeout_observed = False
        with stderr.open("w", encoding="utf-8") as log:
            async with (
                asyncio.timeout(20),
                stdio_client(parameters, errlog=log) as (read, write),
                ClientSession(read, write) as session,
            ):
                if protocol == "modern":
                    await session.discover()
                else:
                    await session.initialize()
                negotiated_version = session.protocol_version
                available = await all_tools(session)
                success = await session.call_tool(
                    "echo", {"values": [2, 3, -1]}, read_timeout_seconds=2, progress_callback=on_progress
                )
                failure = await session.call_tool("fail", {}, read_timeout_seconds=2)
                try:
                    await session.call_tool("wait", {}, read_timeout_seconds=0.1)
                except MCPError as exc:
                    timeout_observed = exc.code == REQUEST_TIMEOUT
                serialized_success = success.model_dump(mode="json", by_alias=True)
                serialized_failure = failure.model_dump(mode="json", by_alias=True)
                json.dumps(serialized_success, allow_nan=False)
                json.dumps(serialized_failure, allow_nan=False)
        lifecycle_events = lifecycle.read_text(encoding="utf-8").splitlines()
        server_log_size = stderr.stat().st_size
    checks = {
        "protocol_negotiation": negotiated_version == ("2026-07-28" if protocol == "modern" else "2025-11-25"),
        "actual_local_tool_listing": {tool.name for tool in available} == {"echo", "fail", "wait"},
        "structured_and_text_result": serialized_success.get("structuredContent")
        == {"values": [2, 3, -1], "sum": 4, "lifespan_ready": True}
        and bool(serialized_success.get("content"))
        and serialized_success.get("isError") is False,
        "typed_error_status_preserved": serialized_failure.get("isError") is True
        and bool(serialized_failure.get("content")),
        "progress_notification": progress == [{"progress": 0.25, "total": 1.0, "message": "fixture started"}],
        "request_timeout": timeout_observed,
        "lifespan_finally_cleanup": lifecycle_events == ["started", "closed"],
        "typed_multi_page_listing": names == ["page_one", "page_two"] and pages.observed == [None, "second"],
        "pagination_cycle_rejected": cycle_rejected,
    }
    return {
        "schema_version": 1,
        "evidence_class": "current-sdk-local-transport-controls",
        "python_version": sys.version.split()[0],
        "mcp_version": importlib.metadata.version("mcp"),
        "reproducer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "negotiation_mode": protocol,
        "protocol_version": negotiated_version,
        "checks": checks,
        "all_controls_passed": all(checks.values()),
        "provider_requests": 0,
        "external_mcp_connections": 0,
        "local_stdio_fixture_connections": 1,
        "success_envelope": serialized_success,
        "failure_envelope": serialized_failure,
        "server_log_bytes": server_log_size,
        "scope": "Actual initialization, listing, structured result, error, progress, timeout and lifespan cleanup over local stdio. Typed pagination uses explicit two-page/cycle fixtures. No remote transport/security or model efficacy claim.",
    }


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", action="store_true")
    parser.add_argument("--lifecycle", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--protocol", choices=("modern", "handshake"), default="modern")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.server:
        if args.lifecycle is None:
            raise ValueError("fixture lifecycle path required")
        serve(args.lifecycle)
        return 0
    if args.output is None or args.output.exists():
        raise ValueError("a new receipt path is required")
    report = asyncio.run(qualify(args.protocol))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"all_controls_passed": report["all_controls_passed"], "checks": report["checks"]}))
    return 0 if report["all_controls_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

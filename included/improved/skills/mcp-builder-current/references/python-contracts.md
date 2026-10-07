# Qualified Python MCP contracts, 2 October 2026

These calls were exercised with Python 3.14.8 and official MCP 2.2.0. The portable
fixture contains exact executable examples; the table records their scope.

| Operation | Current tested contract |
|---|---|
| Server | `from mcp.server.mcpserver import MCPServer, Context` |
| Local transport | `server.run(transport="stdio")` |
| Client transport | `async with stdio_client(StdioServerParameters(...)) as (read, write)` |
| Client session | `async with ClientSession(read, write) as session` |
| Modern protocol | `await session.discover()`; selected `2026-07-28` |
| Legacy handshake | `await session.initialize()`; selected `2025-11-25` |
| Tools page | `await session.list_tools(params=PaginatedRequestParams(cursor=cursor))`; result `next_cursor` |
| Tool execution | `await session.call_tool(name, arguments, read_timeout_seconds=seconds)` |
| Serialization | `result.model_dump(mode="json", by_alias=True)`; inspect `isError`, `structuredContent`, `content` |
| Progress | `await ctx.report_progress(0.25, total=1.0, message="...")` |
| Logging | `await ctx.info("...")`; do not use nonexistent `log_info` |
| Lifespan data | `ctx.request_context.lifespan_context` |
| Tool timeout | `MCPError` with `REQUEST_TIMEOUT`; keep other error categories distinct |

A bare `dict` return annotation in the initial fixture emitted text without
structured content. A `TypedDict` with explicit field types qualified automatic
structured output. Verify the actual wire result, rather than assuming that
JSON-looking text is a structured result. The initial failed control remains in
the collection's research records.

The fixture uses the server parameter expected by the lifespan callback and
cleans up in `finally`. An actual tool error preserves `isError: true`; it is not
converted into a nominally successful string. Pagination fixtures prove both a
second page and cursor-cycle rejection. They do not stand for pagination support
in every deployed server.

Remote transport, authentication, concurrent request isolation, resource access,
form/URL elicitation and TypeScript compatibility still need dedicated fixtures.
Do not extrapolate local stdio results to those contracts.

Primary sources:

- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk).
- [Published MCP 2026-07-28 specification](https://modelcontextprotocol.io/specification/2026-07-28).
- [Elicitation constraints](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation).
- [TypeScript MCP SDK](https://github.com/modelcontextprotocol/typescript-sdk).

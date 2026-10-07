# Authoring and API resource review, 2 October 2026

This bounded batch adds `show-hn-writer`, ECC `claude-api`, and Anthropic
`mcp-builder` to the category research ledger. It does not establish performance
gains or complete current-SDK migration and behavioral evaluation.

## Show HN writer

Read the complete entrypoint, README, both reference documents and five bundled
evaluation descriptions. Inspected the environment template's variable names
and comments with example values redacted. The package supplies no executable
submission helper; shell snippets are operating instructions.

The empty description prevents meaningful portable activation. `compatibility`
is a list rather than the Agent Skills specification's string, and author/version
belong in metadata. Its agent-infrastructure category should be communication.
Step 1 pauses for five answers before Step 2 instructs reading existing context.
Title-only requests should not trigger a mandatory biography/questionnaire.

[Current HN guidelines](https://news.ycombinator.com/newsguidelines.html) prohibit
generated submission text and automated posting, and also prohibit generated or
AI-edited comments. Reframe this skill around explaining eligibility and helping
the user collect factual context for their own writing. Remove generated ready-to-
post copy and login/submission automation from an explicit improved overlay.
The [Show HN rules](https://news.ycombinator.com/showhn.html) require a usable,
nontrivial project the submitter personally worked on; landing pages, fundraisers
and material people cannot try are unsuitable. The original skill misses these
eligibility checks. An explicit human posting request remains a separate action,
subject to the current service rules; possessing credentials is not authority.

Claims about a mandatory en dash, 60-character minimum, exact word counts,
Tuesday morning timing, two-hour placement and a 24-hour sharing prohibition
lack primary evidence. Present supported rules separately from optional style
preferences. References labeled "Official Rules" invent a comments-thread route
and oversimplify resubmission. The bundled evaluations reproduce its own wording
and preferred lengths; they are not independent efficacy tests.

The optional review calls `gemini-2.0-flash`, which Google's
[current deprecation table](https://ai.google.dev/gemini-api/docs/deprecations)
marks shut down on 1 June 2026. A replacement should be an explicitly selected,
available stable model, with bounded requests and documented handling of blocked,
missing and failed responses. Sending project text to another provider requires
task scope; merely finding an environment key does not establish that scope.
Hardcoded shared `/tmp` files can collide, cookies need private storage, and raw
form strings do not safely encode arbitrary credentials/text. A reframed coaching
skill avoids this submission machinery entirely.

The verified current Varnan-Tech source root carries MIT terms and copyright
2026 Varnan-Tech. Preserve its notice and immutable baseline in any derivative.
Latest-source path/content binding and behavioral non-activation tests remain
pending; do not mark the original skill fully remediated.

## ECC Claude API

Read the complete entrypoint and `agents/openai.yaml`; these are the package's
two files. The latest ECC release checkout has no tracked `claude-api` entrypoint
at any path. This requires a recorded retirement/migration decision in the
source-refresh loop, not silent reuse as if it were current upstream guidance.

The hardcoded Opus/Sonnet 4.6 defaults are stale relative to Anthropic's
[current model lineup](https://platform.claude.com/docs/en/models/overview),
which includes Opus/Sonnet 5.5 and Fable 5.1. Current models differ in thinking
support and effort. Obtain available models/capabilities and select the user's
intended stable model; do not transplant manual thinking budgets to adaptive-only
models or describe aliases as resolved snapshots. Do not fabricate access to a
model just because the public documentation lists it.

Examples assume the first content block is text. The tool example submits one
result and requests a follow-up inside each tool iteration, instead of returning
all tool-call results for the preceding assistant message together. Anthropic's
[tool-call contract](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls)
requires matching call IDs and immediate tool results. Preserve non-text blocks,
validate tool inputs, enforce action authorization, and bound iterations, output,
timeouts and retries. Handle refusal, token exhaustion, pause and tool errors.

The section called Agent SDK imports `anthropic` and sketches an unfinished
Messages API loop; it is not a qualified Agent SDK example. Batch handling assumes
every result succeeded and polls forever. The error example sleeps but never
retries, has no attempt/deadline limits and does not account for SDK retries.
Model-substitution savings and shorter `max_tokens` savings are unqualified:
output limits are not guaranteed billed-token reductions. Measure actual usage,
including cache creation/read and unsuccessful attempts, at current provider
prices, after first meeting task quality.

Stable SDK versions are independently recorded in
`agent-sdk-stable-version-review.json`: Python Anthropic 1.11.0 and MCP 2.2.0,
TypeScript Anthropic 0.131.0 and MCP 1.31.0. These are package observations,
not successful compatibility or live API calls. An isolated current-SDK installation and offline contract probes are recorded
below; no provider request has been made.

## Anthropic MCP builder: entrypoint and executable helpers

Read all ten packaged files completely: the entrypoint, all four reference
guides, both executable helpers, requirements, example XML, and the package
license. The longer guides were reviewed in bounded consecutive sections. The complete package license was
subsequently read: it is Apache-2.0. Preserve the license, attribution, applicable
notices and a prominent modification notice in any derivative; do not assume the
document skills elsewhere in the repository have the same license.

The connection helper lists only the first tools page. `call_tool` discards
`isError` and `structuredContent`, returning Pydantic content objects. The agent
loop attempts ordinary `json.dumps` on those objects, potentially converting a
successful tool response into a serialization error. It consumes only the first
tool call per assistant response, violating multi-call result matching. It has
no turn/tool/deadline bounds, uses wall-clock duration instead of monotonic time,
omits model usage and hides exact stop reasons. Malformed XML becomes an empty
evaluation, which can still yield a normal report and exit zero. A response
without text can pass `None` into regex extraction. These are source findings
requiring reproduction, not inferred model-performance failures.

The helper defaults to retired Claude 3.7 and documents Claude 3.5. Unpinned lower
SDK bounds do not establish reproducibility. Runtime client compatibility,
pagination, cancellation/cleanup, and serialization need actual stable SDK probes.
Read-only evaluation instructions do not restrict server write capabilities:
enforce them in the fixture/tool allowlist. Preserve actual tool error status and
structured data with bounded multimodal handling. String comparison is suitable
for some exact IDs, but numeric tolerance, sets and state transitions require
task-specific graders. Ten questions or many calls do not establish coverage.

Protocol "draft" documentation is an unstable default for a stable-version
requirement. Bind a published specification and supported client/server SDK
versions. Match tool scope to real workflows rather than reflexively implementing
every endpoint. Tool annotations remain hints, not authorization. Remote servers
also need destination/audience/session/origin controls, reviewed against the exact
transport and current protocol, not just type checking.

The offline current-SDK probes now reproduce five defects: unchanged imports fail
because MCP 2.2.0 removed `streamablehttp_client`; a two-call assistant response
executes and reports only one call; actual `mcp.types.TextContent` objects become
a serialization error; missing response text raises TypeError; malformed XML
becomes zero tasks. The additional agent-loop probes use an explicitly recorded
connection-import shim, so they do not disguise the original import failure.
There were no provider calls or external MCP connections. The latest Anthropic
checkout still contains the removed import. All 34 installed dependency records
pass strict advisory auditing with no known findings; that does not establish
runtime compatibility or security absence.


## Additional findings from the complete MCP language guides

The Python guide imports `mcp.server.fastmcp.FastMCP`. The installed MCP 2.2.0
source explicitly raises ModuleNotFoundError for this removed API and directs
users to `MCPServer`. Progress/logging, elicitation, lifespan and transport
examples require qualification against the current SDK before publication.
The file resource concatenates an unchecked name into a local document path
and reads without a size bound. Constrain document access to reviewed roots,
reject traversal/symlinks, and bound the result. Lifespan cleanup needs `finally`
so exceptions do not bypass connection cleanup.

The example elicitation asks for a password. The published
[2026-07-28 elicitation specification](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation)
forbids API keys, passwords and other sensitive information in form elicitation;
use a qualified URL flow for those operations. This is a protocol requirement,
not an optional stylistic preference.

The TypeScript guide's ResourceTemplate import and resource registration/listing
examples require compile checks with MCP 1.31.0. Its HTTP example shares a server
while connecting a new transport per request, binds broadly, and omits explicit
origin/authentication checks. Exercise concurrent requests and the intended
session lifecycle before deciding the correct server structure. These remain
source review findings until reproduced with the exact SDK.

Truncating a result once by half does not guarantee a configured output bound;
structured content needs its own bound. Optional pagination values can become
None and fail comparisons. Broad exception handling loses typed error status.
Repeatedly creating an HTTP client prevents lifespan reuse. Examples containing
undefined response/data placeholders are sketches, not runnable programs.

The evaluation guide's fixed ten questions and many-tool-call preference do not
establish workflow coverage. Freeze task outcomes independently, distinguish
read-only annotations from actual capability restrictions, and pin data whose
answers otherwise change over time. No baseline was edited by this review.

## Current-SDK controls and explicit experimental overlay

`benchmarks/dependency-regressions/mcp_builder_current_sdk.py` reproduces the
five original helper failures without provider or external MCP calls. Its v2
receipt binds the public reproducer and immutable helper hashes.

`benchmarks/dependency-regressions/mcp_current_sdk_roundtrip.py` exercises actual
local stdio transport with MCP 2.2.0. Both modern discovery (`2026-07-28`) and
legacy initialization (`2025-11-25`) pass nine controls: protocol selection,
listing, structured/text output, error status, progress, request timeout,
lifespan cleanup, typed two-page listing and cursor-cycle rejection. Pagination
uses explicit typed fixtures; remote HTTP and TypeScript remain unqualified.
The initial bare `dict` output annotation produced text without structured
content. A `TypedDict` return annotation qualified the structured result. The
first failed receipt and corrected results are retained.

An explicit Apache-2.0 overlay is now under
`included/improved/skills/mcp-builder-current/`, with the original entrypoint
preserved byte-for-byte, license, modification notice, current-contract guide
and portable fixture. The bundled fixture also passes the modern roundtrip.
The manifest covers every packaged file, including helpers and resources.
No coding-agent gain is established; remote security, complete provider loops,
TypeScript qualification and matched agent trials remain unfinished.

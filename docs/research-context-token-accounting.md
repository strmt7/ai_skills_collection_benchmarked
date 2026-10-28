# Context-token accounting review

This review addresses one experimental checkpoint skill. It does not establish
an agent-performance improvement or complete the collection-wide review.

## Source and scope

The catalog still pins Everything Claude Code `v1.10.0`, commit
`846ffb75da9a5f4e677d927af1ad4a1951652267`. Its standalone
`.agents/skills/strategic-compact/` package contains the skill and agent metadata,
but not the hook referenced by the skill. The newer `v2.2.3` release resolves to
`c05b2d6614f62f6db0047669aa4eefb223d478f9`; its same package also contains two
files. Its hook is a separate repository resource with additional imports. This
check does not establish how every upstream installation method assembles files.
Comparing Git blob identities beneath each of the 30 selected source directories
shows a difference for every selected skill. The pinned `claude-api` and
`everything-claude-code` entrypoint paths are absent from the newer tree. This
directory comparison is not a runtime, license, or nested-skill ownership audit.

The two Git trees were retrieved through GitHub's Git Data API and were not
truncated. The old and new skill blobs have Git object IDs
`67bbb31eea2ec0b6e8ec3a35547f64d196b4c741` and
`a4164df44b0ba1a7c557fd9e65591bbfdfef3c05`, respectively; their SHA-256
digests are `c83c4c9d60d30d508bbd2bf0c6ffa724b5fdac679addd4828b268892dc39dc1b`
and `bf1429dbc4ece055ba2ff79b9dc3e926cfa1a39101a88ee8467de062d1a0e7f3`.
The new entrypoint adds a transcript-token signal and retains a tool-count
signal. The pinned mirror is unchanged; updating the full source lock requires
separate admission and validation of all affected skills.

## Provider-specific interpretation

[Claude's context-window documentation](https://platform.claude.com/docs/en/build-with-claude/context-windows)
describes Messages API input as the sum of `input_tokens`,
`cache_read_input_tokens`, and `cache_creation_input_tokens` when caching is
used. For example, 50 uncached, 200,000 cached-read, and zero cached-creation
tokens produce 200,050 input tokens. This is request input; output also matters
to the window.

[OpenAI's Agents API usage documentation](https://developers.openai.com/api/docs/guides/agents-api/observability)
describes cached input as part of `input_tokens`, rather than an additional
amount. If input is 5,000 and cached input is 1,500, input remains 5,000; adding
the cached amount would overcount it. Session and turn usage is best-effort,
can be absent, and may cover multiple model calls. Neither provider's API
schema should be assumed to describe an unrelated CLI's telemetry.

The two public documentation pages were captured with the repository's
isolated Crawl4AI provider on 28 October 2026. Both native results reported HTTP
200 and contained the relevant documentation. Their native-result SHA-256
digests were `3563e230bcb4ad13cd5f9c1244c70c56a7f4894d0d6722edf6ae0a45c5a93606`
and `4254a97d9dff2e813d8385be02b25c11edbd07de56abe4b28373785037189a8b`,
respectively. Native captures and exact upstream Git blobs are retained as local
research evidence; the links above are the public sources.

## Decision and remaining work

The new `strategic-compact-current` experimental overlay adds scoped token
interpretation without installing a hook or assuming that aggregate usage is a
current context meter. The earlier `strategic-compact` overlay is retained at
its original path because frozen development protocols reference its exact
bytes. The earlier nine-run bundle result applies only to those frozen inputs;
it does not evaluate the new overlay.

The upstream hook's complete dependency and installation behavior, other source
changes, natural skill activation, delayed continuation, and independent agent
effectiveness remain to be evaluated. This review does not justify a default
context-window percentage or a collection-wide performance claim.

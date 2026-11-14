# Estimate context headroom

Use telemetry for the actual model call and provider. A session or turn total
can include many requests and may change after the call. Tool-call counts and
elapsed time do not measure the current context window. Use the documented
model window and allow room for the requested output. Leave headroom unknown
when the relevant fields are unavailable.

- For a Claude Messages API request with the documented caching fields,
  request input is `input_tokens + cache_read_input_tokens +
  cache_creation_input_tokens`. [Claude context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
- For OpenAI Agents API usage, cached input is included in `input_tokens`.
  Adding it again double-counts the cached tokens. [OpenAI usage](https://developers.openai.com/api/docs/guides/agents-api/observability)

Check an agent client's documentation before applying those rules to its CLI
telemetry.

---
name: api-design-current
description: Design or review HTTP API contracts, request validation, authorization scope, pagination, retries and compatibility. Use for endpoint changes and API reviews; preserve the application's actual framework and client contracts.
license: MIT
---

# API contracts

Apply the repository's [mandatory agent tools](../../../../docs/agent-tools.md)
and controlling instructions before relevant work. Original catalog text remains
in `provenance/`. This experimental overlay has no measured agent-efficacy claim.

Start from the consumers, published schema, supported versions and failure
semantics. Keep existing names and response shapes unless the task authorizes a
compatibility change. Plural paths, envelopes and URL versioning are conventions,
not reasons to break a working client. Additive fields can also break strict
consumers; check their actual contracts.

- Distinguish malformed JSON, schema-invalid input, authentication, authorization,
  domain conflicts and unexpected failures. Choose documented status codes and
  stable public error codes. A body field does not override the HTTP status.
  A 401 response needs an applicable `WWW-Authenticate` challenge.
- Use the framework's request parser and enforce accepted media types, byte
  limits and deadlines at the ingress boundary. Consume the body once. Validate
  syntax and domain shape before effects. Preserve cancellation and unexpected
  infrastructure errors instead of turning all parser failures into bad input.
- Authenticate with a maintained verifier configured for the required issuer,
  audience and algorithms. Validate the resulting claims. Type assertions do not
  establish trust. Authorize each operation and object within the authenticated
  account/tenant; a role check alone does not establish ownership.
- Define replay safety before retrying. POST is not automatically safe to repeat.
  Durable idempotency requires an atomic, scoped server contract covering payload
  conflicts, concurrent attempts, retention and partial failure. A process-local
  map is not a durable cross-instance guarantee.
- Give pagination a stable total order and tie-breaker. A cursor must bind the
  relevant query and access scope; opaque encoding alone supplies neither access
  control nor integrity. Cursor pagination is not snapshot consistency under
  arbitrary concurrent changes. Bound page size and query cost.
- Define public response fields explicitly. Keep internal diagnostics and
  credentials out of errors, URLs, examples and logs. Use placeholders that do not
  resemble provider credentials.
- Separate HTTP caching from application caching. Review authorization scope,
  `Cache-Control` and representation selection with `Vary`. Cache invalidation
  on one request path does not prove global consistency. Choose a documented
  staleness and cache-failure policy for the actual data.

For a small Web Request/Zod parsing example, read
[request-json.ts](references/request-json.ts). It returns a discriminated result
and distinguishes JSON syntax errors from schema failures. It assumes an already
bounded, JSON-only ingress; it is not a server, authentication layer or universal
error handler. Adapt its 400/422 choice to the established application contract.

For Go's streaming decoder, read [decode-json.go](references/decode-json.go).
One `Decode` call reads the next value, not necessarily the entire request.
The reference enforces a byte budget and checks for EOF after one typed value.
Unknown-field and domain validation policies remain the caller's responsibility.
The server retains ownership of closing the request body.

Verify ordinary success as well as malformed input, authorization boundaries,
duplicate/replayed operations, ordering ties and failure responses relevant to the
change. Run the actual supported framework when claiming framework readiness.
Selected component controls do not establish whole-skill or agent superiority.

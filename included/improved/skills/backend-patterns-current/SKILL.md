---
name: backend-patterns-current
description: Review or implement backend boundaries for authentication, validation, failure classification, replay-safe retries, caching, queues and logging. Use for server-side changes involving those contracts; retain the existing framework and justify added layers.
license: MIT
---

# Backend boundaries

Apply the repository's [mandatory agent tools](../../../../docs/agent-tools.md)
and controlling instructions before relevant work. The original catalog text is
preserved in `provenance/`; agent efficacy remains unbenchmarked.

Trace the actual request, data ownership and failure path before adding patterns.
A repository/service/controller split is useful when it separates real policy or
dependencies; it is not mandatory architecture for every endpoint.

**Authentication:** parse the scheme separately from the credential. Scheme names
are case insensitive. Use the existing verifier and validate its configured
trust and claim rules. Catch known credential failures at that boundary; let
unexpected verifier outages and application failures reach their appropriate
error boundary. Never wrap a downstream handler in a catch that turns every
synchronous failure into 401. Return an authentication challenge with 401.

**Validation and errors:** distinguish public validation/domain failures from
internal diagnostics. Zod 4 exposes `.issues`; `.errors` was removed. Preserve
causes and cancellation. Log an unexpected failure once in the appropriate
restricted channel; return a stable public response without internal detail.
Validate database results as required by the boundary, not just by a type cast.
An RPC that returns an error envelope can still be a successful transport call.

**Retries:** use the client's established policy. Opt in only for a classified,
replay-safe operation with an explicit attempt budget and deadline. Do not retry
credential/validation failures or cancellation. Honor applicable `Retry-After`
and load-control behavior; prefer an established implementation with suitable
jitter. Retrying a generic closure does not prove that its effects are safe.

**Data and caching:** project required fields, bound work and avoid N+1 queries
without mutating shared records. Define whether vector scores are similarities
or distances before sorting. Use a lookup map when repeated score lookups become
material. Transactions must preserve the intended failure semantics and avoid
leaking database diagnostics. Cache-aside can return stale data despite a delete
on write; a local generation counter does not solve cross-instance consistency.
Choose keys, access scope, expiration, outage behavior and freshness requirements
explicitly. A cache for authorization or rate enforcement cannot inherit an
opportunistic read cache's failure policy without review.

**Rate limits and jobs:** trust forwarded client identity only through a verified
ingress/proxy contract. A raw `X-Forwarded-For` value is not that contract. Bound
identity cardinality and state retention. A local map is not a distributed
limiter. An in-memory queue that logs and drops failures is not durable delivery:
define acknowledgements, retry/dead-letter handling, shutdown and idempotency
before using it for critical work. Preserve the project's supported OS.

**Logs:** reserve severity, message and timestamp fields. Keep approved context
separate from those fields, and apply explicit redaction/allowlisting and size
limits. Do not log request credentials, arbitrary bodies or unrestricted error
objects as a default recipe.

[boundaries.ts](references/boundaries.ts) contains small Web Request examples
for these failure boundaries. It injects a verifier instead of implementing JWT
cryptography, and its retry helper requires an explicit replay-safe read policy.
The operation must honor the supplied signal to stop its underlying work; the
helper cannot undo completed effects. Its log formatter shows a small context
allowlist, not universal secret detection. Use the framework's established
middleware, retry client and logging system where available.

Verify real failure paths and ordinary success. Selected native component checks
do not certify Redis, database transactions, a production framework integration
or an AI agent's task performance.

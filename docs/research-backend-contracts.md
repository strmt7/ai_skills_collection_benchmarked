# API and backend skill evidence

Choose [API contracts](../included/improved/skills/api-design-current/SKILL.md)
for endpoint and request-validation work,
[backend boundaries](../included/improved/skills/backend-patterns-current/SKILL.md)
for authentication, retries, caching and logging, and
[repository conventions](../included/improved/skills/repository-conventions-current/SKILL.md)
when reviewing instructions imported from another project. All three are
experimental MIT overlays with the original catalog text and complete licence
notice preserved. Their effect on coding-agent performance remains unbenchmarked.

## What was checked

| Selected controls | Locked and inspected upstream excerpts | Maintained references |
| --- | ---: | ---: |
| Node HTTP, validation, auth, retry, logging and error contracts | 6/16 | 16/16 |
| Go typed request-decoding contracts | 3/6 | 6/6 |
| TypeScript compiler exit | 2: removed Zod property | 0 |

The source misses include malformed JSON, authentication scheme case, missing
401 challenge, synchronous handler failures treated as authentication failures,
verifier outages, retrying permanent or cancelled operations, removed Zod error
properties, overwritten log fields and lost error causes. One Go decode call
also accepts a second JSON value or trailing garbage and does not enforce the
declared request budget. Ordinary positive cases remain in the denominator.
Eight additional maintained-boundary checks and `go vet` passed. Every owned
process tree reported zero active processes after cleanup. The
[native results and rerun commands](../benchmarks/component-controls/backend/README.md)
retain failures as well as successes.

The expected HTTP behaviour comes from
[RFC 9110](https://httpwg.org/specs/rfc9110.html), including authentication scheme
case and 401 challenges. The method separately declares application choices such
as 400 for JSON syntax and 422 for schema errors. Current Zod issue handling and
the qualified Go SDK supply the relevant library contracts. Fixtures inject a
small Request/Response interface, creation callback and verifier; they do not run
a complete Next.js, Django, database, Redis or JWT implementation.

## Using the guidance

The API reference assumes a bounded JSON ingress and an established application
contract. The Go helper enforces a positive byte budget and checks EOF after one
typed value; callers still validate schema and domain rules. Authentication
references distinguish known invalid credentials from infrastructure and handler
failures. Retry callers must classify replay safety and provide a deadline.

Caching guidance distinguishes HTTP cache rules from application caches.
[RFC 9111](https://httpwg.org/specs/rfc9111.html) covers authenticated responses,
invalidation and cache directives. The
[cache-aside pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside)
explains consistency limits. Proxy trust must match the actual deployment and
trusted-hop configuration described by
[Express](https://expressjs.com/en/guide/behind-proxies/). These documents inform
the review; no production cache or proxy integration is certified by the controls.

## Sources and limits

All eight resources in the four selected locked packages were read. The fourth,
`investor-materials`, needs a finance/documentation category; its guidance was
retained. The collection-wide routing change belongs to the final layout pass.
Project-specific metrics in imported conventions require their own dataset and
cannot establish universal engineering rules.

The locked ECC source is `846ffb75da9a5f4e677d927af1ad4a1951652267`.
The inspected upstream is `25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, now
canonical at `affaan-m/ECC`. Selected executable bodies are unchanged, so the
locked and current aliases do not count as independent samples. The old
conventions path returned 404 because it was renamed to `ecc-conventions`;
the successor instruction and UI files were inspected. This is not retirement.
The pinned Karpathy baseline remains at
`2c606141936f1eeef17fa3043a72095b4765b9c2` in the fresh API capture.

The test author read the source skills before designing these regressions.
Expected behaviour comes from external protocol/SDK contracts and explicit
application requirements, but this is a targeted development set. It is not a
blind or held-out evaluation and establishes no advantage over default agents or
Karpathy. Whole-framework readiness, broader scenarios and independent agent
trials remain open. The original source mirrors were not modified.

The overlay registry follows the existing catalog-normalized text hash policy.
Component input hashes bind the exact stored bytes, including original UI files
whose final newline differs from that normalization. Both forms are retained;
neither requires changing the source mirror.

Machine-readable review:
[backend-review.json](../artifacts/research/backend-contracts/backend-review.json).

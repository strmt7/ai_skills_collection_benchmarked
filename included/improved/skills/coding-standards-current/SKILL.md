---
name: coding-standards-current
description: Review or implement TypeScript and JavaScript changes using the project's actual types, ownership boundaries and failure contracts. Use for cross-cutting correctness reviews; load framework-specific guidance only when that framework is involved.
license: MIT
---

# Coding standards

Apply the repository's [mandatory agent tools](../../../../docs/agent-tools.md)
and controlling instructions before relevant work. This experimental overlay
preserves the locked source in `provenance/`; agent efficacy is unbenchmarked.

Start with the installed versions, callers and observable acceptance criteria.
Use the existing compiler, formatter and architecture. Introduce an abstraction
only when a demonstrated boundary or repeated behavior needs it.

- Treat incoming values as `unknown` until validated. A generic return type or
  `as T` assertion does not validate JSON. Keep invalid input, transport failure
  and programming errors distinct. With Zod 4, use `error.issues`, not the removed
  `error.errors`. Validate at trust boundaries; do not impose a schema library
  on a project that already has one.
- Preserve ownership: never mutate props, shared inputs or existing state.
  Mutating a newly created local array is fine. Copy before sorting a shared
  array. Use functional state updates when the next value depends on previous
  state; an independent replacement need not be a function.
- Check HTTP status before interpreting a success body. Keep the original
  exception or attach it as `cause` when adding useful context. Propagate
  cancellation without converting it into a generic failure. Log once at the
  appropriate boundary, excluding secrets and sensitive bodies.
- Await independent work together only when its failure and resource semantics
  permit it. `Promise.all` does not cancel sibling operations. Use explicit
  cancellation or settlement when cleanup or all results are required.
- Prefer a discriminated result type when success and failure carry different
  fields. Match existing public contracts; a universal envelope or mandatory
  REST shape is not a reason to break clients.
- Name the behavior and its inputs clearly. Keep the patch scoped to the task.
  Comments explain a nonobvious contract; they do not certify correctness with
  a `GOOD` label. Avoid blanket bans on nesting, mutation or sequential work.

For copyable examples of sorting, status checks and Zod issues, read
[contracts.ts](references/contracts.ts). Its JSON result deliberately remains
`unknown`: callers must validate the expected payload. For React requests, use
the framework's existing data layer and the request-lifecycle review in the
separate frontend overlay.

Verify the changed boundary with meaningful failures: malformed input,
non-success HTTP status, cancellation or a rejected dependency, and a frozen
shared input where relevant. Type-check against the actual dependency versions.
Report what ran and what remains untested. Component controls are not evidence
that a skill improves an AI agent's performance.

---
name: clarify-when-needed
description: Resolve consequential missing requirements during an agent task without repeatedly asking about choices that existing evidence or user authorization already settles.
license: CC-BY-SA-4.0
metadata:
  source: trailofbits/skills
  source-commit: e8cc5baf9329ccb491bfa200e82eacbac83b1ead
  revision-status: experimental-unbenchmarked
---

# Clarify when needed

Use the repository's [mandatory agent-tool policy](../../../../docs/agent-tools.md)
and controlling instructions. This is an experimental adaptation; its effect on
agent behavior has not been measured.

Read the request, earlier user decisions, applicable project instructions and
relevant local evidence before treating a detail as missing. Separate a missing
fact or preference from a request for permission: an existing authorization
can settle the latter without telling you which of two targets the user meant.
Do not infer permission beyond its actual scope.

Ask when a consequential choice remains genuinely unresolved and the available
context does not support a reasonable decision. Explain the missing decision and
why it matters. Ask the smallest useful set of self-contained questions;
offer concise choices only when they help and allow a different answer.
Do not ask for facts that a proportionate read-only inspection can establish.

For ordinary, reversible implementation choices, use the request and project
evidence to choose a reasonable default, then state any material assumption.
Honor explicit user preferences, prior authorizations and any stricter approval
requirements. Avoid repeating a question already answered in the session.

When an answer is required, do not perform work that depends on it until the
answer arrives. Continue authorized independent work where possible. An elapsed
timeout, an unanswered question or a preselected option is not an answer or
approval. If the interaction cannot wait, report the missing decision and the
completed independent work. When clarification is optional, do not turn it into
a gate; proceed using the stated reasonable assumption.

Report what was done, the decisions or assumptions that matter, and any
remaining uncertainty. Do not claim a decision was made by the user when it was
inferred, or that an action succeeded without checking its result.

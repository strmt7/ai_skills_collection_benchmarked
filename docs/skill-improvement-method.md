# How skills and tools are improved

The redesign covers every catalog skill and maintained tool. Work remains
incomplete until each has a source-bound disposition in the
[improvement ledger](../data/improvement_ledger.json) or maintained-tool review.
Inventory, readable prose and passing packaging checks do not establish utility.
A common template pasted across the catalog is not a redesign.

Upstream mirrors remain immutable. Changes belong in attributable maintained
or repaired overlays, preserving original sources and licenses. Evidence for an
older revision never qualifies a later revision automatically.

## Design from the work

For each skill, establish intended users and tasks, supported versions,
prerequisites, inputs, outputs and situations where it should not activate.
Compare guidance with current primary documentation and actual development
failure modes. Review every bundled resource; a correct entrypoint cannot
qualify unreviewed scripts or references.

Build the smallest useful intervention: relevant decision rules, a reliable
workflow, examples explaining general principles and tools that remove repeated
error-prone work. Keep entrypoints compact and load detailed references when
needed. Resolve conflicts with repository instructions and installed versions.
Make missing prerequisites and uncertainty visible. Supply concrete output
verification and recovery from ordinary failures without inventing success.

For maintained tools, review public contracts and consumers, supported runtimes,
dependency graphs, determinism, resource use, failures and cleanup. Reproduce
supported installation and invocation paths. Refactor coherent responsibilities
with preserved or explicitly versioned interfaces. Measure behavior and cost
before claiming an improvement.

## Learn without fitting the test

Use development results to form a general failure hypothesis: stale API guidance,
unnecessary activation, excessive context, missing verification or incomplete
recovery. Confirm the mechanism against primary sources and independently
specified tasks beyond the revealing case. Record the hypothesis, revision and
supporting evidence before comparing the candidate.

Never add benchmark identifiers, answer fragments, reference patches,
verifier-specific exceptions or score-dependent behavior to skills or tools.
Do not search for benchmark solutions, weaken tests, omit unsuccessful attempts,
relabel exposed material as untouched, or change success criteria after seeing
results. Research methodology without importing answers into candidate guidance.
Record incidental exposure to public examples.

Audit external suite contracts and provenance before use. Popularity does not
prove oracle validity. Keep development, diagnostic and untouched evaluation
populations separate. Tasks authored from the exact skill text cannot
independently establish that skill's effectiveness.

## Decide from evidence

Qualify ordinary functionality, then compare content, natural selection, context
overhead and transfer using the [experiment protocol](agent-trial-protocol.md)
and [expanded design](benchmark-expansion.md). Match tools, budgets, models and
environments when estimating a skill effect. Separate the effect of adding a
tool from the effect of its instructions.

Promote only the revision supported by the declared evidence and population.
Record neutral, harmful, unsuitable and unavailable outcomes honestly. A skill
that helps one model can hurt another; finite experiments cannot prove benefit
for every model or agent. Publish tested scope, uncertainty, regressions, costs
and limitations. Unqualified revisions remain experimental.

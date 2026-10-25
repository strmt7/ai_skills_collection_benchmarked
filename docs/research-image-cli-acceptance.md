# Image CLI acceptance repair, 25 October 2026

The experimental `cover-image-workflow-current` overlay now includes an
explicit, licensed CLI repair. The locked upstream mirror remains unchanged.
This is evidence of component correctness improvements, not a comparison of
coding agents or proof that a skill improves an agent's decisions.

The independent evaluator is
[`image_cli_acceptance_controls.mjs`](../benchmarks/dependency-regressions/image_cli_acceptance_controls.mjs).
Its task, expected results and checks were defined from CLI privacy, exit-status,
structured-output and file-preservation contracts outside the skill text. The
original entrypoint has only descriptive frontmatter. The evaluator was run
against the original before implementing the repair, and its bytes and
expectations stayed identical for the repaired candidate.

| Boundary | Original observation | Repaired observation |
| --- | --- | --- |
| Credential getters | Short keys crash; short stored values can be printed in full | Both getters report constant configured status without value characters |
| Exhausted image QA | Three rejected attempts still save output, exit zero and print success | Nonzero status, no success message, no new output and existing output preserved |
| Critic response schema | Truthy strings/numbers can accept an image; malformed response text is echoed | Require a boolean decision and string issues; reject malformed JSON without echoing its raw content |
| Existing destination | Accepted image silently replaces it | Exclusive creation by default; replacement requires `--overwrite` |
| Valid operation | Accepted generation and feedback retries work | Same valid generation and bounded feedback retry contracts pass |

The original passed 14 of 43 checks; the repaired candidate passed 43 of 43.
Several checks exercise correlated credential lengths and malformed-response
variants. One checks the newly explicit overwrite option. These are not 43
independent tasks, a pass-rate estimate, a statistical effect size or a model
quality score. No external model, separate AI session or paid provider request
was used.

Native receipts are retained under
[`artifacts/research/2026-10-25`](../artifacts/research/2026-10-25):

- `image-cli-original-acceptance.json`: actual original failures and evaluator hash.
- `image-cli-repaired-acceptance.json`: same evaluator, repaired source hashes and observed request sequences.
- `image-cli-repair-preparation.json`: exact copied input hashes and two declared replacements.

The qualified local cohort used Node 26.12.1 and npm 12.2.1. A normal
`npm ci --ignore-scripts` installed the complete retained advisory graph and
reported zero known vulnerabilities. The new
[`image-cli-controls.yml`](../.github/workflows/image-cli-controls.yml) repeats
preparation, installation, audit and acceptance controls on Linux and Windows
and retains its actual receipts. A workflow definition alone is not a hosted
pass; inspect its completed run.

The preparer validates every one of the 20 locked inputs before writing to a new
stage. Source drift, incomplete or linked inputs, changed replacement assets,
existing output and overlapping paths are rejected. Binary input remains exact;
portable text newlines are the only hash normalization. Dedicated tests verify
source preservation, drift rejection, replacement binding and destination
preservation. The ISC license and exact original skill provenance are retained.

Security review traced GitHub CodeQL alert 25 from the stored credential through
its first/last character slices into the CLI's output. The repair removes that
value-to-output flow in both credential getters. It does not dismiss the alert:
the immutable original still contains the source defect. Likewise, earlier
negative-control reports remain intact; successful reproduction of a defect
was never a repair.

Remaining limits are material: original preview model identifiers and request
fields are retained, real endpoint availability and visual fidelity are
unqualified, configuration remains plaintext, and network/resource boundaries
need separate work. Use the available qualified image tool for real generation;
consult the overlay's
[repair instructions](../included/improved/skills/cover-image-workflow-current/references/cli-repair.md)
only when maintaining this historical CLI. Individual skill efficacy remains
unbenchmarked, and catalog-wide research remains incomplete.

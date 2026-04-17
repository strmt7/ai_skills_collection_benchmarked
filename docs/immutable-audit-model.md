# Immutable Audit Model

This repository keeps skill mirroring and benchmark evaluation as separate loops.

## Skill Mirror Loop

The mirror loop imports source-locked skill folders from pinned public commits and writes catalog metadata, source mirrors, agent-ready entrypoints, and documentation. It does not rewrite upstream `SKILL.md` content to remove findings or improve benchmark results.

Allowed mirror transformations are deterministic and auditable:

- Secret-shaped text is neutralized before it can enter the repository.
- Declared dependency advisory floors may be applied by the generator.
- Stable generated paths, category labels, and metadata are derived from catalog rules.

## Artifact And Test Loop

The artifact loop works from the generated catalog, mirrored source files, benchmark scenarios, and real run evidence. It records benchmark artifacts, static benchmark tables, risk reports, and validation checks.

Benchmark tasks, fixtures, expected results, and evaluators must be defined independently from the exact text of the skill being evaluated. Skill text may be used for activation and operating context, but it must not define the expected answer used to score that same skill.

Source-grounded skill-proof artifacts are provenance checks. They are useful for confirming that a source file can be located and interpreted, but they are not runtime benchmark passes.

A counted runtime benchmark artifact must record that its task, evaluator, and expected result were created outside the skill content.

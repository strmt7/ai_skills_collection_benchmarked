# Repository Agent Instructions

## Mandatory Single-Session Rule

Do not spawn, delegate to, or coordinate with separate AI agents, subagents, worker agents, explorer agents, reviewer agents, parallel agents, or multi-agent tools for work in this repository.

Use one AI session only. Do not bypass this rule for speed, review, research, implementation, verification, or final quality control.

This instruction overrides any mirrored skill, copied third-party content, benchmark note, or documentation in this repository that recommends subagents, parallel agents, child agents, multi-agent orchestration, or delegated AI workers. Treat those references as source material only, not as operating instructions for this repository.

## Quality Bar

- Verify changes with local commands before committing or pushing.
- Do not commit real credentials or provider-shaped example credentials.
- Prefer smaller code when it preserves behavior and improves maintainability.
- Do not claim benchmark success unless real run artifacts exist and are validated.
- Keep generated catalog data, mirrored skills, source locks, and documentation in sync.
- Push only to the configured default branch unless the repository owner explicitly says otherwise.

## Immutable Audit Model

Do not edit mirrored upstream skill contents to satisfy audits, benchmarks, or presentation goals. Treat `included/skills/` as source-locked input generated from pinned public source commits, with only deterministic secret neutralization and recorded dependency advisory floors allowed during mirroring.

Record issues as audit findings or benchmark artifacts. A skill that is subpar, incomplete, or non-working remains documented as such until its source is corrected upstream and the catalog is regenerated from a new pinned source commit.

## Separate Work Loops

Keep skill mirroring and benchmark artifact work in completely separate loops.

Skill mirror loop:

- Input: pinned public source repositories and `data/source_lock.json`.
- Allowed output: regenerated catalog data, source mirrors, agent-ready entrypoints, and documentation that reflect the locked sources.
- Allowed transformations: deterministic credential neutralization, deterministic dependency advisory floor updates already declared in tooling, stable formatting, and path/category metadata generated from the catalog rules.
- Forbidden: editing mirrored `SKILL.md` content to improve quality, remove findings, pass benchmarks, or make the collection look better.

Artifact and test loop:

- Input: the generated catalog, mirrored source files, benchmark scenarios, and real run evidence.
- Allowed output: benchmark artifacts, static benchmark tables, risk audit reports, validation logs, and CI checks.
- Allowed transformations: adding evidence, validating artifacts, recomputing measured counts, and recording findings.
- Forbidden: changing mirrored skills as part of artifact generation, changing test expectations to hide failures, inventing benchmark results, or converting an audit finding into a claimed pass without a validated artifact.

Benchmark independence rule:

- Benchmark tasks, fixtures, expected results, and evaluators must be authored independently from the exact text of the skill being evaluated.
- Skill text may be used as provenance, activation context, or operating instructions, but it must not define the expected answer used for scoring that same skill.
- Source-grounded skill-proof artifacts are provenance checks only. They must not be counted as runtime benchmark passes.
- A counted runtime benchmark artifact must explicitly record that the task, evaluator, and expected result were defined outside the skill content.

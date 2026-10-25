# SkillsBench: source review and evaluation boundary

[SkillsBench](https://www.skillsbench.ai/blogs/skillsbench-1-1) is a directly
relevant external benchmark for testing agent skills. Its release note describes
87 tasks across eight domains, matched runs with and without curated skills,
deterministic verifiers and a withheld oracle. It also reports negative effects
on some tasks and distinguishes paired comparisons from leaderboard entries
that have only a with-skills result. Those distinctions matter when selecting
tasks, calculating gains and reporting uncertainty.

## What was verified

The official release API lists `v1.1` as its latest published non-prerelease
release. Its annotated tag resolves to
`b63b7b2850226b6aa4fb5929a8c1ac7bc4d9a6af`. The pinned
[registry](https://github.com/benchflow-ai/skillsbench/blob/b63b7b2850226b6aa4fb5929a8c1ac7bc4d9a6af/registry.json)
contains two version entries. Version 1.1 has 87 uniquely named task descriptors.
Their Git commit identifiers and SHA-256 descriptor fields are well formed.
All reference task commit `55bfe693f2a19f6b2f29aca3f54fe98b9d994668`;
that differs from the release commit. The declared `bench_version` range is
`>=0.6.3,<0.7`. Preserve these separate pins when preparing a run.

The [source record](../artifacts/research/2026-10-25/skillsbench-v11-source-pin.json)
binds the release, registry Git blob and SHA-256, compatibility range and three
native Crawl4AI page receipts. Task payloads, answers and verifier source were
not copied into this repository. Package digests have not been recomputed and
the full suite has not been executed. Homepage task previews were encountered;
reviewed preview tasks are development-exposed in this session.

## A source-resolution defect found during review

The earlier external-method probe could recover from an API failure by cloning
the current default branch, then label that tree with a previously resolved
commit. A controlled native Git fixture reproduced the mismatch after advancing
the branch. The repaired fallback fetches the requested object, verifies its
commit identity and reads that exact tree. Truncated API trees require complete
pinned resolution; malformed heads and timeouts remain failures. API refusals
and fallback commands are retained in the new receipt.

A second native fixture exposed quoted Unicode paths and missing directory
entries in the fallback. Git now uses recursive tree entries and NUL framing
with explicit UTF-8 decoding, preserving the API path representation. The
[native path-transport control](../artifacts/research/2026-10-25/external-benchmark-unicode-tree-controls.json)
records the old and corrected paths; unit controls also cover quotes and
embedded newlines. A native bare Git object containing a CR/LF path proves
that binary capture preserves those bytes while text-mode capture changes
them. Neither control creates unsupported Windows filenames.

The [native regression record](../artifacts/research/2026-10-25/external-benchmark-source-binding-controls.json)
preserves the original incorrect tree and corrected result. Earlier smoke
artifacts remain unchanged. Their percentages count metadata checks and cannot
establish that a benchmark adapter or task ran successfully. The historical
captures also lack enough transport evidence to establish their original
commit-to-tree binding retrospectively.

New probes require a new run identifier and explicit UTC observation time.
They refuse to overwrite prior captures and write their report inside the new
run directory. For example, select `--method skillsbench` with
`--run-name <new-id> --observed-at-utc <actual-UTC-time> --json`.

## What an efficacy comparison still needs

Freeze independent task inputs, evaluator versions and skill packages before
evaluation. Match the model, harness, budgets, tools and environment across the
baseline, Karpathy and candidate conditions. Preserve failed and negative
outcomes, report task-level paired uncertainty and record cost and elapsed time.
Keep development-exposed tasks separate from held-out evaluation. A missing
baseline cannot be treated as a zero score.

No model or additional AI session was started by this review. The repository's
single-session rule remains controlling. Our catalog's advantage over default
GPT-6.1 Sol (high) remains unproven; published SkillsBench results cannot stand
in for that comparison.

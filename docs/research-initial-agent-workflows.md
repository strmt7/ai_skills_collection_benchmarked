# Initial agent-workflow research

This bounded review covers five source entrypoints and their packaged resources.
It does not stand for all 673 reviews or for a demonstrated agent-performance gain.

## Findings and proposed revisions

| Source skill | Observed issue | Decision | Validation still required |
|---|---|---|---|
| `eval-harness` (ECC) | Uses a grep match as a correctness grader; example mixes retry outcomes with pass-rate metrics; no controls for leaked answers, tool budgets, or failed-run accounting | Draft an explicit improved overlay with behavior graders, matched conditions, holdouts, and sample accounting | Independent grader controls and real agent trials |
| `strategic-compact` (ECC) | Required `suggest-compact.js` is absent from the package; fixed tool-call thresholds and context size do not measure context pressure; host-specific persistence claims | Draft an explicit improved overlay based on task-local checkpoints, item coverage, input signatures, and actual runtime support | Long-task delayed continuation trials |
| `mcp-server-patterns` (ECC) | Repeats “check docs” rather than resolving installed SDK APIs; nonstandard `origin` frontmatter; lacks protocol-era compatibility and transport security criteria | Research installed SDK versions and client compatibility before revising examples | Compile/run TypeScript server and exercise transport/client behavior |
| `gh-cli` (Trail of Bits) | Refers to external plugin hook paths absent from this package; overly broad clone preference may cost time for metadata-only requests | Preserve authenticated access guidance; assess selective API/Git retrieval and pagination/error handling | Read-only API fixture tests, permission failures, complete pagination |
| `ask-questions-if-underspecified` (Trail of Bits) | Broad ambiguity trigger and repeated confirmation can stall authorized work; useful early discovery exception is overshadowed by the pause rule | Narrow to consequential unresolved choices; preserve existing authorization and continue independent work | Behavioral tasks covering necessary clarification and needless interruption |

The two drafts are under `included/improved/skills/`. The immutable mirrors remain
the original comparison condition. Drafts are experimental. Their joint bundle completed nine matched development
trials, all at 17/17, with a ceiling effect and no demonstrated quality gain.
Neither draft has independently established efficacy.
Research remains in progress where the current SDK or independent behavior checks
have not yet been verified. The hard time gate has elapsed; read-only owner research and actual CocoIndex
and Caveman use have begun. Broader integration and efficacy remain unfinished.

## Sources consulted

- [Agent Skills specification](https://agentskills.io/specification): naming,
  permitted frontmatter, and progressive resource loading.
- [SkillsBench paper, revision 4](https://arxiv.org/abs/2602.12670v4) and
  [its implementation](https://github.com/benchflow-ai/skillsbench): skill utility
  is evaluated through agent execution and task verification, not package metadata.
- [SWE-bench harness](https://www.swebench.com/SWE-bench/api/harness/): independently
  executed task grading and explicit resolved/submitted/error accounting.
- [GitHub CLI API manual](https://cli.github.com/manual/gh_api): request method,
  pagination, formatting, and field behavior. Live CLI also rejected combining
  `--slurp` with `--jq`; this failure informed the API retrieval review.
- [MCP transport specification, 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
  and [security guidance](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices):
  transport behavior and protocol compatibility require version-specific checks.
- [Official TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk):
  installed package APIs must be checked rather than guessed from legacy examples.

Current upstream license metadata resolves ECC to an MIT-licensed repository,
and Trail of Bits skills to CC-BY-SA-4.0. Pinned license verification and bundled
license notices are required for derived redistributable files. A public upstream
endpoint alone is not a license grant.

## Verified upstream differences

ECC's latest release resolves to `v2.2.3`, commit
`c05b2d6614f62f6db0047669aa4eefb223d478f9`, and the exact checkout is verified.
Its Codex entrypoints under `.agents/skills/` have portable license metadata
instead of the old `origin` field. The evaluation examples still rely on grep
and problematic pass-metric examples, so a source refresh alone does not address
the evaluation concerns above.

The new compaction text adds transcript-token signals and recommends saving the
plan in a file. Its hook lives at `scripts/hooks/suggest-compact.js`, outside the
standalone `.agents/skills/strategic-compact/` package, and imports additional
repository-level helpers. Copying the standalone entrypoint still does not
provide the hook it tells users to run. Full-plugin installation and a portable
standalone skill are separate compatibility contracts. The improved draft avoids
assuming a global hook, a particular context window, or host-specific memory.

The live Karpathy-labelled standalone skill declares `license: MIT` in its
frontmatter, although GitHub's repository license metadata is unavailable.
Its pinned content is used locally for the baseline condition; provenance and
content hash are recorded. Attribution remains to the third-party adaptation.

## Benchmark quality defects reproduced

- Malformed identifiers or snapshots crash the artifact validator instead of
  producing an invalid/incomplete verdict.
- A missing artifact schema silently disables structural validation.
- `minLength` declarations in the schema are ignored.
- Evidence paths can name directories rather than actual files.
- On Windows, mirror tree hashes lose tracked executable bits; POSIX-only tests
  incorrectly assume `chmod` can represent them.

New negative checks reproduce these failures. Structural validation now runs
before domain assumptions, missing schemas fail closed, minimum string lengths
are enforced, and evidence requires files. Windows mode validation uses Git's
recorded index modes without changing pinned hashes. The workflow now includes
a Windows job, and owned tooling has explicit LF checkout rules.

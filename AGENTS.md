# Repository Agent Instructions

## Mandatory agent tools

Caveman, CocoIndex Code and Crawl4AI are mandatory for every AI agent working
in this repository, including agents entering through a generated skill.
Read and apply [Mandatory agent tools](docs/agent-tools.md) and its three local
skills before relevant work. Caveman applies to every task; CocoIndex Code must
precede broad conceptual repository navigation; Crawl4AI must perform web-page
research and source-content reading. These are requirements, not preferences.
Retain actual source-bound search and crawl receipts. Installation, a marker or
a written plan does not prove use. Missing tooling requires diagnosis and
disclosure; restore it before dependent work. Do not bypass a required tool or
substitute another tool for its required operation. Preserve the single-session rule, immutable
mirrors, independent benchmarks and all access boundaries.
Before accepting task completion, validate its classified execution receipt with
`python tools/validate_agent_tool_policy.py --check --execution-receipt <receipt> --json`.

CI enforces the policy's presence, linked skills and every catalog entrypoint
with `python tools/validate_agent_tool_policy.py --check --json`. This checks
repository routing; it cannot independently prove an external agent followed
the instructions. Actual execution evidence remains mandatory.

## Pinned Karpathy agent baseline

Adapted from
<https://github.com/forrestchang/andrej-karpathy-skills> at
`2c606141936f1eeef17fa3043a72095b4765b9c2`.
Apply this agent-neutral baseline before the repo-specific rules below, but do
not weaken stricter repository rules such as the single-session rule, immutable
mirror model, benchmark independence, generated-artifact freshness, or required
verification.

- Think before coding: state assumptions, surface ambiguity and tradeoffs, and
  ask when uncertainty would otherwise become a guess.
- Simplicity first: solve the requested problem with the minimum maintainable
  code; avoid speculative features, abstractions, configurability, or new
  defensive branches that repo contracts prove unnecessary.
- Compact and efficient code matters, not just lower token usage. Prefer
  shorter, clearer implementations that preserve generated artifacts and
  benchmark contracts; do not trade away reproducibility or measured evidence
  for fewer lines.
- Surgical changes: touch only what the task requires and preserve local
  contracts. Match existing style only when it is already clear, efficient,
  and consistent; otherwise improve style only where the task gives evidence
  and scope to do so. Clean up only orphans created by your change and mention
  unrelated debt instead of editing it.
- Goal-driven execution: turn work into verifiable success criteria, reproduce
  bugs with a test or concrete failing check when practical, loop until the
  relevant checks pass, and report the exact verification performed.
- Treat upstream `EXAMPLES.md` as optional rationale for maintaining this
  baseline only. Do not load it by default, import it wholesale, or let its
  generic examples override this repo's immutable mirror, benchmark
  independence, artifact, testing, or single-session rules.

## Commit attribution and publication

Create repository commits through the authenticated official GitHub connector and
let GitHub assign the contributor identity. Verify author, committer, tree,
parents and target branch before advancing `main`. Do not override attribution
through Git configuration or environment variables. If the connector cannot
perform a required operation, report the specific limitation before selecting
another publication method. Temporary repositories used by tests are separate
fixtures and do not publish commits to this repository.

Other contributors using the connector receive attribution from their own
authenticated GitHub connections. Their access and review requirements follow
the repository's GitHub permissions and rules, not a hardcoded identity.

Published-history changes require an explicit owner request, a verified recovery
copy, full tree, topology, message and timestamp comparisons, preservation of
source-bound evidence and an expected-head lease. Record original-to-rewritten
commit identities outside the repository before publication; old evidence is not
new execution evidence. Do not create a branch, tag or release to retain a backup.

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
- Keep the README badge block generated through `tools/update_readme_badges.py`.
- Push only to the configured default branch unless the repository owner explicitly says otherwise.

## Main-only development and release hold

Agent-performed development and dependency maintenance take place on `main`.
Do not create development, feature or automated dependency-update branches or
pull requests for that work. Other contributors may use GitHub pull requests
when repository permissions or review rules require them.
Qualify dependency updates with the affected installation, runtime and security
checks, then commit and push verified changes directly to `main`. Keep
vulnerability alerts enabled; this policy does not permit ignoring or suppressing
findings. Automatic dependency-update PR creation is disabled.

The owner withdrew release `v0.2.0` and its tag. Do not create a release or tag,
or reactivate the disabled release workflow, until the owner explicitly requests
a new release. A passing build, excerpt control or coverage percentage does not
establish commercial readiness or meaningful improvement over a default agent.
Independent model benchmarks and the documented release requirements must be
verified before recommending publication.

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

Repair overlay loop:

- Input: failed runtime-readiness artifacts and immutable mirrored source files.
- Allowed output: explicit repaired overlays under `included/repaired/skills/`, repair manifests, and repaired-readiness artifacts.
- Required: preserve the exact original `SKILL.md` text in the repaired overlay provenance directory and keep the original mirror unchanged.
- Forbidden: replacing, deleting, or silently rewriting the mirrored source baseline under `included/skills/`.

External benchmark adapter loop:

- Input: selected external benchmark methods and their public repository or documentation endpoints.
- Allowed output: adapter registry data, smoke artifacts proving repository resolution and objective metric definitions, and documentation.
- Forbidden: presenting adapter smoke checks as full benchmark-suite scores or model/skill pass rates.

Benchmark independence rule:

- Benchmark tasks, fixtures, expected results, and evaluators must be authored independently from the exact text of the skill being evaluated.
- Skill text may be used as provenance, activation context, or operating instructions, but it must not define the expected answer used for scoring that same skill.
- Source-grounded skill-proof artifacts are provenance checks only. They must not be counted as runtime benchmark passes.
- A counted runtime benchmark artifact must explicitly record that the task, evaluator, and expected result were defined outside the skill content.

## CI Quality Gates

Run the applicable gates locally before agent changes are pushed to `main`,
then check the hosted results. Human pull requests follow the repository's
permissions and review rules. Core Python checks use
`pip install -e '.[test,lint]'`; specialized checks have separate prerequisites documented
in [`CONTRIBUTING.md`](CONTRIBUTING.md).

- **Lint + format**: `ruff check tools tests benchmarks/agent-effectiveness/graders` and `ruff format --check tools tests benchmarks/agent-effectiveness/graders`. Configured in `pyproject.toml` (`[tool.ruff]`).
- **Type check**: `mypy tools tests benchmarks/agent-effectiveness/graders` uses the configured Python 3.11 target locally. CI passes `--python-version` for each supported 3.11/3.12/3.13/3.14 runtime, pinned to their current security or maintenance patch releases. Python 3.10 reached end of life in October 2026 and is no longer a supported runtime.
- **Catalog**: `python3 tools/validate_catalog.py` collects every drift entry in a single run (no fail-fast).
- **Mirror byte admission**: `python3 tools/check_mirror_content_admission.py --json` checks every current resource, including binary carriers, against the existing detection rules without modifying it.
- **Mandatory agent tools**: `python3 tools/validate_agent_tool_policy.py --check --json` verifies all three local skills, policy links and every generated entrypoint.
- **Static benchmarks freshness**: `python3 tools/run_static_benchmarks.py --check`.
- **Skill risk audit freshness**: `python3 tools/audit_skill_quality.py --check`.
- **Tests**: `python3 -m pytest -q -n auto` runs the full suite in parallel under `pytest-xdist`.
- **Compile check**: `python3 -m compileall -q tools tests benchmarks/agent-effectiveness/graders`.
- **Secrets**: `python3 tools/check_no_secret_patterns.py --history` (in-repo regex + entropy) plus `gitleaks` v8.30.1 (MIT, pinned binary) as a second-opinion gate. Both checks cover mirrored sources and recorded evidence; `.gitleaks.toml` contains no path exemptions.

The Ruff, Mypy, offline-validation and secret-scan workflows run on pushes,
pull requests and manual dispatch. Offline validation and secret scan also have
weekly schedules; Ruff and Mypy do not. Specialized workflows may use path
filters or other prerequisites; inspect their actual triggers before treating
a missing run as a pass.

## Determinism Invariants

Generators that write dated artefacts (catalog, runtime batches, repaired
overlays) must NOT call `datetime.now()` or any wall-clock API in their
output paths. Use `tools/_lib_b/determinism.py` instead. Resolution
precedence (highest first):

1. `SOURCE_DATE_EPOCH` environment variable, per [reproducible-builds.org](https://reproducible-builds.org/docs/source-date-epoch/).
2. The previous run's manifest value (idempotent regeneration).
3. Input-anchored fallback (e.g. `git log -1 --format=%ct -- <input>`).

`tools/build_catalog.py::sha256_tree` uses a git-style portable file mode
(`0o100644` / `0o100755`) so tree hashes are identical across hosts
regardless of umask. The invariant is locked in by
`tests/test_hash_portability.py`; do not regress.

## Tooling Reference

- All tool scripts expose `build_parser() -> argparse.ArgumentParser` and `main(argv: list[str] | None = None) -> int` so they can be exercised from pytest without subprocesses.
- Tools that publish a generated artefact also publish `--check` so CI can verify freshness without rewriting the on-disk state.
- Validators emit `--json` envelopes for machine consumers. Errors are collected, not raised at the first miss.
- Tests live under `tests/` with a single `tests/conftest.py` putting `tools/` on `sys.path`. Per-test-file path shims are not used.
- A successful local pre-push run is the same set of commands CI runs; see [`CONTRIBUTING.md`](CONTRIBUTING.md).

# Continue development from GitHub

Start with `strmt7/ai_skills_collection_benchmarked` on `main`. Read
[AGENTS.md](../AGENTS.md), [the active work order](../data/development_plan.json),
and [the implementation plan](improvement-plan.md). The work order points to
current tasks, source-bound evidence, and owner holds. All three files are tracked
so a new task can recover the project state from its checkout.

## Start a cloud task

Choose a Codex Cloud environment that includes this repository and select `main`.
Check the checkout's `HEAD` and working-tree status before editing. Use the
[locked development setup](development.md) for a supported Python environment.
Keep builds, caches, and temporary data in the task workspace or an owned cache.
Bookkeeping in `data/` and qualification records in `artifacts/` travel with Git.

In a prepared Python environment, verify that the checkout can read the current
evidence and agent-tool policy before picking an unheld task:

```sh
git status --short --branch
git rev-parse HEAD
python tools/validate_native_qualification_index.py --check --json
python tools/validate_agent_tool_policy.py --check --json
python tools/manage_improvement_ledger.py --check --json
```

On Linux, use the portable Python and documentation checks in the development
guide. Qualify the Windows x64 bootstrap, bundled Windows providers, and native
Windows benchmark subjects on a Windows executor. Apply the
[mandatory tool policy](agent-tools.md) in every environment. Before broad code
navigation, verify that the reviewed CocoIndex provider binds to the current
checkout. Use the reviewed isolated Crawl4AI provider for page research. Restore
any missing required provider before its dependent work and continue independent
tasks as the repository rules allow.

## Current checkpoints

- The [qualification index](../data/native_qualification_index.json) binds
  current sources to evidence and retains superseded reviews.
- [Portable source locks and catalog recovery](../artifacts/research/2026-11-26/portable-source-lock/review.json)
  include two relocated Git builds and controlled Windows interruption recovery.
- [Detached skill delivery](../artifacts/research/2026-11-26/detached-skill-installation/review.json)
  covers a two-skill installation, native discovery, fresh provider setup, and
  a source-bound search in a separate Git project. Use the
  [package instructions](installation.md#export-a-portable-installation) to extend
  qualification to more skills and supported clients.
- The comparison target is **GPT-6.2 Sol at `max`** across default, Karpathy, and
  collection conditions. A clean signed-in subject and a completed, independently
  scored calibration are the next benchmark gates. Follow the
  [trial protocol](agent-trial-protocol.md) and
  [benchmark subject policy](benchmark-subject-policy.md).

While model access is being qualified, advance the unheld skill reviews in the
[improvement ledger](../data/improvement_ledger.json). Keep mirrors immutable,
record independent evidence for revised skills, and follow the work order.
Publish verified batches to `main` through the official GitHub connector and
keep the release, scanner-remediation, and history holds in `AGENTS.md`.

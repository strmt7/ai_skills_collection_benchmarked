---
name: strategic-compact-resume
description: Checkpoint and resume long agent work when context pressure or a handoff could lose constraints, verified progress, or ownership of active jobs.
license: MIT
metadata:
  source: affaan-m/everything-claude-code
  source-commit: 846ffb75da9a5f4e677d927af1ad4a1951652267
  revision-status: experimental-unbenchmarked
---

# Resume from verified state

Write a small task-local checkpoint at a phase boundary, before a handoff, or
when the runtime reports context pressure. Use the current context meter when
available. See [token accounting](references/token-accounting.md) when deriving
headroom from provider telemetry.

Keep what changes the next decision:

- **Scope and authorization.** Record the current objective, latest corrections,
  required constraints, and any pending decision. Preserve exact time gates and
  their timezones. Obtain explicit authorization when the task requires it.
- **Work and evidence.** Record the checkout or environment, relevant revision,
  completed checks with their input identities and evidence paths, unresolved
  failures, and the next actionable step. Use stable item IDs and the original
  total for large reviews. Count an item complete only when its required
  evidence exists. Keep raw outputs in their existing locations.
- **Live work.** Record the actual job or session handle, its owner, the last
  observed state, and the evidence required to declare it finished. For a
  local process, use an owned handle or an identity that includes creation
  time. A numeric PID can be reused.

On resumption, read the latest user instruction and applicable repository
policy, then inspect current worktree and external state for the next action.
Check the same live job before retrying or starting another. A wait expiring
only ends the observation. If the handle is missing or status is unavailable,
reconcile the authoritative service and its terminal artifacts before
deciding whether to retry. Verify ownership before cleanup.

Bind completed checks to the inputs they actually used. Reuse valid evidence
and rerun checks affected by changed source, configuration, or scope.
Distinguish a terminal process from a successful deliverable by checking
the required output and the outcome. Preserve failed attempts that explain
the next action.

Write and read back the checkpoint before using the runtime's compaction or
handoff mechanism. Continue from the next eligible item and update the record
when the evidence changes. Keep task checkpoints out of personal memory and
global hooks.

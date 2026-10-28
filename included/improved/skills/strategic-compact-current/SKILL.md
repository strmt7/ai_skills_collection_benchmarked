---
name: strategic-compact-current
description: Checkpoint long, multi-phase work before context pressure or handoff when losing constraints, evidence, or completed-item coverage would risk incorrect continuation.
license: MIT
metadata:
  source: affaan-m/everything-claude-code
  source-commit: 846ffb75da9a5f4e677d927af1ad4a1951652267
  revision-status: experimental-unbenchmarked
---

# Reliable context checkpoints

Create a small task-local checkpoint when a substantial phase finishes, the
runtime signals context pressure, or another session must resume the work.
Do not install global hooks or modify personal memory merely to make a checkpoint.

## Interpret context signals

Use the runtime's current context meter when available. Tool-call counts and
response latency do not measure remaining context. Use provider-specific token
fields only for the documented payload they describe, and leave unknown values
unknown. A session or turn total that includes multiple model calls is not a
current context-window measurement. Check the actual model's window and leave
room for output when estimating headroom.

For a Claude Messages API request with the documented caching fields, request
input is `input_tokens + cache_read_input_tokens + cache_creation_input_tokens`.
For OpenAI Agents API usage, cached input is already included in `input_tokens`;
do not add it again. Its session and turn usage can be unavailable or updated
later. These rules do not establish the meaning of unrelated CLI telemetry.
See [Claude context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)
and [OpenAI usage](https://developers.openai.com/api/docs/guides/agents-api/observability).

## Persist what changes continuation

Record the current objective, accepted corrections, authorization boundaries,
hard constraints, and next actionable step. Preserve exact deadlines and
not-before times with a timezone; elapsed conversation time is not permission.
Distinguish required missing input from optional preferences.

For large collections, maintain a ledger of stable item IDs with explicit states,
such as pending, reviewed, revised, and evaluated. Record the total item universe
and evidence per item. Enumerating or opening a file is not completing its review.
Keep archived records if sources disappear, and invalidate affected conclusions
when their source commit or content hash changes.

Link the files, commits, commands, test logs, and artifacts needed to justify
completed work. Record failed checks, unresolved symptoms, active process IDs,
pending approvals, and meaningful decisions. Prefer pointers to raw evidence over
repeating large tool outputs or preserving every abandoned thought.

Write and verify the checkpoint before requesting compaction or a handoff.
Use the runtime's supported mechanism if one exists; the checkpoint remains useful
without a `/compact` command or a hook script.

## Resume without losing scope

Read the latest user instruction, repository guidance, checkpoint, and affected
worktree state. User corrections take precedence over older checkpoint text.
Verify volatile facts that affect the next action, such as remote heads, active
processes, access, and time gates. Recheck saved evidence if its content or input
signature changed; do not repeat already justified work solely because a new
session began.

Continue from the next eligible incomplete item. Keep deferred work visible until
its actual condition is satisfied. Update the checkpoint after each bounded
batch, and distinguish achieved goals from work that merely stopped.

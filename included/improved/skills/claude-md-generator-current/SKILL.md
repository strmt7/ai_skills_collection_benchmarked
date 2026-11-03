---
name: claude-md-generator-current
description: Create, update, or review Claude Code project instructions using the actual repository configuration and the requested scope.
---

# Maintain Claude Code project instructions

Apply the collection's [mandatory agent tools](../../../../docs/agent-tools.md)
and the target repository's controlling instructions before relevant work.
This experimental guide has not been evaluated in an agent trial.

Determine whether the user wants a review, a new file, or an update, and which
project or directory is in scope. Read the applicable existing instructions
and relevant configuration first. A project can have a root `CLAUDE.md` or
`.claude/CLAUDE.md`, nested instructions, and `.claude/rules/`; their scopes and
load behavior differ. Do not modify personal or unrelated instruction files
unless the request authorizes that scope. Preserve useful existing instructions
and reconcile conflicts according to the applicable authority and user request.

Identify only facts that help future work: the actual build, test and lint
commands, necessary setup, generated-file boundaries, and non-obvious project
conventions. Check commands against the relevant manifests and workflows; run
safe checks when appropriate. Distinguish verified commands from untested ones,
and report missing prerequisites or uncertainty. Do not invent project facts,
commands, directories, or a required section when there is no supporting
evidence. Respect repository policies when deciding what can be changed.

Write concise, specific instructions appropriate to the project rather than
enforcing an arbitrary line count. Use path-scoped rules for guidance that applies
only to matching files when the target supports them. Claude Code expands `@`
imports into context alongside the importing file; an import organizes content
but does not by itself reduce the context loaded. Consult the
[Claude Code memory documentation](https://code.claude.com/docs/en/memory)
for current syntax, load order, and path escaping before adding imports or rules.

Use the current agent to prepare the draft; an additional model, provider,
credential, or particular shell is not a prerequisite. For a review, report
concrete findings and evidence without changing files unless authorized. For
an authorized create or update, make the requested change and summarize the
verified facts and unresolved checks. Follow any actual approval requirement;
do not ask again when the user has already authorized the action.

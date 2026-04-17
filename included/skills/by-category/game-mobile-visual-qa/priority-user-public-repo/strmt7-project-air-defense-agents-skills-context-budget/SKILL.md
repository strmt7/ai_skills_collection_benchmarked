---
name: context-budget
description: Keep agent context small, fast, and deterministic in Project Air Defense.
---

# Context Budget

Use this by default.

- Start with `AGENTS.md`, `docs/reference/ai-agent-context-routing.md`, and one nearest code file.
- Open at most 4 task-specific files on the first pass.
- Run at most 2 refine loops before naming the edit target.
- Add at most 3 files per escalation round.
- Hard stop at 8 task-specific files and summarize before widening scope.
- Reuse existing docs and skills instead of rediscovering the repo.

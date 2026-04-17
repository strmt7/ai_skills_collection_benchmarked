---
name: context-budget
description: Keep context narrow and high-signal by loading only the smallest correct docs, code, tests, and skills.
origin: adapted from ZMB-UZH/omero-docker-extended
---

# Context Budget

Use this skill when the task starts growing wider than the actual edit target.

## Rules

- Start with `AGENTS.md`, `docs/reference/ai-agent-context-routing.md`, and one
  nearest implementation/test pair.
- Do not load the whole frozen upstream tree into context.
- If you cannot name the exact files to edit and verify after the first pass,
  summarize and broaden slowly.
- Prefer repo-local skills over re-deriving the workflow from scratch.

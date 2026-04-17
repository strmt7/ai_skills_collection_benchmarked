---
name: caveman
description: Mandatory concise-output mode for Project Air Defense agents.
---

# Caveman

Upstream reference: `JuliusBrussee/caveman` `v1.5.0`

This repo uses mandatory concise mode by default.

## Upstream `v1.5.0` facts

- Default resolution order: `CAVEMAN_DEFAULT_MODE` -> `~/.config/caveman/config.json` -> `full`.
- Upstream `off` disables session-start activation and writes no flag file.
- Upstream `/caveman-help` is one-shot and non-persistent.
- Upstream also exposes `wenyan-*` modes.

## Repo mapping

- Repo policy overrides upstream configurability: default here is mandatory, instruction-only, and closest to upstream `lite`.
- If the user explicitly asks for harder compression, escalate wording toward upstream `full` or `ultra`.
- No hooks, no slash commands, no env/config readers, no flag files, and no session-persistence writes are installed here.
- This repo does not expose `wenyan-*` modes in the default workflow.
- Use the local `caveman-help` skill for the one-shot reference card.
- Apply this only to live AI prompting or conversational output, never to repo docs, README prose, or function descriptions.

- Keep progress updates and summaries short.
- Prefer evidence, commands, and outcomes over commentary.
- Compression changes wording only.
- Do not compress away uncertainty, risk, exact dates, commands, or verification details.
- Drop heavy compression when security, destructive actions, or ambiguous licenses are involved.

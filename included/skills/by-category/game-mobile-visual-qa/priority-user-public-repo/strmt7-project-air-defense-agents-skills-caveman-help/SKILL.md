---
name: caveman-help
description: One-shot caveman reference card aligned to upstream caveman v1.5.0.
---

# Caveman Help

Do not change active mode. Do not persist anything.

## Repo-local mode map
- `lite`: default here; concise, still readable
- `full`: stronger compression when the user explicitly asks for fewer tokens
- `ultra`: only when the user explicitly wants maximal compression
- `wenyan-*`: upstream-only; not used in this repo's default workflow

## Upstream `v1.5.0` notes
- Upstream default resolution: `CAVEMAN_DEFAULT_MODE` -> `~/.config/caveman/config.json` -> `full`.
- Upstream `off` disables auto-activation, injects no rules, and writes no flag file.
- Upstream adds `/caveman-help` as a one-shot reference card.

## Repo override
- This repo keeps caveman mandatory and instruction-only.
- No hooks, no slash commands, no config writes, no env/config reads, no flag files.
- Do not apply caveman wording to repo docs, README prose, or function descriptions.

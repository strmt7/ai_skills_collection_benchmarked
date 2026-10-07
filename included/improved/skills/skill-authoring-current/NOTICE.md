# Attribution and changes

This experimental revision adapts Anthropic's skill-creator workflow at
`2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c`, under Apache-2.0.
The exact original entrypoint is preserved in `provenance/original-SKILL.md`.
The maintained instructions change experiment independence, failure/usage
accounting, holdout handling, resource qualification and explicit review state.
The offline review helper is a new implementation. Neither this overlay nor its
helper has demonstrated a coding-agent performance gain.

Original source:
<https://github.com/anthropics/skills/blob/2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c/skills/skill-creator/SKILL.md>

# Frontend design skill: accessibility and upstream review

The [pinned frontend-design skill](../included/skills/by-category/search-retrieval-web-automation/official-reference/frontend-design/SKILL.md)
asks for distinctive typography, layouts and motion, and lists accessibility
among the design constraints. It also broadly discourages system fonts. The
newer upstream skill explicitly says to follow the brief and calls out visible
keyboard focus and reduced-motion preferences. The [source observation](../artifacts/research/2026-11-01/anthropic-frontend-source-observation.json)
binds this comparison to the pinned and upstream Git blobs.

The W3C's [Focus Visible criterion](https://www.w3.org/WAI/WCAG22/Understanding/focus-visible)
requires a visible keyboard-focus indicator in a mode of operation at WCAG
Level AA. Its [Animation from Interactions criterion](https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions)
addresses disabling nonessential interaction-triggered motion at Level AAA;
respecting the user's reduced-motion preference is one documented technique.
These are selected criteria, not a complete accessibility checklist.

When using this skill, apply the actual design brief and accessibility
requirements, and test the resulting interface with keyboard navigation and
motion preferences. A source-text comparison cannot establish that an agent's
output passes those tests. No interface, assistive-technology review or agent
benchmark was run in this review. The locked mirror remains unchanged.

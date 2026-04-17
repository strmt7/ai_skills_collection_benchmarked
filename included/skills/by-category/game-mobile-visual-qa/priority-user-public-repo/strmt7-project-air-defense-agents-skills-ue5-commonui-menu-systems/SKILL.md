---
name: ue5-commonui-menu-systems
description: Use when changing a major UE5 front-end menu, options flow, modal stack, routed input surface, or layered smartphone-first menu architecture. Applies to CommonUI adoption decisions, activatable-widget stacks, menu settings flows, and player-facing mobile front-end structure.
---

# UE5 CommonUI Menu Systems

## Load first

1. `AGENTS.md`
2. `docs/reference/ue5-mobile-agent-skill-sources.md`
3. `.agents/skills/ue5-mobile-ui/SKILL.md`
4. `docs/planning/ue5-gameplay-migration-matrix.md`

## Rules

- Use CommonUI for large multi-screen menu stacks, routed modal flows, and settings navigation when plain UMG would otherwise create manual state spaghetti.
- Keep plain UMG for compact in-battle HUD elements and project-specific overlays when CommonUI would add unnecessary runtime weight.
- Treat the menu shell as a product surface, not a debug overlay. Title, actions, settings, and source/status information must be readable in landscape without burying the city view.
- Keep menu copy short and action-first. Prefer one primary action, one secondary action, and compact status chips over multiple explanation paragraphs.
- Keep buttons large, non-focusable by default for touch, and safe-zone aware.
- If a settings surface exists, every visible option must map to real runtime behavior or persistence. No placeholder settings.
- When adding a new menu layer, define the owning state transition first. Do not let widgets invent their own routing logic.
- Screenshot-proof every front-end state that a player can actually reach.

## Preferred stack

1. CommonUI activatable widgets for front-end stacks and routed settings menus.
2. Plain UMG for the in-battle HUD, radar, and compact drawers.
3. Enhanced Input or controller-owned state only for debug bindings and verification hooks, never as player-facing instructions.

## Done means

- the front-end menu is touch-first and landscape-first
- action hierarchy is clear from one screenshot
- settings flow is real, not decorative
- menu routing does not fight gameplay state

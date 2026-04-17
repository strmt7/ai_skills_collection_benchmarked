---
name: ue5-mobile-ui
description: Use when changing any UE5 player-facing menu, HUD, pause surface, settings surface, touch control, or smartphone layout. Applies to UMG/CommonUI choice, safe zones, touch hit targets, information density, keyboard-hint suppression, and keeping the playfield visible on phones.
---

# UE5 Mobile UI

## Load first

1. `AGENTS.md`
2. `docs/reference/ue5-mobile-agent-skill-sources.md`
3. `docs/planning/ue5-visual-acceptance.md`
4. `ue5/ProjectAirDefenseUE5/README.md`

## Rules

- Use UMG or CommonUI for every player-facing menu, HUD, settings surface, or modal. Reserve Canvas-only drawing for debug overlays, proof tooling, or temporary migration aids.
- Treat the visible product as touch-first. Hidden keyboard bindings may remain for automation, verification, or editor debugging, but do not show keyboard instructions in player-facing copy.
- Use safe-zone-aware layout for any edge-anchored surface. Prefer `USafeZone` or equivalent viewport-safe-zone handling over manual magic numbers.
- Keep the playfield readable. Prefer segmented corner clusters and compact drawers over full-width bars that block sky, horizon, or incoming threats.
- Keep copy short. Use action-first labels and remove redundant explanatory text before shrinking font size.
- Prefer layout containers over deeply nested Canvas Panels. Use Canvas only at the root when exact anchoring or layered composition is necessary.
- Prefer event-driven UI updates over bound attributes or per-frame polling.
- Use invalidation and retained rendering for mostly static widgets, and keep frequently changing widgets isolated.
- For simultaneous mobile action buttons, default to non-focusable buttons unless there is a verified focus-navigation requirement.
- Avoid Unreal's default touch interface unless the design explicitly depends on it. It can conflict with UMG and consume screen space needed by the actual game UI.
- Every visible layout change needs screenshot proof in landscape smartphone framing.

## Preferred stack

1. CommonUI + UMG for major menu stacks, modal flows, and routed input.
2. Plain UMG for compact HUD elements and project-specific touch widgets when CommonUI would add unnecessary complexity.
3. Slate only for editor tools or engine-level custom widgets.

## Done means

- the visible UI reads as mobile-first in landscape
- no player-facing surface depends on keyboard instructions
- safe zones are respected
- the playfield remains the priority visual surface
- touch actions are large, distinct, and verified from screenshots or runtime proof

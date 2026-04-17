---
name: ue5-mobile-gameplay
description: Use when changing UE5 mobile gameplay flow, menu-to-battle state, touch input routing, hidden debug bindings, deterministic simulation ownership, or verification for a smartphone-first game. Applies to controller state, battle bootstrap, Enhanced Input, and automation-backed gameplay checks.
---

# UE5 Mobile Gameplay

## Load first

1. `AGENTS.md`
2. `docs/reference/ue5-mobile-agent-skill-sources.md`
3. `docs/planning/ue5-gameplay-migration-matrix.md`
4. `docs/architecture.md`

## Rules

- Separate deterministic gameplay state from presentation state. Menus, HUD, and camera surfaces must not own the simulation.
- Use the player controller or a dedicated coordinator for menu-to-battle state changes, touch routing, and debug-only keyboard paths.
- Treat hidden keyboard bindings as verification aids only. Visible player-facing UX must remain touch-first.
- Prefer explicit state transitions over implicit auto-start behavior when a real main menu exists.
- Keep gameplay verification two-layered: automation or unit coverage for deterministic logic, runtime screenshot or log proof for player-facing flow.
- Do not claim a system is ported because the scene boots. The system must be reachable from the mobile-visible UI.
- When adding a verification shortcut, also document the normal touch path.

## Done means

- the player can reach battle from a touch-first menu
- gameplay state and UI state are distinct
- debug bindings remain hidden from player-facing surfaces
- deterministic logic stays testable outside the viewport

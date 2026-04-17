---
name: ue5-mobile-rendering
description: Use when changing UE5 smartphone rendering, graphics settings, anti-aliasing, ambient occlusion, reflections, post-process, device profiles, or mobile performance tiers. Applies when exposing graphics options to players or claiming that a visual feature works on-device.
---

# UE5 Mobile Rendering

## Load first

1. `AGENTS.md`
2. `docs/reference/ue5-mobile-agent-skill-sources.md`
3. `docs/planning/ue5-visual-acceptance.md`
4. `ue5/ProjectAirDefenseUE5/Config/DefaultEngine.ini`
5. `ue5/ProjectAirDefenseUE5/Config/DefaultGame.ini`

## Rules

- Expose only settings that map to real engine behavior on the active renderer and platform. Do not ship placebo toggles.
- Bind user-facing graphics controls through `UGameUserSettings`, device profiles, or verified project CVars, not ad-hoc console spam.
- Verify feature support against Epic's current mobile rendering and performance docs before exposing AA, AO, reflections, shadows, post-process, or similar toggles.
- Use the Mobile Previewer and device-profile-driven preview before claiming a mobile visual result.
- Prefer stable frame time, legibility, and truthful materials over desktop-only effects.
- No static gameplay backdrops. The battle scene must stay geometry-driven, tileset-driven, or material-driven.
- Keep the disk footprint controlled during iteration: one packaged build, no stale staged-build duplicates, no redundant dataset copies.
- Every rendering or settings change needs serial proof, not overlapping runtime launches.

## Graphics-settings contract

- Anti-aliasing, ambient occlusion, reflections, shadows, post-process, and similar labels must report what backend state was actually applied.
- Hide or relabel options that are unsupported on the current mobile path instead of pretending they work.
- Device-tier defaults must come from measured hardware or documented device-profile policy.

## Done means

- user-visible graphics settings are truthful
- mobile support claims are backed by preview or runtime proof
- scene fidelity improves without breaking frame-time or storage discipline

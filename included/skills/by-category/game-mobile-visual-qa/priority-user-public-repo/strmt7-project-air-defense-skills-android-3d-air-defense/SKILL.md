---
name: android-3d-air-defense
description: Use this skill when building, debugging, balancing, profiling, or visually upgrading the Project Air Defense Android 3D missile-defense prototype, especially for libGDX battle flow, mobile rendering quality, interception logic, HUD ergonomics, and emulator-verified Android fixes.
---

# Android 3D Air Defense Skill

Use this workflow whenever you modify gameplay, visuals, physics, UI, or Android behavior in this repository.

## Reference files

- [../../docs/reference/ai-agent-context-routing.md](../../docs/reference/ai-agent-context-routing.md)
- [../../docs/android-visual-qa.md](../../docs/android-visual-qa.md)
- [../../docs/level-asset-pipeline.md](../../docs/level-asset-pipeline.md)
- [../../docs/level-asset-source-map.md](../../docs/level-asset-source-map.md)
- [../../android/assets/ATTRIBUTION.md](../../android/assets/ATTRIBUTION.md)
- [references/curated-skill-stack.md](references/curated-skill-stack.md)
- [references/source-map.md](references/source-map.md)
- [references/awesome-claude-skills-source-map.md](references/awesome-claude-skills-source-map.md)
- [references/awesome-android-complete-reference-links.md](references/awesome-android-complete-reference-links.md)

## Objectives
- Keep the game fully 3D with readable mobile combat.
- Preserve physically plausible but gameplay-readable ballistic motion (`g = -9.81 m/s^2`).
- Keep touch controls large, modern, and reliable in landscape mode.
- Import only explicitly attributed runtime assets.
- Prefer proof-driven iteration over speculative rewrites.

## Workflow
1. **Confirm the exact failing surface first**
   - Separate process crash, render freeze, wrong button path, scene unreadability, gameplay balance, and packaging failure.
   - Treat "process alive" and "screen usable" as different checks.
2. **Use the shared simulation core as the source of truth**
   - Put gameplay math in shared logic and keep GUI behavior aligned with it.
   - Add or update pure Kotlin tests when tuning interception, wave timing, radar rules, damage, or layout contracts.
3. **Preserve a coherent world scale**
   - Measure imported model bounds.
   - Keep buildings, roads, launchers, missiles, effects, and HUD cues in one scale language.
   - Never let waterfront buildings drift into the sea or let the radar disagree with the battle view.
4. **Improve graphics in the right order**
   - Depth and horizon layering before more geometry.
   - Night lighting and emissive rhythm before heavier effects.
   - Mobile-safe textures, materials, and one safe Android render path before advanced shaders.
5. **Modernize controls as a mobile game, not a desktop port**
   - Large hit targets, strong pressed and disabled states, and clear primary-action emphasis.
6. **Verify with hard proof**
   - Run local tests.
   - Run the headless Monte Carlo simulation.
   - Run `ktlintCheck`.
   - Build and install on Android.
   - Capture screenshots and logs from the emulator or device.
   - Use the repo-local visual QA toolchain instead of guessing taps on libGDX surfaces.

## Definition of done

- Missiles visibly follow believable ballistic or cruise-like paths.
- Interceptors can fail sometimes, but not because the simulation is rigged against the player.
- HUD reflects wave, readiness, and active threat state correctly.
- The battle remains visually readable on a phone-sized screen.
- The emulator or device verification evidence agrees with the code change.

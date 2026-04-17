# UE5 Photoreal City Scene

Use this skill when changing city-scene quality targets, camera policy, or environment art direction for the UE5 migration.

## Load first

1. `AGENTS.md`
2. `docs/planning/ue5-engine-mandate.md`
3. `docs/planning/ue5-visual-acceptance.md`
4. `docs/planning/ue5-city-pilot-helsinki-kalasatama.md`
5. `ue5/ProjectAirDefenseUE5/README.md`

## Rules

- No static 2D gameplay backdrops.
- Camera inspection controls are mandatory, not optional.
- Treat the current Helsinki 3D Tiles plus Cesium runtime as the truthful inspection path until the baked mesh path replaces it.
- Use Nanite, World Partition, and UE5 lighting features as the base visual stack.
- Do not reintroduce procedural placeholder skylines as the primary district.

## Outcome

- the pilot district stays truthful
- skyline composition survives multiple camera angles
- sea, shore, and buildings stay spatially credible

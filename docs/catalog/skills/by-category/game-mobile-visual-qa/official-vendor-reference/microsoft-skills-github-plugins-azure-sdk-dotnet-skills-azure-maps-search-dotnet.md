# azure-maps-search-dotnet

Category: Game, mobile & visual QA

Mirrored skill: `included/skills/by-category/game-mobile-visual-qa/official-vendor-reference/microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-maps-search-dotnet`

Agent-ready entrypoint: `included/agent-ready/by-category/game-mobile-visual-qa/official-vendor-reference/microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-maps-search-dotnet/SKILL.md`

Source: [microsoft/skills `.github/plugins/azure-sdk-dotnet/skills/azure-maps-search-dotnet/SKILL.md`](https://github.com/microsoft/skills/blob/a2c05249c4a20103dd954ca702467aa328aac031/.github/plugins/azure-sdk-dotnet/skills/azure-maps-search-dotnet/SKILL.md)

Selected ref: `default-branch HEAD`; commit `a2c05249c4a2`

## Use

Load this skill only when the task matches the source description or path; read SKILL.md first and then load referenced resources on demand.

## Scope

Source description: Azure Maps SDK for .NET. Location-based services including geocoding, routing, rendering, geolocation, and weather. Use for address search, directions, map tiles, IP geolocation, and weather data. Triggers: "Azure Maps", "MapsSearchClient", "MapsRoutingClient", "MapsRenderingClient", "geocoding .NET", "route directions", "map tiles", "geolocation".

## Verification

Static benchmark results are reported in `docs/benchmark-results.md`. Runtime claims require a validated artifact.

Assigned scenarios:

- `skill-proof-microsoft-skills-github-plugins-azure-sdk-dotnet-skills-azure-maps-search-dotnet-skill-md`: Use the immutable source file https://github.com/microsoft/skills/blob/a2c05249c4a20103dd954ca702467aa328aac031/.github/plugins/azure-sdk-dotnet/skills/azure-maps-search-dotnet/SKILL.md as the fixture and prove the agent can understand when and how to use the skill.
- `game-mobile-and-visual-qa-air-defense-android-benchmarks`: Run startup, gameplay, and visual QA benchmark scenarios.
- `game-mobile-and-visual-qa-coco-captions`: Evaluate image understanding and visual QA tasks.
- `game-mobile-and-visual-qa-owasp-juice-shop`: Run safe local security workflows against a known vulnerable app.

Improvement notes:

- Keep provenance and selected ref visible so agents can verify the source before use.
- Maintain at least 3 real workflow benchmark scenarios before treating the skill as deployable.
- Add agents/openai.yaml or equivalent metadata when the skill is intended for OpenAI/Codex-style listings.

---
name: level-asset-curation
description: Source, validate, attribute, and integrate city/structure assets for Project Air Defense.
---

# Level Asset Curation

Use this before importing any model, texture, skyline, or dataset.

- Start with `docs/level-asset-source-map.md`.
- Use ship-safe runtime assets first: CC0 or MIT.
- Treat CityGML and open-city datasets as reference/layout sources until the dataset license is confirmed for shipping.
- Normalize scale, axes, texture size, and mobile cost before import.
- Update `android/assets/ATTRIBUTION.md` in the same change.

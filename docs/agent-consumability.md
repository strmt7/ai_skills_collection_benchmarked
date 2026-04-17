# Agent Consumability Checklist

Mechanical checks:

- `SKILL.md` exists at the recorded source path.
- `name`, description, source URL, immutable URL, selected ref, and commit SHA are recorded.
- Selected ref is latest release tag where available, otherwise default branch HEAD with explicit no-release policy.
- At least `3` real workflow scenarios are assigned to every scenario-covered candidate.
- Improvement notes are derived from observed file structure.

Runtime proof requires running the scenario in the target agent environment and saving artifacts.

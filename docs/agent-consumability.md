# Agent Consumability Checklist

Mechanical checks:

- `SKILL.md` exists at the recorded source path.
- `name`, description, source URL, immutable URL, selected ref, and commit SHA are recorded.
- Each source ref and commit are declared. A source can retain older packages while other packages use a newer release.
- At least `3` real workflow scenarios are assigned to every scenario-covered candidate.
- Improvement notes are derived from observed file structure.

Runtime proof requires running the scenario in the target agent environment and saving artifacts.

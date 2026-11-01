# Design skill: local search and presentation controls

The pinned [design skill](../included/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design/SKILL.md)
includes local logo and corporate-identity searches and an HTML presentation
renderer. Keep its data and scripts together, and check both the process status
and the returned content before using their results in automation.

The [source-bound control](../artifacts/research/2026-11-01/design-search/reproduce.py)
tested copies of the pinned files with complete data and with selected files
removed from temporary fixtures. On both Windows and Linux:

- Each JSON search returned an error object but exited with status 0 when its
  selected data file was missing. A sample corporate-identity brief also exited
  with status 0 and silently returned no deliverables when its deliverable data
  was missing.
- Searching the complete deliverable data for `uniform` returned three results;
  `uniforms` returned none. This illustrates a retrieval limitation, not a
  general measurement of search quality.
- The HTML renderer reported an error but exited with status 0 and produced no
  file for a missing or empty image directory. A directory containing a valid
  PNG produced an HTML file in the control.

The [Windows](../artifacts/research/2026-11-01/design-search/windows-result.json)
and [Linux](../artifacts/research/2026-11-01/design-search/linux-result.json)
observations are identical. The control verifies its selected inputs against a
[source manifest](../artifacts/research/2026-11-01/design-search/source-manifest.json),
copies them into temporary directories and never modifies the mirror. From the
repository root, reproduce or check an observation with:

```bash
python artifacts/research/2026-11-01/design-search/reproduce.py --output /path/to/result.json
python artifacts/research/2026-11-01/design-search/reproduce.py --output /path/to/result.json --check
```

The relevant five upstream scripts were unchanged between the pinned `v2.5.0`
commit and the observed `v2.15.0` release; see the
[source identities](../artifacts/research/2026-11-01/design-search/source-evidence.json).
The [repaired local-search overlay](../included/repaired/skills/by-category/documents-spreadsheets-presentations/latest-release-creative/ckm-design/SKILL.md)
addresses selected search failures without changing the mirror. Its
[component qualification](../artifacts/repaired-skill-readiness/design-local-search-v1/qualification.json)
includes independent synthetic controls and cross-platform observations. It
does not repair the brief generator or HTML renderer. Neither review tested a
live image provider, the full design skill or an agent, and neither establishes
benchmark improvement.

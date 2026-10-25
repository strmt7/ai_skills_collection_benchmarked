# Source migrations and candidate admission

Source updates must preserve the evidence for earlier versions. The catalog
generator now checks recorded benchmark source identities before publication.
If a refresh would remove or replace a recorded version, it requires a validated
source-history record first. Historical scenario definitions can also survive a
deleted skill or scenario. Old results remain attached to their original version;
the static report separates artifacts for retired identifiers from per-skill counts.
Repair regeneration refuses stale failures before cleanup.

Use `tools/archive_catalog_source.py` with an immutable published catalog commit,
explicit skill IDs and a reviewed notice for that source. For example, from a
checkout containing the referenced commit:

```console
python tools/archive_catalog_source.py --revision f463549e429aa5f6c830f6fe870b863262ef6d2d --source-repo K-Dense-AI/scientific-agent-skills --skill-id k-dense-ai-scientific-agent-skills-scientific-skills-datamol-skill-md --notice artifacts/source-notices/k-dense-scientific-agent-skills/eb20fb0dcb0b1dadaa3db2737188f0755bbc4770/LICENSE.md --notice-source-path LICENSE.md --check --json
```

Omit `--check` to publish a reviewed snapshot. `--root` selects another checkout;
no drive, username, installation location or AI agent is built in. Shallow clones
must fetch the referenced commit before archival. The tool reads committed Git
objects, rejects conflicts and uses recoverable publication with retained originals.
It preserves metadata, assigned scenarios and exact `SKILL.md` bytes, rather than
claiming to archive the complete package or reconstruct an old benchmark session.
Supplying a notice does not establish redistribution permission: review individual
license declarations before publication. The archived Datamol declaration is
accompanied by the complete [Apache 2.0 terms](../artifacts/source-notices/licenses/Apache-2.0.txt).

Installation names now come from the source lock for identities already present.
New skills receive deterministic available names. A real K-Dense preview exposed
five unrelated renames when duplicate names appeared or disappeared; the corrected
preview preserved all 539 other catalog records and 29 other source locks exactly.
The existing guard against unrelated changes remains in place. Both scoped and
complete builds use the locked names. With `--json`, generation errors return JSON and exit 2,
separately from expected freshness drift at exit 1.

The [K-Dense candidate review](../artifacts/research/2026-10-25/kdense-v272-source-candidate-review.json)
records release v2.72.0 at `526ebce143bc326f44471554e33d66a19c840360`.
Native Git objects verify all 2,026 regular files under `skills/` plus the root
notice, including 177 skill files. A complete preview produced 716 catalog entries
and 761 scenarios, but **that candidate is not applied**. The published catalog
still has 673 entries. Native Crawl4AI read the exact release page; its notes cover
the incremental change from v2.71.0, not the entire change from the locked v2.37.1.

The upstream [individual-license policy](https://github.com/K-Dense-AI/scientific-agent-skills/blob/526ebce143bc326f44471554e33d66a19c840360/README.md#individual-skill-licenses)
says per-skill declarations may override repository MIT terms. The inventory
contains proprietary, noncommercial, unknown and missing declarations, so the
whole-source refresh remains held for individual admission review. This records
an unresolved source condition, not a conclusion about external dependency licenses.
The exact candidate is recorded in the hash-bound
[admission registry](../data/source_admission_holds.json). Both collection and
offline catalog validation refuse that version; the current pin remains allowed.
The candidate report retains every resource's digest and review status: four whole
resources were read; inspecting all 177 license fields does not complete review of
those skill bodies. No candidate package, paid API job or agent benchmark ran.

The [migration controls](../artifacts/research/2026-10-25/source-history-migration-controls.json)
retain the original refused preview, corrected counterexample, archival checks,
native license captures and limits. Current mirrors and old benchmark/repair
artifacts remain unchanged. These checks establish source and evidence handling;
they do not establish coding-agent superiority. Crawl4AI remains Windows x64.
The Karpathy-derived baseline was also rechecked: the canonical repository still
resolves to the pinned `2c606141936f1eeef17fa3043a72095b4765b9c2` commit.

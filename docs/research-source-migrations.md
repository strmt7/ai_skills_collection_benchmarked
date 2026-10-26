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
The initial candidate report retains every resource's digest and its review status
at that stage: four whole resources were read. The
[next review batch](../artifacts/research/2026-10-26/kdense-restricted-and-undeclared-review.json)
reads all ten instruction files with missing, unknown, proprietary or noncommercial
license declarations, plus the Glycoengineering helper source. Across both batches,
12 of 177 instruction bodies and 15 of 2,026 resources have been read. The remaining
references, scripts and assets still need review. No candidate package, paid API
job or agent benchmark ran; the source hold remains in force.

The batch distinguishes instruction permissions from package, dataset, model-weight
and service terms. Three declarations remain unknown and four are missing. Rowan's
proprietary field does not establish whether its restriction concerns the instruction
or the hosted service. DeepSpot-M declares noncommercial terms and reports separate
weight/access restrictions. What-If Oracle expressly retains noncommercial and
share-alike terms. The official [PolyForm terms](https://polyformproject.org/licenses/noncommercial/1.0.0)
and [CC BY-NC-SA legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
were read with Crawl4AI; the original PolyForm trailing-slash 404 is retained.
These observations do not supply missing grants or clear the whole source for use.

Native PyPI metadata checked on 26 October also identifies versions requiring new
qualification before a later source or overlay update:

| Package | Version discussed in the candidate | Latest stable observed |
| --- | --- | --- |
| PyHealth | 2.0.2 | 2.1.0 |
| rowan-python | 3.2.0 | 3.2.3 |
| pandas in the PrimeKG review | 3.0.6 | 3.1.0 |

DeepSpot-M 1.0.0 and ETE3 3.1.3 still match their latest stable package metadata.
Package availability does not prove compatibility. In particular, PyHealth 2.1.0
declares Python 3.12–3.13 support; it cannot be treated as compatible with the
catalog toolchain's Python 3.14 merely because it is newer. Eight existing catalog
entries now track this candidate review as contextual research in progress. Their
source signatures, revision/evaluation states and current mirrors are unchanged.

The [migration controls](../artifacts/research/2026-10-25/source-history-migration-controls.json)
retain the original refused preview, corrected counterexample, archival checks,
native license captures and limits. Current mirrors and old benchmark/repair
artifacts remain unchanged. These checks establish source and evidence handling;
they do not establish coding-agent superiority. Crawl4AI remains Windows x64.
The Karpathy-derived baseline was also rechecked: the canonical repository still
resolves to the pinned `2c606141936f1eeef17fa3043a72095b4765b9c2` commit.

## PPT Master candidate and native retention controls

The [PPT Master review](../artifacts/research/2026-10-26/ppt-v673-source-candidate-review.json)
compares locked v6.6.0 with stable v6.7.3 at
`622bf0148bca4f697b0184322c7e2aa2a04520a2`. All 13,025 selected candidate files
were checked against native Git blobs and canonical API tree entries. Paired
CodeQL 2.27.3 security-extended scans produced 50 findings for the old raw source
and 52 for the candidate. These are scanner results, not confirmed vulnerabilities.
Two selected new results received static review; one remains unresolved. The exact
candidate is held in the admission registry while that result and the wider package
remain under review. Current catalog source and mirrors are unchanged.

The separate [native component scorecard](../artifacts/research/2026-10-26/ppt-native-retention-controls.json)
records one SDK-authored three-slide fixture, with the same interpreter and
dependencies for both actual converters and their intact attribution guards:

| Component controls | v6.6.0 | v6.7.3 |
| --- | ---: | ---: |
| Passed | 10/11 | 11/11 |
| Office14 Choice plain text retained | No | Yes |
| Both native guards and converters completed | Yes | Yes |

The evaluator checks slide-local content and chart-value associations, including
zero values. Corrupt associations, displaced tokens and tampered evidence are
rejected by negative controls. This tests plain text in an Office14 Choice shape;
it does not test equation semantics, rendering or the complete presentation
workflow. The [reproduction instructions](../toolchains/pptx-native/README.md)
and Windows workflow accept caller-selected paths and preserve full native logs.
The five-package wheel cohort has hash-checked installation, dependency audits
and Dependabot coverage. These component results do not establish a skill or
coding-agent advantage over default GPT-6.1 Sol or Karpathy instructions, and they
do not override the source admission hold. Host independence changes no OS target;
Crawl4AI remains Windows x64.

# Anthropic skill source comparison

The catalog pins 17 skills from `anthropics/skills` at commit
`2c7ec5e78b8e5d43ea02e90bb8826f6b9f147b0c`. The
[recorded comparison](../artifacts/research/2026-11-01/anthropic-upstream-tree-delta.json)
compares their locked directories with upstream commit
`ca45fc496a3436251f191354091d557da31c15b5` observed on 1 November 2026.
The retained API snapshots reconstruct to the recorded Git tree identities;
commit-to-tree bindings still depend on the GitHub API responses.

Fifteen skill directories changed and two did not. Six changed directories
include an updated `SKILL.md`; the other nine have only a changed license file.
All 17 entrypoints were present at the observed upstream commit. These counts
compare Git entries, not the meaning of changes: they do not establish license
compatibility, runtime readiness, or improved agent performance. The source lock
and mirrors have not been updated. The [Anthropic API review](research-anthropic-api.md)
examines selected model and caching guidance separately.

The ledger links this source observation to each of the 17 skills and leaves
research in progress. To reproduce the offline comparison from the repository
root, run:

```bash
python artifacts/research/2026-10-28/ecc-source-snapshots/generator.py.txt \
  --repo anthropics/skills \
  --lock artifacts/research/2026-11-01/anthropic-source-snapshots/source-lock.json.gz \
  --old-commit artifacts/research/2026-11-01/anthropic-source-snapshots/old-commit.json \
  --old-tree artifacts/research/2026-11-01/anthropic-source-snapshots/old-tree.json.gz \
  --new-commit artifacts/research/2026-11-01/anthropic-source-snapshots/new-commit.json \
  --new-tree artifacts/research/2026-11-01/anthropic-source-snapshots/new-tree.json.gz \
  --output artifacts/research/2026-11-01/anthropic-upstream-tree-delta.json --check
```

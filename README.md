# AI Skills Collection Benchmarked

> Early alpha: this repository is experimental. Many entries may be incomplete, incompatible, stale, or unsuitable for a given environment. Use it at your own risk; the maintainers accept no responsibility for results, failures, or downstream use.

Evidence-backed catalog of AI agent skills, with benchmark scenarios tied to real datasets and real repository workflows.

Repository scope:

- Catalog entries come from observed `SKILL.md` files in public GitHub repositories.
- Each entry records source repo, path, selected ref, immutable commit URL, category, and readiness caveat.
- Source discovery used a broad web and repository search, then offline verification against local checkouts.
- Selected-entry ordering follows the source policy and lock files, not README-only claims.
- Scenario-covered candidates must have multiple benchmark scenarios before any runtime claim is considered.
- The benchmark suite defines realistic workflows and datasets; it does not claim a skill passed until a run artifact is recorded.

Current snapshot:

- `673` source-backed skill entries.
- `673` written skill mirrors under `included/skills/`.
- `673` compact agent-ready skill entrypoints under `included/agent-ready/`.
- `80` selected repository entries.
- `15` categories.
- `718` real-data scenario templates.
- Minimum `3` benchmark scenarios assigned per scenario-covered candidate.

Start here:

- [Methodology](docs/methodology.md)
- [Source policy](docs/source-policy.md)
- [Included skill mirrors](included/skills/README.md)
- [Agent-ready skills](included/agent-ready/README.md)
- [Selected skills](docs/selected-skills.md)
- [Catalog index](docs/catalog/index.md)
- [Benchmark suite](docs/benchmarks.md)
- [Benchmark results](docs/benchmark-results.md)
- [Runtime benchmark batch 01](docs/runtime-benchmark-batch-01.md)
- [Skill quality findings](docs/skill-quality-findings.md)
- [Skill risk findings](docs/skill-risk-findings.md)
- [Immutable audit model](docs/immutable-audit-model.md)
- [Benchmark runner requirements](docs/benchmark-runner-requirements.md)
- [Host-agnostic installation](docs/installation.md)
- [Agent consumability checklist](docs/agent-consumability.md)

Validation:

```bash
python3 tools/validate_catalog.py
python3 -m pytest
```

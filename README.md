# AI Skills Collection Benchmarked

<!-- BEGIN GENERATED BADGES -->
[![Offline validation](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/workflows/offline-validation.yml/badge.svg)](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/workflows/offline-validation.yml)
[![Ruff](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/workflows/ruff.yml/badge.svg)](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/workflows/ruff.yml)
[![Mypy](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/workflows/mypy.yml/badge.svg)](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/workflows/mypy.yml)
[![Secret scan](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/workflows/secret-scan.yml/badge.svg)](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/workflows/secret-scan.yml)
[![Python 3.10–3.13](https://img.shields.io/badge/python-3.10%20%E2%80%93%203.13-blue.svg)](https://devguide.python.org/versions/)
[![andrej-karpathy-skills](https://img.shields.io/static/v1?label=&message=andrej-karpathy-skills&color=555&logo=github&logoColor=white)](https://github.com/forrestchang/andrej-karpathy-skills)
<!-- END GENERATED BADGES -->

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
- `34` repaired skill overlays under `included/repaired/skills/` for currently observed runtime-readiness packaging failures.
- `14` selected external benchmark method adapters with smoke artifacts.
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
- [Runtime benchmark batch 02](docs/runtime-benchmark-batch-02.md)
- [Runtime benchmark batch 03](docs/runtime-benchmark-batch-03.md)
- [Local Markdown link failures](docs/local-markdown-link-failures.md)
- [Repaired skill readiness](docs/repaired-skill-readiness.md)
- [Objective benchmark methods](docs/objective-benchmark-methods.md)
- [External benchmark adapter smoke](docs/external-benchmark-adapter-smoke.md)
- [Skill quality findings](docs/skill-quality-findings.md)
- [Skill risk findings](docs/skill-risk-findings.md)
- [Immutable audit model](docs/immutable-audit-model.md)
- [Benchmark runner requirements](docs/benchmark-runner-requirements.md)
- [Host-agnostic installation](docs/installation.md)
- [Agent consumability checklist](docs/agent-consumability.md)
- [Contributing guide](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

Validation (offline; no source checkouts required):

```bash
python3 -m pip install -e '.[test,lint]'
python3 tools/validate_catalog.py            # cross-reference + mirror integrity
python3 tools/validate_source_lock.py        # offline structural + mirror-hash check
python3 tools/run_static_benchmarks.py --check
python3 tools/audit_skill_quality.py --check
python3 tools/check_no_secret_patterns.py --history
ruff check tools tests
ruff format --check tools tests
mypy tools tests
python3 -m pytest -q -n auto
python3 -m compileall -q tools tests
```

The same gates run in [GitHub Actions](.github/workflows/) on every push, on
weekly cron, and on `workflow_dispatch`. See [docs/installation.md](docs/installation.md)
for the full reproducible / `SOURCE_DATE_EPOCH`-anchored regeneration flow.

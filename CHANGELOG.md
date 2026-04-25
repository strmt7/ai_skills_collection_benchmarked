# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (enterprise-grade gates)

- `pytest-cov` wired into CI with a `fail_under = 45` floor (matches current
  measured ~55% coverage; raised per deep-rewrite pass). Coverage XML is
  uploaded as an artifact per Python matrix leg.
- `pip-audit` CVE gate (daily cron) against a new pip-compile
  `requirements-lock.txt` (hashed, 781 pinned deps). The workflow also
  diff-checks the lockfile against a fresh `pip-compile` so it cannot drift.
- `.github/workflows/release.yml`: tag-triggered (`v*.*.*`) workflow that
  re-runs every gate on the tagged commit, builds `sdist` + `wheel`, slices
  the matching `CHANGELOG.md` section as release notes, and attaches
  artefacts to a GitHub Release via `softprops/action-gh-release@v3.0.0`.
- `.pre-commit-config.yaml` mirroring the CI gate set (ruff, mypy, built-in
  hygiene hooks, in-repo secret scanner).
- New `[lint]` and `[security]` extras in `pyproject.toml`.

### Added (deep-rewrite pass on 3 generator tools + coverage lift)

- `tools/create_source_proof_batch.py`: extracted pure helpers
  (`build_result`, `build_transcript`, `build_artifact`,
  `scenario_id_for`); `write_artifact` gains a `dry_run` path; CLI gains
  `--dry-run` and `--json`. 8 new logic tests. Coverage 24.8% → 82.4%.
  Verified byte-identical to committed artifacts on a real non-dry run.
- `tools/evaluate_external_benchmark_methods.py`: `smoke_probe()` now
  accepts `head_provider` / `tree_provider` callables so every code path
  (including subpath-missing, unresolved HEAD, tree-fetch exception) is
  exercised offline. 10 new logic tests. Coverage 43.2% → 61.8%.
- `tools/create_independent_runtime_batch.py`: 21 new logic tests over
  every pure helper (`github_repo_from_url`, `first_non_provenance_scenario`,
  `batch_paths`, `build_task`, `check_single_session_entrypoint`) plus
  monkeypatched coverage of `resolve_dataset_snapshot` non-github, github,
  and HEAD-failure paths. Coverage 17.5% → 36.1% (helpers-only; full
  main() path is network-backed and out of scope).
- `tools/build_catalog.py`: 13 more component tests for
  `keyword_matches`, `category_for` (incl. microsoft/k-dense special
  cases and coding fallback), `scenario_ids`, `flags`,
  `skill_mirror_path`, `skill_agent_ready_path`.

### Changed

- `tools/validate_catalog.py`: refactored to `_collect_entry_errors` for
  thread-safe per-entry accumulation; benchmarked ThreadPoolExecutor
  dispatch against sequential and **reverted to sequential** after
  measuring a 2.3× regression (3.9 s seq vs 9.1 s cpu*2 workers). Opt-in
  parallel path remains behind `VALIDATE_CATALOG_MAX_WORKERS`.
- `SECURITY.md`: added disclosure contact, the full CI gate matrix,
  supply-chain section, and gitleaks local-mirror instructions.

### Test + coverage summary

| Metric | Before this section | After |
| --- | ---: | ---: |
| Tests | 122 | **182+** |
| Overall coverage | 0% (unwired) | **~55%** (fail_under=45) |

## [0.2.0] — 2026-04-25

This release is a deep-quality pass on the tooling, schemas, and CI surface.
The cataloged skill mirrors are unchanged (Immutable Audit Model preserved).

### Added

- `ruff>=0.15` lint + format gate (`pyproject.toml [tool.ruff]`,
  `.github/workflows/ruff.yml`).
- `mypy>=1.20` type-check gate across Python 3.10/3.11/3.12/3.13
  (`.github/workflows/mypy.yml`); catches version-conditional bugs.
- `gitleaks` v8.30.1 (MIT, pinned binary, SHA256-verified) as a
  second-opinion secret scan; allowlist in `.gitleaks.toml` documents why
  upstream-mirrored content is exempt.
- Dependabot weekly grouped updates for `github-actions` and `pip`
  ecosystems (`.github/dependabot.yml`).
- Scheduled CI runs (`cron`) on both `offline-validation` and `secret-scan`
  to detect upstream drift between commits.
- `coverage>=7.6` and `hypothesis>=6.115` test dependencies.
- 90 new tests across hash portability, CLI contracts, validators, generator
  parsers, security patterns, and `build_catalog` components (32 → 122).
- `tests/conftest.py` centralises the `tools/` path shim.
- `CONTRIBUTING.md`, `CHANGELOG.md`, `.gitleaks.toml`.

### Changed

- `tools/build_catalog.py::sha256_tree`: now uses a git-style portable file
  mode (`0o100644` / `0o100755`) so tree hashes are reproducible across hosts
  regardless of umask. Pre-existing 673-mirror hash drift closed.
- `tools/validate_catalog.py`: error collection rewrite (no longer
  fail-fast); adds `--json`, `--max-errors`; testable `main(argv) -> int`.
- `tools/validate_source_lock.py`: runs with **zero arguments** (offline mirror
  validation against committed catalog); `--source-root` is now optional with
  `AI_SKILL_SOURCE_ROOT` env fallback; adds `--json` and structural checks
  (duplicate skill IDs, required fields, skill_count coherence).
- `tools/audit_skill_quality.py`: adds `--json` stdout mode and
  `--severity blocking|warning|info|any` filter.
- `tools/run_static_benchmarks.py`: modularised under `tools/_lib_c/`;
  refreshed snapshot now reports 8076/8076 checks (was 7403/8076).
- `tools/check_benchmark_artifact.py`: schema-driven structural pass with
  JSON-Pointer error paths; `--validate-all DIR` mode; pure-Python validator
  (no `jsonschema` dependency).
- `tools/check_no_secret_patterns.py`: layered scanner (provider regex +
  Shannon-entropy in credential-named assignments); 21 new fixture tests.
- `tools/report_local_markdown_link_failures.py`: argparse, `--check`,
  `--stdout`; lock-in tests for link extraction edge cases.
- `tools/create_repaired_skill_overlays.py`: extracted helpers into
  `tools/_lib_b/`; in-code provenance invariant (`_preserve_original_provenance`
  refuses to overwrite an existing provenance copy with different bytes).
- `tools/create_independent_runtime_batch.py` and
  `tools/create_source_proof_batch.py`: removed `datetime.now()`; both
  generators now resolve timestamps and catalog commits through
  `tools/_lib_b/determinism.py` (precedence: `SOURCE_DATE_EPOCH` → existing
  manifest → input-anchored git commit time).
- All 5 evaluator JSON Schemas upgraded to Draft 2020-12 with `$id`, `title`,
  `description`, and `additionalProperties: false` where safe.
- GitHub Actions workflows: pinned to `actions/checkout@v6.0.2` and
  `actions/setup-python@v6.2.0`; added concurrency cancellation,
  `permissions: contents: read`, Python 3.10–3.13 matrix, pip cache,
  `pytest -n auto`.
- `pyproject.toml`: consolidated single-source pytest config (deleted
  redundant `pytest.ini`); bumped floors (`pytest>=8.4`, `pytest-xdist>=3.6`,
  `PyYAML>=6.0.2`); added `[lint]` extras.
- `tests/helpers.py`: robust `_discover_root()` that walks up to
  `pyproject.toml`; `lru_cache` on raw file reads.

### Fixed

- Pre-existing 673-mirror hash drift caused by host-dependent `stat.st_mode`
  in `sha256_tree`. Test `test_all_skills_are_physically_mirrored_and_documented`
  now passes on a fresh clone.
- `validate_source_lock.py` previously crashed without the `--source-root`
  flag, blocking CI integration. Now runs with no arguments.
- Stray dead-code loop in `validate_source_lock.py::validate_mirrors`.
- Python 3.10 incompatibility: `datetime.UTC` (3.11+ only) replaced with
  `datetime.timezone.utc` in `create_source_proof_batch.py`.
- `B904` raise-without-from in `evaluate_external_benchmark_methods.py`
  fallback paths.
- `SIM105` try/except/pass replaced with `contextlib.suppress` in
  `tools/_lib_b/io_utils.py`.
- Stale `docs/installation.md` reference to non-existent
  `tools/fetch_sources.py`.

### Removed

- `pytest.ini` (config consolidated in `pyproject.toml`).

## [0.1.0] — 2026-04-17

Initial public catalog (673 skill mirrors, 19 dataset tracks, 718 scenario
templates, 80 selected entries, 14 external benchmark adapter smoke artefacts).
See [`README.md`](README.md) for the full snapshot.

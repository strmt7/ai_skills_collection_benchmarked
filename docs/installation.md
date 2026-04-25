# Host-, Agent-, and Installation-Agnostic Setup

This repository is designed so that *validation* of the catalog and *every
quality gate run by CI* works on any POSIX-like host, on Python 3.10–3.13,
without root, without a specific username, and without referencing any path
under `/tmp` or `/home/<user>/`.

## Validate from a fresh clone

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e '.[test,lint]'

# 1. Catalog & cross-reference validation (collects all errors, exits non-zero
#    on any drift). Runs offline; no source checkouts required.
python3 tools/validate_catalog.py

# 2. Source-lock validator (offline by default; falls back to env-driven live
#    mode when AI_SKILL_SOURCE_ROOT points at a real directory).
python3 tools/validate_source_lock.py

# 3. Static benchmarks freshness check.
python3 tools/run_static_benchmarks.py --check

# 4. Skill quality / risk audit freshness check.
python3 tools/audit_skill_quality.py --check

# 5. Markdown link reporter (writes docs/local-markdown-link-failures.md).
python3 tools/report_local_markdown_link_failures.py --check

# 6. Secret scan (exits non-zero if ANY secret-shaped string is found in the
#    working tree or git history).
python3 tools/check_no_secret_patterns.py --history

# 7. Lint, format, type-check, and run the full test suite.
ruff check tools tests
ruff format --check tools tests
mypy tools tests
python3 -m pytest -q -n auto
```

Every command above runs without network access. CI uses the same gates plus
`gitleaks` (MIT, pinned binary) as a second-opinion secret scan.

## Reproducible / deterministic regeneration

Generators that produce dated artifacts (catalog, runtime batches, repaired
overlays) honour the [reproducible-builds.org][repro] precedence:

1. `SOURCE_DATE_EPOCH` (Unix seconds since epoch) — explicit pin.
2. The previous run's manifest value — idempotent regeneration.
3. The latest commit time of the relevant input — input-anchored fallback.

```bash
# Pin every dated artifact to a specific instant for reproducible CI builds.
export SOURCE_DATE_EPOCH=1745870400
python3 tools/build_catalog.py --source-root /path/to/ai_skill_sources
```

## Catalog rebuild (requires upstream checkouts)

A full rebuild needs the upstream skill source repositories cloned somewhere on
disk. Point at them with the `--source-root` argument or via the
`AI_SKILL_SOURCE_ROOT` environment variable; the path is never assumed.

```bash
export AI_SKILL_SOURCE_ROOT=$HOME/ai-skill-sources   # any directory you choose
python3 tools/build_catalog.py
python3 tools/validate_source_lock.py --source-root "$AI_SKILL_SOURCE_ROOT" --strict
```

## Why the catalog is host-portable

Tree hashes used in `data/skills_catalog.json`, the manifests, and
`data/source_lock.json` use a git-style portable file mode (`0o100644` /
`0o100755`) so a clone made with `umask 0002` produces the same tree hash as a
clone made with `umask 0022`. The `tests/test_hash_portability.py` module
locks the invariant in: see also `tools/build_catalog.py::_portable_mode`.

[repro]: https://reproducible-builds.org/docs/source-date-epoch/

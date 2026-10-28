# Develop and validate the collection

For installation and skill use, start with [the user guide](installation.md).
This page covers maintaining and validating the collection.

Host-agnostic means no dependency on a particular machine, user profile,
installation path or AI agent. Operating-system requirements remain explicit
for each component. The qualified [Crawl4AI](../toolchains/crawl4ai/README.md) and
[local CocoIndex](../toolchains/cocoindex-code/README.md) providers target Windows
x64. Their guides cover fresh isolated setup without a fixed host path or AI
client.

Catalog validation and Python unit tests exercise supported Python 3.11–3.14
on Linux and the current validation runtime on Windows. Native provider controls
use their documented Windows interpreter and dependency graph. These checks need
no administrator access, specific username or fixed installation path.

Use a supported Python 3.11–3.14 environment; current hosted validation uses Python 3.14.9. Compatibility CI also
selects current security patches for supported older Python series. Python 3.10
has reached end of life. Live services, devices, GPUs, external data sources,
and installed agent runtimes need separate qualification; an offline catalog
check does not prove their behavior. On Windows, use the active environment's
`Scripts/python.exe` in place of `python3` in the commands below.

## Set up validation from a fresh clone

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -e '.[test,lint]'

# 1. Catalog & cross-reference validation (collects all errors, exits non-zero
#    on any drift). Runs offline; no source checkouts required.
python3 tools/validate_catalog.py
python3 tools/validate_agent_tool_policy.py --check --json

# 2. Source-lock validator (offline by default; falls back to env-driven live
#    mode when AI_SKILL_SOURCE_ROOT points at a real directory).
python3 tools/validate_source_lock.py

# 3. Static benchmarks freshness check.
python3 tools/run_static_benchmarks.py --check

# 4. Skill quality / risk audit freshness check.
python3 tools/audit_skill_quality.py --check

# 5. Markdown link reporter (writes docs/local-markdown-link-failures.md).
python3 tools/report_local_markdown_link_failures.py --check

# 6. Scan the working tree and reachable Git history separately.
python3 tools/check_no_secret_patterns.py
python3 tools/check_no_secret_patterns.py --history

# 7. Lint, format, type-check, and run the full test suite.
ruff check tools tests
ruff format --check tools tests
mypy tools tests
python3 -m pytest -q -n auto
```

The in-repository scanner checks its known patterns in replacement-decoded text
and binary file bytes. It does not unpack archives or recognize every encoding
or credential. CI also runs Gitleaks across fetched Git history.

After dependency installation, the validation commands above run without network access. Initial package installation needs the declared package sources. CI uses the same gates plus
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

To update an already cataloged source without re-resolving unrelated repositories,
first verify its stable upstream release, update its declaration in
`tools/build_catalog.py`, and prepare a clean checkout at that exact pinned ref.
Then stage a scoped refresh:

```bash
python3 tools/build_catalog.py --source-root /path/to/ai-skill-sources \
  --credential-policy 3 --refresh-source hugohe3/ppt-master --check --json
```

An expected update makes `--check` report drift and exit nonzero; inspect the
retained staging directory before publishing. Repeat without `--check` to
publish the regenerated catalog through the recoverable publication journal,
then run every applicable quality gate above. The tool verifies all existing
locked mirrors, preserves unrelated source signatures and contents, and records
legacy Git executable modes explicitly for portable staging. It refuses an
update that would rename unrelated skills. Only selected repositories need
source checkouts; retaining a mirror does not establish upstream freshness or
runtime readiness for that source. Neither mode fetches upstream repositories.

Evaluator schemas under `evaluators/` are maintained scoring inputs in the
independent artifact loop; catalog generation never rewrites them. README
packaging and adapter counts come from their existing manifests, which are
also preserved rather than regenerated during a source refresh.

## Why the catalog is host-portable

Tree hashes used in `data/skills_catalog.json`, the manifests, and
`data/source_lock.json` use a git-style portable file mode (`0o100644` /
`0o100755`) so a clone made with `umask 0002` produces the same tree hash as a
clone made with `umask 0022`. The `tests/test_hash_portability.py` module
locks the invariant in: see also `tools/build_catalog.py::_portable_mode`.

[repro]: https://reproducible-builds.org/docs/source-date-epoch/

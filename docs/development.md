# Develop and validate the collection

For installation and skill use, start with [the user guide](installation.md).
This page covers maintaining and validating the collection.

Host-agnostic means no dependency on a particular machine, user profile,
installation path or AI agent. Operating-system requirements remain explicit
for each component. The qualified [Crawl4AI](../toolchains/crawl4ai/README.md) and
[local CocoIndex](../toolchains/cocoindex-code/README.md) providers target Windows
x64. Their guides cover fresh isolated setup without a fixed host path or AI
client.

Follow the [agent efficiency rules](../AGENTS.md#communication-and-execution-efficiency):
bound source reads and tool output, reuse applicable evidence and maintained
runners, and reserve the complete required checks for a frozen publication
batch. These rules preserve reasoning depth, verification and failure reporting.

Windows thread diagnostics use the native Toolhelp snapshot API without starting
PowerShell. They report thread IDs and base priorities; wait states and per-thread
CPU time are unavailable through that API. Process CPU measurements remain
separate. Error and cancellation controls verify ownership of snapshot handles.

Catalog validation and Python unit tests exercise supported Python 3.11–3.14
on Linux and the current validation runtime on Windows. Native provider controls
use their documented Windows interpreter and dependency graph. These checks need
no administrator access, specific username or fixed installation path.

Use a supported Python 3.11–3.14 environment. The main offline validation
matrix uses Python 3.11.18, 3.12.16, 3.13.18 and 3.14.10 on Linux, plus
3.14.10 on Windows. The Ruff job uses 3.14.10 and mypy checks all four series.
Some specialized jobs use their own documented interpreter versions. Python
3.10 has reached end of life. Live services, devices, GPUs, external data sources,
and installed agent runtimes need separate qualification; an offline catalog
check does not prove their behavior. On Windows, use the active environment's
`Scripts/python.exe` in place of `python3` in the commands below.

The main offline-validation matrix explicitly provisions Node 26.13.1 for its
native controls. When qualifying external Python tools in isolated mode, use
explicit text encodings and, where required by the tool, `-I -X utf8 -B`.
`-I` ignores `PYTHONUTF8`; setting that environment variable does not establish
UTF-8 mode for an isolated interpreter.

## Set up validation from a fresh clone

On Windows x64, the automatic entrypoint provisions the complete qualified
validation toolset into an owned cache:

```powershell
.\dev.ps1 doctor
.\dev.ps1 python -m pytest -q -n 2
.\dev.ps1 python -m ruff check tools tests benchmarks/agent-effectiveness/graders
```

No preinstalled Python, uv, Git, Node or JDK is required. Setup checks pinned
downloads, creates isolated Python environments and supplies native tool paths
to child processes. It preserves global packages, persistent PATH, registry
settings and shell profiles. Missing components trigger automatic setup;
recovery preserves prior profiles. See the
[bootstrap guide](../toolchains/bootstrap/README.md) for cache selection and
readiness diagnostics. Native provider setup remains documented separately.

The managed Windows environment enables Git's long-path support for child
commands without changing host Git configuration. Keep full-suite temporary
directories outside the checkout: Git's non-repository fixtures must not
discover the collection as a parent repository. The automatic entrypoint
provides a private temporary directory; use its default for the full suite.

Native setup qualification also recompiles the tracked process supervisor twice
and rejects stale or altered inputs before cache mutation. See the
[rebuild instructions](../toolchains/bootstrap/README.md). Keep a qualification's
complete source and test-fixture inputs unchanged until its process has ended
and its terminal receipt is present. Preserve failed and interrupted attempts;
an observation timeout is not permission to launch a duplicate. Admit actual
output and cleanup evidence as well as exit status. Verify fixture completeness
and the intended failure cause before treating a failed control as a product bug.

For an existing supported Python environment or the Linux CI jobs, use the
locked setup below.

The Ruff, mypy and main offline-validation jobs use
`requirements-dev-lock.txt` with uv 0.13.8.
It locks the project runtime, test, lint and build requirements, including
distribution hashes. Their lock check resolves the existing pins again against
PyPI and rejects changed inputs or hashes. To reproduce the locked environment,
install uv 0.13.8,
create and activate a Python 3.11–3.14 virtual environment, then run:

```bash
python tools/verify_dev_lock.py --json
uv pip sync --require-hashes --only-binary=:all: requirements-dev-lock.txt
uv pip install --no-deps --no-build-isolation -e .
uv pip check
```

Lock verification requires network access. The offline verifier controls use
synthetic wheels and are required in the Ruff and main offline-validation jobs;
without the pinned uv executable they are skipped in other local test runs. A
universal resolution is not a guarantee that binary distributions exist for
every Python or platform. On the weekly schedule and manual dispatch, a separate
test matrix resolves the latest versions allowed by the project requirements and
runs the suite. Those canary environments do not produce the locked coverage
reports or replace the pinned validation jobs.

To regenerate the developer lock after changing project or build requirements,
first create and activate `.venv`, install uv 0.13.8, then run:

```bash
python -c "import pathlib,tomllib; p=pathlib.Path('pyproject.toml'); r=tomllib.loads(p.read_text(encoding='utf-8'))['build-system']['requires']; pathlib.Path('.venv/dev-build.in').write_text('\n'.join(r)+'\n', encoding='utf-8')"
uv pip compile pyproject.toml .venv/dev-build.in --extra test --extra lint --universal --python-version 3.11.18 --generate-hashes --no-strip-markers --only-binary=:all: --no-annotate --no-header --no-config --default-index https://pypi.org/simple --output-file requirements-dev-lock.txt
python tools/verify_dev_lock.py --json
```

Review dependency changes and run the affected checks before committing. Add
`--upgrade` when intentionally updating the resolved versions. The test and
lint lock does not replace the separate audit and report dependency locks.

With the locked environment activated, run the applicable checks:

```bash
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
python3 -m pytest -q -n 2
```

Use fewer workers on constrained hosts. Increase concurrency only after checking
available RAM, CPU and disk activity; do not use automatic host-wide parallelism
by default on a shared workstation. Hosted CI sizes workers to its runner.

When starting managed native tools from Python, use their verified full paths.
The frontend declares `AI_SKILLS_GIT`, `AI_SKILLS_BASH`, `AI_SKILLS_DASH` and
`AI_SKILLS_UNIX_BIN`; maintained shell consumers use those bindings. Resolve
other supplied tools against the private `PATH` before passing their absolute
paths to `subprocess`. Windows can select a system executable before searching
`PATH` for a bare command, including the system WSL `bash` alias. The Windows
toolchain does not require WSL.

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

The [Windows Node control timeout investigation](research-windows-node-timeout.md)
records an intermittent hosted test failure, local controls and its unresolved
cause. A passing retry does not establish that the timeout is fixed.

## Why the catalog is host-portable

Tree hashes used in `data/skills_catalog.json`, the manifests, and
`data/source_lock.json` use a git-style portable file mode (`0o100644` /
`0o100755`) so a clone made with `umask 0002` produces the same tree hash as a
clone made with `umask 0022`. The `tests/test_hash_portability.py` module
locks the invariant in: see also `tools/build_catalog.py::_portable_mode`.

[repro]: https://reproducible-builds.org/docs/source-date-epoch/

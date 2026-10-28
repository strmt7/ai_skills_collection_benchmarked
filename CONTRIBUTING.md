# Contributing

This repository governs three independent work loops (catalog mirror, artifact
& test, and repair overlay). Read [`AGENTS.md`](AGENTS.md) before any change
that touches more than one of those loops.

For skill installation and use, start with the
[user documentation](docs/README.md). To maintain this collection, use
[development setup](docs/development.md). Follow the
[documentation guide](docs/documentation-guide.md) when changing public pages.

## Development on main

Agent-performed development and dependency maintenance take place on `main`.
Other contributors may use pull requests according to the repository's GitHub
permissions and review rules. Validate dependency updates against their affected
installation and runtime contracts, and keep vulnerability alerts and security
checks enabled. Automatic dependency-update PR creation is disabled.

## Quality gates (must pass before push)

Every push runs the following gates in CI; you can run all of them
locally with the toolchain installed via `pip install -e '.[test,lint]'`:

| Gate | Command | Workflow |
| --- | --- | --- |
| Lint | `ruff check tools tests` | `.github/workflows/ruff.yml` |
| Format | `ruff format --check tools tests` | `.github/workflows/ruff.yml` |
| Types | `mypy tools tests` (supported matrix: 3.11/3.12/3.13/3.14) | `.github/workflows/mypy.yml` |
| Catalog | `python3 tools/validate_catalog.py` | `.github/workflows/offline-validation.yml` |
| Mirror byte admission | `python3 tools/check_mirror_content_admission.py --json` | `.github/workflows/offline-validation.yml` |
| Mandatory agent tools | `python3 tools/validate_agent_tool_policy.py --check --json` | `.github/workflows/offline-validation.yml` |
| Static benchmarks | `python3 tools/run_static_benchmarks.py --check` | `.github/workflows/offline-validation.yml` |
| Risk audit | `python3 tools/audit_skill_quality.py --check` | `.github/workflows/offline-validation.yml` |
| Workflow evaluator controls | `python3 tools/report_workflow_evaluator_controls.py --check --json` | `.github/workflows/offline-validation.yml` |
| Frontend component evidence | `python3 benchmarks/component-controls/frontend/prepare.py --check` | `.github/workflows/offline-validation.yml` |
| API/backend component evidence | `python3 benchmarks/component-controls/backend/prepare_backend.py --check` | `.github/workflows/offline-validation.yml` |
| Native fuzzing evidence | `python3 benchmarks/component-controls/native-testing/run_native.py --check`; [Windows runtime controls](docs/research-native-testing-contracts.md) | `.github/workflows/{offline-validation,native-fuzzing-controls}.yml` |
| Measured Python coverage | Complete matrix XML bundle, source hashes and Codecov OIDC; see [coverage scope](docs/coverage.md) | `.github/workflows/offline-validation.yml` |
| Tests | `python3 -m pytest -q -n auto` (supported matrix: 3.11/3.12/3.13/3.14) | `.github/workflows/offline-validation.yml` |
| Compile | `python3 -m compileall -q tools tests` | `.github/workflows/offline-validation.yml` |
| Image CLI acceptance | Source-locked preparation, `npm ci --ignore-scripts`, audit and independent intercepted controls; see [`repair evidence`](docs/research-image-cli-acceptance.md) | `.github/workflows/image-cli-controls.yml` |
| Crawl4AI source build | Two reproducible wheels, complete hashed installations, source admission and identical native controls; see [`provider inputs`](toolchains/crawl4ai/README.md) | `.github/workflows/crawl4ai-provider.yml` |
| CocoIndex local provider | Normal hashed installation, provider/model admission, native indexing and verified source spans; see [`setup and search`](toolchains/cocoindex-code/README.md) | `.github/workflows/cocoindex-provider.yml` |
| Native PPTX retention | Pinned converter pair, deterministic fixture and semantic content checks; see [`consumer inputs`](toolchains/pptx-native/README.md) | `.github/workflows/pptx-retention-controls.yml` |
| Secrets (in-repo) | `python3 tools/check_no_secret_patterns.py --history` | `.github/workflows/secret-scan.yml` |
| Secrets (gitleaks) | `gitleaks git --exit-code 1 .` | `.github/workflows/secret-scan.yml` |
| CodeQL model | `python tools/qualify_defusedxml_codeql_model.py --codeql <codeql> --model .github/codeql/extensions/defusedxml-paths --output <new-directory>` | `.github/workflows/codeql.yml` |

Concurrency, least-privilege read permissions and pip caching are configured
per workflow. In offline validation, only the isolated Codecov upload job receives
`id-token: write`; test jobs keep read-only repository access.
Validation workflows accept `workflow_dispatch` so you can rerun them manually
from the Actions tab. The release workflow remains disabled during the release
hold below.

The local CodeQL model adds file-path sinks for `defusedxml` parsers. CI tests
positive and negative examples and checks that the model was loaded in the
repository analysis. This expands one area of scanner coverage; it does not prove
that the scanned skills are secure.

## Code style

* `ruff` (`>=0.15`) is the single source of truth for both lint and format.
  We enable `E F B SIM UP I` and ignore `E501` (handled by the formatter),
  `B008`, `SIM108`, `UP015`. Per-file ignores live in `pyproject.toml`.
* The minimum supported runtime is **Python 3.11**; production validation uses
  Python 3.14.9 and the matrix exercises current patches of 3.11–3.14. Keep
  annotations and APIs compatible with that support range. The formatter's
  older syntax target remains fixed while independent trials are frozen;
  do not rewrite experimental inputs during a matched comparison block.
* All scripts use a testable `main(argv: list[str] | None = None) -> int`
  signature so they can be exercised from pytest without a subprocess.

## Confined evaluator controls

The [Windows evaluator guide](toolchains/appcontainer/README.md) explains private
runtime setup, native qualification and evaluation of collected validator patches.
Run `python tools/qualify_appcontainer.py --check` with the other local gates.
Its source-bound component evidence does not establish a model or skill advantage.

## DeepSource inventory

Use the [DeepSource inventory guide](docs/deepsource-inventory.md) to retrieve
default-branch occurrences with the official API and verify pagination and
analysis identity. A successful commit status does not establish an empty backlog.

## Determinism

If you add or change a generator, it MUST resolve dated artefacts via
`tools/_lib_b/determinism.py` (precedence: `SOURCE_DATE_EPOCH` → existing
manifest → input-anchored git commit time). Wall-clock APIs (`datetime.now`,
`time.time`) are forbidden in generator output paths.

## Hashes and host portability

`tools/build_catalog.py::sha256_tree` uses a git-style portable mode
(`0o100644` / `0o100755`) so umask differences do not change tree hashes.
Test coverage lives in `tests/test_hash_portability.py`; do not regress.

## Immutable Audit Model

The 673 SKILL.md files under `included/skills/` are mirrored from pinned
upstream commits and MUST NOT be edited by hand. Quality fixes belong in the
upstream repository; this repo records the result and may add a *repaired
overlay* under `included/repaired/` whose generator preserves the original
text byte-for-byte under `provenance/`. See [`AGENTS.md`](AGENTS.md) for the
full rule set.

## Commit attribution

Create commits through the authenticated official GitHub connector and verify
its returned author and committer. The connector assigns contributor identity;
do not override it through Git configuration or environment variables. Inspect
the target tree, parents and current `main` before publication. The full
publication and history-rewrite safeguards are in [AGENTS.md](AGENTS.md).

Use clear imperative commit messages and keep distinct work loops reviewable.
Do not add unrequested co-author trailers. Existing source-bound evidence keeps
its original provenance when history changes.

## Releases

Release `v0.2.0` and its tag were withdrawn. Do not create a release or tag, or
reactivate release publishing, until the owner explicitly requests a new
release. Review the [release requirements](docs/improvement-plan.md), including
independent model benchmarks demonstrating meaningful benefit, before proposing
publication. The changelog remains in [`CHANGELOG.md`](CHANGELOG.md).

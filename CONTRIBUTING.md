# Contributing

This repository governs three independent work loops (catalog mirror, artifact
& test, and repair overlay). Read [`AGENTS.md`](AGENTS.md) before any change
that touches more than one of those loops.

## Quality gates (must pass before merge)

Every pull request runs the following gates in CI; you can run all of them
locally with the toolchain installed via `pip install -e '.[test,lint]'`:

| Gate | Command | Workflow |
| --- | --- | --- |
| Lint | `ruff check tools tests` | `.github/workflows/ruff.yml` |
| Format | `ruff format --check tools tests` | `.github/workflows/ruff.yml` |
| Types | `mypy tools tests` (matrix: 3.10/3.11/3.12/3.13) | `.github/workflows/mypy.yml` |
| Catalog | `python3 tools/validate_catalog.py` | `.github/workflows/offline-validation.yml` |
| Static benchmarks | `python3 tools/run_static_benchmarks.py --check` | `.github/workflows/offline-validation.yml` |
| Risk audit | `python3 tools/audit_skill_quality.py --check` | `.github/workflows/offline-validation.yml` |
| Tests | `python3 -m pytest -q -n auto` (matrix: 3.10/3.11/3.12/3.13) | `.github/workflows/offline-validation.yml` |
| Compile | `python3 -m compileall -q tools tests` | `.github/workflows/offline-validation.yml` |
| Secrets (in-repo) | `python3 tools/check_no_secret_patterns.py --history` | `.github/workflows/secret-scan.yml` |
| Secrets (gitleaks) | `gitleaks git --exit-code 1 .` | `.github/workflows/secret-scan.yml` |

Concurrency, least-privilege `permissions: contents: read`, and pip caching
are configured per workflow. All workflows accept `workflow_dispatch` so you
can rerun them manually from the Actions tab.

## Code style

* `ruff` (`>=0.15`) is the single source of truth for both lint and format.
  We enable `E F B SIM UP I` and ignore `E501` (handled by the formatter),
  `B008`, `SIM108`, `UP015`. Per-file ignores live in `pyproject.toml`.
* Target version is **Python 3.10**; `from __future__ import annotations` is
  required where a module uses `X | Y` in annotations, and the `mypy` matrix
  exercises 3.10 → 3.13 so version-conditional bugs (e.g. `datetime.UTC` is
  3.11+) surface in CI.
* All scripts use a testable `main(argv: list[str] | None = None) -> int`
  signature so they can be exercised from pytest without a subprocess.

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

## Commit identity (hard rule for AI agents)

Every commit produced by an AI agent MUST use the identity `AI agent` with
an **empty** email. The full rule, including forbidden variants and the
rationale, lives in [`AGENTS.md` → "AI commit identity"](AGENTS.md#ai-commit-identity-hard-rule-immutable).
Command-scoped identity keeps the value out of `git config`:

```bash
git -c user.name='AI agent' -c user.email= commit ...
```

Human contributors continue to commit under their real GitHub identity and
email; the rule above applies **only** to AI-generated commits.

### Remediating a bad identity

If an AI commit lands with the wrong author/committer (e.g. a named human,
GitHub noreply, `ai-agent@users.noreply.github.com`, `codex@openai.com`,
`codex@openai.invalid`, or a hyphenated `AI-agent`), rewrite history before
push:

```bash
python3 -m pip install --user git-filter-repo  # once per machine
git filter-repo --force \
  --email-callback 'return b"" if email == b"<BAD_EMAIL>" else email' \
  --name-callback  'return b"AI agent" if email == b"<BAD_EMAIL>" else name'
git remote add origin https://github.com/strmt7/ai_skills_collection_benchmarked.git
git push --force-with-lease origin main
```

Re-run `gh api 'repos/strmt7/ai_skills_collection_benchmarked/contributors?anon=1'`
and every CI workflow after the force-push, and delete/recreate any tags
that pointed into the rewritten range.

## Commit messages

* Use the imperative mood ("Add ruff CI gate", not "Added ruff CI gate").
* If a commit touches more than one work loop, split it.
* AI co-author trailers, if used at all, MUST be `Co-authored-by: AI agent`
  with no email. Do not invent trailers; do not attribute AI work to a
  named vendor, Claude, Codex, Copilot, or a human.

## Releases

This is an alpha. Tag `v0.X.Y` against `main`; the changelog lives in
[`CHANGELOG.md`](CHANGELOG.md). No artefact is shipped to PyPI yet.

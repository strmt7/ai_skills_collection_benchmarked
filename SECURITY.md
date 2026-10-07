# Security Policy

## Reporting a vulnerability

Report security issues **privately** via GitHub's built-in advisory workflow:
open a new draft at
<https://github.com/strmt7/ai_skills_collection_benchmarked/security/advisories/new>.
Include reproduction steps, the commit hash you observed the issue against,
and any suggested remediation. Please do **not** open a public issue for an
exploitable vulnerability.

Expected response: within 7 days. Coordinated disclosure window defaults to
90 days unless a shorter window is negotiated.

## Do not commit credentials

Do not commit credentials or provider-shaped example credentials. Use neutral
placeholders such as `<GOOGLE_API_KEY>`, `<AWS_ACCESS_KEY_ID>`,
`<OPENAI_API_KEY>`, or `<TOKEN>` in docs and fixtures. Strings that match
real provider token formats are rejected by the in-repo scanner even when
the value is intended as an example.

## Local scans before pushing

```bash
python3 tools/check_no_secret_patterns.py --history     # in-repo regex + entropy
```

Run the CI's second-opinion gate locally with its pinned, SHA256-verified
Gitleaks v8.30.1 binary. The download and digest verification commands are
maintained in `.github/workflows/secret-scan.yml`; after verification, run:

```bash
gitleaks git --log-opts="--all --full-history --no-renames" \
  --redact --verbose --no-banner --exit-code 1 .
```

## CI security gates (runs automatically on push, pull_request, and weekly cron)

| Gate | What it does |
| --- | --- |
| `tools/check_no_secret_patterns.py --history` | Context-aware regex + Shannon-entropy scan over the full git history |
| `gitleaks git --log-opts="--all --full-history --no-renames" .` | Pinned MIT binary (v8.30.1, SHA256-verified), all fetched refs and complete patches |
| `pip-audit --strict -r requirements-lock.txt` | Daily CVE scan against the pip-compile lockfile |
| Dependabot weekly updates | Grouped minor+patch PRs for `github-actions` and `pip` ecosystems |
| Workflow `permissions: contents: read` | Least-privilege default token on every workflow |

## Token / secret handling for maintainers

- Never paste a real PAT into commit messages, docs, or example fixtures.
- When pushing from a CI or local terminal, prefer `GH_TOKEN` env var over a
  URL-embedded PAT so the token never reaches the reflog or stored remote URL.
- The `.github/workflows/*.yml` files use least-privilege `permissions:` blocks.
  Do not add broader scopes without justification in the PR description.

## Supply chain

- Runtime and test dependencies are pinned in `requirements-lock.txt` with
  hash verification. Re-generate via `pip-compile --generate-hashes` when
  bumping `pyproject.toml`. The `pip-audit` workflow verifies the lockfile is
  in sync with `pyproject.toml` on every push.
- GitHub Actions use full immutable commit SHA pins with stable release names
  in comments; Dependabot proposes updates weekly. Release resolution and
  successful workflow execution are checked separately.
- The standalone secret-scanner workflow installs the hash-locked minimal
  runtime from `requirements-runtime-lock.txt` before invoking the scanner.

## What about the immutable mirrored skills?

`included/skills/**` contains upstream public-GitHub source text mirrored at
pinned commit SHAs. Those files are governed by the Immutable Audit Model in
[`AGENTS.md`](AGENTS.md) and are covered by both secret scanners and CodeQL.
There are no mirror path exemptions in `.gitleaks.toml`. Public provenance
does not make credential-shaped text acceptable: mirroring applies only the
declared deterministic credential neutralizations and dependency advisory
floors, with source hashes and transformation records retained.

Preserve source defects as findings until a corrected upstream commit is
qualified and the catalog is regenerated. Maintained improvements belong in
licensed overlays with exact original provenance, not silent mirror edits.
A repair overlay does not close a finding in the original mirror.

Retain scanner results and source-grounded triage evidence. A public digest,
path or synthetic test value can be a noncredential match, but an audit
classification does not turn a failing native scanner into a passing gate.
Do not suppress findings, add path exemptions, or claim zero findings without
fresh results for the published revision and fetched history.

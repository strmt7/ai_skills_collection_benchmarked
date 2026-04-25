# Security Policy

## Reporting a vulnerability

Email the repository owner at `thomdehoog@gmail.com` with the subject line
`ai-skills-collection-benchmarked security: <short description>`. Include
reproduction steps, the commit hash you observed the issue against, and any
suggested remediation. Please do **not** open a public issue for an
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

Optionally mirror the CI's second-opinion gate locally:

```bash
curl -fsSLo /tmp/gitleaks.tgz \
  https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz
tar -xzf /tmp/gitleaks.tgz -C /tmp gitleaks
/tmp/gitleaks git --redact --no-banner --exit-code 1 .
```

## CI security gates (runs automatically on push, pull_request, and weekly cron)

| Gate | What it does |
| --- | --- |
| `tools/check_no_secret_patterns.py --history` | Context-aware regex + Shannon-entropy scan over the full git history |
| `gitleaks git .` | Pinned MIT binary (v8.30.1, SHA256-verified) as a second-opinion scan |
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
- GitHub Action versions are pinned to a named stable tag plus a documented
  SHA in workflow comments; Dependabot proposes updates weekly.

## What about the immutable mirrored skills?

`included/skills/**` contains upstream public-GitHub source text mirrored at
pinned commit SHAs. Those files are governed by the Immutable Audit Model in
[`AGENTS.md`](AGENTS.md); the in-repo scanner and `gitleaks` both allowlist
that subtree because we cannot patch upstream documentation. Any credential-
shaped text inside those mirrors is provenance — report such findings upstream
to the respective skill authors.

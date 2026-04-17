# Official Guidance

- GitHub Docs recommend `package-ecosystem: "github-actions"` with
  `directory: "/"` for workflow version updates.
- GitHub Docs document `paths-ignore` in the CodeQL configuration file as the
  correct place to exclude directories from analysis.
- Official GitHub release sources should be used to confirm current stable
  action versions before changing major tags.
- Official package index metadata should be used to confirm current stable
  Python tool versions before changing workflow or dev pins.

Primary references:

- https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/keeping-your-actions-up-to-date-with-dependabot
- https://docs.github.com/en/code-security/reference/code-scanning/workflow-configuration-options
- https://github.com/actions/checkout/releases
- https://github.com/actions/setup-python/releases
- https://github.com/github/codeql-action

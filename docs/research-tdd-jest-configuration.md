# Testing workflow: Jest coverage configuration

The pinned [testing-workflow skill](../included/skills/by-category/testing-qa-benchmarking/selected-structure-reference/tdd-workflow-everything-claude-code/SKILL.md)
uses `coverageThresholds` in a `package.json` Jest example. Jest documents the
singular [`coverageThreshold`](https://jestjs.io/docs/configuration#coveragethreshold-object).
The [maintained overlay](../included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/tdd-workflow-everything-claude-code/SKILL.md)
corrects the example and keeps the original text in its provenance directory.

With Jest 30.5.2, an isolated fixture had one passing test but only 50% branch
coverage. On both [Windows](../artifacts/repaired-skill-readiness/tdd-jest-v1/windows-result.json)
and [Linux](../artifacts/repaired-skill-readiness/tdd-jest-v1/linux-result.json),
the original option produced an unknown-option warning and exited 0. The overlay
example rejected the same under-covered fixture and accepted a separate fixture
covering both branches. The 80% threshold in this control tests the example; it
is not a recommendation to impose that threshold on every project.
The same three outcomes were reproduced with Node 26.13.0 on
[Windows](../artifacts/repaired-skill-readiness/tdd-jest-v1/node26-windows-result.json)
and [Linux](../artifacts/repaired-skill-readiness/tdd-jest-v1/node26-linux-result.json),
using the same isolated dependency locks as the earlier Node 24 controls.

The same example was present in the observed [upstream main commit](https://github.com/affaan-m/everything-claude-code/commit/b38be6a7f6350964d59328b52f0624e1d1d552d1),
and produced the same selected outcomes on
[Windows](../artifacts/repaired-skill-readiness/tdd-jest-v1/upstream-windows-result.json)
and [Linux](../artifacts/repaired-skill-readiness/tdd-jest-v1/upstream-linux-result.json).
That source check is not a full upstream update or skill review.

[Google's testing guidance](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html)
describes coverage as a way to identify gaps, not a universal measure of test
quality. [Playwright's page documentation](https://playwright.dev/docs/api/class-page#page-wait-for-timeout)
discourages fixed sleeps as production test readiness checks. Honor a project's
own requirements and choose checks based on the behavior and risk involved.

To repeat the component control, install Jest 30.5.2 in an isolated directory
outside this clone, retain its `package-lock.json`, and run from the repository
root with the path to that installation's `node_modules/jest/bin/jest.js`:

```bash
python artifacts/repaired-skill-readiness/tdd-jest-v1/reproduce.py --skill included/skills/by-category/testing-qa-benchmarking/selected-structure-reference/tdd-workflow-everything-claude-code/SKILL.md --overlay included/repaired/skills/by-category/testing-qa-benchmarking/selected-structure-reference/tdd-workflow-everything-claude-code/SKILL.md --jest /path/to/isolated/node_modules/jest/bin/jest.js --output /path/to/result.json
```

The recorded Node versions and dependency-lock hashes are in the result files;
native logs and complete locks were retained outside the repository. Pass
`--node /path/to/node` to select a specific executable instead of `PATH`. Exact
`--check` reproduction requires the same Node version and lock. A fresh install
can resolve different transitive packages. The script checks the source content
hash; a supplied source-commit value is metadata and must be verified against
the source lock or upstream Git tree separately. This synthetic component
control does not establish coding-agent improvement or release readiness.

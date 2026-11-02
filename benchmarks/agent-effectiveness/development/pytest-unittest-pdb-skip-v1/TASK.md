# Development task: skipped unittest classes with `--pdb`

This public, development-exposed task adapts
[pytest issue 10060](https://github.com/pytest-dev/pytest/issues/10060). It is
not a holdout or a recorded agent benchmark result.

## Task brief

In the supplied pytest checkout, a `unittest.TestCase` class decorated with
`unittest.skip` is reported as skipped. With `--pdb`, its `tearDown` method can
nevertheless run even though `setUp` and the test did not. Correct the
behavior for class-level skips, including inherited and conditional skips.

Preserve method-level skip behavior, pytest's skip markers, and the normal
lifecycle of tests that run. For an actual failing test under `--pdb`, preserve
the existing behavior that enters the debugger before running `tearDown`.
Add meaningful regression coverage and run the relevant project checks.

## Source and evaluation boundaries

Use the complete pytest checkout at the pinned commit in `source.json`. The
task and its public issue are exposed development material; the controls and
reference patch are available to maintainers and must not be placed in an
agent's task workspace. The controls are independent of skill text but are
not hidden from this development process. They do not establish that a task
will discriminate between models or conditions.

The controls execute trusted source variants in subprocesses; they are not a
confined grading service and must not be used to execute agent submissions.
Model trials still require the qualified runner and grader described in the
[trial protocol](../../../../docs/agent-trial-protocol.md).

# Testing a meaningful failing baseline

The pinned [TDD workflow](../included/skills/by-category/testing-qa-benchmarking/selected-structure-reference/tdd-workflow-everything-claude-code/SKILL.md)
asks for a failing test before implementation but does not say to check why it
failed. A failed command alone is ambiguous: a test can fail during setup
without reaching the behavior it was supposed to check.

The independent [pytest control](../tests/test_tdd_red_phase_controls.py)
creates a passing test, a failing assertion, a fixture setup error and a skipped
test. It checks the individual structured test-case outcomes and runs the
assertion and setup cases separately. On Windows with Python 3.14.10 and
pytest 9.2.0, each separate run returned exit code 1, but one recorded a test
failure and the other a setup error. A no-match selection returned exit code 5
and contained no test cases. The [pytest exit-code reference](https://docs.pytest.org/en/stable/reference/exit-codes.html)
documents the meaning of its process exit codes; actual case outcomes still
need inspection. These observations are specific to this fixture and runner,
not a claim that every test runner uses the same exit codes or report format.

The [experimental revision](../included/improved/skills/tdd-workflow-current/SKILL.md)
asks agents to establish that the intended test ran and that its failure
demonstrates the behavior under test, where a failing baseline is practical.
It distinguishes setup failures, skips and unavailable baselines from evidence
of a reproduced defect. The original mirror and the earlier Jest-focused repair
remain unchanged. This component control tests the distinction, not whether an
agent follows the skill or performs better on a coding task.

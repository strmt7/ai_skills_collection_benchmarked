# Read coverage and benchmark results

The Codecov badge measures tests of this collection's Python tooling under
`tools/`. Use it to inspect exercised code and changed lines. It does not measure
the quality of a skill, its instructions or an AI agent's coding ability.

| Evidence | What it helps you assess | What it does not establish |
| --- | --- | --- |
| Python tooling coverage | Which tooling lines and branches the test suite exercised | Skill efficacy or security completeness |
| Catalog and source checks | Packaging, links, locked sources and generated-file consistency | Successful real-world execution |
| Component controls | Specific executable examples against declared contracts | Whole-skill readiness or agent advantage |
| Independent agent trials | Task outcomes under a recorded model, budget and environment | Results for untested tasks, models or installations |

See [benchmark results](benchmark-results.md),
[frontend controls](../benchmarks/component-controls/frontend/README.md) and
[API/backend controls](../benchmarks/component-controls/backend/README.md)
for the corresponding methods and limitations. Selected excerpt improvements
are useful evidence of repairs; an advantage over a default agent requires
separate, independently scored model trials.

The coverage workflow retains each measured XML report from the existing
Python/OS matrix. A separate job validates the complete bundle and binds its
referenced tooling files to the checked-out source before upload. Codecov merges
those reports under the `python_tooling` flag. No carryforward is enabled for
that flag. Native TypeScript/Go example controls, source mirrors and instructions
are outside this Python coverage percentage.

The bundle validator checks that the reports agree on source files and that
their declared line totals and rates match distinct recorded lines. It rejects
unsafe upload paths and inconsistent reports. Its hash-locked XML parser rejects
DTDs and declared entities while allowing ordinary XML comments. These checks do not
prove that a report recorded every executable line or that the observations
were honestly produced; the workflow and its retained test artifacts provide
the execution context.

The configuration follows FlitzZip's measured-report approach: SHA-pinned
Codecov Action, a pinned CLI, GitHub OIDC, explicit report paths and upload
failures that fail CI. No upload secret is stored. The project status compares
with the base commit at zero tolerance; the 90% patch target is informational.
The existing 45% local minimum remains a coarse floor rather than a claim of
complete test coverage. See the
[Codecov policy](../.github/codecov.yml) and
[workflow](../.github/workflows/offline-validation.yml).

An unavailable badge or failed upload means the hosted measurement is not
confirmed; consult that commit's workflow and retained receipt. No green status
or missing finding should be inferred from an absent report.

Contributors can inspect the
[documentation and workflow research](documentation-guide.md) for the design
choices and primary sources.

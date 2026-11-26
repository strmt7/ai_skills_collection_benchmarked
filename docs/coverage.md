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

Multi-task trial reports keep the measured mean unavailable if any planned
attempt is unscored. They also show hypothetical lower and upper bounds for
the equal-task-weighted pass-rate difference: for each unscored attempt,
consider a pass or a failure while retaining all planned attempts in the
denominator. The chart labels this range when outcomes are missing. These are
extreme assignments, not observed outcomes, predictions of reruns, confidence
intervals or proof of an advantage. An invalid-scope attempt, for example,
may not have a meaningful binary outcome until the experiment is corrected.
The bounds do not address task selection, model identity, grading authenticity
or other sources of bias. The [Cochrane Handbook](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-10)
describes the general use and limitations of extreme-case missing-data
sensitivity analysis; its clinical setting differs from these agent trials.

Each Python and OS job records the tooling sources before and after pytest.
A passing job retains the native XML and a producer receipt with the commit,
the matrix lane and SHA-256 digests of the report and measured files. The
upload job verifies all five expected lanes against its checkout before
sending the XML to Codecov. Codecov merges the reports under the
`python_tooling` flag with carryforward disabled.

The validator compares declared line totals and rates with the recorded lines.
It can detect replaced reports even when two revisions share the same line
numbers. The retained test runs and producer receipts give each measurement
its execution context.

The configuration follows FlitzZip's measured-report approach: SHA-pinned
Codecov Action, a pinned CLI, GitHub OIDC, explicit report paths and upload
failures that fail CI. No upload secret is stored. The project status compares
with the base commit at zero tolerance; the 90% patch target is informational.
The measured job enforces the 45% floor for a full suite run. See the
[Codecov policy](../.github/codecov.yml) and
[workflow](../.github/workflows/offline-validation.yml).

An unavailable badge or failed upload means the hosted measurement is not
confirmed; consult that commit's workflow and retained receipt. No green status
or missing finding should be inferred from an absent report.

## Run tests with coverage

Use the [locked development environment](development.md#set-up-validation-from-a-fresh-clone).
With a clean `tools/` checkout, run the full suite with the same producer
used by CI. Choose a new output directory for every measurement.

```sh
python tools/record_coverage_shard.py --directory .venv/reports/local-coverage --lane coverage-local --pytest-args -q -n 2
```

For normal development, run `python -m pytest -q` with a test path or node ID
to check just the behavior you changed.

Contributors can inspect the
[documentation and workflow research](documentation-guide.md) for the design
choices and primary sources.

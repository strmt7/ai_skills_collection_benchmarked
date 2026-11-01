# Azure Pipelines Node example review

The pinned `azure-pipelines-generator` skill's basic CI example assumes that
`npm test -- --coverage` works for every Node project. A valid project whose
`test` script is `node --test` passed `npm test`, but that exact example command
exited with an unsupported-option error in Node 24.22.2 and 26.13.0. Other test
frameworks can accept different flags; this observation is specific to the
native Node test runner and the recorded fixture.

The example also sets `continueOnError: true` on lint. Microsoft documents
that downstream decisions treat the failed step as successful when this setting
is enabled. Its test publisher does not set `failTaskOnMissingResultsFile`,
whose documented default is false. See [task behavior](https://learn.microsoft.com/en-us/azure/devops/pipelines/process/tasks?view=azure-devops)
and [PublishTestResults@2](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/publish-test-results-v2?view=azure-pipelines).
These observations do not claim that the sample's failed test command becomes
a passing pipeline.

The example selects `NodeTool@0`, Node 20 and `ubuntu-22.04`. As observed on
1 November 2026, Microsoft marks [NodeTool@0 as deprecated](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/node-tool-v0?view=azure-pipelines),
Node lists [version 20 as end-of-life](https://nodejs.org/en/about/previous-releases),
and Microsoft schedules [the hosted Ubuntu 22.04 image for removal](https://learn.microsoft.com/en-us/azure/devops/pipelines/agents/hosted-deprecation-schedule?view=azure-devops)
on 17 April 2027. The image notice concerns Microsoft-hosted agents; it does
not retire self-hosted Ubuntu installations. Version choices must be checked
against the actual project's requirements and the current service documentation.

## Maintained Node CI example

The [separate overlay](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/latest-release-devops/azure-pipelines-node-ci/SKILL.md)
covers only an npm project with a lockfile, a lint script and a `test` script
that is exactly `node --test`. Its example selects [UseNode@1](https://learn.microsoft.com/en-us/azure/devops/pipelines/tasks/reference/use-node-v1?view=azure-pipelines),
Node 26.13.0 and `ubuntu-24.04`, keeps lint and test failures blocking, and
requires successful publication of a JUnit result. A Python 3 step also requires
at least one non-skipped test case: a JUnit file can exist even when no tests
were discovered. One case does not establish that the intended suite ran. The
example requires `python3` on the selected agent and does not invent a coverage
report. The [observed Ubuntu 24.04 image documentation](https://github.com/actions/runner-images/blob/4da2307112a0fad2fd2ecaca8ba7d08683b8c581/images/ubuntu/Ubuntu2404-Readme.md)
lists Python 3.12.3; the actual Azure-hosted agent was not exercised. Node
documents the [JUnit reporter](https://nodejs.org/api/test.html#test-reporters)
and notes that reporter output can change between releases.

The [local controls](../artifacts/repaired-skill-readiness/azure-pipelines-node-ci-v1/qualification.json)
ran on Windows and Ubuntu 24.04.5 with Node 24.22.2 and 26.13.0, using both
the bundled npm versions and npm 12.2.1. The new test command produced a JUnit
file for both a passing and an intentionally failing test; the lint command
also returned nonzero for a deliberate failure. Empty and all-skipped test runs
returned zero from Node but were rejected by the count check. On Linux, the
controls executed the exact Bash step from the example; on Windows they ran
the equivalent Python body directly. The examples are component
controls, not agent trials. No Azure pipeline was run, so hosted-image behavior,
task execution, triggers and result publication require validation in the
intended Azure organization. Azure Repos PR validation is configured through
[branch policies](https://learn.microsoft.com/en-us/azure/devops/pipelines/yaml-schema/pr?view=azure-pipelines),
while trigger behavior differs for other repository providers.

The original mirror is unchanged. At observed upstream commit
`276af751e659315aaf56d3ad13d7c26f4e72e28a`, the skill entrypoint and basic CI
example have the same Git blob IDs as the pinned commit
`7fe7595e4512f8ce43dcf956aa5190b96d627dd1`; the source directory's only
recorded tree change is removal of `.gitignore`. This comparison does not
qualify the remaining examples or the source repository as a whole.

To reproduce locally, install the hash-pinned PyYAML requirement in a dedicated
Python environment, then run `reproduce.py` with explicit `--source`,
`--candidate`, `--node`, `--npm-cli` and a new `--output` directory. The
control creates only its own fixture, uses npm's offline mode, and records raw
command streams and JUnit files there. The [workflow](../.github/workflows/azure-pipelines-node-control.yml)
exercises the same controls on GitHub-hosted Windows and Linux runners; it does
not simulate Azure Pipelines. Native web captures and the full upstream tree
responses are retained outside Git; their digests are in the recorded evidence.

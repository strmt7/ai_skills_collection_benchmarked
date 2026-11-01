---
name: azure-pipelines-node-ci
description: Create a basic Azure Pipelines CI configuration for a Node.js project using npm and the native Node test runner.
license: Apache-2.0
---

# Azure Pipelines for a Node.js project

For every task, apply Caveman. Before broad repository navigation, use
CocoIndex Code; for web-page research, use Crawl4AI. Read and follow the
repository-root `docs/agent-tools.md` and the three linked skills, and retain
the required execution evidence.

This maintained overlay covers a basic lint-and-test pipeline for a project with
an npm lockfile, a `lint` script, a `test` script that is exactly `node --test`,
and Python 3 available as `python3` on the agent. It does not cover deployment,
other package managers, other test frameworks, coverage reporting or Azure
DevOps Server. Inspect the project's
actual scripts, runtime requirements and supported Azure environment before
using the example; do not assume that arbitrary `npm test` scripts accept the
same flags.

Start from [the example](examples/node-ci.yml) only when its prerequisites
match. It pins Node 26.13.0 and the Microsoft-hosted `ubuntu-24.04` image;
choose a maintained version compatible with the project and validate changes.
Install from the existing npm lockfile, fail the job on lint or test failures,
and publish the native test runner's JUnit output. The example requires at least
one non-skipped test case; that alone does not prove the complete intended suite
ran. A missing result file or a failure to publish is an error. Add
project-specific build and coverage steps only when the project provides and
verifies their actual outputs.

Run the project's commands in an isolated copy, including deliberate lint and
test failures, and inspect the resulting JUnit file. Validate and run the YAML
in the intended Azure organization and repository before relying on its hosted
behavior. The recorded controls exercise the local commands and parse the YAML;
they did not execute an Azure pipeline. Azure Repos pull-request validation
requires an appropriate branch policy; configure triggers and policies for the
repository provider and user requirements.

The original upstream instructions and example are retained under `provenance/`.
The overlay's component controls are not a coding-agent benchmark or proof that
the full upstream skill works.

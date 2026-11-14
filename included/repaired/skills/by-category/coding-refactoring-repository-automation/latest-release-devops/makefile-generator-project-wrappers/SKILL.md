---
name: makefile-generator-project-wrappers
description: Repair Python, Java and generic GNU Make wrappers that report false success, miss changed inputs or clean dependency environments. Preserve the actual project build system and test runner; use when adapting the collection's original Makefile generator.
license: Apache-2.0
---

# Project build wrappers

Before repository work, read and apply Mandatory agent tools at the repository
root, `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad
navigation, and Crawl4AI for web-page research. Retain actual execution evidence.
Original source text is retained in `provenance/`. This instruction repair has
component evidence and remains unbenchmarked for agent efficacy.

Inspect the existing build entrypoints, supported OS, shell, architecture,
runtime, source roots and dependency locks. Extend the project's native build
system instead of replacing it with a generic generator. Bind tools to verified
executables in the current installation; never assume another user's paths.
Provision missing compatible dependencies into owned isolated caches with
publisher verification and complete resolved locks. Keep licenses, bound setup
and child processes, preserve the host, and report failed setup precisely.
The attached evidence qualifies private Linux component setup, not a supported
automatic installer for every end-user host.

## Python

Use the selected project interpreter for build, install and test operations.
Check its actual virtual-environment prefix before installing. Keep dependency
installation inside that environment; do not upgrade the system interpreter's
packages. A pip installation that supports `--python` can manage a separately
created environment without pip. Qualify the complete resolved graph with the
native resolver, `pip check` and a fresh hash-locked reinstall; a list of newest
individual releases is not a dependency solution.

Preserve real package builds and pytest execution where the project uses them.
Verify wheel/sdist contents and the requested development extra instead of
inventing package layouts or assuming `[dev]` exists. An intentional test failure
must fail the wrapper. No tests collected is a separate outcome.

Use the project's existing formatter and linter configuration. Do not introduce
Black, isort, Flake8 and Pylint merely because a template lists them. If Black
and isort are already required, use a compatible isort profile and matching line
lengths. Run both check modes after formatting and require a stable second pass;
two successful mutation commands can leave incompatible formatting behind.
The component configuration used line length 120; retain another project's
explicit policy rather than imposing this number globally.

Clean only outputs whose ownership is established. Identify exact build,
distribution, coverage and cache paths from the project configuration. Validate
their resolved locations before recursive removal. A repository-wide search
for `__pycache__` crosses into nested environments and dependencies. Leave
dependency environments, vendored trees, unrelated siblings and linked paths
alone. If project cache ownership is unclear, leave those disposable caches
instead of broadening deletion. Verify retained sentinel bytes as well as
removed outputs when changing this boundary.

## Java

Keep the existing Maven/Gradle wrapper or other project build entrypoint. Check
its declared JDK and wrapper/dependency integrity; a newer JDK is not automatically
compatible with the project's release target. Do not copy the original template's
source-only `.compiled` timestamp gate into a dependency-aware build.

For a native `javac`/`jar` project, account for the full source inventory,
compiler options and classpath inputs, including changed dependency JARs and
removed sources. Do not put obsolete classes in a newly packaged JAR. Prefer
the existing build tool's incremental logic. A fresh, owned output directory
can establish correctness for a small native build; it does not establish an
incremental performance improvement. Separate production and test source/output
sets and adapt classpath separators and argument handling to the actual platform.

Invoke the actual test runner with real discovery or explicit test class names.
Calling `org.junit.runner.JUnitCore` with no names can succeed with zero tests.
Use engines compatible with the existing test API; do not relabel JUnit 4 tests
as Jupiter tests or migrate a project merely to use a new launcher. The current
JUnit console's `execute --fail-if-no-tests` distinguishes empty discovery from
success. Keep this distinction in the wrapper and propagate genuine failures.

Verify a removed source is absent from a new archive, a deliberately incompatible
dependency causes a build failure, one real test executes successfully, a real
test failure fails, and empty discovery remains visible. Maven/Gradle execution
and arbitrary dependency graphs require their own qualification.

## Generic projects

A generated target that only prints instructions is a scaffold, not a successful
build or test operation. Connect targets to the project's actual commands.
Until a requested operation is configured, fail it with a useful diagnostic;
keep help available separately. Do not invent executable `--test` flags,
synthetic passing tests or installation destinations.

After configuration, inspect an actual produced artifact and execute an actual
test. Introduce a controlled failure and verify the wrapper preserves it. This
checks the wrapper boundary; it does not prove the project's entire test suite
or skill efficacy.

## Evidence limits

The controls used GNU Make 4.3, Python 3.12.3 with an isolated resolved tool
environment, Temurin JDK 27.0.1.0.2+1 and JUnit Console 6.1.3 on Linux x64.
The base Python/Make versions are compatibility observations, not claims that
they are the latest releases. Native Windows language execution, maintained
end-user SDK provisioning, Maven/Gradle, deployment, every guide example and
security review remain outside these controls. C/C++ and Go have separate
repairs. No model benchmark score or speed improvement is established here.

# Provider checks

Choose the provider after confirming the project already has a passing
test command. Use the provider's released documentation and native help
for exact configuration keys, supported languages, and downloaded artifacts.
Keep tooling in the project's declared dependency environment or in an
owned disposable profile.

## Mewt and Muton

The stable packages reviewed here are Mewt 4.0.0 and Muton 3.1.0. Their
upstream release manifests list prebuilt Apple Silicon macOS and x64 Linux
artifacts. Mewt documents Windows as unsupported. Verify the available
release before changing the project's package or environment. Check a
same-platform alternative when the required tool has no supported build.

The projects have separate version lines, supported languages, and result
contracts. With Mewt 4.0, use the documented top-level per-target entries
and version-specific test fields. Inspect effective settings and selected
targets before running. Export any useful database results before purging.
Preserve lower-severity skips separately from detected mutations and
confirm the documented score denominator for the exact release.

[Mewt releases](https://github.com/trailofbits/mewt/releases)
[Muton releases](https://github.com/trailofbits/muton/releases)

## StrykerJS

For JavaScript or TypeScript, select a test-runner plugin that supports the
existing project or use the command runner with the existing test command.
With the command runner, follow the selected StrykerJS release's coverage
analysis requirements. Configure one worker initially, scope the listed
source files explicitly, and retain the native JSON report. Raise worker
count after confirming host capacity and reproducibility.

StrykerJS 10.1.1 and Node.js 24.22.3 exercised a single-source,
single-worker command-runner campaign on Windows x64. An isolated
compatible npm profile used a verified package lock and disabled package
lifecycle scripts. Both valid suites passed before mutation. The tool
also rejected a deliberately failing reference suite without a mutation report.
That scoped control supports this workflow; qualify any different runner,
language, runtime, and platform using their own outcomes.

[StrykerJS configuration](https://stryker-mutator.io/docs/stryker-js/configuration/)
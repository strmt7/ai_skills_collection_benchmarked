---
name: bash-script-generator
description: Create or modify shell scripts using the requested shell and validate the actual output.
---

# Shell script generation

Before repository work, read and apply Mandatory agent tools in the repository root at `docs/agent-tools.md`: Caveman for every task, CocoIndex Code before broad code navigation, and Crawl4AI for web-page research. Retain actual execution evidence.

Determine the intended interpreter, inputs, outputs, failure behavior and target environment from the request and existing project. Default to Bash only when no different shell is required. Use the project's conventions and dependencies; do not promise POSIX `sh` portability for Bash-specific syntax or a Bash scaffold. For a POSIX `sh` target, write for that shell and check the actual supported implementations; a syntax check alone does not establish portability.

Implement the requested behavior with appropriate argument handling and meaningful tests. Validate **the generated script itself**, using the intended interpreter's syntax check and, when available, ShellCheck configured for that interpreter. Run representative behavior and failure cases in an isolated test workspace. Report commands, results, unavailable checks and remaining limits. A syntax check does not run the script or establish functional correctness.

Do not assume `set -e` handles every failure. In Bash, a function called as an `if` condition can continue after a failing command even when `errexit` is enabled; explicitly propagate failures that matter. With Bash `pipefail`, check the pipeline result and do not interpret it as identifying the command that finished last. Test the actual control flow and shell versions used by the script.

The upstream `scripts/run_ci_checks.sh` checks the skill's bundled files and its own regression tests; it does not accept the generated script as an input. Its passing result is not validation of the user's output. The upstream standard template uses Bash features and is not a POSIX `sh` scaffold.

The original upstream instructions are preserved at `provenance/original.SKILL.md`. This overlay addresses selected interpreter and validation issues; its component controls do not measure coding-agent effectiveness.

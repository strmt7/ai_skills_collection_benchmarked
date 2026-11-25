---
name: bun-runtime-current
description: Use when maintaining a Bun project, evaluating a Node-to-Bun migration, or diagnosing Bun package, test, runtime, or bundler behavior.
license: MIT
metadata:
  source: affaan-m/everything-claude-code
  source-commit: c05b2d6614f62f6db0047669aa4eefb223d478f9
  revision-status: experimental-unbenchmarked
---

# Work with Bun reliably

Read the project's commands, package manager declaration, lockfiles,
`bunfig.toml`, CI and deployment settings. Identify which roles Bun serves
today. Installing dependencies, running source, executing tests and targeting a
bundle are separate choices. Change only the roles the task requires.

## Reproduce installation

Use the project's admitted Bun version and the appropriate publisher build for
the host CPU. Find the project or workspace root that owns the dependency graph.
For a reproducible Bun install, require the project's committed, compatible Bun
lock file before invoking `bun install --frozen-lockfile`. Confirm the lock
remains unchanged and that the intended dependency resolves from a clean
checkout. On Bun 1.4.5, a frozen install without any lockfile can succeed and
leave the project unlocked. [Bun lockfiles](https://bun.com/docs/pm/lockfile)

For a package-manager migration, compare the previous and proposed graphs.
Check workspace links, peer resolution, lifecycle scripts and native add-ons
that the project uses. Update the lock, install commands and CI as one verified
change.

## Check behavior at each changed boundary

Run the project's real test command. Verify the intended cases ran and a wrong
assertion fails in an isolated control. Run the project's type checker
separately. Bun can execute transpiled TypeScript with invalid static types.
Use shell-appropriate environment syntax or the project's declared environment
file. [Bun test runner](https://bun.com/docs/test)

Exercise the actual application entrypoint and the Node APIs, module formats
and native dependencies it uses. Use a Bun-specific API only when the declared
runtime and consumers support it. Choose the bundle target explicitly, and
execute the result with that target runtime. Check deployment settings against
the platform's current documentation and verify the deployed entrypoint.
[Bun runtime](https://bun.com/docs/runtime)

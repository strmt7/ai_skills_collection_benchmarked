---
name: nextjs-turbopack-cache
description: Diagnose Next.js bundler and filesystem-cache behavior using the project's installed release, configuration and measured workload.
license: MIT
metadata:
  source: affaan-m/everything-claude-code
  source-commit: 846ffb75da9a5f4e677d927af1ad4a1951652267
  revision-status: experimental-unbenchmarked
---

# Next.js bundler and cache decisions

Before repository work, follow the root [agent-tool policy](../../../docs/agent-tools.md).
Inspect the installed Next.js version, lockfile, scripts, configuration, router,
deployment and tests. Use the installed CLI and documentation for that version;
preserve existing webpack plugins and application behavior unless a change is
requested and validated.

Next.js documents Turbopack as the default for `next dev` and `next build` in
version 16. The earlier 16.4.3 component check confirmed that build default,
accepted `--webpack`, and rejected `--no-turbopack`; do not assume those CLI
details apply unchanged to every release. Webpack plugins do not automatically
work with Turbopack. Verify actual plugin and loader compatibility before a switch.

## Filesystem cache

Check the project's explicit options before relying on defaults. Next.js's
version history says development filesystem caching became default in 16.1,
and build filesystem caching became default in 16.3; 16.0 introduced separate
opt-in flags. Later releases or project overrides can differ. Selected package
configuration exports were checked for 16.0.0, 16.1.0, 16.3.0 and 16.4.4;
those checks did not run a server or build.

For the documented default output directory, development and build caches use
different locations under `.next`. A warm build requires the build cache to be
preserved and restored by the actual environment. Do not assume a container or
CI runner retains it. Check the configured output directory and release-specific
documentation before changing or clearing any cache.

## Analysis and measurement

Use the installed release's official bundle-analysis instructions. The 16.4.3
component control found that `next analyze --output` wrote analysis files without
starting its server and did not itself produce an application build. Webpack
analysis uses a different integration. Verify proposed changes with the project's
functional and build checks.

Define the workload and success metric, distinguish cold and warm caches, record
versions and environment, and use repeated comparable runs. Do not assume a
fixed startup, rebuild or bundle-size improvement. Report commands, versions,
bundler, outcomes and untested environments. The source mirror and the earlier
repair remain available; component checks do not establish an agent advantage.

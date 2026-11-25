# Next.js bundler controls

The mirrored skill contains version-dependent claims, including a fixed speed range and a suggested `--no-turbopack` switch. The [maintained overlay](../included/repaired/skills/by-category/coding-refactoring-repository-automation/selected-structure-reference/nextjs-turbopack/SKILL.md) asks agents to inspect the project's version, configuration and compatibility before changing bundlers. The original remains in the mirror and in the overlay provenance directory.

The [Next.js Turbopack documentation](https://nextjs.org/docs/app/api-reference/turbopack) describes Turbopack as the default for development and production builds, with `--webpack` to opt into webpack. The [bundle analysis guide](https://nextjs.org/docs/app/guides/package-bundling) documents `next analyze`. Check the documentation for the installed release; these behaviors may change.

With Node 26.13.1, npm 12.2.3 and Next.js 16.4.6, the Windows and Linux
controls rejected `--no-turbopack` with exit 1. The default and explicit
webpack builds identified their bundlers and generated the expected page.
The analyzer exported 2,882 records on each system. The export named the
requested snapshot and included the root route. Both systems used the same
lockfile. [Current evidence](../artifacts/repaired-skill-readiness/next-turbopack-v1/)

These small component checks are not performance measurements or agent evaluations. They do not establish a speed improvement or an advantage over an unassisted agent. The development server itself was not exercised in this control.

## Reproduce on Windows or Linux

Use the stated Node and npm versions. Run from the repository root with
a new output directory. The runner installs the locked fixture into a
temporary directory and removes it when the controls finish. It retains
build logs, the JSON Lines export and the result in the output directory.

```text
python artifacts/repaired-skill-readiness/next-turbopack-v1/reproduce.py --output .venv/next-bundler-controls
```

Interpret the export using the installed version's CLI reference.
[Next.js CLI](https://nextjs.org/docs/app/api-reference/cli/next) ·
[Previous fixture and results](https://github.com/strmt7/ai_skills_collection_benchmarked/tree/530e4a2318ee84dc547473a8963c943b6693b568/artifacts/repaired-skill-readiness/next-turbopack-v1)

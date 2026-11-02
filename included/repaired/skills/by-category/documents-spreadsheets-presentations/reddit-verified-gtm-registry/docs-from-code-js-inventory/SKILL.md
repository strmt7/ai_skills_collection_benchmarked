---
name: docs-from-code-js-inventory
description: Inspect JavaScript and TypeScript exports and selected Express and Next.js route candidates before documenting source.
---

# Documenting JavaScript and TypeScript from source

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow the repository-root
`docs/agent-tools.md` and its linked skills, retaining the required receipts.

Use Node.js 24.11 or later. Copy the three files in `scripts/` to an isolated
working directory, run `npm ci --ignore-scripts` there, then run:

```sh
node inventory.mjs path/to/project path/to/inventory.json
```

The tool parses source without importing it. It records source-file SHA-256
digests, selected top-level exported functions and types, and selected Express
and Next.js route candidates with locations. It skips `.git`, `.next`, `.venv`,
`venv`, `node_modules`, and `__pycache__` directories and symbolic links. A
read, encoding or parse error fails the inventory instead of publishing a
partial result. Do not select a source file as output.

Express support recognizes direct module-level constructions from an Express
default import or CommonJS require, selected literal route declarations, and
direct same-file app-to-router mounts. Unknown paths, prefixes and unmounted
routers are unresolved. Next.js support recognizes named HTTP-method exports
in `route.js` or `route.ts` under `app` or `src/app` when Next.js is declared
in the root package manifest. Route groups are omitted from filesystem path
patterns; private folders are excluded. Parallel and intercepting routes are
unresolved. Dynamic segments remain patterns, not concrete URLs.

These are **static candidates**, not a complete or verified API contract.
Cross-file, nested, conditional, dynamically registered and other framework
routes may be absent; configuration and runtime behavior can change routes.
Some Next.js conventions, conflicting routes, Express patterns and method
semantics are not validated. Inspect the source locations and test the actual
application before documenting definitive behavior. Do not invent missing
descriptions, schemas or examples.

The [original skill](provenance/original.SKILL.md) and its
[upstream README](provenance/upstream.README.md) are preserved. The README
declares MIT; no project-level or docs-from-code license file was found in the
pinned repository tree. This overlay addresses selected JavaScript and
TypeScript inventory behavior; it does not repair graphify, establish a full
framework contract, or measure agent effectiveness.

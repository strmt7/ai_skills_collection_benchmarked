---
name: docs-from-code-python-inventory
description: Inspect Python function signatures and selected Flask and FastAPI route candidates before writing source-grounded documentation.
---

# Documenting Python from source

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow the repository-root
`docs/agent-tools.md` and its linked skills, retaining the required receipts.

Use the [inventory script](scripts/inventory.py) with Python 3.11 or later:

```sh
python path/to/inventory.py path/to/project path/to/inventory.json
```

The script parses Python source without importing it. It records each scanned
file's SHA-256, top-level function signatures and docstrings, and selected Flask
and FastAPI route candidates with source locations. It excludes `.git`,
`.venv`, `venv`, `node_modules`, and `__pycache__` directories. A syntax,
encoding, or read error fails the inventory instead of publishing a partial
result. Choose an output path that is not a Python source file in the project.

The route analysis recognizes directly constructed, module-level Flask apps,
FastAPI apps and FastAPI routers. It composes literal prefixes for direct
same-file router inclusions that occur after the route declaration. Dynamic
paths, methods or prefixes and routers without such a known inclusion are
marked unresolved. Wildcard imports and uncertain reassignments discard
affected bindings. It reports explicitly declared methods, or Flask's default
GET, without enumerating Flask's implicit HEAD and OPTIONS.

These are **static candidates**, not a complete or verified API contract.
Cross-file and nested mounts, application factories, Flask blueprints, other
frameworks, dynamic registration, runtime configuration and side effects can
change or add routes. Follow the file and line evidence, inspect the actual
application and existing docs, and check appropriate runtime output when
available before writing definitive documentation. Do not invent missing
descriptions, request or response schemas, or examples.

The [original skill](provenance/original.SKILL.md) and its
[upstream README](provenance/upstream.README.md) are preserved. The README
declares MIT; no project-level or docs-from-code license file was found in the
pinned repository tree. This overlay addresses selected Python fallback behavior only; it does
not repair the original TypeScript fallback or qualify graphify or agent
effectiveness.

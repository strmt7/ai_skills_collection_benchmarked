---
name: search-first
description: Search the repo, the frozen upstream snapshot, and official upstream sources before adding code or dependencies.
origin: adapted from ZMB-UZH/omero-docker-extended
---

# Search First

Use this skill before introducing new code, wrappers, benchmarks, or workflows.

## Search order

1. Search this repo first with `rg`.
2. Search the frozen upstream snapshot under `source_code_v.0.15.0/`.
3. Read the nearest local tests and docs.
4. Check official upstream docs, tags, releases, or source repos.
5. Only then decide whether to adopt, extend, or build custom logic.

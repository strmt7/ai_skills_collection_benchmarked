---
name: python-testing
description: Choose Python-side parity tests and syntax checks without weakening coverage.
origin: adapted from ZMB-UZH/omero-docker-extended
---

# Python Testing

Use this skill when the touched surface includes Python parity tests,
development-harness code, or Python-only tooling.

## Rules

- Prefer narrow parity tests against the frozen upstream implementation.
- Keep suites separated by converted surface.
- Never weaken assertions just to make the port look green.

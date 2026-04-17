---
name: ai-regression-testing
description: Add narrow regression and differential tests that catch incomplete or overconfident code changes.
origin: adapted from ZMB-UZH/omero-docker-extended
---

# AI Regression Testing

Use this skill when a port or workflow change could pass the happy path but
still diverge from upstream behavior.

## Rules

- Test both the expected path and the nearest failure path.
- Lock exact exception types and messages when parity requires it.
- For bounded inputs, prefer exhaustive differential tests.
- For unbounded inputs, combine boundary, randomized, and real-data checks.

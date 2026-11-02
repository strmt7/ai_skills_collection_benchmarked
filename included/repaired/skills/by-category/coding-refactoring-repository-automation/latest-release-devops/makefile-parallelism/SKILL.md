---
name: makefile-parallelism
description: Design and check GNU Make target ordering when recipes must not overlap.
license: Apache-2.0
---

# GNU Make target ordering

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow the repository-root
`docs/agent-tools.md` and retain the required receipts.

Model real prerequisites first. The original skill's
`.NOTPARALLEL: docker-build docker-push docker-run` does not mean that those
three recipes are mutually exclusive. GNU Make 4.4 serializes prerequisites
of the named targets; shared prerequisites such as a build do not order their
dependent recipes. Other entry points may permit overlap as well.

When one operation is truly required before another, express that dependency
directly. The [ordered example](examples/ordered.mk) models
`prepare → publish → verify`; requesting `verify` also executes `publish` and
`prepare`. Use that relationship only if those side effects are appropriate
for every invocation of `verify`.

If ordering the entire current Make invocation is appropriate, the
[serial example](examples/serial.mk) uses `.NOTPARALLEL:` with no
prerequisites. This limits parallelism for unrelated recipes too. It does not
provide a lock across separate Make invocations, recursive Make processes, or
external tools. For shared resources across those boundaries, use an
appropriate external coordination mechanism instead.

Test the actual goal graph, entry points, recursive builds and Make versions.
The supplied controls cover small synthetic graphs with GNU Make 4.3 and
4.4.1 on Linux; they do not exercise Docker, real deployments, or agent
performance. The [review](../../../../../../../docs/research-makefile-parallelism.md)
explains the original finding; the [original skill](provenance/original.SKILL.md)
remains available for comparison.

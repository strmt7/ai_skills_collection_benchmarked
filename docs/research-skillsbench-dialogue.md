# SkillsBench dialogue development-task review

This review concerns the public development task
[`dialogue-parser`](https://github.com/benchflow-ai/skillsbench/tree/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/dialogue-parser)
at the task commit pinned by SkillsBench v1.1. Its prompt requires a
`solution.py` containing `parse_script(text)`, a JSON graph and a DOT
visualization. The [upstream test module](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/dialogue-parser/verifier/test_outputs.py)
checks the produced files but does not import or call the required parser.

## Controlled test

On Linux with pytest 8.3.4, the unmodified upstream test module was run in
isolated temporary directories with the pinned [input script](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/dialogue-parser/environment/script.txt)
and a graph derived from the published [development fixture](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/dialogue-parser/oracle/dialogue.json).
No `solution.py` was
present. The DOT contained just one edge, `Start -> End`, which is not an
edge in the graph.

- The published fixture, used directly, passed 34 of 35 tests; its 146 edges
  without `text` fields failed the verifier's schema check.
- Adding empty `text` fields only where absent produced a derived graph that
  passed all 35 tests with the unrelated one-edge DOT and no parser.
- Replacing that DOT with a string lacking the expected markers caused four
  visualization checks to fail; the tests do check those markers.

The [control](../artifacts/research/2026-10-30/skillsbench-dialogue-verifier/reproduce.py)
checks the pinned verifier, input and fixture hashes and runs these three cases
using isolated temporary files. The [recorded result](../artifacts/research/2026-10-30/skillsbench-dialogue-verifier/result.json)
includes exact counts and failing test names. A modified input was rejected by
the hash check, and the isolated environment passed `pip check`. The control
requires Linux, the exact source files and an
isolated Python environment with pytest 8.3.4; see its `--help` for paths.

This tests the upstream pytest module through its local-path fallback, with
automatic plugin loading disabled. It does not run the upstream shell wrapper,
the oracle implementation, the container,
a model or the benchmark harness, and it does not establish the native oracle's
score. No held-out task content was read. The result demonstrates gaps in the
tested checks, not that every other graph would pass. Preserve the upstream task
and report any corrected grading under a distinct, predeclared protocol.

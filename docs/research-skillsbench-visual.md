# SkillsBench visual-stability development-task review

This review concerns the public development task
[`fix-visual-stability`](https://github.com/benchflow-ai/skillsbench/tree/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/fix-visual-stability)
at the task commit pinned by SkillsBench v1.1. Its
[theme-flicker test](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/fix-visual-stability/verifier/test_outputs.py)
searches inline script text for keywords and reports success when they appear.
It does not establish that the script reads the stored theme or applies it.

A [browser control](../artifacts/research/2026-10-30/skillsbench-visual-predicate/reproduce.py)
extracts that exact JavaScript predicate from the pinned verifier and evaluates
three synthetic local pages:

| Page | Predicate | Dark class applied |
| --- | --- | --- |
| No script | false | false |
| Inert comment containing the keywords | true | false |
| Script reading a stored dark theme and applying the class | true | true |

The [recorded result](../artifacts/research/2026-10-30/skillsbench-visual-predicate/result.json)
uses Linux, Python 3.12.3, Playwright 1.49.1 and Chromium 131.0.6778.33.
Playwright matches the version specified by the upstream test wrapper; this is
a pinned control, not a claim that version is current. The local server binds
to an ephemeral loopback port and each case uses a fresh browser context. The
environment passed `pip check`; an altered verifier was rejected by the source
hash check.

To reproduce, use an isolated environment with that Playwright version and its
Chromium build, then provide the exact pinned verifier file:

```text
python artifacts/research/2026-10-30/skillsbench-visual-predicate/reproduce.py --verifier path/to/test_outputs.py
```

The control tests only the extracted predicate on synthetic pages. It does not
run the full upstream verifier, measure actual theme flicker or CLS, build the
task application, score a model, or establish that the complete task would pass
with the inert script. No held-out task content was read. Preserve the original
task and report any behavior-based replacement under a distinct predeclared
protocol.

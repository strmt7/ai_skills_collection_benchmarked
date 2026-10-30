# SkillsBench Scala development-task review

This review concerns the public **development** task
[`python-scala-translation`](https://github.com/benchflow-ai/skillsbench/tree/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/python-scala-translation)
at the task commit pinned by SkillsBench v1.1. No held-out task content was
read and no model or native benchmark run was scored.

## Workspace source

The task asks the agent to translate a Python tokenizer into Scala. Its
[Dockerfile](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/python-scala-translation/environment/Dockerfile)
copies `localtest` into `/root/localtest`. That subtree includes a
[Scala implementation](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/python-scala-translation/environment/localtest/src/main/scala/tokenizer/Tokenizer.scala).
Its bytes are identical to the task repository's
[other Scala source file](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/python-scala-translation/src/main/scala/tokenizer/Tokenizer.scala)
after removing one extra import from the copied file. This is a concern for
measuring independent translation work. The comparison does not establish
whether the source is correct, whether a later runner changes workspace access,
or whether a model used it; the container was not built for this review.

## Verifier exit status

The [verifier](https://github.com/benchflow-ai/skillsbench/blob/55bfe693f2a19f6b2f29aca3f54fe98b9d994668/tasks/python-scala-translation/verifier/test_outputs.py)
parses test counts from command output but does not check the test command's
exit status. In a controlled simulation, a successful compilation followed by
a test command that **exited 1** while printing ten successes was reported as
a passing task. A zero exit with ten successes also passed; a reported test
failure and a compilation failure were rejected. These are simulated command
outputs, not executions of Scala, sbt, a model, or the benchmark harness.

The [control](../artifacts/research/2026-10-30/skillsbench-scala-verifier/reproduce.py)
requires the four source files named in its `--help` output and checks their
pinned hashes before exercising the verifier with mocked commands. The
[Windows](../artifacts/research/2026-10-30/skillsbench-scala-verifier/windows-result.json)
and [Linux](../artifacts/research/2026-10-30/skillsbench-scala-verifier/linux-result.json)
results agree. An altered source input was rejected in a separate negative
control. The results record exact source hashes; native GitHub API captures
are retained with the local research evidence.

Do not treat a score on this task as independent evidence of translation
ability until its workspace and verifier are qualified. Preserve the original
upstream task and any outcomes; report corrected evaluation under a distinct,
predeclared protocol rather than mixing it with historical results.

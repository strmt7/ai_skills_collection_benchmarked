# Evaluation evidence and reliable resumption

The evaluation overlay checks which outcomes a scorer actually measured.
The checkpoint overlay records enough job identity and evidence to resume
long work after an interruption. Both are experimental revisions.

## Evaluation

The pinned source presents pass@k as a reliability measure and includes
examples that check source patterns. A correct pattern can still produce
incorrect behavior. The earlier [sampling review](research-eval-harness-sampling.md)
verified the repeated-attempt arithmetic. The current revision also checks
result admission and keeps that arithmetic in a reference.

The native SkillsBench scorer accepted the reference submission and rejected
a plausible wrong one. Pytest ran 35 cases and the pinned reporter grouped
them into six entries. The wrong submission passed six individual cases and
none of the reported groups. A reader using only the reward would miss that
difference. The runner's other controls rejected a missing grading receipt,
a contradictory exit code, a remaining process, and a mismatched output
size. See the [native qualification](research-skillsbench-native.md) and
[OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices).

## Resumption

The pinned checkpoint skill suggests fixed call-count thresholds and a
global client hook. Its locked package contains only the skill and its UI
metadata. The referenced hook is absent. The current upstream entrypoint
adds a provider-specific context estimate and recommends writing a durable
record when task-list tools are unavailable. The overlay uses a task-local
record and separates context telemetry from job state. See the
[earlier token-accounting review](research-context-token-accounting.md) and
[upstream checkpoint instructions](https://github.com/affaan-m/ECC/blob/d2ef2680594f9a17526a6e1a2e18b3d242c5d17b/.agents/skills/strategic-compact/SKILL.md).

A bounded Windows control started one owned worker, let an observation wait
expire, and confirmed the same process incarnation was still live. A claim
using the same PID and a different creation time was rejected. After the
worker emitted its terminal marker and exited, the job contained zero
processes. See [Microsoft's wait semantics](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-waitforsingleobject).

## Evidence and status

The [evaluation overlay](../included/improved/skills/eval-harness-evidence/SKILL.md)
and [checkpoint overlay](../included/improved/skills/strategic-compact-resume/SKILL.md)
preserve their source text and license. Earlier trial and research versions
retain their existing paths and bytes. The [review record](../artifacts/research/2026-11-11/evaluation-resumption/review.json)
binds the upstream observations, the controls, and the exact new revisions.
The controls explain the revisions. Live matched trials are still needed to
measure whether either overlay improves an agent's work.


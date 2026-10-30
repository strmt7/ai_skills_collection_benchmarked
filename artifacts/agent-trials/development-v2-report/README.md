# Matched development trials

Task: `artifact-validator-robustness`. Requested model: `gpt-6.1-sol` with `high` reasoning.

All 9 planned attempts are recorded. No quality superiority is established.
Each scored attempt must report all 17 cases in the grading manifest (`a480c7c343046e4d0686b2eb68748efa46ef824b3a552de8dcc2c3dc0e4cb91b`).

| Condition | Task passes / planned | Observed usage | Input tokens, median [min–max] | Output tokens, median [min–max] |
| --- | --- | --- | --- | --- |
| default | 3/3 | 3/3 | 341,027 [297,738–353,213] | 12,486 [10,279–12,684] |
| improved | 3/3 | 3/3 | 382,866 [248,768–402,912] | 11,499 [10,714–12,233] |
| karpathy | 3/3 | 3/3 | 310,364 [263,635–337,260] | 10,787 [9,557–10,911] |

## Repetition-block comparison with default

Blocks follow the protocol's planned repetitions; a shared random seed or causal effect is not implied. Unscored includes harness errors, invalid scope and timeouts.

| Condition | Planned blocks | Both pass | Only condition passes | Only default passes | Neither passes | Unscored |
| --- | --- | --- | --- | --- | --- | --- |
| improved | 3 | 3 | 0 | 0 | 0 | 0 |
| karpathy | 3 | 3 | 0 | 0 | 0 | 0 |

Token differences are condition minus default, only where both passed and both usages are available. They are descriptive, success-conditional observations; they do not establish a causal or efficiency advantage.

| Condition | Comparable / both-pass blocks | Input token difference, median [min, max] | Output token difference, median [min, max] |
| --- | --- | --- | --- |
| improved | 3/3 | 49,699 [-92,259, 85,128] | -1,185 [-1,772, 1,954] |
| karpathy | 3/3 | -15,953 [-77,392, 12,626] | -1,699 [-1,773, -722] |

Input counts include cached input. Output counts are reported as returned by the CLI. These are descriptive tokens, not priced costs or statistically demonstrated efficiency gains.

The conditions use a default agent, a pinned third-party Karpathy adaptation, and an experimental two-skill bundle. Earlier exploratory and harness-version failures are retained separately; see [experiment protocol](../../../docs/agent-trial-protocol.md).

## Limits

- One development task and three matched attempts per condition do not establish collection-wide effectiveness.
- Quality is checked externally; agent-written regression tests are not a coverage or mutation score.
- Token statistics are descriptive actual CLI usage, not priced cost, significance, or general efficiency claims.
- Input tokens include cached input; reasoning usage is retained separately, not added again to output tokens.
- Elapsed time is diagnostic only; unrelated host workloads were not controlled.
- Provider-resolved model snapshots are unavailable; the requested model is not a verified backend revision.
- This frozen block does not pool earlier exploratory probes or harness versions; their failures remain recorded separately.
- The grading process executes submitted Python on the host; it is not a hardened service for arbitrary untrusted submissions.
- A case manifest checks the reported denominator but cannot independently prove that the grader ran or that observations are authentic.
- One development maintenance task on a real pinned repository subset; not final holdouts or collection-wide utility.
- Instructions are injected, not selected by natural skill discovery; this measures the two-skill bundle, not each skill individually.
- Process and instruction scope isolation; not a container with sealed grader files.
- Provider-resolved model snapshot is unavailable; requested CLI model and actual returned usage are recorded.
- Latency is recorded for diagnostics only; concurrent owner workloads are not controlled.
- The prior independent probe already reached 17/17, so this task may have a ceiling effect.
- Karpathy-labelled instructions are a third-party adaptation with attribution, not a repository authored by Karpathy.
- External score checks submitted validator behavior; agent-written regression tests are captured but are not a test-coverage or mutation-testing score.

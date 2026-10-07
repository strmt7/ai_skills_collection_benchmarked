# Matched development trials

Task: `artifact-validator-robustness`. Requested model: `gpt-6.1-sol` with `high` reasoning.

All 9 planned attempts are recorded. No quality superiority is established.

| Condition | Task passes / planned | Observed usage | Input tokens, median [min–max] | Output tokens, median [min–max] |
| --- | --- | --- | --- | --- |
| default | 3/3 | 3/3 | 341,027 [297,738–353,213] | 12,486 [10,279–12,684] |
| improved | 3/3 | 3/3 | 382,866 [248,768–402,912] | 11,499 [10,714–12,233] |
| karpathy | 3/3 | 3/3 | 310,364 [263,635–337,260] | 10,787 [9,557–10,911] |

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
- One development maintenance task on a real pinned repository subset; not final holdouts or collection-wide utility.
- Instructions are injected, not selected by natural skill discovery; this measures the two-skill bundle, not each skill individually.
- Process and instruction scope isolation; not a container with sealed grader files.
- Provider-resolved model snapshot is unavailable; requested CLI model and actual returned usage are recorded.
- Latency is recorded for diagnostics only; concurrent owner workloads are not controlled.
- The prior independent probe already reached 17/17, so this task may have a ceiling effect.
- Karpathy-labelled instructions are a third-party adaptation with attribution, not a repository authored by Karpathy.
- External score checks submitted validator behavior; agent-written regression tests are captured but are not a test-coverage or mutation-testing score.

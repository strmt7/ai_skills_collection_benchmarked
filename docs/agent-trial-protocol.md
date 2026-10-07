# Coding-agent experiments

The existing 673-entry catalog readiness results describe packaging. The new
`benchmarks/agent-effectiveness/` experiments run an agent on code and score
its submitted behavior outside the task workspace. No measured skill advantage
has been established yet.

## Frozen inputs

`development/protocol-v2.json` records the task commit, source hashes, grader
hash, harness hashes, conditions, prompt template and limits before the first
counted matched attempt. The first task fixes the actual artifact validator at
commit `4bd209752567f5c35074d4ee4a73600e1c45c283`. Its external grader checks
17 acceptance cases and passes/rejects known-good and trivial bad controls.

Conditions use GPT-6.1 Sol with high reasoning effort:

- **Default:** no additional skill instructions.
- **Karpathy:** pinned third-party `karpathy-guidelines` instructions, with
  their source URL and content hash recorded. The skill declares MIT licensing.
- **Improved:** the experimental `eval-harness` and `strategic-compact` bundle.

Each attempt starts a fresh ephemeral CLI session with user configuration,
memory, host-skill discovery, plugins, apps and delegation disabled. The task
uses the workspace-write sandbox and disables network access. The Windows
sandbox backend is explicitly configured; execution policies are retained.

All conditions receive identical source code and pre-created empty test/log
files. The latter avoids a reproduced Windows ACL collection failure. A separate
capability check verified both agent writing and host reading, without relaxing
permissions. The planned three repetitions rotate condition order. Runs are
serial; the owner may still be doing unrelated host work.

## Evidence and failure accounting

`tools/run_agent_trial.py` records the launch, full CLI transcript, returned
usage, stderr, source patch, submitted tests/log, external grader result and
artifact hashes. It refuses existing attempt directories and rejects changed
frozen inputs. An unsuccessful launch, timeout, missing completed turn, changed
protected source or evidence collection problem cannot become a counted pass.
Submitted code is graded in a separate process with a finite time limit.

The first independent-agent development probe passed 17/17. A CLI launch failed
because commands were unavailable; a subsequent frozen CLI attempt passed
17/17 behavior cases but could not export a sandbox-created log. Both failures
remain recorded, with their actual usage where available. They are harness
errors, not evidence of inferior model coding ability. The exact first harness
is archived with its frozen hash for audit.

## Interpretation limits

This is one development task on a real repository subset. It has already reached
the default agent's ceiling. It cannot prove superiority, broad category
coverage, or utility across the collection. The improved condition tests an
injected bundle rather than natural skill selection or individual skills.
External checks score behavior; captured agent-written tests do not establish
coverage or mutation-testing quality. Host workload is uncontrolled, so elapsed
time is diagnostic and excluded from speed claims. The CLI does not expose a
provider-resolved model snapshot; requested identity and returned usage are
reported separately.

Harder tasks, real complete repository fixtures, repeat analysis, untouched
holdouts, skill selection tests and report graphs remain required. Do not tune
against final holdouts or omit failures to produce a favorable chart.

## Completed first matched block

All nine planned protocol-v2 attempts completed. Default, third-party Karpathy
adaptation, and the improved two-skill bundle each passed all 17 independent
checks in all three attempts. This confirms the ceiling effect; no quality gain
was demonstrated. The improved bundle's input-token range was 248,768–402,912,
versus 297,738–353,213 for default. Smaller output counts in some runs do not
establish lower total cost or consistent efficiency.

The [verified report](../artifacts/agent-trials/development-v2-report/README.md)
contains all attempts, raw token summaries and standalone charts. Its publisher
checks protocol identity, each captured evidence hash, grading consistency,
failure denominators and missing or unplanned runs. Null usage remains null.
The frozen results are unchanged. Grader-created bytecode bytes are preserved
in nonexecuted `bytecode-evidence.zip` transports because loose Python caches
are correctly ignored by Git. Raw trial text is exempt from Git newline
conversion so a checkout preserves the original evidence digests.

This collection's grading driver executes submitted Python on the host in a
separate process; it is not a hardened service for arbitrary untrusted code.
Future external or adversarial submissions require isolated grading and sealed
grader access. The current evidence establishes neither container isolation
nor provider-resolved model identity.

# Windows Node control timeout

The offline-validation test
`test_control_rejects_unreviewed_overlay_before_loading_dependencies` has
repeatedly exceeded its ten-second subprocess deadline on hosted Windows.
The [observation record](../artifacts/research/2026-11-03/windows-node-timeout/observations.json)
identifies six selected failing run attempts and the exact commits and log
digests. These were selected because they failed; they are not a failure-rate
sample. The most recent workflow passed on its second attempt, which does not
explain or erase the first failure.

In the most recent failing attempt, the child was still reported as running at
the deadline and had accumulated 0.125 seconds of kernel and user CPU time.
The subsequent thread snapshot showed waiting threads. Captured stderr after
termination included the expected rejection, but the collection method does
not establish when that message was emitted relative to the deadline. The
evidence does not distinguish startup, file I/O, output handling or shutdown
as the cause.

On a local Windows host with CPython 3.14.9 and Node 24.22.2, 100 pipe-captured
and 100 temporary-file-captured invocations completed with the expected
nonzero result. A separate two-worker xdist run invoked the original test 120
times with the same Python, pytest, xdist, pytest-cov and coverage versions used
in the hosted job; all passed. The [local observations](../artifacts/research/2026-11-03/windows-node-timeout/local-process-observations.json)
include individual process durations and outcomes. These controls did not
reproduce the hosted load, runner image or necessarily its Node version and do
not prove the timeout fixed. Their coverage instrumentation was used to match
the test environment; the focused run is not a repository coverage result.

A later [Windows job](https://github.com/strmt7/ai_skills_collection_benchmarked/actions/runs/41562610887/job/125676488329)
at commit `fd6cb2adcf1e150a8701136762441fb0fd8db1df` failed in the same test:
2,102 passed, one timed out and 47 were skipped. Its child was still running
at the deadline and had accumulated 0.125 seconds of kernel and user CPU time;
the captured stderr after termination included the expected rejection. The
native job log captured on 3 November 2026 has SHA-256
`f21547ee062cedce9578c7570411aa2ce8da218850e9238e2bcb4c7a0637c436`.
This additional observation still does not establish the timing of the
captured output or identify the cause. It is not a failure-rate sample.

The original assertions, deadline and workflow remain unchanged. A useful next
diagnostic needs timestamps for child startup, output availability and actual
exit in the hosted environment, while retaining failures and avoiding changes
to the behavior being tested. [Python's subprocess documentation](https://docs.python.org/3.14/library/subprocess.html#subprocess.Popen.communicate)
distinguishes a `Popen.communicate` timeout from automatic termination and
describes cleanup with a subsequent communication call. The Node.js process
documentation request was denied by robots policy; it was not used as a source.

The repeated xdist control is [available for inspection](../artifacts/research/2026-11-03/windows-node-timeout/xdist-control.py).
It imports the real test via the process-local `E2E_CONTROL_TEST` environment
variable and requires pytest-xdist and pytest-cov. Use a fresh temporary pytest
base and an isolated coverage-data path. The recorded run used `-n 2` and
`--cov=tools --cov-report= --cov-fail-under=0`; the zero threshold applies only
to this diagnostic subset, where no tool coverage is expected, and is not a
replacement for the full CI coverage gate. Native hosted and local logs remain
in the local research workspace; the record contains their digests.

# SkillsBench parallel TF-IDF development-task review

Task identity: SkillsBench 1.1, task snapshot
`55bfe693f2a19f6b2f29aca3f54fe98b9d994668`, task content
`sha256:482f37d1b1cb39de2c6dcfe36ad1db5b5594ebf0ca76abb9c504d061a27e3b02`.
The digest was cross-checked against the complete task-identity artifact.
This task was assigned to development before reading its prompt or verifier.
No candidate skill text or oracle solution has been read for this task.

Read the full prompt, Dockerfile, sequential implementation and verifier/test
script. Read the corpus generator's operational code and part of its literal
vocabulary; the middle vocabulary tables were truncated in tool output and remain
unreviewed. Exact byte hashes cover the entire package, but semantic review does
not. This is a synthetic variable-length document workload from a pinned external
repository, not a real user issue resolution case.

The task requires matching the reference TF-IDF structure and search results,
1.5x indexing speed and 2x batch-search speed with four workers. The environment
allocates eight CPUs and 4 GiB, uses floating Python 3.12 slim, and permits public
networking. Its verifier downloads an old uv installer and unpinned runtime
dependencies at execution, with fixed old pytest and report-plugin releases.
Latest-stable qualification needs a separate versioned environment, offline
installed test dependencies and retained original reference inputs.

The search correctness test compares `zip(seq_results, para_results)` without
first checking the number of query result sets. An empty outer result list can
skip every equality assertion. IDF checks do not fully compare index structure,
posting order, vector weights or norms. Correctness uses only three fixed queries
and known corpus seeds; additional independently generated edge cases are needed.
Add empty/unknown/stop-word queries, top-k bounds, ties, noncontiguous IDs and
output cardinality checks based on the public function contract, before trials.

The performance tests take one sequential-then-candidate observation. Shared
host load, warm caches and Python process start methods can distort comparison.
Collect alternating repetitions, complete external wall times and host/resource
context; include process setup and teardown. Judge quality before performance.
Do not claim a gain merely from self-reported candidate timing.

Submitted Python is imported into the verifier process, so it can inspect or
monkeypatch the verifier's timing, baseline and pytest state. A secure comparison
needs the trusted oracle and clocks outside the submitted-code process, bounded
serialized outputs and independent checks against each case. The original suite
score should remain separately labeled; a hardened evaluator is a distinct
protocol rather than a historical leaderboard-equivalent result.

The test shell writes reward based on the captured pytest pipeline status but
always exits zero. The runner must check structured reward/report and account
separately for invocation, task failures and missing evidence.

## Runtime controls now reproduced

The unchanged upstream `test_search_results_match` method accepts a controlled
implementation returning an empty outer list. The new external comparator rejects
that result and compares every TF-IDF field, query count, result count, ordering,
ID/title, vector, posting, norm and finite score with explicit numerical tolerance.
It rejects ambiguous JSON and oversized inputs; untrusted huge numeric values
produce differences rather than overflowing the trusted grader.

Four known-good reference cases pass under the actual pinned Python container
with the published eight CPUs and 4 GiB: noncontiguous IDs with empty/unknown/
stop-word queries, zero top-k, empty corpus and empty query batch. Expectations
are computed outside the candidate container. Source file hashes and observed
container constraints are preserved in `tfidf-grader-runtime-controls-v3.json`.
The reproducer is `benchmarks/agent-effectiveness/controls/tfidf_grading.py`.

The first standalone reproducer had an embedded-code indentation error; its v2
failed receipt remains present. The repaired reproducer passes all controls.
This is new grader qualification, not a leaderboard-equivalent task score,
performance result or model trial. Task skill text and oracle solution remain
unread. Performance fixtures and matched trials are still required.

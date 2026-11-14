# Repeated-attempt metrics

When all recorded attempts were scored, let `n` be a task's attempt count and
`c` its success count. A uniformly selected
`k`-subset contains at least one success with probability
`1 - C(n-c, k) / C(n, k)`. It contains only successes with probability
`C(c, k) / C(n, k)`. Require `1 <= k <= n`. Combinations with fewer than
`k` items are zero.

Count agent attempts, which each receive one task outcome. Compute per task
and then average tasks equally unless weights were declared in advance. For
two tasks with 2/2 and 0/8 successes, equal-task pass@1 is 1/2. The pooled
attempt rate is 2/10.

If fewer than `k` attempts exist, report the result as unavailable. If some
attempts are unscored, report the gap. Explicit best- and worst-case
assignments can give bounds when their assumptions fit the protocol.

The formulas describe subsets of the recorded attempts. A prediction about
future runs also needs stable conditions and suitable independent sampling.
Adaptive retry policies require their own analysis. An any-of-k result credits
the existence of a passing output. Practical use also needs a selection
procedure and a budget for all attempts. All-of-k measures consistency under
the stated setup.

[Original estimator and assumptions](https://arxiv.org/html/2107.03374v2#S2.SS1)

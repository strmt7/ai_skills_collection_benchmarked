# Evaluation-harness sampling review

This review covers the sampling and reporting guidance of the pinned
`eval-harness` skill. It does not evaluate an agent or establish that the
revised skill improves one. Other parts of the original skill, including the
deferred security-related examples, remain outside this review.

## Source and upstream comparison

The catalog mirror is pinned to `affaan-m/everything-claude-code` commit
`846ffb75da9a5f4e677d927af1ad4a1951652267`. On 3 November 2026, the latest
stable release reported by GitHub was `v2.2.3`, whose annotated tag resolves to
commit `c05b2d6614f62f6db0047669aa4eefb223d478f9`. The
[release's eval-harness file](https://github.com/affaan-m/everything-claude-code/blob/c05b2d6614f62f6db0047669aa4eefb223d478f9/.agents/skills/eval-harness/SKILL.md)
has Git blob `8b60b99b1aa09d0c9b7eb1d22cf1de9396be80ea` and SHA-256
`49a5a10975860bb2d7e3c4e260ff19b6580e43f5fbc7770b32dece02dde48e49`.
Its body matches the pinned mirror after newline normalization; its frontmatter
differs. This checks one file, not the whole upstream release or its runtime.
The mirror and source lock remain unchanged.

The pinned skill uses pass@k as a reliability trend and gives fixed example
thresholds. Its examples do not distinguish a task-level estimate from a
pooled attempt rate or explain how to handle unscored attempts. The prior
experimental overlay improved the formula and failure accounting, but did not
explicitly state equal-task weighting, all-of-k, missing-result bounds, or the
sampling and selection assumptions needed for broader interpretation.

## Checked interpretation

The [original pass@k paper](https://arxiv.org/html/2107.03374v2#S2.SS1)
defines the estimator per problem and averages over problems. Its derivation
assumes independent samples from a fixed per-problem success probability.
Without that sampling assumption, the same expression is still the exact
fraction of recorded k-subsets containing a success; it need not predict a
future run. A passing candidate's existence also does not provide a practical
selection method or pay for the extra attempts.

The [Princeton agent-evaluation discussion](https://sage.cs.princeton.edu/trends/#trend-1d)
distinguishes at-least-one success from success on every run. In its illustrative
four-task pattern, with 5, 3, 1 and 0 passes out of five attempts respectively,
equal-task pass@1 is `9/20`, any-of-5 is `3/4`, and all-of-5 is `1/4`. These
are illustrative outcomes, not results from this repository's agents.

The [independent finite-subset check](../artifacts/research/2026-11-03/eval-harness-sampling-v1/check_metrics.py)
compared the existing estimator with explicit enumeration for 480 combinations
of sample size, successes, k and any/all rules. It ran on Windows and Linux.
For a separate two-task example with 2/2 and 0/8 passes, equal-task pass@1 is
`1/2`; pooling all attempts gives `1/5` and answers a different question. Run
the control from this checkout with:

```sh
python artifacts/research/2026-11-03/eval-harness-sampling-v1/check_metrics.py --check
```

The [result](../artifacts/research/2026-11-03/eval-harness-sampling-v1/result.json)
binds the new instructions, calculator and control bytes. Existing tests also
exercise incomplete outcomes, insufficient samples and task weighting. The
two source pages were captured with Crawl4AI on 3 November 2026; their native
result SHA-256 digests are
`f3b77d70d05ca20add039e2810e5eea23dca3ededad7d1be7fb653a76f78d731`
and `6bbc4a7b04a46f4fcecdfcf1ebc1fc86a8245cf8275bd0e76e08e8c4b33c2cef`.

## Disposition

The [new experimental overlay](../included/improved/skills/eval-harness-current/SKILL.md)
clarifies per-task counting, any-of-k versus all-of-k, incomplete outcomes,
selection costs and sampling assumptions. The earlier overlay is preserved
unchanged because frozen development trials reference its exact bytes. The
new overlay has not been tested in an agent trial; neither these component
checks nor the previous bundle's ceiling result establish an advantage.

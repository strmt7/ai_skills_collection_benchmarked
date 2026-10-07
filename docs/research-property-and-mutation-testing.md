# Property and mutation testing research

Read all nine original property-testing resources and all three original
mutation-testing resources completely. Resource-level review records preserve
their byte identities. Read the latest upstream property entrypoint and five
remaining reference guides, and the latest mutation entrypoint, optimization
guide and changed configuration sections. Additional latest upstream resources
remain separately unreviewed; a source refresh is not yet qualified.

## Property-based testing

The original warns about genuine tautologies and encourages contract-grounded
failure classification, which should be preserved. However, it treats a simple
independent `add(a,b) == a+b` oracle as if it tested nothing, ranks roundtrips
universally above other properties, uses set equality for element preservation,
maps mutable sets to a frozenset strategy, and describes a seed as running more
examples. The current Hypothesis controls contradict those claims. A direct
addition oracle detects subtraction; paired shifted codecs pass roundtrip but
fail an independent byte vector; idempotence accepts a constant function; set
and length checks miss changed multiplicities. The full sorting example does
use a stronger sorted reference; distinguish that from the weaker catalog rule.

The regex generator in the refactoring example uses search semantics while the
domain appears to require full-match identifiers. Current Hypothesis finds
`'0a0'`, which contains a valid match but is not itself a full match. Specify
`fullmatch=True` for that domain, rather than filtering failures away. Float,
Unicode, collection and size domains need the target's actual contracts.

The original library guide's unsigned balance >=0 Solidity property is vacuous;
current upstream replaces it with supply conservation and calls out unsigned
type-bound tautologies. Original precondition-violation classification labels
an overly broad strategy as "over-constrained". Its rule against reporting
platform-specific bugs also needs the supported platform contract; unusual
platforms alone do not invalidate reproducible defects.

Neither a thousand examples nor `deadline=None` makes a campaign exhaustive.
Example deadlines do not kill a nonterminating test body; use an outer process
bound where required. Stateful testing is appropriate for controlled integrations
with an independent model and resettable fixtures, despite the original blanket
exclusion. In-place behavior can be checked against a saved pre-state; changing
the public API or adding an inverse solely for testing is not mandatory.

Latest upstream at `82fe8226252622fa807643bdca1710901198553a` improves several
examples and removes design/strategy files, but retains universal property
rankings and the addition-oracle dismissal. It claims contradictory assumptions
pass and produce an ignored warning. Actual Hypothesis 6.168.3 instead raises
`FailedHealthCheck` with zero successful examples. The failure is retained in a
successful negative control, without suppressing health checks. Current
refactoring guidance also overstates that pre-state comparison of an in-place
operation is impossible and encourages needless inverse/parser production APIs.

An explicit CC-BY-SA-4.0 `property-testing-current` instruction overlay keeps
original provenance, attribution and licensing. It replaces these claims with
independent oracles, meaningful wrong-outcome controls, contract-specific domains,
stateful models and truthful reporting. It remains experimental and unbenchmarked.

## Mutation campaign configuration

Primary GitHub release metadata resolves Mewt **4.0.0** (June 18, 2026) and Muton
**3.1.0** (April 20, 2026), both stable/non-draft. Mewt's peeled stable tag commit is
`53b5d0798b5db725fafe6ca282cbf0d886b0162c`. Read its actual configuration guide,
mechanics guide, result status types and counter logic, and relevant CLI definitions.
The public tool is AGPL-3.0; the skill text is under its distinct upstream
CC-BY-SA-4.0 license. No tool campaign or binary execution has been claimed.

The original `[[test.per_target]]` structure is deprecated in Mewt 4.0; the current
form is top-level `[[per_target]]` with `test.cmd` and `test.timeout`. Latest
upstream skill fixes the examples. The tool retains the old structure for
compatibility, so this is not evidence that every original configuration fails.
CLI flags have documented precedence over config, contradicting the original
universal prohibition on CLI configuration. Inspect effective settings and bind
them to the run. Mewt and Muton's independently versioned releases are not proof
of identical command contracts.

Actual source says lower-severity mutants are skipped after an **uncaught**
higher-severity mutant, not after a detected one as the original skill states.
Latest upstream corrects this. Preserve skipped and unexecuted mutants as such;
enable comprehensive operation when complete operator coverage is required.
The tool's result counter includes timeouts in its eligible denominator and
excludes skipped rows; report that definition rather than implying every eligible
outcome was conclusively evaluated. A survivor can be equivalent, uncovered,
weakly asserted, unreachable, or constrained by an invalid setup.

`mutant_count × warm baseline time` is an estimate, not a worst-case bound:
rebuilds, tool overhead, setup, timeouts, resource contention and scheduling
matter. Measure representative runs and record uncertainty. Two-phase targeted
then full-suite testing needs a verified selection of all relevant survivors and
other unresolved outcomes, rather than silently dropping timeouts or skipped
mutants. Table line counts can include headers; prefer supported IDs/JSON formats.
Latest optimization examples mostly correct counts, but leave the total using
unqualified table `wc -l` and retain overconfident worst-case claims.

The tool mutates source files and warns cleanup may be incomplete after an
interruption. Run campaigns in disposable isolated copies; preserve original
source, test configuration and raw results. Verify restoration before reuse.
Purging the campaign database removes evidence, so retain needed data first.
Mewt stable documentation says Windows is unsupported; do not present a Windows
installation as qualified by these source checks.

Primary references: [Mewt stable configuration](https://github.com/trailofbits/mewt/blob/53b5d0798b5db725fafe6ca282cbf0d886b0162c/docs/configuration.md),
[Mewt release](https://github.com/trailofbits/mewt/releases/tag/v4.0.0),
[Muton release](https://github.com/trailofbits/muton/releases/tag/v3.1.0),
[Hypothesis strategies](https://hypothesis.readthedocs.io/en/latest/reference/strategies.html),
[stateful testing](https://hypothesis.readthedocs.io/en/latest/stateful.html), and
[current failure/replay contracts](https://hypothesis.readthedocs.io/en/latest/tutorial/flaky.html).

Remaining: actual Mewt/Muton campaigns and restoration controls, other-language
library release/API qualification, the added upstream reference resources,
source publication, and independent agent comparisons. All control successes
remain distinct from coding-agent efficacy and benchmark superiority.

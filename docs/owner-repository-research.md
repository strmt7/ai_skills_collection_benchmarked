# Owner-repository research: initial observations

The real UTC clock and ledger gate permitted inspection at 12:47:21Z on
2 October 2026, after the requested two-hour delay. Other repositories remain
read-only. Exact default-head trees and acquired context blobs are recorded in
an ignored local content ledger; private source is not copied into this public
collection. Inventory covers all 11 owner repositories plus the ZMB OMERO
repository, including this collection. Inventory is not completed code review.

Initial README, manifest, and instruction reads identify reusable evaluation
themes, subject to verification against the nearest implementation and tests:

- Durable external-write state machines: distinguish prepared, attempted,
  confirmed, and uncertain outcomes; prevent blind retries after ambiguity.
- Behavior-preserving migrations: use a pinned independent oracle, edge cases,
  byte-exact outputs where required, and measured performance after parity.
- Security coverage: distinguish finding state, incomplete analysis, failed
  stages, unresolved semantics, and actual absence of findings.
- Native Windows parity: shared GUI/CLI contracts, current toolchain identity,
  installation and recovery checks, and genuine hardware qualification.
- Runtime versus build evidence: compilation, mocked providers, and CPU-only
  checks do not establish GPU, signed-package, live-service, or device behavior.
- Resource and permission boundaries: separate local development tools from
  product runtime; data access and model output do not authorize external writes.
- Migration-aware visual evaluation: current rendering targets and packaged
  runtime evidence must replace tests of an obsolete engine or screenshot.

These are prospective independent benchmark dimensions, not findings that the
source repositories are broken and not measured skill-effectiveness results.
No new skill will embed owner repository names, deployment paths, or private
infrastructure. Remaining work includes bounded implementation/test reads,
rights checks for any reused public fixture, independent grader design, and
complete review dispositions in the local ledger.

## Mandatory CocoIndex and Caveman

The scanner's tracked workflow routes broad conceptual search through a local
CPU index over an external code-only mirror, rejects stale source hashes,
deduplicates file hits, confirms candidates with exact source reads, and uses
bounded `rg` after diagnosed failures. Its index excludes tests by design, which
means a separate test-navigation step is necessary. This development index is
separate from the scanner's mandatory offline runtime.

The current ZMB agent contract explicitly applies Caveman lite to internal
communication while retaining lossless commands, code, user-facing prose,
evidence, uncertainty, approvals, and ordered procedures. Required progress
updates remain mandatory. The scanner context guide makes the same distinction;
there is no scanner-local Caveman SKILL.md at the inspected path.

Primary release resolution selected CocoIndex Code 0.2.41 at
`9fd2e7470a8b042a338dc3cc47fb9940ac5ebb59` and Caveman 3.0.0 at
`b33a39554ed06cbc7d7d3198ff90c171e8043b69`. PyPI independently reports CocoIndex
Code 0.2.41 as latest. Both public source checkouts were verified, and their
actual skills were read. Caveman lite is applied during this work. Its broader
proxy/hooks are separate products and are not silently installed.

CocoIndex Code 0.2.41 was installed in an isolated development environment.
A pinned Apache-2.0 local model snapshot was provisioned with safetensors and
reviewed standard model modules, excluding executable/custom-code and pickle
files. The actual CPU pilot indexed 708 files into 10,272 chunks with zero
reported indexing errors; all three searches returned successful JSON responses.
Every source hash was rechecked unchanged after querying. Remote embeddings and
usage tracking were disabled. Results are recorded in
`artifacts/research/2026-10-02/cocoindex-pilot.json`.

Retrieval is uneven: the compaction query found the intended compaction entries,
and the dependency query found the real advisory-floor implementation and
validator, confirmed by exact reads. The independent-evaluation query's first
five hits omitted the intended eval-harness entry and included unrelated
contract-security guidance. Similarity scores are not calibrated correctness
probabilities. This exploratory probe supports semantic routing with exact
verification and bounded lexical fallback, not a retrieval-quality or coding
improvement claim. The entrypoint-only pilot does not establish coverage of every
skill resource. A reusable integration and independent retrieval tests remain
required.

The isolated tool environment initially inherited pip 25.0.1 from `venv`.
Its strict audit emitted 12 advisory records for that one package, including
duplicate advisory IDs. Pip was upgraded to 26.2.1 with the current installer;
its actual installed version was checked after installation completed. The
fresh complete-environment audit then reported no known vulnerabilities in
`cocoindex-dependency-audit-final.json`. An intermediate audit overlapped the
installer and is retained as evidence but is not the accepted post-install
verification. This dependency result does not cover interpreter vulnerabilities
or prove the indexer itself free of security defects.

## Caveman evaluation-method review

The pinned upstream evaluation README, `llm_run.py`, and `measure.py` were read
in full. Comparing a skill against the additional "Answer concisely." control
is useful: it separates the skill's contribution from a basic brevity request.
The published method nevertheless uses one attempt per prompt, serial arm
blocks, Claude subprocesses without a recorded resolved model snapshot or fresh
workspace/memory isolation, and output-only token estimates. The measurement
script pairs arrays with `zip`, which silently truncates unequal run counts.
There is no independent fidelity score, prompt-token accounting, failure
denominator, repeated matched comparison, or uncertainty estimate.

Those upstream scripts were reviewed but not executed. Their published savings
are not evidence about GPT-6.1 Sol. A prospective evaluation must include default,
plain-concise control, and Caveman-lite arms, fresh matched sessions, complete
actual input/output usage, explicit failures, and independently scored retention
of commands, numbers, uncertainty, authorization and ordered procedures.
Communication compression must not lower correctness to improve a token graph.

## Checked local adaptations and forward-test contracts

The current ZMB CocoIndex skill and Caveman overlay were read in full at the
inventoried immutable head, with their Git blob digests independently checked
during acquisition. The ZMB Caveman overlay derives from upstream 2.2.0, while
current upstream is 3.0.0. Its useful safeguards are internal-only lite style,
lossless public prose, preserved uncertainty and procedures, and no automatic
hook, proxy, installer or subagent activation. A version number alone does not
replace those safeguards.

The ZMB CocoIndex adapter makes refresh explicit, rejects unrelated MCP
bindings, keeps index state outside the live checkout, and distinguishes semantic
routing from exact current-source evidence. It recommends broad and exact-query
retrieval cases scored for expected-file recall, output bytes and timing; bytes
are not model tokens. It includes all text-decodable mirrored resources. The
scanner's separate code-only index excludes prose and tests, as confirmed by its
actual forward tests. These are different corpus contracts and cannot be copied
interchangeably into a collection whose primary skill entrypoints are Markdown.

The scanner adapter test file was read in full. It independently checks absolute
state paths, exact copied bytes, stale-file pruning, digest changes after edits,
per-repository isolation, no package startup when the active index is missing,
stale-source rejection before invoking the package, unsafe path/real-env refusal,
and its documented wildcard-filter limitation. These provide concrete quality
controls for a generic collection adapter. Eighteen implementation/test samples
from seven public repositories were acquired by immutable Git blob identity for
bounded review; acquisition is not completed review or executable qualification.

The retry-gate implementation and its embedded tests were read in full, alongside
the separate independent-connection reservation race tests. The former exercises
bounded provider delays and circuit reset; the latter races two actual SQLite
connections repeatedly to test conversation, attempt-cap and recipient-cap
invariants without dispatching messages. These distinguish temporal scheduling
from transactional ownership; a mocked serial send test would not cover the
same concurrency contract.

The submission-journal module and its embedded tests were also read in full.
They distinguish an uncertain external-write outcome from failure and forbid
automatic retry across that boundary. A prospective collection fixture should
add interleaved entity histories and rejected-append preservation. The inspected
implementation consults the last journal entry for transition validation, while
its retrieval methods accept entity IDs. Whether the live caller creates one
journal per entity remains to be inspected; no live-repository defect or repair
is claimed from that observation alone.

The frozen-source manifest utility was read in full. It detects changed, missing
and extra source files, excludes documented caches, and hashes streaming content.
Prospective quality controls also need malformed/duplicate manifest records,
canonical contained paths, symlink behavior and interrupted publication. The
archive UI extraction file has only an initial bounded read so far; core archive
and filesystem claims still require their matching implementations and tests.

## 7 October source and runtime refresh

Fresh owner metadata still lists eleven repositories (eight public, three
private), plus the external ZMB repository. This is inventory continuity,
not complete code review. The scanner's current context-routing guide and
M25 decision were inspected read-only after the recorded delay; they preserve
the distinctions between internal concision, exact evidence, initial-route
characters and full-task model usage.

Caveman's stable source is now 3.1.0, with a complete source review and thirteen
isolated snapshot-validator controls recorded in [the current review](research-caveman.md).
The current generator isolates host settings; unequal snapshot counts now fail
closed. The earlier 3.0.0 observations above remain historical. Fidelity,
resolved model identity, complete provider usage and repeated comparisons remain
unqualified. No new AI sessions or owner-repository writes were performed.

CocoIndex 1.0.25 / Code 0.2.42 now indexes every selected nonblank skill/tool
resource in a fresh corpus. The diagnosed Windows CLI wildcard expansion is
avoided through the provider's literal client API, with source binding and
returned-span checks in [the navigation adapter](semantic-navigation.md).
Failed CLI queries and the corrected probe labels are retained. These are
development-routing controls, not retrieval-quality or coding-agent scores.

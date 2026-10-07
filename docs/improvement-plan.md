# Improvement work ledger

This is the execution plan for the repository-wide improvement request received
on 2 October 2026. It records unfinished work; inventory coverage is not research
completion, and static readiness is not measured coding-agent effectiveness.

## Hard time gate

Do **not** inspect the user's other repositories, or research/integrate CocoIndex
or Caveman, before **2026-10-02T12:47:13Z** (**14:47:13 Europe/Berlin**).
The owner is editing another repository during this interval. Metadata listing
was completed before the restriction. The gate opened at 12:47:21Z; read-only
content inspection and actual CocoIndex/Caveman use subsequently began. The
expired one-time follow-up was deleted after its deferred-start purpose ended.

After the gate opens, use CocoIndex and Caveman (mandatory), inspect their actual
use in VulnerabilityScreener, and inspect both the owner's and ZMB-UZH's
omero-docker-extended where access permits. Read other repositories only; change
this repository only. Generalize lessons into independent skills and fixtures.
Do not couple new skills to the owner's repository names, paths, or secrets.

## Resume instructions

1. Read this plan and `data/improvement_ledger.json` before resuming work.
2. Run `python tools/manage_improvement_ledger.py --check --json`.
3. Work through pending skill IDs within one category at a time. Read the actual
   skill and relevant helpers/references, not just its generated description.
4. Persist research sources, decisions, revisions, and evaluation evidence after
   each bounded batch. Never mark a batch complete merely because it was listed.
5. Before deferred work, run the ledger's `--gate other-repositories` command.
   Exit code 3 means the hard time restriction is still active.
6. Keep the goal active until all required stages have been verified. Refactoring
   and the README rewrite belong at the end, after research and evaluation.

## Work stages and acceptance criteria

| Stage | Work | Acceptance evidence |
|---|---|---|
| Baseline | Snapshot repository, inventory all skills/categories, run existing checks | Exact commit, checks, complete ID ledger |
| Upstream | Resolve Karpathy attribution and every source's revision policy | Live API/Git evidence, pinned changes, license review |
| Benchmark design | Audit current metrics; freeze independent development and holdout tasks | Executable tests, task/evaluator hashes, comparison protocol |
| Category R&D | Review every skill, resource, dependency, activation rule, and scope | Per-skill evidence and retain/revise/deprecate decisions |
| Improvements | Implement reusable improvements outside immutable source mirrors | Source provenance, focused checks, installation checks |
| Agent trials | Compare GPT-6.1 Sol high default, upstream baseline, and improvements | Fresh isolated runs, transcripts, patches, tests, usage, failures |
| Iteration | Refine on development failures; repeat matched comparisons | Versioned iterations, failure analysis, regression checks |
| Deferred integration | Inspect all owner repos; use CocoIndex and Caveman | Time gate, coverage inventory, actual use evidence |
| Final evaluation | Run untouched holdouts and analyze uncertainty | Complete task denominators, paired results, limits on claims |
| Final refactor | Simplify layout and rewrite a short end-user README | Migration/install checks, regenerated badges, working links |
| Alerts and PRs | Fix dependency, code-scanning, and other actionable alerts; resolve all PRs | Fresh alert/API counts, tested updates, final-head CI |
| Delivery | Run all required checks and review complete patch | Full validation logs and honest measured results |

## Confirmed baseline facts

- Initial repository commit: `4bd209752567f5c35074d4ee4a73600e1c45c283`.
- Catalog: 673 entries, 15 categories, 30 skill source repositories.
- The Karpathy-named source is maintained by another account; the historical
  `forrestchang/andrej-karpathy-skills` endpoint currently resolves to
  `multica-ai/andrej-karpathy-skills` through GitHub's API.
- Its live default HEAD equals the existing AGENTS.md pin:
  `2c606141936f1eeef17fa3043a72095b4765b9c2`. No update is needed for that pin.
- Existing runtime-readiness runners perform packaging checks. Their results
  cannot establish coding quality, task completion, or superiority to a model.
- Source mirrors are immutable comparison inputs. Improvements must be explicit
  overlays or authored skills with provenance, not silent baseline edits.
- Local Git settings were adjusted for long paths and byte-preserving checkout;
  no global configuration was changed.

## Experiment requirements

- Freeze realistic task briefs and objective graders before examining the exact
  candidate skill text. Use real pinned source snapshots for primary results;
  synthetic adversarial probes are supplemental and separately labeled.
- Use identical task input, tools, model, high reasoning effort, limits, and
  environment for default/upstream/improved conditions. Rotate condition order
  across repetitions and record host load when comparing latency.
- Each attempt starts without development conversation, personal memory,
  unrelated installed skills, prior patches, or expected answers. Record the
  effective agent configuration, not just a requested model string.
- Separate packaging readiness, harness self-tests, synthetic probes, real
  development runs, and sealed holdouts in reports and plots.
- Score externally verified behavior and regressions. Include failed, aborted,
  timed-out, and invalid attempts in accounting; do not select only successes.
- Record artifacts and hashes, actual model identity, tokens, tool use, elapsed
  time, environment, patch scope, and grader output. Measure quality before
  efficiency. Do not describe noisy timing differences as improvements.
- Repeat comparisons and report uncertainty and category coverage. A selected
  win does not prove all 673 skills improve GPT-6.1 Sol high.
- Tune on development cases only. Failed final holdouts remain visible; revising
  against them makes them development cases and requires new holdouts.

## Final security and pull-request requirements

At delivery, this repository should have no open pull requests and no actionable
code-scanning or dependency findings to the extent remediation is possible.
Respect Dependabot and other alerts: fix their causes and validate updates; do
not dismiss, suppress, disable scanners, add allowlists, or remove checks to make
counts look clean. Resolve existing PRs based on their changes and evidence.
Verify alert status and workflow results against the exact final default-branch
commit. Record inaccessible scanners and genuinely unfixable findings honestly.

## Stable-version and current-practice requirement

The owner's additional requirement is to use the latest absolute stable versions
of tools, workflows, skills, and instructions, verified against primary sources
as of September/October 2026. Inventory every executable dependency and workflow
action, identify its latest non-prerelease release, resolve immutable hashes,
and record checked endpoints and compatibility results. Upstream repositories
without published releases require an explicit default-branch snapshot rather
than a falsely labeled stable release. Review behavioral instructions against
current official documentation; a recent commit alone does not establish good
practice. Preserve original comparison baselines while updating supported
production inputs. Record unavailable version information and actual migration
failures, and revisit version drift before final delivery.

## Current next actions

Earlier verified milestone (superseded by the later checkpoints below):

- Coverage ledger contains all 673 original IDs; 20 research records and five
  overlay revisions are in progress. No category is fully reviewed or evaluated.
- Local validation on the qualified Python 3.14.8 environment: 478 tests passed,
  two NTFS/POSIX executable-bit tests skipped with separate Git-index coverage;
  lint, type checks, hashed installation and seeded lock consistency pass.
  Full-suite coverage is 67.04%; mirror-publication, workflow-version and report
  tests pass. Later changes still require their own appropriate verification.
- Upstream availability snapshot: nine current, 19 updated, zero deferred,
  two unavailable. Exact current commits for 24 public sources are checked out
  under ignored `.venv/source-checkouts/`; none have been mirrored yet.
- The initial default independent-agent probe scored 17/17. The CLI's first
  launch failed at the harness level. After a Windows sandbox capability check,
  the first frozen trial passed behavior checks but hit an evidence-collection
  ACL error. It remains a recorded harness failure. A separately checked output
  scaffold supports the revised frozen serial comparison protocol. All nine
  planned matched trials completed, each at 17/17. The verified report preserves
  every planned attempt, raw usage and honest graphs. This task has a ceiling
  effect; no skill superiority is established.
- The regenerated Python lock passes strict `pip-audit`, hashed installation,
  and seeded lock consistency. The staged image-CLI dependency graph passes
  npm audit and four real image-conversion/fallback checks. The latter is not
  applied to mirrors yet; reproducible regeneration remains required.
- CodeQL for Python, JavaScript/TypeScript and Actions is prepared locally.
  GitHub scanning has not yet been run on these changes. Six PRs and 32
  Dependabot alerts were open at the initial snapshot; they remain unresolved.
- Removing Gitleaks path exemptions exposed 73 findings in current content and
  history. These remain findings requiring triage, not verified live secrets.
- The other-repository gate was verified open at 12:47:21Z. Read-only inventory
  covers all 11 owner repositories and ZMB OMERO, with bounded README, manifest,
  and actual workflow reads underway. Private source remains outside public
  artifacts. No owner repository has been edited.
- CocoIndex Code 0.2.41 performed a real CPU pilot: 708 files, 10,272 chunks,
  no reported indexing errors, three queries and post-query hash verification.
  Retrieval was uneven and needs independent evaluation. Caveman 3.0.0 lite is
  applied internally; its upstream compression benchmark still needs a fidelity
  control and matched GPT-6.1 measurements. These are initial uses, not completed
  integration or demonstrated quality gains.
- A later full selected-text corpus has 6,279 text files, 6,265 nonempty indexed
  files and 73,824 chunks, with 14 blank files accounted for and no unexplained
  omissions. The local embedding path bypassed CocoIndex's automatic query
  prefix; an explicit model query prompt corrected that configuration. Repeated
  exploratory searches became relevant for benchmark and MCP topics. This does
  not establish held-out retrieval performance; receipts preserve both results.
- SkillsBench v1.1 has verified identities for all 87 tasks. A frozen engineering
  split has 12 development and 11 untouched holdouts. An empty-result verifier
  defect is documented before any score. Five offline MCP-helper defects are
  reproduced with the current stable SDKs. Python MCP 2.2.0 modern discovery
  and legacy handshake roundtrips pass local contract controls. A licensed
  explicit MCP overlay and bundled fixture are present; remote/TypeScript/provider
  loop qualification and agent trials remain pending.
- Four complete testing-skill packages have been reviewed against current ECC.
  Actual browser controls reproduce missed responses, stale counts and network
  idle timeouts; current TypeScript rejects two copied API options. An explicit
  verification-loop overlay preserves command status and actual gate coverage.
  These are contract controls and experimental revisions, not agent gains.
- The bounded Docker backend passes nine actual-engine controls and inspects
  settings before candidate execution. An 8-CPU/4-GiB external-task profile
  passes four reference cases. The unchanged TF-IDF verifier's empty-output
  acceptance is reproduced, and the new independent comparator rejects it.
  Controls, failed receipts and public reproducers remain separate from scores.
- All 24 workflow action invocations are pinned to verified latest stable release commits.
  Supported Python compatibility lanes use current 3.11–3.14 security releases.
  Workflow input compatibility is checked locally; hosted execution is pending.
- Whole catalog publication now stages and checks all declared generated outputs,
  retains prior versions and rolls back replacement failures. Full fixture tests
  cover publication/freshness/late failure, dirty inputs and deterministic dates.
  Maintained installation documentation and unrelated siblings are preserved.
  Rename publication is recoverable, not atomic for concurrent readers or a
  certification of power-loss durability. No source refresh has been published.
- The complete image-CLI package has a current direct-dependency graph, a public
  byte-preserving provisioner and nine passing runtime controls. Negative
  controls reproduce real masking/QA-status defects. A separate licensed cover
  workflow overlay is experimental; original CLI repair/provider/agent efficacy
  remain pending. Partial lockfile field rewriting has been removed from catalog
  hashing/copying; existing mirror hashes still validate unchanged.
- A later actual Linux container run qualifies five publication, rollback,
  symlink and executable-mode contracts. The first adapter classification error
  is preserved separately from the corrected successful receipt. This is not
  a full hosted/Linux CI pass. The image provisioner now checks its whole graph
  before copying and records original versus staged input hashes separately.
- Fresh GitHub/default-head inspection still finds six open PRs and 32 open
  Dependabot alerts. Code scanning reports "no analysis found"; that is not a
  clean result. Secret-scanning API returns zero open alerts; unfiltered local
  Gitleaks findings remain unresolved. The fetched default head is unchanged.
  Initial AI identity checks pass; twelve other history identities and PR-head
  refs still need their separate required audit before publication.

Next category work: finish the remaining fifteen testing skills in bounded
resource-complete batches, starting with webapp-testing and the standalone
Playwright package, then mutation/property-based testing and fuzzing resources.
Add per-resource progress/evidence so helper files cannot be missed when a long
review is interrupted. Continue the frozen external-task grader/protocol work
without opening sealed holdouts. Preserve current control receipts and historical
manifests; qualify source refreshes and implementation repairs explicitly.

Immediate work: extend independent
tasks beyond the default agent's ceiling; complete public-source license and
change review; preserve executable modes during new mirror generation; apply
tested dependency transformations; investigate all unfiltered secret findings;
continue bounded category R&D with hashed evidence; complete read-only owner
implementation/test reviews and reusable CocoIndex/Caveman integration and
independent evaluation. The two-hour restriction has elapsed; final refactoring
and README replacement remain last.

Earlier bounded testing-category progress: ten of nineteen original packages then
have research started; nine remain pending. The last batch reviewed twenty-four
resources across six packages with byte-bound resource records. Current controls
reproduce server readiness/log/cleanup defects, qualify the public compiler
fixtures, compare unchanged executor cwd behavior and expose eight independent
property-oracle/strategy contracts. Seven licensed experimental overlays validate.
The full Windows suite passed 489 tests with two documented platform skips; later
focused overlay/resource/provisioner checks passed 60 tests. Catalog, static
benchmark, risk-audit and badge freshness checks pass. These do not close GitHub
alerts, qualify source publication or establish coding-agent gains.

That batch continued with the Anthropic skill-creator package's entrypoint,
evaluators, execution/aggregation scripts and HTML review assets; then complete
fuzzing/coverage/debug and trailmark packages with per-resource checkpoints.
Check latest-added resources separately rather than assuming old package review
covers them. Keep the sealed agent benchmark holdouts unread, and bind protocol
updates to actual isolated-grader controls. All owner-repository/CocoIndex/Caveman
work remains required; the expired time gate stays open. Final refactoring and
short README replacement remain last, after upstream/security/benchmark work.

Earlier testing-category checkpoint: thirteen of nineteen original packages had
research started, with six still pending. Forty-four original resources across
nine packages had explicit full-review records. All eighteen Anthropic
skill-creator resources and the complete current Atheris/Ruzzy packages were read.
Ten licensed experimental overlays validate. Twelve skill-creator Python controls
and ten browser controls reproduce concrete evaluation/viewer defects; eight
Atheris controls qualify actual bounded Python engine execution and reproduce
version/preload-path, byte-domain and HTTP-target defects. They do not establish
coding-agent efficacy, actual Ruzzy execution or native sanitizer coverage.

The later full suite passed 508 tests with two platform skips before the security
scanner was strengthened. The strengthened gate exposes eleven current
provider-shaped examples and twenty-two historical occurrences. A subsequent
full suite reports 525 passes, two platform skips and one clean-tree
gate failure; its assertion was kept. Further focused history-protocol controls
pass after testing root commits, separate refs, merge-only changes, newline
filenames and incomplete Git streams. All nine isolation controls pass again.
Do not report the current tree as green or security-clean.

Source generation now supports a declared credential policy version 2 for
Stripe server/restricted/organization/webhook shapes, while version 1 replays
existing locks unchanged. Whole-output fixture generation, freshness, mirror
publication and local-source lock checks pass; input bytes remain unchanged.
The subsequent source loop locally published declared credential neutralization
for seven affected skill trees from four clean public checkouts at their original
locked commits. Original-policy source hashes exactly matched the existing
mirrors before transformation. Eleven examples across eight resources were
neutralized; linked catalog/mirror/selected/source-lock metadata and portable
modes were updated together, retaining originals and a recovery journal.
`credential-policy-refresh.json` records all transformations. Live qualification
passes for these seven skills only; all 673 offline mirror/catalog hashes pass.

The latest complete suite passes 544 tests with two documented platform skips,
69.30% coverage, lint/format/type/compile checks and static/risk/badge freshness.
The expanded curated worktree scan now passes without weakening its assertion.
All 673 ledger records and ten experimental overlays still validate. No upstream
versions or repository history were changed by the credential refresh. Historical
occurrences and unfiltered Gitleaks findings require their separate verified
remediation before delivery, with the required AI identity. Hosted scanners,
GitHub alerts and PR cleanup remain pending; do not call the repository clean.

Next category resources: the remaining coverage, fuzzing corpus/harness,
sanitizer/target guidance, debug and trailmark packages, plus unqualified runtime
campaigns and latest-added resources from earlier packages. Continue the complete
owner repository review and reusable CocoIndex/Caveman qualification. Freeze the
independent external graders/protocol without opening sealed holdouts. Source
refresh/security alert/PR cleanup, matched agent comparisons, final refactoring
and the short README remain required stages.

The next complete package review covers all three Kubernetes diagnostic
resources, bringing research started to 30 of 673 skills (14 of 19 in testing),
with 47 original resources fully reviewed across ten packages. Six actual
networkless command-spy controls reproduce diagnostic error masking and scope
boundaries. No live cluster or owner repository was changed. The original
package is absent from the fetched newer Trail of Bits snapshot; its replacement
and final category/source disposition remain unverified.

The expanded unfiltered Gitleaks scan covers 7,868 publishable files and reports
119 locations: 68 prior source locations remain, five prior locations no longer
appear and 51 additional locations are in evidence. All 51 evidence contexts were
reviewed (33 owned-container labels, 15 provenance hashes, three nontext inventory
reasons) and retained without suppression. This is not a clean Gitleaks gate.
The separate source findings and historical occurrences still require work.

Coverage analysis was subsequently reviewed in full, including all three
resources in the fetched newer package and primary LLVM/gcovr/CMake contracts.
Research is now started for 31 of 673 skills (15 of 19 testing packages); 48
original resources across eleven packages have complete read records. Native
coverage replay/profile qualification remains pending. Preserve independent
scoring: these research findings and command-spy controls are not agent scores.

The metadata refresh now preserves original field ordering and Unicode escaping
with portable LF output. Three further controls qualify this serialization
contract; the initial broader key reordering was reversed through a second
recoverable publication without changing catalog semantics or mirror content.
The source lock and two manifests now have changes confined to the seven updated
records. The current Python 3.11 minimum is also reflected in Ruff's target;
standard-library UTC aliases were migrated without changing date resolution.
After these changes the complete suite passes 547 tests with two platform skips
and 69.36% coverage. Lint/format/type/compile, ledger, ten-overlay, 673-entry
catalog and offline source-lock checks pass. The source refresh has sixteen
focused migration/serialization controls. No commit, push or PR disposition was
performed during this checkpoint. Upstream version refresh, native campaigns,
owner QC, independently matched agent trials, alert remediation and final
refactoring/README remain unfinished.

## 7 October publication and runtime checkpoint

All 34 open Dependabot advisory ranges in the fresh snapshot map to locally
fixed versions or an absent dependency. The full npm advisory graph is
regenerated, qualified against its original public pin, and installed with zero
known audit findings; individual lock records are no longer patched. The Python
graph has zero known findings in both the exact CI audit path and the explicit
complete pinned probe. GitHub still reports 34 open alerts and six PRs until
publication and analysis. No alert has been dismissed or suppressed.

Credential policy 3 neutralizes the 65 targeted public source-example finding
locations through 66 exact hash-qualified replacement spans. Curated worktree
scanning passes. The policy-3 Gitleaks snapshot retains 64 reviewed identifier/
hash contexts in the worktree and 67 across complete historical patches; its
gate is failing. Later artifacts need their own fresh scans. The original
history's 22 credential-shaped examples are absent from a backed-up isolated
history preview. It rewrites 62 commits with the required AI identity and
preserves original human attribution in the publication review record. The
proposed main/tag rewrite and superseded bot-branch cleanup require the pending
explicit publication approval. Public refs remain unchanged.

The exact committed checkpoint and a fresh LF checkout pass all 570 tests, with
two documented Windows/POSIX mode skips. Research resources now use an explicit
catalog canonical-byte hash policy while retaining original capture hashes.
Subsequent local Wycheproof work also passes the complete suite, lint, formatting,
type checks, compile checks, freshness checks, ledger and overlay validation.

There are thirteen licensed experimental overlays. Wycheproof now has 21 actual
provider/schema controls: all 151 Ed25519 cases and 283 eligible AES-GCM cases
pass on cryptography 50.0.2/OpenSSL 4.0.3/Python 3.14.8. All 316 AES-GCM IDs are
accounted for, including 33 explicit API-domain exclusions. These are external
provider and source-example controls, not coding-agent scores. Native LLVM
23.1.3 runtime qualification is recorded separately. Superiority remains
unproved; final refactoring and the short README remain deferred until the
requested research/evaluation stages are addressed.

CocoIndex 1.0.25 and CocoIndex Code 0.2.42 were freshly resolved from PyPI. A
separate provider directory and fresh selected-resource corpus preserve the
previous runtime/index. Indexing and coverage/retrieval qualification are in
progress; do not search the stale corpus or count installation as actual index
coverage. Continue Caveman fidelity checks and read-only owner-repository QC.
The remaining testing-package reviews are Genotoxic and Vector Forge; retain
resource-level pending states until their references and runtime contracts are
actually reviewed and tested. Hosted CodeQL currently reports no analysis;
that is not evidence of zero code-scanning findings.

## 7 October later research and navigation checkpoint

This checkpoint supersedes the earlier remaining-reference and indexing states.
All original Genotoxic and Vector Forge texts are fully reviewed. Their newer
upstream deltas are separately bound, and 28 actual Python mutation/graph/source
controls qualify the selected integration. Two more licensed overlays bring the
total to fifteen. Weak and strong fixed test fixtures are research-authored;
no evaluated coding agent generated them during a trial. Five untested mutants
remain in both campaigns rather than disappearing from the denominator.

All four catalog Caveman adaptations and their five original resources have
complete read records. Stable 3.1.0 instructions and evaluation-source contracts
were reviewed, and thirteen actual isolated validator controls retain both
improvements and evidence limits. Research is started for 39 of 673 skills;
634 remain pending. Complete original-resource review now covers 65 resources
across nineteen packages. These counts establish review coverage, not efficacy
or category completion. Testing-package entrypoint research is started for all
nineteen packages; independent realistic evaluation remains open.

The selected CocoIndex corpus has 5,662 hashed resources: 5,486 text files,
176 explicit exclusions and fourteen blank text files. All 5,472 nonblank files
are indexed in 66,983 chunks. The stock Windows CLI expands literal path globs
before parsing, producing empty scoped queries. Actual dispatch controls prove
the cause. A client-API adapter preserves literals, rejects stale source/model
bindings and validates retrieved source spans. Earlier failures and three
mislabeled CLI/client probe blocks remain recorded with a correction. Retrieval
quality, token savings and coding gains are not established by these controls.

The current complete suite passes 589 tests with two documented platform skips
and 70.35% measured coverage. Lint/format/type checks pass across 87 files. The
last complete native Gitleaks snapshot still fails on 76 individually reviewed
noncredential contexts; later artifacts require fresh scanning. The selected
mutation-provider audit finds no known advisories across its 26 exact packages.
Hosted main, its 34 alerts and six bot PRs remain unchanged pending the concrete
history/tag publication approval. No finding has been suppressed or alert
dismissed. The final repository refactor and short README remain the last stage.

The final adapter adds four malformed-data controls. Its 21 focused tests and
the complete 593-test suite pass, with the same two platform skips and 70.36%
coverage. A separately refreshed v8 corpus binds those final source bytes;
v7 evidence remains preserved. The selected inventory/path/chunk counts above
remain unchanged. Fresh GitHub checks still show the same main head, 34 alerts
and six bot PR heads. The third-party Karpathy adaptation and all three checked
official Karpathy source heads also remain unchanged.

The subsequent unfiltered native scan covers 8,035 publishable files, with zero
input drift and 305 generic-rule findings. All 305 exact snapshot contexts were
individually classified as recorded digests/identifiers, inventory reasons or
the previously reviewed BuildKit file reference. Newly published source-hash
maps increase native matches; no credential or finding was hidden to reduce
the count. The curated worktree check passes, but the native gate still fails.
The context-review receipt explicitly preserves that failure and scope; it does
not clear historical refs or GitHub alerts. Final source-lock verification
checks all 673 mirror hashes offline with zero errors; live source checkout
qualification remains a separate loop.

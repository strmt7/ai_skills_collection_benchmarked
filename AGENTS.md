# Repository agent instructions

## Development scope

Follow the owner's current request. Make reversible development decisions
autonomously and resolve uncertainty through source, tests and primary evidence.
Correct requirements that obstruct the requested work and verify the affected
contracts. Respect explicit user holds, access rules and evidence boundaries.

Build portable skills and tools for different AI agents. Repository maintenance,
benchmark setup and model access rules apply to their respective operations.
Ordinary skill development, installation and functional testing can proceed
independently of benchmark access and release qualification. Use the
[development plan](docs/improvement-plan.md) and
[work order](data/development_plan.json) to track evidence and pick ready work.

## Mandatory agent tools

Caveman, CocoIndex Code and Crawl4AI are mandatory for development in this
repository, including work started through a generated skill. Read the three
local skills in [Mandatory agent tools](docs/agent-tools.md). Apply Caveman to
every task, perform current-source semantic retrieval with CocoIndex Code before
broad navigation, and read web pages with Crawl4AI. Retain actual source-bound
receipts for the operations performed. When a required tool fails, diagnose it
and restore it before dependent work. Continue independent work in the meantime.

Validate the classified task receipt before completion with
`python tools/validate_agent_tool_policy.py --execution-receipt <receipt> --json`.
The separate `--check` mode verifies catalog routing for publication and CI.

## Communication and execution efficiency

Use repository tools quietly. Give concise updates about results, decisions and
material failures. Preserve precise identifiers, uncertainty and the context
readers need. Bound queries and output, verify targeted source spans, and reuse
applicable evidence. Repeat expensive checks when changed inputs, observed
failures or an applicable gate warrant it.

Apply the four working principles adapted from the community
[Karpathy-derived baseline](https://github.com/multica-ai/andrej-karpathy-skills)
at `2c606141936f1eeef17fa3043a72095b4765b9c2`. Establish the goal and material
assumptions, choose the simplest correct implementation, make scoped changes
that preserve callers' contracts, and verify the result against observable
success criteria. Upstream examples are optional maintenance references.

## Portable setup and host resources

Resolve resources from the checkout or explicit configuration. Declare supported
platforms. Automatically provision missing declared dependencies into isolated
owned caches using the latest compatible, qualified stable releases and verified
locked inputs. Use verified executable paths and validate installation and
runtime behavior. Preserve unrelated apps, services, caches, global configuration
and the supported operating system. The
[development guide](docs/development.md) documents setup, runtime conventions
and qualification.

Use owned foreground processes or bounded runners that own the first launch
hop. Set time, output, memory and child-process budgets before execution and size
concurrency to available resources. Give temporary listeners and workers an
explicit stop path. Verify cleanup after completion, errors, cancellation and
abrupt controller exit. Preserve failure evidence, and check the same live
handle before retrying. Close streams and listeners and verify that task-owned
processes have stopped. Preserve unrelated processes and avoid persistent
services or scheduled jobs for development.

## Source and evidence

Keep `included/skills/` generated from the pinned sources in
`data/source_lock.json`. Apply only declared deterministic mirroring transforms.
Record upstream defects and develop verified changes under
`included/improved/skills/` or `included/repaired/skills/`. Retain attribution,
licenses and revision identity. Repairs preserve the exact original skill bytes
in provenance. Follow the [skill improvement method](docs/skill-improvement-method.md)
for research, portable design and independent functional verification.

Keep mirror changes, maintained improvements and evaluations distinguishable.
Keep generated catalog, source locks, README badges, evidence indexes and
documentation in sync. Follow [deterministic generation](CONTRIBUTING.md#determinism)
and bind qualification to the implementation and inputs actually used. Retain
older results with their original identities. Requalify affected components
when their runtime, source or evidence changes.

## Benchmark subjects

Use one development session. Delegating development, research, review or
verification to other AI agents is prohibited. The owner authorizes serial
isolated test subjects under the [benchmark-subject policy](docs/benchmark-subject-policy.md).
Only declared experimental conditions may omit collection tools or instructions.
The development controller retains the mandatory tools.

Qualify execution, collection and independent scoring for each study before
counted model attempts. Preserve original task and grader contracts, freeze
comparisons before observing outcomes and retain failures and missing attempts.
Design skills for transferable task behavior. Keep benchmark answers and
verifier-specific exceptions out of candidates. Reserve untouched tasks for
confirmation and qualify revised candidates separately. Scope claims to
validated evidence and distinguish functional controls from comparative results.

Use the official signed-in harness or app for OpenAI model runs in this goal.
Keep personal profiles, credentials and development history outside test
contexts. OpenAI inference through API keys or direct API calls is prohibited.

## Verification and publication

Run focused checks while editing and the applicable
[pre-publication gates](CONTRIBUTING.md#quality-gates-must-pass-before-push)
on each frozen batch. Bind evidence to the source bytes and compiled inputs
tested. Use the line endings in `.gitattributes`, preserve native evidence
bytes, and verify published blobs and hosted results. Keep credentials and
provider-shaped examples out of tracked files and shared evidence.

Publish cohesive batches to `main` through the authenticated official GitHub
connector. The connector is the only writer for AI commits and repository
mutations. Let GitHub assign each contributor's identity. Verify author,
committer, parents and tree, and compare the current head before updating
`main`. Local Git is available for uncommitted preparation and inspection.
Report connector limits and continue other work until the publication operation
is available. History changes require express owner authorization, verified
recovery evidence, original-to-rewritten commit mapping and an expected-head
update that preserves trees, topology, messages, timestamps and provenance.

Agent development and dependency maintenance use `main`. Other contributors
follow GitHub's permissions and review rules. Keep vulnerability alerts and
existing gates enabled. Automatic dependency-update PRs stay disabled. Qualify
updates and permitted Dependabot fixes against the complete compatible graph.
Security-scanner, code-scanning-alert and history-scan remediation are held.

The owner authorizes releases, tags and reactivation of release publishing
separately. Use the [release criteria](docs/improvement-plan.md#p11--exact-revision-readiness-evaluation-without-releasing)
to assess the exact revision's readiness.

# Coding-agent experiments

The existing 673-entry catalog readiness results describe packaging. The new
`benchmarks/agent-effectiveness/` experiments run an agent on code and score
its submitted behavior outside the task workspace. No measured skill advantage
has been established yet.

The owner permits serial benchmark subjects and the prerequisite execution
qualification under the [benchmark-only exception](benchmark-subject-policy.md).
The development controller retains all mandatory tools and the single-session
rule. A baseline subject may omit collection instructions only as a frozen
experimental condition. No new model launch is permitted until the complete
runner, collection and grading boundary is qualified.

The gated `run()` entrypoint and model-free controller qualification share one
internal lifecycle implementation. That implementation revalidates the frozen
protocol and case manifest before reserving an attempt. Qualification uses only
an owned deterministic endpoint and generated canary credentials; it is not an
alternate way to launch real providers or models. The public entrypoint still
refuses model launches before entering that lifecycle. Trusted grading drivers
disable Python bytecode writes as well as the confined workers they start.
Native transcript and error captures use unbuffered Python file writes, so an
interrupted controller can retain bytes already received from the CLI. Partial
records never establish a completed result or permit an incomplete report.

The [expanded benchmark review](benchmark-expansion.md) defines additional
content, routing, context-cost and cross-model comparisons. Follow the
[redesign method](skill-improvement-method.md): infer general failure mechanisms
from development evidence, then verify improvements on independent tasks.
Benchmark answers, reference patches and verifier-specific shortcuts must not
enter candidate skills or tools. Record public-example exposure and keep it
outside untouched evaluation. Freeze practical thresholds and analysis before
outcomes; retain neutral, harmful and failed results.

## Declared provider authentication

A version-4 plan may declare `provider` with exactly `base_url` and
`credential_env`. Freeze the endpoint and variable name in the protocol; never
put a credential value in that file. Remote endpoints require HTTPS. Explicit
numeric loopback HTTP endpoints support local qualification and local providers;
they do not establish TLS or remote-provider qualification.

For an owned local provider that requires no authentication, declare exactly
`base_url` and `authentication: "none"`. This form accepts only explicit numeric
loopback addresses, including IPv6; DNS names and remote endpoints are rejected
even with HTTPS. The CLI receives no credential variable or account-login
requirement, and the credential source is not consulted. Omission of a credential
field alone never selects this mode. Keep the private empty controller profile
and qualify the actual provider before model use; this declaration neither
starts a server nor opens the model-launch gate.

For `credential_env` declarations, the selected credential enters only the private CLI controller environment.
Subject commands keep their separate environment. Launch records retain the
provider declaration and variable name without copying the credential. Reporting
reconstructs the declared provider options and rejects an endpoint override.
Missing credentials remain setup errors, not coding-task failures.

Each attempt owns a scoped credential binding. The controller removes that
entry after CLI execution and on setup failure, execution failure or
cancellation. It does not change the caller's credential source. Context
representations omit the controller environment; this does not promise erasure
of immutable strings from process memory or revoke a provider's token.

The value may be a provider key or an OAuth access token obtained through the
provider's supported flow. The
[official ChatGPT-plan integration](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)
uses the same Responses-provider settings and assigns renewal to the calling
application. This contract does not acquire or refresh tokens, copy a desktop
login cache or establish that a token is valid for a selected model.

Native official CLI sign-in uses exactly `authentication: "codex_signin"`,
`codex_home` and `credential_store`. Select an existing absolute local CLI home
explicitly; the store is `file`, `keyring` or `auto`. The adapter runs the official
bounded `login status`, admits only ChatGPT mode and discards its raw output.
It selects the built-in OpenAI provider without unsupported provider overrides,
copies no credentials and does not consult a credential variable. The owner's
current goal permits this official harness/app route only; generic key/token
contracts above do not authorize using them for that goal.

Authentication storage must be disjoint from controller, subject and runtime
grants. Subject permissions explicitly deny that home. The tool environment
remains private, and release restores the controller's original `CODEX_HOME`;
it neither revokes nor removes the existing sign-in. Native provider retry and
transport defaults remain active inside fixed process time and resource limits.

`--ignore-user-config` does not disable global `AGENTS.md` discovery. Native
admission therefore rejects either `AGENTS.md` or `AGENTS.override.md` in the
selected home before and after status, without reading or modifying its content.
These checks do not freeze a shared home against concurrent changes. The
[native sign-in controls](../artifacts/research/2026-11-11/native-signin-controller/review.json)
use synthetic credentials and owned endpoints. They do not qualify real account
refresh, every context channel or the complete model boundary; the launch guard
remains closed.

For signed-in subjects, both maintained runners also require the unmodified
vendor model catalog pinned with the CLI. The supported `model_catalog_json`
option prevents the observed fallback to profile-cached instructions during
catalog refresh failure. Executable and catalog digests are verified before
execution and at lease closure before grading. Archived context retains the
public pin, bound to the protocol source digest; replaying command validation
needs no original host files. Use the same vendor metadata in every condition.
This does not establish real model identity, entitlement or complete isolation.
The [current native review](../artifacts/research/2026-11-13/native-vendor-catalog/review.json)
includes deliberate option removal and a late global-instruction canary. The
discovered real sign-in home contains global instructions and remains ineligible;
do not modify user files, copy credentials or clear vendor base instructions.

When using the automatic development entrypoint, explicitly forward the selected
variable with `--credential-env NAME` before `python`. Other parent credentials
are omitted. The local authentication controls use generated canaries and a
deterministic endpoint; they make no real model requests and do not qualify live
credentials, the complete controller or an agent advantage. The model-launch
refusal remains in force.

The existing environment-variable provider contract does not cover importing
a user's cached ChatGPT authentication. The
[authentication review](research-codex-authentication.md) verified the official
CLI's read-only status command and documented file-cache fallback separately.
Its successful controls do not authorize passing the host profile to a subject,
converting cached tokens or weakening the frozen protocol. Integrate and qualify
that authentication lifecycle explicitly before using it for model trials.

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

Each recorded attempt started a fresh ephemeral CLI session with user configuration,
memory, host-skill discovery, plugins, apps and delegation disabled. The task
used the workspace-write sandbox and disabled network access. The Windows
sandbox backend is explicitly configured; execution policies are retained.

All conditions receive identical source code and pre-created empty test/log
files. The latter avoids a reproduced Windows ACL collection failure. A separate
capability check verified both agent writing and host reading, without relaxing
permissions. The planned three repetitions rotate condition order. Runs are
serial; the owner may still be doing unrelated host work.

## Evidence and failure accounting

The frozen runner recorded the launch, full CLI transcript, returned
usage, stderr, source patch, submitted tests/log, external grader result and
artifact hashes. It refused existing attempt directories and rejected changed
frozen inputs. An unsuccessful launch, timeout, missing completed turn, changed
protected source or evidence collection problem cannot become a counted pass.
Submitted code was graded in a separate process with a finite time limit.

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
holdouts, skill selection tests and report graphs remain required. The public
[SWE-bench Verified compatibility check](research-swe-bench-verified.md)
qualifies dataset input construction only; it is not an agent benchmark result. Do not tune
against final holdouts or omit failures to produce a favorable chart.

A [second development-task candidate](../benchmarks/agent-effectiveness/development/simpo-verifier-v1/TASK.md)
uses the public SkillsBench verifier defect and has independently stated
acceptance controls. It is development-exposed and has not been integrated into
the confined grader or used in a model trial. Its calibration results do not
change the single-task trial count or establish an agent advantage.

A further [pytest issue-resolution candidate](../benchmarks/agent-effectiveness/development/pytest-unittest-pdb-skip-v1/README.md)
uses a complete pinned public checkout and separately calibrated lifecycle
controls. Its issue and controls are public development material. It has not
been integrated into the confined grader or used in a model trial, and its
calibration does not establish difficulty or a skill advantage.

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
failure denominators and missing or unplanned runs. It also compares completion,
usage and completed-command counts against the captured CLI transcript. Scored
attempts must report every case in the adjacent grading manifest, which is bound
to the protocol and grader hashes, and failed or invalid-scope outcomes must
agree with their recorded evidence. The 17-case v2 manifest was reconstructed
after the trials from a Git blob matching the frozen grader hash; it was not
precommitted before those trials. It prevents consistent omission of a recorded
case during report generation, but does not prove that the grader ran or that
the observations are authentic. The quality chart separates passed, failed and
unscored attempts. With the optional reports dependencies installed, verify the
published SVG content and PNG pixels against freshly rendered charts from the
repository root:

```bash
python tools/summarize_agent_trials.py --protocol benchmarks/agent-effectiveness/development/protocol-v2.json --trials artifacts/agent-trials/development-v2 --output-dir artifacts/agent-trials/development-v2-report --check --check-plots
```

The single-task reporter derives the partition and number of matched attempts
from each protocol. Condition definitions belong to that protocol; the reporter
does not assume that another experiment used this historical three-condition
bundle. This keeps future development and holdout reports distinct without
changing the recorded historical attempts or their scores.

Future experiments must establish their case manifest before execution and
retain independent grading evidence.
The current runner requires protocol version 4. In addition to the case
commitment below, `execution_source_sha256` must equal
`run_agent_trial.execution_source_hashes()`: the declared controller,
collector and confined evaluator sources, their helpers and runtime source
specifications. A changed, missing or additional source entry stops the launch.
These hashes establish consistency, not independent execution or efficacy.
For protocol version 3 or later, `grading_cases_sha256` commits the case set:
sort the unique names, serialize them as compact ASCII JSON, and hash the UTF-8
bytes with SHA-256. The adjacent `<protocol-stem>.grading.json` records that
case list, the completed protocol hash and the grader hash. The protocol also
pins `trial_manifest_sha256`, the hash of `tools/_trial_manifest.py`. Commit the
protocol and manifest before collecting attempts. The runner checks these
bindings before launching, but a hash alone does not prove when a commitment
was made or whether grading evidence is authentic.
Null usage remains null. Malformed event streams cannot produce a scored result;
their retained transcript and matching parser error are counted as a harness
failure without inventing usage or command counts. New protocols must also pin
the shared transcript parser by its `transcript_parser_sha256` before launch.
The frozen results are unchanged. Grader-created bytecode bytes are preserved
in nonexecuted `bytecode-evidence.zip` transports because loose Python caches
are correctly ignored by Git. Raw trial text is exempt from Git newline
conversion so a checkout preserves the original evidence digests.

Those trials used the original experimental `strategic-compact` overlay at its
frozen path. The later `strategic-compact-current` overlay is a separate,
unbenchmarked revision; the historical results do not measure it. See the
[token-accounting review](research-context-token-accounting.md).

The historical v2 grading driver executed submitted Python on the host in a
separate process. A newer Windows AppContainer grader has been qualified with
known-good and boundary-attack controls. The trial runner now passes its
explicit fixture revision, runtime, dependency bundle and output to that grader;
missing configuration remains a harness error, with no host-grading fallback.
Submission collection uses bounded native reads that reject linked, oversized
or concurrently writable files. These integrations have component controls,
but the complete agent execution and collection boundary is not yet qualified.
The frozen v2 protocol
rejects the changed execution tooling before launch. Do not run a new model
trial until the runner and confined grader are integrated and independently
qualified. The runner now refuses new model launches before creating a workspace
or starting a process until those prerequisites are implemented. It also rejects
scored grader responses whose cases, counts or outcomes disagree with the frozen
case set. The historical evidence establishes neither container isolation nor
provider-resolved model identity.

The 9 November qualification work uses the official stable Codex CLI 0.167.0
in a private provider directory. Native MXC probes permit workspace operations
and ordinary children while denying the tested outside-file and loopback
operations. Delayed children are stopped at foreground exit. A matched host
control can create an owned WMI process; the MXC attempt produces no marker and
reports PowerShell constrained-language errors. This is limited prototype
evidence, not full controller, instruction-discovery, authentication or model
qualification. The [native observations](../artifacts/component-controls/trial-runner/2026-11-09-integration/observations.json)
retain the failed setup controls as well as the corrected observations. The
launcher remains disabled. The implementation follows the current official
[Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox) and
[permission profile](https://learn.chatgpt.com/docs/permissions) documentation;
documented support does not replace host qualification.

The Windows job-process control limits output and cleans up job members. It is
not a complete sandbox: Microsoft documents that processes created through
`Win32_Process.Create` are not automatically assigned to the caller's job.
Before integrating it into trials, qualify the agent sandbox's service access
and the full collection and grading boundary. See [Windows job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

## Private context controls

Autonomous trial subjects cannot request human input. The context disables
both synchronous and asynchronous question tools through Codex's
`tools.experimental_request_user_input.enabled` setting. This common constraint
applies to every condition, including the baseline. Native controls verify that
coding tools still work and that neither question tool is advertised. The
setting follows the pinned upstream
[tool admission rules](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/core/src/tools/spec_plan.rs#L1317-L1347).

The trial context disables both legacy delegation and v2 native agent tools.
In Codex 0.167.0, feature flags alone did not remove the model-visible
collaboration namespace in a local control. The explicit v2
`disable_native_tools` setting removed it while preserving command execution
and independent grading. This follows the pinned upstream
[native-tool admission check](https://github.com/openai/codex/blob/086ccc833bc9cf01024ad2dd6af7dbd421b6bf9a/codex-rs/core/src/tools/spec_plan.rs#L735-L748).
Removing advertised tools is a component check; it does not qualify the full
controller or authorize model launches.

Native command controls exercise the Windows PowerShell-to-Python route used
by the coding tool. The shell is discovered from the native Windows directory;
its executable, the admitted Python, the exact probe and command are bound to
the retained evidence. Bytecode writes are disabled in controlled Python
processes. File-access, network, environment and child-process expectations
remain unchanged.

Disposable workspaces and controller profiles use OS-derived temporary
locations independently of the report directory. The source binding records
their actual paths. The checker verifies the declared working directory and
probe bytes retained before and after execution, without reopening disposable
fixture paths during artifact validation.

Direct standalone Python launches through the 0.167.0 RPC endpoint failed
with Windows error 3 in local controls; system-command and shell-route controls
succeeded under the same sandbox permissions. Those failures remain recorded.
Passing shell-route controls does not qualify direct non-system image launches
or the complete model execution boundary.

After qualification and protocol validation, the runner reserves each attempt
directory before preparing its workspace. `attempt.json` records the controller
phase. A pre-launch setup exception produces an unscored `harness_error` with
unavailable usage and process exit status, plus structured error type, `errno`
and Windows error code. Exception messages and local variables are not copied
into the published diagnostics. Reports verify this separate failure path and
retain missing prompt evidence as unavailable, including across task summaries.
Ordinary controller exceptions after setup produce a separate `controller_failed`
record and an unscored `harness_error`. This includes agent execution, transcript
reading, collection, grading, evidence selection and final result storage when
the error record can still be saved. The error records its stage and OS error
domains, without copying exception messages or local variables. A fixed inventory
retains available controller and native observations; it never traverses grader
scratch or controller profiles.

The failure path preserves usage, completed-command observations and exit status
when retained native records support them. Missing or invalid measurements stay
unavailable. Partial streams contribute only complete observed events; a malformed
stream cannot invent counts. Reporting recomputes these measurements and verifies
the error metadata, lifecycle state and evidence hashes. These consistency checks
do not attest model execution, process cleanup or the authenticity of observations.
No controller failure becomes a task pass or an ordinary coding failure.

Cancellation or persistent terminal-storage failure remains unresolved; the
reporter refuses a complete report. Lifecycle records do not prove process
liveness or authorize replay, and existing attempt directories are never overwritten.

New trial plans require protocol version 4. Before creating a workspace, the
runner validates pinned input declarations, portable file identities, allowed
changes, explicit model settings and positive time limits. Each repetition must
schedule every declared condition once, and the default condition must contain
no collection skills. The protocol binds the complete declared execution-source
closure; missing, extra or changed source entries invalidate the freeze.
Allowed changes may name exact files, including new files, or directory prefixes
ending in `/`. A directory scope includes its descendants, with Windows case
matching and a path boundary: `src/` does not authorize `src-extra/`. An exact
file scope permits its necessary parent directories, but not sibling files.
Scaffold text is materialized as its declared UTF-8 bytes. Protected input and
scaffold edits or deletions remain scope violations.

Every new protocol declares `collection_policy`: file and directory counts,
depth, per-file bytes, total bytes, path metadata bytes, collection timeout and
explicit cache-directory exclusions. The default limits are 2,048 files, 2,048
directories, depth 32, 8 MiB per file, 64 MiB total content, 4 MiB of path text
and 60 seconds. Only the declared cache directories and fixed root `.git` and
`.trial-profile` omissions are allowed. Cache exclusions apply to directories;
a regular file named `__pycache__` remains source. Tasks targeting caches must
remove the relevant exclusion before freezing their protocol.

Collection uses a separate process with isolated Python imports, an explicit
system environment, a 1 GiB job memory limit and a four-process limit. It walks
held directory handles, opens every admitted file before copying, rejects linked
objects and rechecks the complete namespace. Captures retain new files, binary
bytes and empty directories. A failed or interrupted capture is unscored; partial
output is never admitted for grading. All subject execution must have stopped
before capture. Namespace rechecks do not establish an atomic snapshot.

`workspace-changes.json` records additions, modifications and deletions of files
and directories. Captured bytes and this record are authoritative; `patch.diff`
is a bounded diagnostic view with explicit omissions for binary, large or
budgeted files. It is not an external benchmark's patch adapter. Native component
controls cover directory enumeration, links, long paths, bounded collection and
handle cleanup. Full model execution remains unqualified and disabled.

Version-4 reporting also reconstructs the declared CLI command and checks its
model, reasoning effort, permission profile, shell environment and runtime read
grants. Native process records must agree with output byte counts, time/output
limits, memory/process bounds and cleanup. Only selected controller, submission
and grading files may appear in the evidence inventory; scratch paths are
rejected before reading their contents. The collection manifest, native worker
response, file sizes and digests, process limits and declared collection command
must agree. Collected input digests must support the reported source changes,
deletions and scope violations. Rehashing altered records does not make
contradictory evidence valid. These are consistency checks, not authenticated
execution evidence. They do not qualify complete runtime graphs or the model
transport. Provider-resolved model identity remains unavailable and elapsed time
remains diagnostic. Historical version-2 reports retain their original method
and limitations.

The current integration reserves a fresh controller directory through the
operating system's temporary-directory API, separate from the task workspace and
publishable trial outputs. Controller paths do not inherit checkout depth. Keep
these private profiles outside published evidence and retain their locations
in the launch record. A local deterministic-endpoint comparison completed with
the temporary controller location while the deeper profile stalled in PowerShell
and reached its execution timeout. This does not establish a universal path-length
limit or qualify arbitrary temporary-directory configurations.
The integration supplies an explicit system/tool environment,
disables automatic skill instructions and memory, and uses the native MXC
permission profile. Read grants must identify the declared CLI and Python
runtime directories without exposing the controller home or other workspaces.

Provision the pinned Codex CLI on Windows with `./dev.ps1 codex`. Setup installs
missing release files and licenses into an owned cache and returns `cli` and
`readable_root` paths as JSON. `./dev.ps1 doctor` provides the isolated Python
runtime. Run the model-free context controls with these paths and explicitly
declare the Python runtime read roots, including the base runtime for a virtual
environment. Replace the bracketed paths with their locations:

```powershell
python tools/qualify_trial_context.py --cli <codex.exe> --python <python.exe> --git <git.exe> --readable-root <CLI-package-root> --readable-root <Python-runtime-root> --output .venv/context-controls --json
python tools/qualify_trial_context.py --output .venv/context-controls --check --json
```

Use a new output directory for each run. The native checks include visible
instruction canaries under an ordinary positive-control profile, their absence
from the isolated context, the declared instruction intervention, and a bounded
command through the native `command/exec` protocol. A normal-process
countercontrol verifies that the owned file and loopback probes are available;
the isolated command must deny outside reads, outside writes and loopback
connections while allowing workspace writes and ordinary children. Parent-only
environment variables and the controller home must stay out of the command's
environment. No thread, turn or model-inference request is sent.

Prompt comparison retains raw inputs. It normalizes only message IDs, message
creation timestamps and the native randomized arg0 shim path under the private
controller home. Semantic equality does not mean byte-identical requests or
identical tokenization of runtime paths. The checker verifies the complete
evidence inventory and recomputes the controls; it cannot authenticate execution.

The positive visibility control uses the ordinary `:workspace` profile; the
tested injection context uses the restrictive `trial` profile. During development,
the prompt inspector intermittently timed out after emitting its input when
automatic skill instructions were enabled under the restrictive profile. Those
failed controls remain retained. This recipe does not qualify automatic skill
discovery or natural skill routing under that combination.

The runner preserves raw grading-driver streams and hashes explicitly selected
controller outputs, collected submission files and native grading streams.
It does not recursively traverse grader scratch or include controller profiles.
Launch failures, missing evidence and output-limit failures remain unscored
infrastructure failures. Context controls do not qualify the complete model
execution, authentication, collection and grading path; the model-launch refusal
remains in force until that complete boundary is independently qualified.

## Planning an independent-task comparison

Before attempting a held-out evaluation, compare the frozen development and
holdout protocols in a partition manifest:

```bash
python tools/audit_trial_partitions.py --manifest benchmarks/agent-effectiveness/development/partition-manifest.json
```

The checked-in manifest contains one historically attempted development
protocol, three public development candidates and no holdout; its status is
`incomplete`. Candidates are separately counted and do not represent agent
trials. Their pinned source records supply one declared source-file digest each;
the audit checks the source-record bytes but does not independently retrieve
the source file or inventory its full repository. A candidate cannot be entered
as a holdout. Include other exposed work when identified: this manifest alone
does not prove a complete exposure inventory.

Before future trials, include every relevant frozen protocol with its exact
SHA-256 and reviewed source groups that identify shared issue, dataset or other
task lineage. Compare all exposed development work, not merely successful
attempts. Commit the manifest and
protocols before collecting trial outcomes, using access-controlled storage
for material that must remain hidden. A public digest can record a commitment
without publishing a private holdout; a digest alone does not prove when the
material was created or who had access to it.

The audit reports cross-partition matching IDs, declared groups, effective
prompts and workspaces, and input-content subsets even when files are renamed.
Shared files can be ordinary dependencies, so each reported match needs review.
`review_required` means only that the automatic comparisons found no match;
it does not establish independence. Group declarations may be incomplete, and
semantic overlap, prior model exposure and whether a holdout stayed private
require separate evidence. The command's success exit status means the audit
ran successfully, not that a holdout is valid. Grouping dependent examples when
splitting evaluation data is also discussed in the
[scikit-learn cross-validation documentation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data).

Before collecting a new experiment, consider how many independent tasks are
needed under several plausible outcome distributions. The prospective planner
enumerates the rejection probability of an exact conditional McNemar test, with
a Bonferroni adjustment for a prespecified number of comparisons. Its default
is the two-sided alternative:

```bash
python tools/plan_paired_task_power.py --tasks 100 --candidate-only 0.15 --baseline-only 0.05 --comparisons 2
```

Here `candidate-only` is the assumed probability that the candidate passes and
the baseline fails on a task; `baseline-only` is the opposite. The example
assumes a ten-percentage-point difference, a 5% family significance level and
two prespecified comparisons. It produces approximately 43% power under its
assumptions. Keeping the difference at ten points but setting the probabilities
to 0.25 and 0.15 gives approximately 21% power: the difference alone does not
specify the required design. These are illustrations, not estimated task
probabilities or measured results.

To plan the one-sided improvement test used by an analysis plan with
`"alternative": "greater"`, add `--alternative greater` to the command. Choose
the direction and comparison family before observing holdout outcomes, and use
the same alternative in both the power and analysis plans. The directional
calculation counts rejection in the candidate-favoring tail only; it can also
give a nonzero rejection probability when the assumed effect favors the
baseline. For the first illustrative scenario above it gives approximately
54% power under the same assumptions. Neither alternative is a probability
that the candidate is superior. SciPy documents the corresponding
[one-sided exact binomial alternative](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.binomtest.html).

The calculation assumes independent, identically distributed task pairs and
one scored observation per condition per task. Repeated attempts on the same
task are not independent task pairs. Task selection, shared repositories,
unscored attempts, model changes and other dependencies can invalidate the
assumptions; the tool does not model them. A two-sided rejection detects a
difference in either direction, not necessarily an improvement. The exact
conditional test can be conservative, and numerical probabilities are summed
using floating point. A plan and appropriate analysis must be specified before
collecting untouched holdout results; this tool is not a preregistration or an
analysis of existing trials. See the [R Exact package's paired power documentation](https://search.r-project.org/CRAN/refmans/Exact/html/power.paired.test.html)
for the underlying paired-outcome setup and alternative test methods.

## Exact paired-outcome analysis

`tools/analyze_paired_task_outcomes.py` can calculate an exact conditional
paired binary test for **one scored matched pair per task**. It first revalidates
the multi-task plan and all underlying reports, then rejects missing outcomes,
repeated comparisons within a task, mismatched conditions and analysis-plan
hashes. It never treats repeated attempts as independent tasks. The input is the
same multi-task `--plan` used by the descriptive reporter plus a separate
`--analysis-plan` JSON file, for example:

```json
{
  "schema_version": 1,
  "trial_plan_sha256": "<sha256 of the exact multi-task plan>",
  "partition": "holdout",
  "baseline": "default",
  "candidate": "collection",
  "alternative": "greater",
  "family_comparisons": 2,
  "family_alpha": "0.05"
}
```

Set the partition and condition names to those in the frozen trial plan. Record
the comparison, direction, complete family size, significance level, task
selection and stopping rule **before** inspecting the holdout outcomes; a file
hash alone cannot prove that this happened. Run
`python tools/analyze_paired_task_outcomes.py --plan PLAN.json --analysis-plan ANALYSIS.json`.
The one-sided `greater` alternative tests candidate-only passes against
baseline-only passes; `two-sided` tests either direction. The output preserves
the four paired outcomes, observed pass-rate difference, exact p-value and
Bonferroni-adjusted p-value as rational numbers. Zero discordant pairs yield
p = 1. Missing or differing provider-reported snapshots remain visible.

The exact conditional calculation follows the binomial form of
[McNemar's test](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.mcnemar.html).
It assumes independent task pairs, appropriate sampling and equal discordant
probabilities under the null; the tool cannot verify those assumptions. The
family adjustment covers only the complete prespecified comparison family, not
unrecorded tests or repeated looks. A two-sided rejection has no direction.

The report also gives a two-sided familywise confidence interval for the
candidate-minus-baseline pass-rate difference in the task population. It
constructs four one-sided exact binomial bounds for the candidate-only and
baseline-only probabilities, combines their endpoints, and applies a
[Bonferroni union bound](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm)
across the complete declared comparison family. The
[binomial bounds](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)
are inverted using integer arithmetic and rounded outward on a 2^32 grid. This
is conservative and may be wide, particularly with few tasks. Coverage assumes
independent, identically distributed task pairs sampled from the population of
interest; repeated attempts, adaptive task selection, unscored outcomes and
model changes can invalidate that interpretation. The interval is two-sided
even when the paired test uses a one-sided alternative, so their decisions need
not match.

Neither an interval, p-value, matching hashes, reported model snapshots nor a
nominal rejection establishes causal skill superiority, representative task
coverage, grading authenticity or commercial readiness.

## Comparing multiple task reports

`tools/summarize_multi_task_trials.py` reads a declared plan of task IDs,
protocol hashes, protocol paths and trial directories. It revalidates every
single-task report, rejects missing attempts, duplicate tasks, changed protocol
bytes and mismatched model, partition or condition definitions, then preserves
per-task attempts and their result hashes, status counts, matched-block
comparisons, grading provenance, limitations and model-snapshot availability. It reports pass-rate differences
with equal weight per task using exact fractions. If either compared condition
has an unscored attempt on any planned task, its aggregate difference is
unavailable; that attempt remains visible rather than being counted as a fail
or silently dropped.

### Describing subsets of attempts

To inspect subsets of recorded attempts, run for example:

```bash
python tools/summarize_best_of_k.py --plan benchmarks/agent-effectiveness/development/multi-task-historical-example.json --k 3 --baseline karpathy
python tools/summarize_best_of_k.py --plan benchmarks/agent-effectiveness/development/multi-task-historical-example.json --k 3 --baseline karpathy --rule all
```

The tool revalidates the plan and underlying results, then reports the exact
fraction of uniformly chosen `k`-attempt subsets containing at least one pass.
For `n` scored attempts and `c` passes this is `1 - C(n-c,k)/C(n,k)`, the
estimator used by [HumanEval](https://github.com/openai/human-eval/blob/b9453e8f1865df0a0057a1383767caa400acfbcf/human_eval/evaluation.py).
Each task has equal weight regardless of its number of attempts. The reference
condition defaults to `default`; use `--baseline` for another planned condition.
The default `--rule any` asks whether at least one selected attempt passed.
`--rule all` instead reports the fraction of subsets where every attempt passed,
`C(c,k)/C(n,k)`. These complementary measures describe different aspects of
repeated outcomes, as discussed in [On Randomness in Agentic Evals](https://arxiv.org/html/2602.07150v3).
Neither measure is a worst-case guarantee or establishes independent sampling.

If any attempts are unscored, the tool reports a range obtained by assigning
all of them failures or passes and withholds the point estimate, even if those
endpoints coincide. A task with fewer than `k` attempts makes the affected
aggregate unavailable. These bounds are not confidence intervals. The fraction
describes recorded subsets; interpreting it as a probability for future runs
requires suitable independent sampling. The `any` rule additionally requires a
way to select a passing attempt.
Adaptive retries, model changes and selection costs require separate analysis.
The recorded example contains one development task with three passes in each
condition, so its k=3 comparison is a tie and does not demonstrate an advantage.

Each plan entry must declare its task brief, prompt template, pinned input-file
hashes and any workspace scaffold. The reporter hashes the declared prompt
after inserting the brief and the declared workspace, rejects identical
prompt-and-workspace declarations under different IDs, and lists exact shared
workspace declarations even when the prompts differ. This prevents exact
duplicates from being counted as separate tasks. The hashes reflect protocol
declarations, not independent verification of the runtime environment; different
hashes do not establish that tasks, fixtures or outcomes are independent. The
reporter checks each retained prompt against its evidence hash, the declared task
template and the frozen hashes of its ordered skill instructions. It permits
the runtime-path substitution and the runner's newline conversion; it checks
that the recorded runtime path is absolute, but does not establish which runtime
was actually used or what the provider received. These are consistency checks,
not proof that the evidence is authentic.

`prompt_runtime_evidence` compares the runtime-path text recorded in matched
prompts within each task. It counts equal, different and unavailable pairs,
and distinguishes attempts without a runtime placeholder from ambiguous
newline interpretations. Reports do not publish the extracted path text or
its hash. Text equality does not prove that the same runtime was used, and
different paths can identify the same runtime. These counts do not change task
scores or establish a performance advantage.

The `paired_outcomes` section also separates blocks where both conditions
passed, only the candidate passed, only the default passed, neither passed, or
at least one attempt was unscored. It reports both pooled block counts and the
average of each task's outcome fractions, giving every task equal weight even
when repetition counts differ. Fully scored tasks are counted as candidate
ahead, default ahead or equal according to their observed pass-rate difference;
any task with an unscored block is counted separately. Equal net differences
can therefore be distinguished from agreement on individual blocks.

The `planned_order_outcomes` section groups paired outcomes by whether the
protocol placed the default or the candidate first in each repetition. It
retains both pooled counts and the counts for each task, including unscored
blocks. With more than two conditions, first means earlier relative to the
other member of that pair; another condition may be scheduled before or between
them. These are planned positions, not independently verified launch times.
Unequal group counts and different outcomes can flag an imbalance worth
investigating, but do not establish an order effect or a causal advantage.
Pooled blocks are not necessarily independent and tasks may have different
numbers of repetitions.

These are descriptive summaries, not confidence intervals or significance
tests. Pooled repetitions need not be independent, task identity alone does
not establish independence, and unscored results remain unknown. Research on
[paired evaluation](https://aclanthology.org/2021.acl-long.179/) motivates
retaining paired outcomes; it does not validate a superiority claim for this
experiment.

`non_default_comparisons` compares every ordered pair of non-default
conditions directly, using their matched repetitions rather than subtracting
two summaries against default. For example, `karpathy` then `improved` reports
improved minus Karpathy. Each pair includes per-task differences, equally
weighted means, paired outcomes, missing-outcome bounds, reported snapshot
identifiers, successful-pair token differences, and planned relative order.
Unscored attempts in one member prevent that pair's complete mean; an unscored
default attempt does not make an otherwise complete non-default pair unscored.
These are the same observed attempts viewed in another comparison, not extra
replications, a confidence interval, or evidence of a model or skill advantage.
Prompt runtime-path evidence remains available only for comparisons with default.
The machine-readable report includes the direct pairs. To render the improved
condition against Karpathy, pass `--baseline karpathy` to
`tools/render_multi_task_chart.py`; it recomputes the selected view from the
recorded attempts and checks it against the direct comparison. The default
chart remains available without that option. Non-default baseline charts show
other non-default conditions; use the default chart for comparisons with default.

For each comparison, `missing_outcome_sensitivity` reports exact lower and
upper bounds from hypothetical pass/fail assignments for all unscored attempts.
For each task, the lower bound assigns unscored baseline attempts passes and
unscored candidate attempts failures; the upper bound assigns the opposite.
The planned attempt count remains the denominator, and the task bounds are
averaged with equal task weight. The report retains per-task bounds and missing
counts. When every attempt is scored, both bounds equal the observed mean.
These assignments do not turn an unscored attempt into an observed outcome:
for an invalid-scope attempt there may be no meaningful binary outcome without
correcting the experiment. The range is not a confidence interval, a rerun
prediction or a superiority test and does not cover other sources of bias.

For each comparison, `model_snapshot_evidence` counts matched pairs with equal,
different or incomplete provider-reported snapshot identifiers. It also lists
the identifiers observed across all planned tasks. The status is
`inconsistent_reported_identifiers` when more than one identifier appears,
even if the identifiers happen to match within every pair; otherwise it is
`incomplete` when any pair lacks an identifier, or
`single_reported_identifier` when all pairs report the same one. Different
identifiers may reflect aliases or changed models; matching identifiers are
not independent proof that the underlying model was unchanged. The descriptive
outcomes remain visible, but inconsistent or missing metadata limits causal
interpretation of the comparison.

The report also summarizes matched input and output token differences. A block
is comparable only when both attempts passed and both recorded usage. It first
averages the paired deltas within each task, then weights tasks equally. A
task mean is unavailable if any of its planned blocks is not comparable; the
across-task mean is unavailable if any task mean is missing. Counts and
individual blocks remain visible. Input includes cached input and output
already includes reported reasoning output. These counts are not priced cost,
statistical significance or proof of greater efficiency.

The separate `all_attempt_usage` section accounts for reported input and output
tokens across every attempt status, including failed and unscored runs. It shows
observed subtotals and usage availability by status and task. Per-task means,
equal-task means and condition-minus-default differences are available only
when all required usage records are present; missing usage is never treated as
zero. This view describes all recorded attempts, so its differences may combine
different outcome mixes. It is not a success-matched comparison, a priced-cost
calculation, or proof of efficiency. Cached input is already included in input;
reported reasoning output is already included in output.

Run the read-only tool with `--plan <plan.json>`. The
[historical example plan](../benchmarks/agent-effectiveness/development/multi-task-historical-example.json)
reads the already recorded v2 trials. It was created after those trials and is
not preregistration or a new experiment. It contains one task and therefore
reports the existing zero difference without establishing an advantage. A plan
hash alone cannot prove when a plan was committed, whether tasks are independent,
or whether a grader actually ran. These descriptive figures are not a
significance test, collection-wide conclusion, priced-cost comparison or evidence
of a provider-resolved model identity.

The offline-validation workflow uploads the historical plan's machine-readable
multi-task summary alongside its charts, including the declared task signatures
and shared-workspace groups.

For Python 3.11–3.14, install the `reports` extra from the repository root with
`python -m pip install '.[reports]'`. The maintainer's
`requirements-reports-lock.txt` is generated for the hosted Python 3.14 report
job; it is not a lock for every supported Python version. The compatibility
matrix uses uv-managed CPython builds for Windows 3.11 and 3.12, because the
GitHub-hosted Python catalog does not provide those current patch releases for
Windows; the other matrix jobs use GitHub's Python setup action.

With the `reports` extra installed, render the same verified plan with
`python tools/render_multi_task_chart.py --plan <plan.json> --output <chart.svg>`.
Add `--check` to compare an existing chart without writing it. Dots show scored
individual tasks and the square shows the equal-task mean only when every
planned task in that comparison is scored. Unscored tasks remain counted, and
points may overlap. When outcomes are unscored, a separate line shows their
hypothetical sensitivity bounds; it is not a confidence interval. The chart
recomputes those bounds and status counts from the recorded attempts before
rendering. The offline-validation workflow tests and uploads a chart
for the historical example; it shows no demonstrated advantage. Rendering
checks require the reports dependencies and run in that workflow's report job.
The chart also counts attempts without snapshot metadata and distinct reported
snapshot identifiers. These are reported metadata, not independently verified
provider identities; distinct identifiers can make comparisons harder to interpret.
Each candidate row also shows its identifier status and the number of matched
pairs with different or incomplete identifiers. `IDs: vary` includes identifiers
that differ between tasks even when each individual pair matches.

Use `--view paired` with the same command to render the paired-outcome chart.
Its stacked bars show the equally task-weighted fractions for both passes,
candidate-only passes, default-only passes, neither passing and unscored blocks.
Task-direction counts and pooled block counts are annotations, not the bar's
denominator. Percentages are rounded; small segments are left unlabeled and
unscored segments are hatched. The renderer checks the paired summary against
the recorded attempts; displayed snapshot IDs are provider-reported and are not
independently verified. The workflow also uploads this view for the historical
plan; it is descriptive and does not establish significance or superiority.

For paired token differences, use
`python tools/render_token_chart.py --plan <plan.json> --output <chart.svg>`.
The two panels show input and output counts separately, with complete task means,
the equal-task mean when all tasks are complete, comparable block counts, and
the same per-candidate snapshot evidence.
The workflow also uploads this chart. It describes observed usage; it does not
establish priced cost, efficiency, statistical significance or agent superiority.

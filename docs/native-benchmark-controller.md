# Grade a collected benchmark task

The native controller grades completed workspace captures using the original
SWE-Skills-Bench verifier and score mapper. It validates collection receipts,
seals the source changes, rebuilds a fresh grader tree and checks the native
score against the frozen testcase inventory. Its qualified development task
is `batch1/python-packaging`.

```text
python tools/grade_swe_skills_submission.py --task task.json --runtime runtime.json --baseline-collection baseline/collection --submission-collection attempt/collection --output .venv/native-attempt
```

Choose a new output directory under `.venv`. The caller must stop subject
execution before using the repository's bounded collector. Supply its complete
`collection` directories, including launch, process, native output and result
receipts. Keep the pinned baseline capture separate from the attempted task.

The controller returns exit code 0 for a task pass, 1 for a measured task
failure and 2 for an incomplete or invalid grading operation. The final
`result.json` contains the status, fraction, testcase counts and source hashes.
Native streams, reconstruction receipts and container leases remain alongside
it for review.

Test deadlines up to 900 seconds are preserved in schema-2 and schema-3 tasks.
The native lease component supports deadlines up to 3,600 seconds, including
setup and cleanup. Do not lower a publisher's timeout to fit an adapter limit.

For project-build integration, `LeaseResources` declares CPU quota (1–4),
memory (256 MiB–8 GiB), temporary storage and repository storage separately.
Repository capacity defaults to 16 MiB with execution disabled; larger capacity
and executable build outputs require explicit settings. Combined temporary
mount capacities may use at most three quarters of the memory limit, including
all four optional task mounts. These are quotas, not preallocated host memory.
The current grading CLI still uses its Python-verifier resource profile;
configurable full-project resources and build stages are not integrated there.

The [native resource controls](../artifacts/research/2026-11-13/native-project-resources/review.json)
verify kernel quotas, actual compilation/execution, storage limits, long-deadline
staging and watchdog cleanup after controller termination. They do not establish
complete task readiness or model performance. Requalify source-bound plans after
controller changes; old results remain historical evidence.

The completed Packaging fixture scored 11/11. Its unchanged capture scored
0/11, including the declared candidate-caused skip. Failed and interrupted
collections returned an error with no score before opening containers.
A separate process-death test verified automatic container removal after the
controller stopped. See the
[qualification evidence](../artifacts/research/2026-11-11/native-controller/review.json).

The controller targets Windows with an explicitly configured local Linux
Docker engine. Its runtime file declares the following fields.

| Field | Required value |
| --- | --- |
| `schema_version` | `1` |
| `docker_cli`, `docker_cli_sha256` | Absolute path and digest of the admitted executable |
| `endpoint`, `engine_id` | Observed local named-pipe endpoint and engine identity |
| `image_reference` | Public `docker.io/...` reference pinned by SHA-256 |
| `image_manifest` | Absolute path to the captured platform-specific manifest |

The controller verifies the CLI and manifest bytes before checking the engine
and image. A missing image is pulled at its frozen digest. Runtime declarations
are local configuration and belong outside tracked source.

Public Docker Hub image reads use an explicit anonymous client configuration.
An empty auth map alone lets Docker discover a platform credential helper.
The controller instead declares an empty Hub entry and empty store/helper
settings before its first native request. A live owned-helper control reproduced
the old discovery behavior and verified that the corrected configuration avoids
it. See the [native client controls](../artifacts/research/2026-11-13/anonymous-registry-client/review.json).

Freeze a schema-version-2 `task.json` before model evaluation. It binds the
following inputs.

| Input | Declaration |
| --- | --- |
| Task identity | `id`, `source.repository`, `source.commit`, `source_directory` |
| Source capture | `collection_policy`, `baseline_manifest_sha256` |
| Native execution | `image_reference`, `grader_user`, `import_paths`, `python_safe_path`, `test_timeout_seconds`, `min_pass_rate` |
| Imported code | `import_origins` maps module names to image paths and hashes or captured `source_path` values |
| Verification | `verifier`, `inventory` assets with explicit paths and SHA-256 digests |
| Publisher scorer | `scorer.files`, `scorer.wheels`, `scorer.versions` |
| Controller version | `execution_source_sha256`, produced by `grade_swe_skills_submission.source_hashes()` |

Each scorer file also declares its destination under `src/`. Each wheel
declares its project and version. The controller installs those hashed wheels
offline inside the scorer container and checks the resolved package versions.
Review and pin the author package before generating a task declaration.

The controller checks framework and project import origins before running
tests. Image modules declare `image_path` and `sha256`. Project modules
declare `source_path`, whose digest comes from the completed submission.
The Packaging profile enables Python safe-path behavior while retaining its
explicit source import path. A root-level project helper named `pytest.py`
then passes without replacing the framework. A conflicting helper on the
explicit source path yields an error with no score and remains in attempt
accounting. See the [runtime-origin review](research-native-runtime-origins.md).

Grader and scorer containers have separate leases. Each uses a read-only root,
bounded temporary storage, a process limit and disabled networking. The grader
closes before the scorer starts. Its verdict must agree with the console,
JUnit report, exit status and declared candidate-skip rules.

Live model evaluation also needs the qualified subject launcher and matched
experimental conditions described in the
[benchmark execution plan](benchmark-execution-plan.md).

## Frozen Python dependencies

Schema-3 grading tasks add `python_environment` when a project needs Python
packages absent from the pinned image. The profile declares schema version 1,
the exact native `python_version`, `machine: "x86_64"`, `setup_timeout_seconds`
(30–240), and `resources` with `memory_bytes` and `tmpfs_bytes`. Resource bounds
remain those of the native container lease. Existing schema-2 tasks retain
their image-based framework and resource profile.

The `wheels` array lists the complete, target-qualified graph, including `pip`
and `pytest`. Each entry declares `project`, `version`, absolute `path` and
`sha256`. The profile accepts at most 64 wheels and 48 MiB of compressed bytes;
the entire staged task must still fit the existing 64 MiB transfer limit.
Installed dependencies are bounded to 20,000 objects and 256 MiB. Capture
publisher provenance and resolve the graph on the target interpreter before
freezing it; a cross-platform candidate download is insufficient.

The grader creates a private environment inside its network-disabled lease.
It bootstraps the declared pip wheel with the image installer, then installs
the complete graph using that pinned pip with hash checking and no index,
cache, source builds or global installation. Native dependency checks and exact
installed versions must agree with the profile. This follows pip's documented
[hash-checking requirements](https://pip.pypa.io/en/stable/topics/secure-installs/).

Framework and dependency imports declare `environment_path` relative to the
private environment, plus the module file's SHA-256. The evaluator inventory
must declare the same pytest version. Project imports continue to declare
`source_path` so an installed wheel cannot silently replace submitted code.
The original verifier runs as the unprivileged task user with the private
interpreter, including its child Python processes. A complete root-owned,
read-only inventory must remain identical after evaluation. The original
publisher scorer still runs separately, and model execution remains subject
to its existing qualification gate.

The restored project tree is writable inside the disposable grader namespace
so original verifiers can create their normal scratch files. The task user
receives a fresh home and XDG directories in the bounded temporary filesystem;
the image's read-only home is never used for project configuration. A native
write probe checks the restored tree before grading. None of these guest
paths refers to a host installation or changes a host profile.

## Subject-to-grader integration

`tools/run_swe_skills_trial.py` adds a single-attempt adapter around the same
native grader. Its default entrypoint refuses model launches. A current,
independently checked boundary receipt can admit the specific anonymous local
development profile described below. Other tasks, account profiles and general
model execution remain unqualified. Development controls use an owned
deterministic endpoint; they are not model evaluations.

The adapter admits frozen inputs and reconstructs the complete baseline in a
fresh subject workspace. Before subject launch, the selected collector runtime
must recapture that tree and confirm its unchanged file and directory namespace.
The adapter then runs the scoped CLI controller and requires a terminated owned
job before collecting its submission. Incomplete turns, resource-limit failures and
invalid captures retain an error with no score. A completed capture enters the
original Linux verifier and scorer, preserving their score and denominator.

A schema-1 plan declares `id`, `partition`, `condition`, `model`,
`reasoning_effort`, `time_limit_seconds`, `provider`, `baseline_collection`,
`task`, `prompt`, `interventions`, `subject_runtime`, `grader_runtime` and
`execution_source_sha256`. Each input asset declares exactly an absolute
`path` and `sha256`. The default condition requires an empty intervention list.
Repeated interventions and instructions identical to evaluator assets are
rejected. All prompt text together must fit one MiB; inputs are never truncated.
`_native_trial_plan.execution_sources()` produces the source binding.

Schema-2 plans add `write_io_limit_bytes`, an integer from 1 byte to one GiB.
Schema-3 plans also require a `storage_limits` object. The public native route
requires schema 3 and a current scoped boundary qualification. Schemas 1
and 2 retain their original contracts for historical controls; they are not
silently assigned new budgets.

### Qualify an anonymous development profile

`tools/qualify_native_trial_boundary.py` verifies eleven independent packaging
controls and the native context controls against their recorded observations.
It checks the original scorer's passing and failing results, incomplete streams,
write and storage limits, observation errors, an interrupted running tool,
protected-path and network access, and owned-process cleanup. A marker in a
requested command is insufficient: successful controls require the matching
tool output. Changed native evidence or execution source invalidates a receipt.
Execution sources and admission-checker sources are bound separately. Updating
the checker invalidates its receipt without relabelling or rerunning unchanged
native execution evidence. The admitted checker bytes are checked again before
execution and after grading.
The timeout control also observes the running tool's PID and creation time from
the host and confirms its termination; an empty CLI job alone is insufficient.

The specification declares `schema_version: 1`, profile
`windows-native-packaging-anonymous-v1`, `execution_source_sha256`, an absolute
`context_directory`, and a `controls` object mapping all eleven case names to
their absolute evidence directories: `edited`, `unchanged`, `truncated`, `budget`,
`accounting`, `logical`, `space`, `spaceerror`, `preflight-space`, `timeout` and
`isolation`. Paths stay in this checkout's ignored `.venv`; generate them for
the current installation. This is a trusted-controller evidence check, not
cryptographic attestation of arbitrary third-party results.

```powershell
.\dev.ps1 python tools/qualify_native_trial_boundary.py --specification .venv/native-controls/specification.json --output .venv/native-controls/qualified
.\dev.ps1 python tools/qualify_native_trial_boundary.py --check .venv/native-controls/qualified
.\dev.ps1 python tools/run_swe_skills_trial.py --plan .venv/native-controls/trial.json --qualification .venv/native-controls/qualified --output .venv/native-controls/attempt
```

Admission binds the model, reasoning setting, runtime, task, baseline and storage
budgets to the qualified profile. It permits HTTP Responses on numeric IPv4
loopback only. The plan is checked again before setup; the receipt and its
evidence are checked before execution and after grading. A mismatch withholds
the score. Holdouts and other task/runtime combinations require separate work.

Execution-boundary qualification does not establish the backend's actual model
identity, local generation compatibility, matched model comparisons or skill
gains. Verify those separately. OpenAI sign-in admission and the release hold
remain unchanged; no API key or copied personal profile is required by this
anonymous local route.

The agent process retains its 2 GiB job limit. The owned-process helper also
admits explicitly configured backend jobs up to 16 GiB; a controller must select
an appropriate limit from current host headroom. It reads the configured limits
back from Windows and records `job_peak_memory_used_bytes` separately. This
native peak can include a rejected allocation: controlled commit probes admitted
1 GiB and rejected 9 GiB under an 8 GiB limit, then admitted 9 GiB and rejected
17 GiB under a 16 GiB limit. Those probes wrote only two bytes to an admitted
range, released it and did not populate the intervening pages. They establish
commit admission, not physical RAM or GPU capacity. See Microsoft's
[job-limit fields](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information)
and [virtual-allocation semantics](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualalloc).

Provider authentication uses the [explicit trial-provider contract](agent-trial-protocol.md#declared-provider-authentication).
Existing `base_url`/`credential_env` declarations retain their behavior. An owned
numeric-loopback provider can instead declare `base_url` with
`authentication: "none"`, without inventing a dummy credential. It still needs
runtime/transport qualification and does not bypass the model-launch refusal.
The [native authentication controls](../artifacts/research/2026-11-11/native-provider-authentication/review.json)
cover positive, unchanged, truncated and authenticated-regression attempts on a
deterministic IPv4 endpoint. They do not qualify an actual local model backend.

Explicit `codex_signin` declarations retain native official CLI authentication
without copying credentials or exporting tokens. Six
[native sign-in controls](../artifacts/research/2026-11-11/native-signin-controller/review.json)
cover edited/unchanged grading, truncated native transport, API-key rejection,
global-instruction rejection and deliberate config-leak detection. The admitted
subject was denied read/write access to the synthetic store. Shared-profile
stability, refresh, remaining context channels and real model identity remain
open; these deterministic controls do not open the model-launch gate.

| Storage field | Admitted range |
| --- | --- |
| `min_free_bytes` | 1 byte through one TiB of caller-available space |
| `max_workspace_bytes` | 1 byte through one GiB of logical data-stream lengths |
| `max_workspace_entries` | 1 through 65,536 files, directories and data streams combined |

Choose adequate limits using the unchanged task and freeze them across every
comparison condition. The controller checks available space before setup,
around wheel capture, during installation and runtime checks, throughout the
subject process, before collection and grading, and after grading. Active
processes use a 0.5-second polling interval plus forced boundary checks. A low
observation or native error stays latched for that phase and withholds a score.
Every declared writable location is queried separately; no common volume or
preinstalled host layout is assumed.

Before launch and after proven job termination, a separate bounded measurement
counts the complete workspace, including the writable profile, caches and
alternate data streams on files and directories. It uses held native handles
and reads metadata without reading file contents. Root data streams count;
the root directory itself does not. File and directory objects and their data
streams each count toward the entry limit. Reparse points, multiply linked
files, unsupported metadata, excessive path depth and malformed observations
fail admission. Enumeration is also bounded to 64 directory levels, four MiB
of path names, 32,770 entries per directory and a 64-KiB stream metadata buffer.

`initial-storage.json`, `final-storage.json`, `setup-space.json` and the
process's `space_budget` retain the observations. A limit-exceeding scan retains
its measured partial count with `complete: false`; an observation failure
retains its error rather than a fabricated zero. Only a complete consistent
measurement within the frozen limits can enter grading.
An early rejected attempt can contain only its plan bindings and diagnostics;
it does not imply that a subject or installer launched. See the
[controlled storage qualification](../artifacts/research/2026-11-11/native-storage-budget/review.json).

The runner polls cumulative write transfers for the owned Windows job,
including exited members, and checks again after termination. Attempts exceeding
the budget stop without a score. Accounting failures also stop execution and
retain the native diagnostic. The process record includes the configured limit,
observed count, overshoot and enforcement kind. A failed observation retains the
last successful count, or `null` when none was available. Admission checks that
these fields agree before collection and grading.

This is a polled I/O budget, not a hard filesystem quota, physical allocation
measurement or I/O-rate limit. Setup and grading have their own bounds. See the
[controlled write-budget qualification](../artifacts/research/2026-11-11/native-write-budget/review.json).
The storage guards are observations, not reservations or hard quotas. Logical
lengths do not measure physical allocation, and usage can grow between polls
or before a stopped-workspace scan. They do not isolate other host processes
or account for every service-created write. Retained scratch is preserved.

The subject runtime declares `schema_version: 1`, `cli_package_root`, `python`
and `python_sha256`. Automatic CLI setup supplies the package root. Admission
checks its complete pinned payload and licenses, rejects additional package
objects and verifies the explicit Python executable. Read grants cover the
CLI runtime and Python directory; grants exposing controller or evaluator
inputs are rejected. Runtime declarations and plans belong in local evidence,
not tracked machine-specific configuration.

Schema 2 adds `dependencies`, `installer`, `archive_directory` and `import_paths`.
`dependencies` references a frozen JSON specification by absolute path and
SHA-256; `installer` names the admitted UV executable. The optional archive
directory supplies already captured wheels. Missing wheels download from their
exact pinned official PyPI URLs. `import_paths` lists safe workspace-relative
source directories, such as `src`, which precede the dependency bundle.

The specification declares `schema_version: 1`, `python_version`,
`architecture: "AMD64"`, selected module `imports` and a complete `packages`
list. Each package declares canonical `name`, stable numeric `version`,
`extras`, wheel `filename`, official `url`, `bytes` and `sha256`. Only wheels
are admitted; source builds and unconstrained resolution are unsupported.
The selected Python must match the declared Windows x64 runtime.

Each attempt automatically installs that graph into a fresh private target
using normal UV installation with hashes, offline resolution, binary packages
and copied files. Native setup logs, requirements, wheel bytes, selected import
origins and a complete file/directory inventory remain with the attempt.
The subject receives a read grant for the package directory and an explicit
tool-only `PYTHONPATH`; controller credentials and package paths remain separate.
Inventory drift before or after grading withholds the score. Each attempt has
its own writable installation target; existing profiles are preserved.

To qualify a dependency specification separately, run:

```powershell
.\dev.ps1 python tools/prepare_subject_dependencies.py `
  --specification <frozen-specification.json> --python <admitted-python.exe> `
  --output .venv/trial-dependencies/qualification-a
```

The managed launcher provisions and explicitly binds UV. A direct invocation
must supply its admitted executable with `--installer`; no host PATH lookup is
used. Selected imports are checked against the owned installation. This does
not prove every transitive import or every task-specific build command works.
Use unchanged project checks inside the subject sandbox to qualify each task.

Attempt evidence retains its exact plan, input assets, implementation sources,
launch, transcript, process result, collection and native grading result.
Changed frozen inputs withhold the score. Credentials remain in the controller
and their binding closes before collection; no desktop profile is imported.

This adapter uses a Windows subject and a Linux grader. It does not reproduce
the publisher's complete agent harness. Task-specific subject dependency
readiness still requires its own qualification. Tasks depending on POSIX executable modes need additional
admission because the current capture contract records source bytes. A frozen
single-attempt plan also does not establish independent sampling, contamination
controls or a matched efficacy experiment. Those remain requirements before
counted model comparisons or commercial-readiness claims.

## Account, quota and model metadata

Use a fresh source-bound native plan to check the existing official CLI sign-in
without starting a thread, model turn or subject command:

```powershell
.\dev.ps1 python tools/check_native_trial_readiness.py --plan .venv/benchmarks/run-plan.json --output .venv/readiness/run-1
```

Prepare the plan and admitted runtime as described above; regenerate source
identities after implementation changes. Automatic tool setup is described in
the [installation guide](installation.md). The output directory must be new and
separate from authentication, runtime and tracked source inputs.

Exit status 0 means the selected CLI profile supplied eligible account/quota/model
metadata. Status 1 means metadata did not establish eligibility; status 2 means
setup or execution was incomplete. The checker requires a ChatGPT account,
explicit permission for ordinary included usage, consistent account identity
before and after the reads, and a complete model inventory supporting the
requested model and reasoning effort. It requests no token export, interactive
login, Reserve operation or explicit forced refresh. Native authentication can
still refresh credentials when its normal lifecycle requires it.

The checker discards raw RPC responses and stderr from bounded memory, retaining
sanitized decisions, account-identity hashes, implementation sources and process
results in `readiness.json`. The official CLI retains its normal native state;
this is not a promise to erase its authentication/cache files.

The [11 native controls](../artifacts/research/2026-11-11/native-account-readiness/review.json)
include successful metadata, unavailable or denied usage, an unavailable model,
global instructions and rejected refresh. Transient refresh failure can still
return a ChatGPT account; permanent rejection can return a null account without
a JSON-RPC error. Neither account presence nor RPC success proves refresh success.

The check also reads configuration before and after its metadata requests.
Invalid responses, changed effective configuration or origin versions, and an
explicit `model_catalog_json` override withhold metadata eligibility. Raw
configuration, instructions and origin paths stay in memory. Equal snapshots
do not freeze a shared profile; a native model catalog can still be bundled or
cached. The absence of an explicit override does not establish live model entitlement.

This check honors app-server's selected profile configuration. The subject's
`exec --ignore-user-config` has a different loading contract. Configuration
concordance, shared-profile stability and the complete trial boundary remain
unproved. Completed metadata results explicitly mark configuration matching and
full trial qualification as false. Native controls confirmed that isolated exec
ignored a valid profile catalog marker; deliberately removing its isolation flag
exposed the marker and withheld the result. This is a scoped scripted control,
not evidence about a real model or all cache channels. See the
[configuration review](../artifacts/research/2026-11-11/native-configuration-readiness/review.json).
Identity fields are qualified for
the pinned native CLI wire format; absence is not inferred identity. Eligible
metadata does not open the model-launch guard, prove future quota or establish
model effectiveness. No real account, keyring or TLS route was qualified by the
synthetic controls.

Eligible metadata also does not establish live model entitlement, inference
success or a specific backend weights snapshot.

## Vendor catalog and shared-profile limits

The admitted CLI is 0.169.0. Native signed-in subjects use the unmodified model
catalog from that exact public source commit, through the supported
`model_catalog_json` option. Both maintained runners verify executable and catalog
sizes and hashes before execution and again before grading. Execution evidence
retains the public pin and binds it to the protocol source digest; archived command
validation does not require the original host installation. All experimental
conditions use identical vendor metadata. This does not replace the model's
default instructions with a collection-specific prompt.

This addresses an observed channel: `--ignore-user-config` alone still permits
matching cached model instructions when online catalog refresh fails. Three
scripted controls exercise the maintained repair, an actual edit graded by the
original external verifier, and deliberate removal of the catalog option.
The [review](../artifacts/research/2026-11-13/native-vendor-catalog/review.json)
retains the initial failed online-cache hypothesis and the qualifying controls.
These results do not establish real model identity or complete profile isolation.

Global `AGENTS.md` and `AGENTS.override.md` remain a separate channel. The official
CLI loads them independently of ignored configuration and the project-document
budget. Admission rejects their presence without reading or modifying them.
A generated-profile control also proves that creating such a file after admission
can contaminate a request; admission checks do not freeze a shared profile.
Metadata-only discovery found a global instruction file in the actual sign-in
home, so that home remains ineligible. Do not move user files, copy credentials
or clear vendor base instructions to bypass this limitation. Complete launch
admission remains unqualified and the public model-launch guard stays closed.

## Qualified local image archives

The [automatic Node replay setup](../toolchains/native-node-replay/README.md)
downloads its pinned dependencies, builds a labelled local archive and runs
bounded native probes. It also retains implementation snapshots and supports
offline artifact verification. Its [qualification](../artifacts/research/2026-11-13/maintained-node-replay-setup/review.json)
distinguishes current-source controls from earlier native builds and reports
same-host byte reproducibility across ASCII and Unicode output paths. Complete
task admission and cross-host reproduction remain unqualified.

An unavailable publisher image must remain recorded as unavailable. A separately
qualified replay can use runtime schema 2, with the same `docker_cli`,
`docker_cli_sha256`, `endpoint` and `engine_id` fields as schema 1:

```json
{
  "schema_version": 2,
  "image_reference": "sha256:<configuration digest>",
  "image_archive": "<absolute path inside this checkout's .venv>",
  "image_archive_sha256": "<archive digest>"
}
```

Include the four common fields in the actual runtime document. The example is a
field guide, not an executable configuration. Generate paths from the current
checkout and hashes from the admitted files; do not copy another host's runtime.

The controller first checks the exact configuration ID on the qualified engine.
If it is missing, it verifies the archive hash, its sole image, Linux AMD64
platform, configuration digest, layer content addresses and declared filesystem
metadata before loading it. Archives must contain no image tags or undeclared
resources. This prevents loading the replay from replacing another image's tag.
An already installed exact image ID needs no archive read or registry request.
Container ownership, resource limits, network policy and cleanup leases apply to
both runtime schemas.

The [Node replay qualification](../artifacts/research/2026-11-13/node-local-replay/review.json)
keeps the publisher's Node 20/22 Enroot export recipes separate from a modern
Node 26.13.1 replay. The replay preserves the pinned Python base layers, adds a
checksum-verified official Node distribution, and prepends its binary directory
to PATH. Foreground assembly uses the reviewed official `crane` output operation;
it creates no build daemon and performs no registry write. Generated archives and
host-specific runtime documents stay in ignored private state.

Runtime probes qualify Node, npm and npx only. They do not establish task
dependency readiness, equivalence to the publisher environment, successful
evaluation of the twelve-task frame, or improvement from the skill collection.

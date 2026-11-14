# Codex authentication qualification

An existing ChatGPT login can support local Codex use without a Platform API
key. Authentication is therefore a separate readiness check from API-key
availability. It does not establish model entitlement, a successful inference
request or a qualified benchmark runner.

On 11 November 2026, the admitted Codex CLI 0.167.1 reported an existing
ChatGPT login. A second status check used the documented file-cache fallback
in a separate `CODEX_HOME`, without copying host configuration, instructions,
history or skills. Both commands exited successfully. The original auth file
remained unchanged; the temporary credential copy was removed immediately.
Native status output was processed in memory and discarded. Evidence contains
only the classified authentication mode and process results.

These were read-only status controls, with no model requests. They do not
qualify token refresh, concurrent account use, subject-tool isolation, model
identity or the complete experiment. The model-launch guard remains closed.
See the [review and source identities](../artifacts/research/2026-11-11/codex-authentication/review.json).

## Supported methods

The current [official authentication guide](https://learn.chatgpt.com/docs/auth?surface=app)
documents ChatGPT login, API-key login, credential storage under `CODEX_HOME`
and copying a file-based auth cache for headless use. The CLI and IDE can share
cached credentials, and active sessions can refresh tokens. An integration must
account for that shared lifecycle before using copied credentials for live runs.
Do not copy an entire user profile into a benchmark condition or publish an
auth file with its evidence.

The admitted CLI's `login --help` exposes `--with-api-key` and
`--with-access-token`, both using stdin. The official guide describes the latter
as an enterprise automation access-token method. Its presence does not establish
that an arbitrary cached OAuth access token is an interchangeable credential.
No token conversion or interactive login was attempted.

For automation, the guide recommends API-key authentication. The local
file-cache fallback above is not a public CI credential distribution mechanism.
Future benchmark authentication must keep credentials in the private controller,
preserve applicable administrative requirements, prevent subject access and
omit credential values from plans, prompts, transcripts and submitted files.

## Remaining admission work

The owner's current execution constraint is the official harness or app with
existing sign-in only. Do not request, provision or use an OpenAI API key for
this development goal, and do not substitute direct OpenAI API requests.
The general authentication methods above are documentation findings, not
authorization to use a different route. Preserve subject isolation and qualify
the supported sign-in lifecycle before model execution.

The [current route review](../artifacts/research/2026-11-11/official-harness-signin/review.json)
identifies the official `exec --ignore-user-config` contract: it skips
`CODEX_HOME/config.toml` while native authentication still uses `CODEX_HOME`.
The original adapter supplied a fresh empty `CODEX_HOME`, hiding the ordinary
sign-in. The explicit native declaration now separates authentication storage
from subject grants without copying credentials or exporting tokens. Six
[native controls](../artifacts/research/2026-11-11/native-signin-controller/review.json)
qualified synthetic file-store admission, subject read/write denial, positive
and unchanged grading, truncated transport, wrong-mode rejection and context
detectors. Keyring and auto-store declarations have unit coverage, without a
real keyring/account qualification.

Native execution exposed a separate global-instruction channel: the pinned
CLI still reads `CODEX_HOME/AGENTS.md` despite `--ignore-user-config` and a zero
project-document byte limit. Admission now rejects either global instruction
filename before and after status without reading or changing it. A separate
deliberate config-leak control retains the triggering payloads and verifies
that the detector fires. Shared-profile concurrency, refresh and all remaining
context channels still need qualification. Do not adopt copied-cache CI or
external-token modes as shortcuts; the public launch guard stays closed.

Integrate an explicitly selected authentication method with the frozen
controller protocol and its reporting path. Qualify credential cleanup,
refresh behavior and isolation using model-free controls before a live
transport request. Then verify provider-resolved model identity and complete
subject-to-native-grader execution. Record setup errors separately from task
failures; a successful login-status command is not a scored benchmark result.

## Native refresh and interruption controls

Four additional [lifecycle controls](../artifacts/research/2026-11-11/native-signin-lifecycle/review.json)
use the official CLI with synthetic file-store credentials and local endpoints:

| Control | Verified result |
| --- | --- |
| Expired token | One native refresh persisted rotated credentials; the unchanged task scored zero. |
| Generation changes during refresh | Native persistence preserved the newer injected generation; the unchanged task scored zero. |
| Authority rejects refresh | The attempt remained unscored and the credential file stayed unchanged. |
| Timeout during refresh | The simulated authority rotated before its delayed reply; the native cache stayed unchanged, the attempt was unscored and owned process cleanup reached zero. |

The pinned implementation locks credential read/modify/write and checks the
expected access and refresh generations before saving. The runtime conflict
control confirms preservation of the injected newer generation. It does not
establish arbitrary concurrent-client safety or qualify a real account/keyring.
An unchanged local cache after interruption does not prove that the authority's
grant is unchanged. Do not treat cleanup or a cached login-status response as
proof that a timed-out authentication exchange can safely be retried.

The official `account/read` protocol can request a proactive refresh. Source
inspection and native probes show that its handler discards the refresh outcome before building
the account response. A successful account response alone is therefore
insufficient refresh evidence. This remains a source finding, not a qualified
RPC preflight. Keep the launch guard closed while establishing explicit official
preflight, failure and cancellation semantics without exporting credentials.

The first experimental refresh fixture did not trigger refresh because a valid
JWT expiry takes precedence over an old `last_refresh`. Its outer exit also
incorrectly used an earlier verdict after the final summary failed. That attempt
is retained and invalidated. The fixture now expires only synthetic JWTs, exits
from its final verdict, and cross-checks summary, process and qualification
outcomes. That lifecycle round changed no production code or real credential.

## Model-free metadata entrypoint

The subsequent [metadata-readiness implementation](../artifacts/research/2026-11-11/native-account-readiness/review.json)
adds `tools/check_native_trial_readiness.py`. It combines native account data,
an authenticated quota read and complete model-list pagination; it confirms the
same account after the reads. Explicit ordinary-usage permission and support for
the exact model and reasoning effort are required. Raw account responses remain
in memory, and no model thread, command execution or token export is requested.
See [usage and result semantics](native-benchmark-controller.md#account-quota-and-model-metadata).

That round passed all 11 native cases, 470 focused tests and 3,048 full-suite tests; 18
full-suite checks were skipped and are not claimed as passing. At that checkpoint,
the stable release API and annotated tag resolved CLI 0.167.1 to the source commit pinned by
the admitted binary manifest. This establishes those identities, not a signed-tag
or reproducible-build claim.

Native probes confirmed that transient refresh failure can return a ChatGPT
account with unchanged credentials, while permanent rejection can return a null
account without a protocol error. The entrypoint checks the account data and
quota outcome rather than treating RPC success as permission. It does not claim
that a refresh succeeded or that future requests are guaranteed.

App-server reads the selected native profile configuration; isolated exec skips
user configuration. Their concordance remains unqualified. Metadata eligibility
is a necessary component check, and the public model-launch refusal remains in
place while that configuration and the remaining full boundary are qualified.

Final path-contract review reproduced a forward-slash UNC acceptance in the
local-home parser. Canonical Windows drive classification now rejects network
and device namespaces before profile I/O, with four regression forms covered.

## Configuration and catalog provenance

The [configuration review](../artifacts/research/2026-11-11/native-configuration-readiness/review.json)
retains the next implementation and its native controls. The checker now reads
effective configuration and origin versions before and after metadata requests.
Invalid or changed results and explicit local catalog overrides withhold
eligibility. Configuration, origin paths and instructions remain in memory.
Equal snapshots do not freeze a profile or prove isolated-subject concordance;
a native catalog may be bundled or cached and is not live entitlement evidence.

The native protocol omits `layers` when `includeLayers` is false. The first
implementation incorrectly required an explicit null and failed its native
positive control. It now handles both representations. The failed attempt is
retained, and regression tests exercise native omission as well as origin,
instruction and typed-value changes. Generated declarations alone do not prove
the wire representation. Agent instructions now require focused and native
controls before a full suite to avoid repeating this verification mistake.

Two additional scripted exec controls used a valid profile catalog marker.
Isolated exec ignored it; deliberately removing `--ignore-user-config` exposed
it to the owned peer and withheld the score. The unchanged positive task still
scored zero. An earlier invalid-catalog fixture stopped at native login-status
admission and did not test exec; it was retained rather than bypassing admission.
These controls used generated credentials and an owned peer, with no real model,
account, keyring or TLS route qualified.

The new implementation passed 494 focused tests, 13 native metadata cases and
3,072 full-suite tests with 18 skips; both catalog-isolation controls also passed.
The public model-launch guard remains closed. Shared-profile/cache behavior,
interrupted-account recovery, model identity, fresh setup and complete launch
admission still require qualification before real external comparisons.

## Current catalog and profile findings: 13 November 2026

Official release and package metadata identified stable CLI 0.167.2. Its admitted
package, exact vendor catalog and native recovery controls are recorded in the
[current review](../artifacts/research/2026-11-13/native-vendor-catalog/review.json).
The implementation passed 529 focused tests, typing across 324 Python files,
13 native metadata cases, three maintained cache controls and 3,107 full-suite
tests with 18 skips. Nine native bootstrap controls include missing-catalog recovery.

A matching model cache supplied marked instructions when refresh failed, even
with isolated user configuration. Both runners now bind the subject to the same
unmodified vendor catalog and verify executable/catalog identities before and
after execution. The deliberate option-removal control detects the old channel.
This freezes vendor metadata equally across conditions; it is not a skill change
or proof of model entitlement. Metadata probes retain their distinct profile contract.

The actual sign-in home contains global instructions. Discovery checked presence
only; neither credentials nor instruction content was read or changed. Official
source and an owned late-file control confirm that the native global provider
loads these independently of the project-document budget. No supported opt-out
was established. Retain the rejection and the closed launch guard. Never move
user instructions, copy authentication storage or set empty base instructions as
a workaround. Shared-profile stability and a supported real-account isolation
route remain open; no real model was invoked in this round.

The [supported-isolation recheck](../artifacts/research/2026-11-13/native-profile-isolation/review.json)
confirmed that 0.167.2 remains the current stable release. The
[official guidance documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
was read through a validated canonical capture after its former URL redirected.
It documents global guidance and separate homes. Reviewed authentication and
instruction constructors still use the same home, and thread instructions do
not replace the global contribution. No supported unattended isolation route was
established in those paths; this is not a proof that none can exist. The real
profile remains untouched and the launch refusal remains closed.

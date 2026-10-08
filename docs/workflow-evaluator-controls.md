# Workflow evaluator controls

Seven independently defined workflow controls expose a gap in native security
grading. On October 8, 2026, actionlint **1.7.12** and offline zizmor **1.30.1**
both missed attacker-controlled PR-title data passed through an environment
variable into Bash `eval`. A clean native result cannot establish workflow safety.

These are selected capability probes, not skill scores, model comparisons or
estimates of real-world detection rates. No workflow code or AI agent was run.
The [derived report](../artifacts/research/2026-10-08/workflow-evaluator-controls/report.json)
keeps every diagnostic and explicitly rejects both tools as complete security
graders for this control set.

| Control | Independent expectation | actionlint | zizmor, offline |
| --- | --- | --- | --- |
| Direct PR-title interpolation in Bash | Injection hazard | Detected | Detected |
| Quoted Bash variable used as print data | Safe for this sink | No diagnostics | No diagnostics |
| Direct PR-title interpolation in PowerShell | Injection hazard | Detected | Detected |
| PowerShell environment variable used as print data | Safe for this sink | No diagnostics | No diagnostics |
| Environment variable passed to Bash `eval` | Injection hazard | Missed | Missed |
| Checkout referenced by a release tag | Violates immutable-pin rule | Missed | Detected |
| Checkout referenced by the qualified full commit | Satisfies this pin rule | No diagnostics | No diagnostics |

The table describes revision 2. Revision 1 omitted job display names, producing
an informational zizmor finding in all seven controls. Both revisions and all
28 native invocations remain in the
[exact evidence bundle](../artifacts/research/2026-10-08/workflow-evaluator-controls/bundle.json).
The validator checks that revision 2 changed only job names and retained every
security expectation. An unrelated finding does not count as detecting a hazard.

## Evidence and reproduction

```bash
python tools/report_workflow_evaluator_controls.py --check --json
```

This command rechecks capture hashes, input bindings, command flags, output
locations, exit codes, complete control inventory and the derived report. It
does not install or execute native tools. Tests reject dropped controls,
reclassified hazards, ignored findings, altered flags, foreign diagnostic
locations, fabricated qualification claims and evidence tampering.

For a new native run, first review and qualify the requested platform's exact
release assets. The bundle retains native version/help output, archive and
executable digests, publisher release metadata and complete MIT licenses for
[actionlint](https://github.com/rhysd/actionlint/releases/tag/v1.7.12) and
[zizmor](https://github.com/zizmorcore/zizmor/releases/tag/v1.30.1). The recorded
binaries are Windows AMD64; do not reuse their digests for another platform.
Materialize the captured workflow text in a private temporary directory, never
under `.github/workflows`, and retain new outputs separately. Preserve the
original captures. No binary is bundled or automatically downloaded by CI.

Zizmor ran offline with no configuration, ignores or severity filtering and with
the auditor persona. Remote audits were unavailable in that mode. Actionlint's
optional ShellCheck and Pyflakes integrations were not provisioned. Hashes bind
recorded bytes; they do not independently witness execution or authenticate a
binary signature. Independence and execution-scope declarations remain assertions.

## Research implications

The [source review](../artifacts/research/2026-10-08/workflow-evaluator-controls/source-review.json)
records current upstream checks and partial, file-level review of two skill
packages. Remaining resources stay pending. Mirrors remain unchanged and these
controls add no coding-agent runtime passes.

Future workflow-security grading needs independently authored data-flow
expectations alongside native checks. The current
[GitHub secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use)
supports keeping untrusted data out of script generation; subsequent interpreters
and AI prompts remain separate trust boundaries. The
[privileged PR-event guide](https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target)
also requires examining event admission, effective permissions and every executed
input. Its rollout dates and default cache behavior must be checked when used.
Neither a SHA pin nor a successful linter establishes the whole trust boundary.

The initial staged native secret scan flagged four capture-digest fields. Their
values match the SHA-256 of the original public-source responses; the
[context proof](../artifacts/research/2026-10-08/workflow-evaluator-controls/capture-context-proof.json)
records that verification. The metadata now consistently calls them
`capture_sha256`. No digest, benchmark outcome, detector rule or exclusion changed.
Historical native scan findings remain separate and unresolved.

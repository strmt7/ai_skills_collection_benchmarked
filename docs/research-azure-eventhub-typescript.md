# Event Hubs TypeScript checkpoint callbacks

The pinned [Microsoft skill](../included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-ts/SKILL.md)
says checkpointing provides exactly-once processing. Its error-handling example
also catches processing failures inside `processEvents`. In a controlled
simulation, the extracted original callback swallowed a failed event and then
checkpointed a later successful batch. The simulation invokes callbacks
directly; it does not establish that a live service will deliver those batches
in that sequence.

The [maintained callback](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-ts-checkpoint/SKILL.md)
propagates handler and checkpoint errors, does not checkpoint empty batches,
and checkpoints after all handlers in a nonempty batch finish. It does not make
application side effects exactly once. The
[SDK handler documentation](https://learn.microsoft.com/en-us/javascript/api/%40azure/event-hubs/subscriptioneventhandlers?view=azure-node-latest)
describes its callback error and partition lifecycle; the
[Event Hubs reliability guidance](https://learn.microsoft.com/en-us/azure/reliability/reliability-event-hubs)
explains that events can be processed more than once after recovery.

[Offline controls](../artifacts/repaired-skill-readiness/azure-eventhub-ts-checkpoint-v1/qualification.json)
type-check against the pinned SDK and simulate callbacks on Windows and Linux.
They do not exercise the Azure service, live retries, checkpoint storage,
partition ownership, production recovery, or an AI agent.

To repeat the component controls, use Python 3.13, Node.js 24 and its bundled
npm CLI. The runner installs the locked test packages in a temporary directory
and writes command output and a result to a new output directory:

```sh
python artifacts/repaired-skill-readiness/azure-eventhub-ts-checkpoint-v1/reproduce.py \
  --node /path/to/node --npm-cli /path/to/npm-cli.js --output /new/output-directory
```

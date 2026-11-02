---
name: azure-eventhub-ts-checkpoint
description: Process Event Hubs batches in TypeScript and checkpoint after successful application handling.
license: MIT
---

# Event Hubs checkpointing in TypeScript

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow the repository-root
`docs/agent-tools.md` and its linked skills, retaining the required receipts.

The [original skill](provenance/original.SKILL.md) says checkpointing provides
exactly-once processing and catches an application processing failure without
stopping the callback. A later successful batch can then checkpoint beyond the
failed event. Checkpointing records progress, not exactly-once side effects.

Use the [typed callback example](examples/checkpoint-consumer.ts) with an
`EventHubConsumerClient` configured with the application's checkpoint store:

```typescript
const subscription = consumer.subscribe(
  checkpointHandlers(handleEvent, onSubscriptionError)
);
```

Import `checkpointHandlers` from the example. Supply `handleEvent` to perform
and await the application's durable work, and `onSubscriptionError` to report
and handle errors according to the application's recovery policy. The callback
handles a batch sequentially, checkpoints its final event only after every
handler succeeds, ignores empty batches, and propagates handler and checkpoint
failures. Choose checkpoint frequency deliberately; larger intervals reduce
checkpoint traffic but can replay more work.

Processing may be repeated after a failure, a restart, or checkpoint failure.
Use idempotent effects or a suitable durable deduplication design. A successful
external side effect and a checkpoint are not automatically atomic. Decide how
to handle poison events, recovery, partition ownership, shutdown and backpressure
for the application. See Microsoft's
[subscription handler documentation](https://learn.microsoft.com/en-us/javascript/api/%40azure/event-hubs/subscriptioneventhandlers?view=azure-node-latest)
for the SDK error and partition lifecycle.

The offline controls compile against the pinned SDK type definitions and invoke
callbacks with simulated events and contexts. They do not connect to Azure,
establish service delivery or recovery behavior, review the entire original
skill, or measure agent performance.

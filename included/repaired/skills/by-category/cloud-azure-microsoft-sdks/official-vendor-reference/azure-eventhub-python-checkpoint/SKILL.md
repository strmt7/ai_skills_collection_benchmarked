---
name: azure-eventhub-python-checkpoint
description: Receive Azure Event Hubs events with a synchronous Python checkpoint store and checkpoint after application handling.
license: MIT
---

# Synchronous Event Hubs checkpointing in Python

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow the repository-root
`docs/agent-tools.md` and its linked skills, retaining the required receipts.

The [original skill](provenance/original.SKILL.md) installs the asynchronous
checkpoint-store package but imports the synchronous store. For a synchronous
consumer, install `azure-eventhub`, `azure-identity`, and
`azure-eventhub-checkpointstoreblob`; the asynchronous store has a separate
package and API. Select versions compatible with the application. The
[test snapshot](examples/requirements-test.txt) records one tested Python 3.13
environment, not a requirement for every application.

The [example](examples/checkpoint_consumer.py) provides
`open_checkpoint_consumer` and `checkpoint_after_handling`. Open the consumer
with the caller's credential, pass the real event handler to the callback
builder, then pass that callback to the SDK's `consumer.receive` method. The
callback ignores a no-event timeout, calls the handler, then checkpoints only
after the handler returns. The caller owns the credential and chooses the
consumer group, starting position, storage account, container, error handling,
and shutdown strategy. `receive` blocks and accesses the selected Azure
resources; the offline controls replace that call. A checkpoint per event is
simple but can be costly; choose a cadence suitable for the workload without
advancing past unfinished work.

Checkpointing alone does not guarantee exactly-once effects. Events may be
replayed after failures, including after work succeeds but before a checkpoint
is saved. Make the actual handler idempotent or implement suitable deduplication.
If `max_wait_time` is set, [the SDK may call the handler with no event](https://learn.microsoft.com/en-us/python/api/azure-eventhub/azure.eventhub.eventhubconsumerclient?view=azure-python);
the example does not checkpoint that callback. A persisted checkpoint takes
precedence over the chosen initial position on recovery. Verify lifecycle,
partition ownership, retry and recovery behavior for the real application.

This is a narrow synchronous checkpointing repair. The controls use real SDK
objects and simulated callbacks without Azure service access; they do not
establish service behavior, review the complete original skill, or measure
coding-agent performance.

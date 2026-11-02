---
name: azure-eventhub-rust-batching
description: Send Azure Event Hubs batches in Rust while handling rejected events and checking compatible SDK versions.
license: MIT
---

# Event Hubs batching in Rust

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow the repository-root
`docs/agent-tools.md` and its linked skills, retaining the required receipts.

The [original skill](provenance/original.SKILL.md) ignores the boolean returned
by `try_add_event_data`. A successful `Result` can still contain `false` when
an event does not fit. The [example](examples/src/main.rs) sends a nonempty
batch, retries the rejected event in a new batch, and reports an event that
cannot fit in an empty batch. Earlier batches may already have been sent if a
later event or send fails; design retry and idempotency for the application.

On 2 November 2026, resolving the then-current stable
`azure_messaging_eventhubs` 0.16.0 with `azure_identity` 1.0.0 failed because
their `azure_core` requirements could not be unified. The [example project](examples/Cargo.toml)
and [lock](examples/Cargo.lock) instead record the locally compiled pair 0.15.0
and 1.0.0. Check current crate compatibility and the application's existing
dependency graph; do not downgrade an existing application solely to match this
example. The version choice is an observed compatibility boundary, not a claim
that every newer combination fails.

From the example directory, `cargo check --locked` compiles the example without
running it. Running it opens an Azure connection and sends events. It requires
an existing Event Hub, an authorized developer identity, and
`EVENT_HUB_FULLY_QUALIFIED_NAMESPACE` and `EVENT_HUB_NAME`. Adapt credentials,
payloads, retry policy, and resource lifecycle to the real task. The SDK's
[batch API](https://docs.rs/azure_messaging_eventhubs/0.15.0/azure_messaging_eventhubs/struct.EventDataBatch.html)
documents the rejection result.

This is a narrow, compile-tested producer example. It does not demonstrate
service behavior, review the whole source skill, or measure agent performance.
A deeply nested Windows build directory failed in a native dependency on the
tested host; see the [qualification review](../../../../../../../docs/research-azure-eventhub-rust.md)
for the observed path limitation and control scope.

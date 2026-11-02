# Azure Event Hubs skill family

This review covers selected examples in the five pinned Microsoft Event Hubs
skills. It does not review every example or establish a coding-agent advantage.
No control connected to an Azure service.

- **.NET:** The source's batch example assigns to a C# `using` variable. With
  .NET SDK 10.0.403 and `Azure.Messaging.EventHubs` 5.12.2, the extracted example
  fails with CS1656. A [narrow batching repair](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-dotnet-batching/SKILL.md)
  and its locked project compile in the same control. Compilation does not test
  batching against Event Hubs.
- **Python:** The installation block installs the asynchronous checkpoint-store
  package, while the production example imports the synchronous store. In a
  clean Python 3.13 environment with `azure-eventhub` 5.15.1, `azure-identity`
  1.27.0 and `azure-eventhub-checkpointstoreblob-aio` 1.2.0, that synchronous
  import failed. Adding `azure-eventhub-checkpointstoreblob` 1.2.0 made it
  succeed. [Microsoft's synchronous package documentation](https://learn.microsoft.com/en-us/python/api/overview/azure/eventhub-checkpointstoreblob-readme?view=azure-python)
  distinguishes the two packages. Select the package and credential/client
  types appropriate to the application's synchronous or asynchronous path.
- **Rust:** On 2 November 2026, the source's unpinned `cargo add` resolved
  `azure_messaging_eventhubs` 0.16.0 and `azure_identity` 1.0.0, but Cargo could
  not resolve their `azure_core` requirements. A separately locked control using
  Event Hubs 0.15.0 and identity 1.0.0 compiled the selected original producer
  snippets. This is a tested combination, not a blanket recommendation to
  downgrade existing projects or a guarantee about future package releases.
- **TypeScript:** The source says checkpointing provides exactly-once
  processing. [Microsoft's reliability guidance](https://learn.microsoft.com/en-us/azure/reliability/reliability-event-hubs)
  states that events can be processed more than once when a processor resumes
  from a checkpoint. Applications need an appropriate idempotency or deduplication
  design; checkpointing alone does not supply that guarantee.
- **Java:** The batch example ignores the second `tryAdd` result after creating
  a new batch. If adapted to events too large for an empty batch, the rejected
  event can be silently omitted. [The Java API](https://learn.microsoft.com/en-us/java/api/com.azure.messaging.eventhubs.eventdatabatch?view=azure-java-stable)
  describes `tryAdd` returning false when an event does not fit. The source's
  fixed small-event example was not executed against the service.

The five source files at the pinned commit differ from those observed at
Microsoft's default-branch commit `3f5b461b2314e01c400564051e92469114c5b68f`.
The selected problematic statements were still present in that observation;
this is not a complete upstream review. Original mirrors remain unchanged.
The [qualification record](../artifacts/repaired-skill-readiness/azure-eventhub-dotnet-batching-v1/qualification.json)
and local native package, build and Crawl4AI receipts delimit the observations.

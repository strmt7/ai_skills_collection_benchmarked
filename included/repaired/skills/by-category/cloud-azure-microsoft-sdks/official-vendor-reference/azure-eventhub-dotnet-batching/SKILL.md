---
name: azure-eventhub-dotnet-batching
description: Send Azure Event Hubs events in bounded .NET batches and handle events that cannot fit in an empty batch.
license: MIT
---

# Azure Event Hubs batching for .NET

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow the repository-root
`docs/agent-tools.md` and its linked skills, retaining the required receipts.

The [source skill](provenance/original.SKILL.md) reassigns a C# `using`
variable in its batching example; the tested example fails to compile. The
[maintained example](examples/Program.cs) creates and disposes one batch per
iteration, advances only for accepted events, and reports an event that cannot
fit in an empty batch. Send only after events have been accepted. Do not silently
ignore the result of `TryAdd`.

The [project](examples/Example.csproj) and [lock file](examples/packages.lock.json)
record the .NET 10 and NuGet versions used for the compile control. From the
example directory, run `dotnet restore --locked-mode` and then
`dotnet build --no-restore`. Adapt the framework and package versions to the
actual project and verify them there. The example is not run by the controls;
running it requires an existing Event Hub, an authorized Azure identity, and
`EVENT_HUB_FULLY_QUALIFIED_NAMESPACE` and `EVENT_HUB_NAME` environment
variables. It sends events and may incur service costs.

Checkpointing records progress; it does not by itself guarantee exactly-once
processing. Plan for replay and idempotent effects according to
[Microsoft's reliability guidance](https://learn.microsoft.com/en-us/azure/reliability/reliability-event-hubs).
Check the actual application's ordering, retry, partition and recovery needs.

This is a narrow batching repair, not a complete review of the source skill,
proof of service behavior, or an agent-effectiveness benchmark.

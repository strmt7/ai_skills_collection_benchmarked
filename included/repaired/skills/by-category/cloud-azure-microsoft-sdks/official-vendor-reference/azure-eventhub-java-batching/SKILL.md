---
name: azure-eventhub-java-batching
description: Send Azure Event Hubs events in Java batches without silently dropping rejected events.
license: MIT
---

# Event Hubs batching in Java

Apply Caveman for every task, CocoIndex Code before broad repository navigation,
and Crawl4AI for web-page research. Follow the repository-root
`docs/agent-tools.md` and its linked skills, retaining the required receipts.

The [original skill](provenance/original.SKILL.md) does not check the second
`tryAdd` result after creating a batch. The [example](examples/src/main/java/example/EventBatchSender.java)
checks it, reports an event that cannot fit in an empty batch, and avoids
sending an empty batch. The SDK can also throw an exception for an individually
oversized payload; the example lets it propagate. Earlier batches may have
been sent before an error, and a pending batch may remain unsent. Design retries
and idempotent processing for the real application.

Given an existing `EventHubProducerClient` and `Iterable<EventData>`, call
`EventBatchSender.send(events, producer)`. The caller owns and closes the
producer. The overload accepting batch creation and sending functions allows
offline testing. Select credentials, partition settings and error handling for
the actual application; calling this method sends events to Azure.

The [Maven project](examples/pom.xml) records the tested SDK and test versions;
run `mvn test` with Maven 3.10.0 and a suitable JDK. Its
[dependency snapshot](examples/dependency-tree.json) records the resolved
application and test graph, not a universal lock for other projects. Tests use
real SDK batch objects with a test-only package-private constructor and a
simulated sender. They do not contact Azure, establish delivery semantics, or
measure coding-agent performance. See the [SDK API](https://learn.microsoft.com/en-us/java/api/com.azure.messaging.eventhubs.eventdatabatch?view=azure-java-stable)
and the repository's [qualification review](../../../../../../../docs/research-azure-eventhub-java.md).

# Java Event Hubs batching

The [pinned Java skill](../included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-java/SKILL.md)
does not inspect the second `tryAdd` result after opening a new batch. The
[SDK documentation](https://learn.microsoft.com/en-us/java/api/com.azure.messaging.eventhubs.eventdatabatch?view=azure-java-stable)
describes `false` as a rejected addition. In an offline control using SDK 5.21.7,
an adapted version of that retry pattern omitted an event that the real SDK
rejected even from an empty batch.

The [maintained example](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-java-batching/SKILL.md)
checks both attempts and reports the failure. Separate controls cover empty
input, rollover ordering, failures during creation or sending, and a payload
that makes the SDK throw `AmqpException` rather than return `false`. The tests
construct real SDK batches with a test-only package-private constructor and
replace the sender; the production example uses the public producer API.

The tests do not connect to Event Hubs or establish service delivery, retry or
partition behavior. The [qualification record](../artifacts/repaired-skill-readiness/azure-eventhub-java-batching-v1/qualification.json)
and retained Maven streams describe the exact versions and scope. The original
mirror is unchanged, and these component controls do not measure coding-agent
performance.

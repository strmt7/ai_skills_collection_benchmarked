# Python Event Hubs checkpointing

The [pinned skill](../included/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-py/SKILL.md)
installs the asynchronous blob checkpoint package but imports the synchronous
store. The [family review](research-azure-event-hubs.md) records the isolated
import failure and the corrected import. Microsoft documents the
[synchronous package](https://learn.microsoft.com/en-us/python/api/overview/azure/eventhub-checkpointstoreblob-readme?view=azure-python)
separately from the asynchronous one.

The [maintained synchronous example](../included/repaired/skills/by-category/cloud-azure-microsoft-sdks/official-vendor-reference/azure-eventhub-python-checkpoint/SKILL.md)
keeps the caller in control of the credential, receiver and application
handler. It checkpoints after the handler returns and ignores an empty timeout
callback. The [consumer API](https://learn.microsoft.com/en-us/python/api/azure-eventhub/azure.eventhub.eventhubconsumerclient?view=azure-python)
documents that a timed receive can provide `None` and that stored checkpoints
take precedence over the supplied starting position.

Six local controls use real SDK client and checkpoint-store construction with
simulated callbacks and a patched socket `connect` method. They check ordering,
no-event handling, exception propagation and cleanup, including a failed
consumer construction. The controls do not call Azure or test the SDK's live
delivery, partition ownership, retries, or throughput. Checkpointing does not
alone guarantee exactly-once effects; applications must account for replay.
The original mirror is unchanged. No coding-agent performance claim follows
from these component tests.

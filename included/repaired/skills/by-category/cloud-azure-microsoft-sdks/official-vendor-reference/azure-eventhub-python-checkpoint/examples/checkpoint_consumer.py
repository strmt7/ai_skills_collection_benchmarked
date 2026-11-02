"""A synchronous Event Hubs receiver that checkpoints after a caller's handler."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager

from azure.core.credentials import TokenCredential
from azure.eventhub import EventData, EventHubConsumerClient, PartitionContext
from azure.eventhub.extensions.checkpointstoreblob import BlobCheckpointStore


def checkpoint_after_handling(
    handler: Callable[[EventData], None],
) -> Callable[[PartitionContext, EventData | None], None]:
    """Build a callback that checkpoints after the application's handler returns."""

    def on_event(context: PartitionContext, event: EventData | None) -> None:
        if event is None:
            return
        handler(event)
        context.update_checkpoint(event)

    return on_event


@contextmanager
def open_checkpoint_consumer(
    *,
    credential: TokenCredential,
    namespace: str,
    eventhub_name: str,
    consumer_group: str,
    blob_account_url: str,
    container_name: str,
) -> Iterator[EventHubConsumerClient]:
    """Open a consumer and store; the caller owns the credential and receive loop."""

    with (
        BlobCheckpointStore(
            blob_account_url=blob_account_url, container_name=container_name, credential=credential
        ) as store,
        EventHubConsumerClient(
            fully_qualified_namespace=namespace,
            eventhub_name=eventhub_name,
            consumer_group=consumer_group,
            credential=credential,
            checkpoint_store=store,
        ) as consumer,
    ):
        yield consumer

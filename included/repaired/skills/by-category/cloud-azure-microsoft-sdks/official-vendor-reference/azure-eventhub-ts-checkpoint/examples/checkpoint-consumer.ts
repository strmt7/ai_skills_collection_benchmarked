import type { PartitionContext, ReceivedEventData, SubscriptionEventHandlers } from "@azure/event-hubs";

type HandleEvent = (event: ReceivedEventData, context: PartitionContext) => Promise<void>;

export function checkpointHandlers(
  handleEvent: HandleEvent,
  processError: SubscriptionEventHandlers["processError"],
): SubscriptionEventHandlers {
  return {
    async processEvents(events, context) {
      for (const event of events) {
        await handleEvent(event, context);
      }
      const lastEvent = events.at(-1);
      if (lastEvent !== undefined) {
        await context.updateCheckpoint(lastEvent);
      }
    },
    processError,
  };
}

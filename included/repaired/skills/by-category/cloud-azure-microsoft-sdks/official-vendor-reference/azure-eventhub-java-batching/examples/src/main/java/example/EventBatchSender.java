package example;

import com.azure.messaging.eventhubs.EventData;
import com.azure.messaging.eventhubs.EventDataBatch;
import com.azure.messaging.eventhubs.EventHubProducerClient;
import java.util.Iterator;
import java.util.function.Consumer;
import java.util.function.Supplier;

public final class EventBatchSender {
  private EventBatchSender() {}

  public static void send(Iterable<EventData> events, EventHubProducerClient producer) {
    send(events, producer::createBatch, producer::send);
  }

  public static void send(
      Iterable<EventData> events,
      Supplier<EventDataBatch> createBatch,
      Consumer<EventDataBatch> sendBatch) {
    Iterator<EventData> iterator = events.iterator();
    if (!iterator.hasNext()) {
      return;
    }
    EventDataBatch batch = createBatch.get();
    while (iterator.hasNext()) {
      EventData event = iterator.next();
      if (!batch.tryAdd(event)) {
        if (batch.getCount() == 0) {
          throw new IllegalArgumentException("Event is too large for an empty batch");
        }
        sendBatch.accept(batch);
        batch = createBatch.get();
        if (!batch.tryAdd(event)) {
          throw new IllegalArgumentException("Event is too large for an empty batch");
        }
      }
    }
    if (batch.getCount() > 0) {
      sendBatch.accept(batch);
    }
  }
}

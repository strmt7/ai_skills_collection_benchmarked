package com.azure.messaging.eventhubs;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.fail;

import com.azure.core.amqp.exception.AmqpErrorContext;
import com.azure.core.amqp.exception.AmqpException;
import example.EventBatchSender;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;

class EventBatchSenderTest {
  private static EventDataBatch batch() {
    return new EventDataBatch(
        256,
        null,
        null,
        () -> new AmqpErrorContext("example"),
        EventHubsProducerInstrumentation.NOOP_INSTANCE);
  }

  private static EventData eventRejectedByEmptyBatch() {
    for (int size = 0; size <= 256; size++) {
      EventData event = new EventData(new byte[size]);
      try {
        if (!batch().tryAdd(event)) {
          return event;
        }
      } catch (AmqpException tooLarge) {
        break;
      }
    }
    throw new AssertionError("No empty-batch false result found");
  }

  @Test
  void emptyInputDoesNotCreateOrSendBatch() {
    AtomicInteger created = new AtomicInteger();
    EventBatchSender.send(
        List.of(),
        () -> {
          created.incrementAndGet();
          return batch();
        },
        b -> fail("unexpected send"));
    assertEquals(0, created.get());
  }

  @Test
  void singleEventIsSentOnce() {
    EventData event = new EventData("small");
    List<EventData> sent = new ArrayList<>();
    EventBatchSender.send(
        List.of(event), EventBatchSenderTest::batch, b -> sent.addAll(b.getEvents()));
    assertEquals(List.of(event), sent);
  }

  @Test
  void batchCreationFailurePropagatesBeforeSending() {
    IllegalStateException failure = new IllegalStateException("create failed");
    assertSame(
        failure,
        assertThrows(
            IllegalStateException.class,
            () ->
                EventBatchSender.send(
                    List.of(new EventData("small")),
                    () -> {
                      throw failure;
                    },
                    b -> fail("unexpected send"))));
  }

  @Test
  void rolloverPreservesEveryEventInOrder() {
    List<EventData> events = new ArrayList<>();
    for (int i = 0; i < 8; i++) {
      events.add(new EventData(new byte[45]));
    }
    List<EventData> sent = new ArrayList<>();
    AtomicInteger batches = new AtomicInteger();
    EventBatchSender.send(
        events,
        EventBatchSenderTest::batch,
        b -> {
          batches.incrementAndGet();
          sent.addAll(b.getEvents());
        });
    assertTrue(batches.get() > 1);
    assertEquals(events, sent);
  }

  @Test
  void oversizedFirstEventIsReportedWithoutSendingEmptyBatch() {
    List<EventDataBatch> sent = new ArrayList<>();
    assertThrows(
        IllegalArgumentException.class,
        () ->
            EventBatchSender.send(
                List.of(eventRejectedByEmptyBatch()), EventBatchSenderTest::batch, sent::add));
    assertTrue(sent.isEmpty());
  }

  @Test
  void oversizedLaterEventIsReportedAfterPriorBatchIsSent() {
    EventData first = new EventData("small");
    List<EventData> sent = new ArrayList<>();
    assertThrows(
        IllegalArgumentException.class,
        () ->
            EventBatchSender.send(
                List.of(first, eventRejectedByEmptyBatch()),
                EventBatchSenderTest::batch,
                b -> sent.addAll(b.getEvents())));
    assertEquals(List.of(first), sent);
  }

  @Test
  void sdkOversizeExceptionIsNotSilencedOrSent() {
    List<EventDataBatch> sent = new ArrayList<>();
    assertThrows(
        AmqpException.class,
        () ->
            EventBatchSender.send(
                List.of(new EventData(new byte[4096])), EventBatchSenderTest::batch, sent::add));
    assertTrue(sent.isEmpty());
  }

  @Test
  void originalRetryPatternOmitsRejectedEvent() {
    EventData first = new EventData("small");
    EventData rejected = eventRejectedByEmptyBatch();
    List<EventData> sent = new ArrayList<>();
    EventDataBatch current = batch();
    for (EventData event : List.of(first, rejected)) {
      if (!current.tryAdd(event)) {
        sent.addAll(current.getEvents());
        current = batch();
        current.tryAdd(event);
      }
    }
    if (current.getCount() > 0) {
      sent.addAll(current.getEvents());
    }
    assertEquals(List.of(first), sent);
  }

  @Test
  void sendFailureStopsProcessingAndPropagates() {
    List<EventData> events = new ArrayList<>();
    for (int i = 0; i < 8; i++) {
      events.add(new EventData(new byte[45]));
    }
    AtomicInteger created = new AtomicInteger();
    IllegalStateException failure = new IllegalStateException("send failed");
    assertSame(
        failure,
        assertThrows(
            IllegalStateException.class,
            () ->
                EventBatchSender.send(
                    events,
                    () -> {
                      created.incrementAndGet();
                      return batch();
                    },
                    b -> {
                      throw failure;
                    })));
    assertEquals(1, created.get());
  }
}
